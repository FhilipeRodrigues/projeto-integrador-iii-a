import contextlib
import io
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from scripts import gerar_certificados

RAIZ = Path(__file__).resolve().parent.parent


def _openssl():
    try:
        return gerar_certificados.localizar_openssl()
    except gerar_certificados.OpenSslAusente:
        return None


def _servir_uma_conexao(servidor_crt, servidor_key):
    """Sobe um servidor TLS que aceita uma conexão; devolve (porta, thread)."""
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto.load_cert_chain(servidor_crt, servidor_key)
    escuta = socket.socket()
    escuta.bind(("127.0.0.1", 0))
    escuta.listen(1)

    def atender():
        with escuta:
            conexao, _ = escuta.accept()
            with conexao:
                try:
                    with contexto.wrap_socket(conexao, server_side=True):
                        pass
                except (ssl.SSLError, OSError):
                    pass

    thread = threading.Thread(target=atender, daemon=True)
    thread.start()
    return escuta.getsockname()[1], thread


def _cliente_confiando_em(ca_crt):
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    contexto.minimum_version = ssl.TLSVersion.TLSv1_2
    contexto.verify_mode = ssl.CERT_REQUIRED
    contexto.check_hostname = True
    # A verificação estrita do Python 3.13+ é o que os certificados precisam atender.
    contexto.verify_flags |= ssl.VERIFY_X509_STRICT
    contexto.load_verify_locations(cafile=ca_crt)
    return contexto


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class CertificadosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.pasta.cleanup)
        cls.padrao = Path(cls.pasta.name) / "certs"
        cls.outra = Path(cls.pasta.name) / "outra"
        gerar_certificados.gerar_certificados(cls.padrao)
        gerar_certificados.gerar_certificados(cls.outra)
        cls.openssl = _openssl()

    def _openssl_run(self, *argumentos):
        return subprocess.run(
            [self.openssl, *argumentos], capture_output=True, text=True, check=False
        )

    def test_gerar_a_ca_e_o_certificado_do_servidor(self):
        for nome in gerar_certificados.ARQUIVOS:
            self.assertTrue((self.padrao / nome).is_file(), nome)
        nomes = sorted(p.name for p in self.padrao.iterdir())
        self.assertEqual(nomes, sorted(gerar_certificados.ARQUIVOS))

    @unittest.skipIf(sys.platform == "win32", "permissões POSIX não se aplicam no Windows")
    def test_as_chaves_privadas_so_o_dono_le(self):
        for nome in ("ca.key", "servidor.key"):
            self.assertEqual((self.padrao / nome).stat().st_mode & 0o077, 0, nome)

    def test_o_certificado_do_servidor_e_assinado_pela_ca_do_projeto(self):
        resultado = self._openssl_run(
            "verify", "-CAfile", str(self.padrao / "ca.crt"), str(self.padrao / "servidor.crt")
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    def test_o_certificado_vale_para_o_endereco_local(self):
        resultado = self._openssl_run(
            "x509", "-in", str(self.padrao / "servidor.crt"), "-noout", "-text"
        )
        self.assertIn("DNS:localhost", resultado.stdout)
        self.assertIn("IP Address:127.0.0.1", resultado.stdout)

    def test_os_certificados_atendem_a_verificacao_estrita_do_python(self):
        for nome_servidor in ("localhost", "127.0.0.1"):
            with self.subTest(servidor=nome_servidor):
                porta, thread = _servir_uma_conexao(
                    str(self.padrao / "servidor.crt"), str(self.padrao / "servidor.key")
                )
                contexto = _cliente_confiando_em(str(self.padrao / "ca.crt"))
                with socket.create_connection(("127.0.0.1", porta), timeout=5) as bruto:
                    with contexto.wrap_socket(bruto, server_hostname=nome_servidor) as seguro:
                        self.assertIsNotNone(seguro.version())
                thread.join(timeout=5)

    def test_erro_ao_gravar_remove_o_que_ja_foi_gravado(self):
        with tempfile.TemporaryDirectory() as pasta:
            self._gravar_com_falha(pasta)

    def _gravar_com_falha(self, pasta):
        destino = Path(pasta) / "certs"
        verdadeiro_move = shutil.move
        chamadas = []

        def move_falhando(origem, alvo):
            chamadas.append(alvo)
            if len(chamadas) == 3:
                raise OSError("disco cheio")
            return verdadeiro_move(origem, alvo)

        with mock.patch.object(gerar_certificados.shutil, "move", move_falhando):
            with self.assertRaises(OSError):
                gerar_certificados.gerar_certificados(destino)
        self.assertFalse(destino.exists())
        self.assertEqual(list(Path(pasta).iterdir()), [])

    def test_gerar_de_novo_em_outra_pasta_nao_e_aceito_pela_ca_da_pasta_padrao(self):
        for nome in gerar_certificados.ARQUIVOS:
            self.assertTrue((self.outra / nome).is_file(), nome)
        resultado = self._openssl_run(
            "verify", "-CAfile", str(self.padrao / "ca.crt"), str(self.outra / "servidor.crt")
        )
        self.assertNotEqual(resultado.returncode, 0)

        porta, thread = _servir_uma_conexao(
            str(self.outra / "servidor.crt"), str(self.outra / "servidor.key")
        )
        contexto = _cliente_confiando_em(str(self.padrao / "ca.crt"))
        with socket.create_connection(("127.0.0.1", porta), timeout=5) as bruto:
            with self.assertRaises(ssl.SSLCertVerificationError):
                contexto.wrap_socket(bruto, server_hostname="localhost")
        thread.join(timeout=5)


class ChavesForaDoGitTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("git"), "git não encontrado")
    def test_as_chaves_privadas_nao_vao_para_o_repositorio(self):
        for caminho in ("certs/ca.key", "certs/servidor.key"):
            with self.subTest(caminho=caminho):
                resultado = subprocess.run(
                    ["git", "check-ignore", caminho], cwd=RAIZ, capture_output=True, text=True
                )
                self.assertEqual(resultado.returncode, 0, f"{caminho} não está ignorado")


class SemOpensslTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.destino = Path(self.pasta.name) / "certs"
        sem_openssl = [
            mock.patch.object(gerar_certificados.shutil, "which", return_value=None),
            mock.patch.object(gerar_certificados, "CANDIDATOS_OPENSSL", ()),
        ]
        for patch in sem_openssl:
            patch.start()
            self.addCleanup(patch.stop)

    def test_falta_o_programa_que_gera_os_certificados(self):
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            codigo = gerar_certificados.main([str(self.destino)])
        self.assertEqual(codigo, 1)
        self.assertIn("openssl", erro.getvalue())
        self.assertIn("Git for Windows", erro.getvalue())
        self.assertFalse(self.destino.exists())
        self.assertEqual(list(Path(self.pasta.name).iterdir()), [])

    def test_falha_do_openssl_nao_deixa_arquivos(self):
        erro = io.StringIO()
        with mock.patch.object(
            gerar_certificados, "localizar_openssl", return_value="openssl"
        ), mock.patch.object(
            gerar_certificados, "_executar",
            side_effect=gerar_certificados.FalhaOpenSsl("x"),
        ), contextlib.redirect_stderr(erro):
            codigo = gerar_certificados.main([str(self.destino)])
        self.assertEqual(codigo, 1)
        self.assertFalse(self.destino.exists())
        self.assertEqual(list(Path(self.pasta.name).iterdir()), [])

    def test_a_funcao_levanta_erro_claro_sem_openssl(self):
        with self.assertRaises(gerar_certificados.OpenSslAusente):
            gerar_certificados.gerar_certificados(self.destino)


if __name__ == "__main__":
    unittest.main()
