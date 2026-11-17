import contextlib
import io
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from consulta import base, cliente, dominio, servidor
from scripts import gerar_certificados

RAIZ = Path(__file__).resolve().parent.parent


def _openssl():
    try:
        return gerar_certificados.localizar_openssl()
    except gerar_certificados.OpenSslAusente:
        return None


@contextlib.contextmanager
def servidor_no_ar(servidores, pasta_certs):
    """Sobe o servidor numa porta livre; devolve (servidor, linhas de log)."""
    linhas = []
    srv = servidor.Servidor(servidores, pasta_certs, "127.0.0.1", 0, log=linhas.append)
    srv.iniciar()
    fio = threading.Thread(target=srv.servir)
    fio.start()
    try:
        yield srv, linhas
    finally:
        srv.parar()
        fio.join(timeout=5)


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class CanalSeguroTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        raiz = Path(cls._tmp.name)
        cls.certs = gerar_certificados.gerar_certificados(raiz / "certs")
        cls.certs_de_outra_ca = gerar_certificados.gerar_certificados(raiz / "outra")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _cliente(self, srv, ca=None):
        return cliente.ClienteRede("127.0.0.1", srv.porta, ca or self.certs / "ca.crt")

    def test_O_cliente_obtem_a_lista_de_municipios_pelo_servidor(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            resposta = self._cliente(srv).consultar({"op": "municipios"})
        esperado = sorted({s["municipio"] for s in self.servidores}, key=dominio.normalizar)
        self.assertTrue(resposta["ok"])
        self.assertEqual(len(resposta["dados"]), 10)
        self.assertEqual(resposta["dados"], esperado)

    def test_A_comunicacao_e_cifrada_com_TLS(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, linhas):
            self._cliente(srv).consultar({"op": "municipios"})
            self.assertTrue(self._esperar(linhas))
        registro = linhas[0]
        self.assertRegex(registro, r"127\.0\.0\.1:\d+")
        self.assertRegex(registro, r"TLSv1\.[23]")
        self.assertIn("op=municipios", registro)

    def test_texto_puro_nao_e_atendido_pelo_canal(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, linhas):
            with socket.create_connection(("127.0.0.1", srv.porta), timeout=5) as bruto:
                bruto.sendall(b'{"op": "municipios"}\n')
                try:
                    recebido = bruto.recv(4096)
                except OSError:
                    recebido = b""
            self.assertNotIn(b"Anapolis", recebido)
            self.assertNotIn("Anápolis".encode(), recebido)
            self.assertTrue(self._esperar(linhas))
        self.assertIn("falha_de_conexao", linhas[0])

    def test_O_log_do_servidor_nao_mostra_dados_das_fichas(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, linhas):
            self._cliente(srv).consultar({"op": "municipios"})
            self.assertTrue(self._esperar(linhas))
        registro = "\n".join(linhas)
        for servidor_da_base in self.servidores:
            self.assertNotIn(servidor_da_base["nome"], registro)
            self.assertNotIn(str(servidor_da_base["ultima_remuneracao_centavos"]), registro)

    def test_O_cliente_recusa_um_servidor_com_certificado_de_outra_CA(self):
        with servidor_no_ar(self.servidores, self.certs_de_outra_ca) as (srv, _):
            with self.assertRaises(cliente.ErroDeRede) as contexto:
                self._cliente(srv).consultar({"op": "municipios"})
        self.assertIn("não é confiável", str(contexto.exception))

    def test_O_cliente_recusa_um_servidor_cujo_certificado_nao_vale_para_o_endereco(self):
        real = socket.create_connection

        def conectar_no_local(endereco, timeout=None):
            return real(("127.0.0.1", endereco[1]), timeout=timeout)

        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            externo = cliente.ClienteRede("outro.exemplo", srv.porta, self.certs / "ca.crt")
            with mock.patch("consulta.cliente.socket.create_connection", conectar_no_local):
                with self.assertRaises(cliente.ErroDeRede) as contexto:
                    externo.consultar({"op": "municipios"})
        self.assertIn("não corresponde ao endereço", str(contexto.exception))

    def test_O_servidor_esta_parado(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            porta = srv.porta
        parado = cliente.ClienteRede("127.0.0.1", porta, self.certs / "ca.crt")
        with self.assertRaises(cliente.ErroDeRede) as contexto:
            parado.consultar({"op": "municipios"})
        self.assertIn("Não foi possível conectar", str(contexto.exception))

    def test_cliente_sem_a_CA_informa_como_gerar(self):
        sem_ca = cliente.ClienteRede("127.0.0.1", 1, self.certs / "nao-existe.crt")
        with self.assertRaises(cliente.ErroDeRede) as contexto:
            sem_ca.consultar({"op": "municipios"})
        self.assertIn("gerar_certificados.py", str(contexto.exception))

    def test_CA_corrompida_vira_erro_de_rede_tratado(self):
        with tempfile.TemporaryDirectory() as pasta:
            lixo = Path(pasta) / "ca.crt"
            lixo.write_text("isto não é um certificado", encoding="utf-8")
            with self.assertRaises(cliente.ErroDeRede) as contexto:
                cliente.ClienteRede("127.0.0.1", 1, lixo).consultar({"op": "municipios"})
        self.assertIn("gerar_certificados.py", str(contexto.exception))

    def test_o_log_padrao_do_servidor_comeca_com_a_hora(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            servidor._registrar("127.0.0.1:1 TLSv1.3 op=municipios resultado=ok")
        self.assertRegex(saida.getvalue(), r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} 127\.0\.0\.1")

    def test_O_servidor_nao_inicia_sem_os_certificados(self):
        with tempfile.TemporaryDirectory() as vazia:
            with self.assertRaises(servidor.CertificadosAusentes) as contexto:
                servidor.Servidor(self.servidores, vazia, "127.0.0.1", 0)
            self.assertIn("gerar_certificados.py", str(contexto.exception))

            erro = io.StringIO()
            with contextlib.redirect_stderr(erro):
                codigo = servidor.main(["--certs", vazia, "--porta", "0"])
        self.assertEqual(codigo, 1)
        self.assertIn("gerar_certificados.py", erro.getvalue())

    @staticmethod
    def _esperar(linhas, segundos=5):
        """O log é escrito pela thread de atendimento, depois da resposta."""
        evento = threading.Event()
        for _ in range(int(segundos * 20)):
            if linhas:
                return True
            evento.wait(0.05)
        return bool(linhas)


if __name__ == "__main__":
    unittest.main()
