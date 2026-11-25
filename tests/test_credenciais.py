import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from consulta import credenciais, servidor
from scripts import gerar_hash

RAIZ = Path(__file__).resolve().parent.parent
SENHA = "uma-senha-de-teste"


class HashDaSenhaTest(unittest.TestCase):
    def test_O_hash_nao_contem_a_senha_e_muda_a_cada_geracao(self):
        primeiro, segundo = credenciais.gerar_hash(SENHA), credenciais.gerar_hash(SENHA)
        self.assertNotEqual(primeiro, segundo)  # sal diferente
        for valor in (primeiro, segundo):
            self.assertTrue(valor.startswith("scrypt$"))
            self.assertNotIn(SENHA, valor)

    def test_Os_dois_hashes_validam_a_senha_certa_e_recusam_a_errada(self):
        for _ in range(2):
            cred = credenciais.Credenciais("ana", credenciais.gerar_hash(SENHA))
            self.assertTrue(cred.verificar("ana", SENHA))
            self.assertFalse(cred.verificar("ana", SENHA + "x"))

    def test_Usuario_errado_falha_mesmo_com_a_senha_certa(self):
        cred = credenciais.Credenciais("ana", credenciais.gerar_hash(SENHA))
        self.assertFalse(cred.verificar("ANA", SENHA))
        self.assertFalse(cred.verificar("", SENHA))

    def test_O_scrypt_roda_tambem_quando_o_usuario_erra(self):
        cred = credenciais.Credenciais("ana", credenciais.gerar_hash(SENHA))
        with mock.patch("consulta.credenciais._derivar", wraps=credenciais._derivar) as derivar:
            cred.verificar("outro", SENHA)
        derivar.assert_called_once()

    def test_Hash_em_formato_invalido_e_recusado(self):
        for invalido in ("", "senha", "scrypt$zz$zz", "scrypt$ab", "md5$ab$cd", "scrypt$ab$cd$ef"):
            with self.subTest(invalido=invalido), self.assertRaises(ValueError):
                credenciais.Credenciais("ana", invalido)
        with self.assertRaises(ValueError):
            credenciais.Credenciais("", credenciais.gerar_hash(SENHA))


class ArquivoEnvTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.env = Path(self._pasta.name) / ".env"

    def test_Le_chaves_ignorando_comentarios_e_linhas_em_branco(self):
        self.env.write_text("# login\n\nUSUARIO = ana\nSENHA_HASH=scrypt$a$b\nsolta\n", encoding="utf-8")
        self.assertEqual(
            credenciais.carregar_env(self.env), {"USUARIO": "ana", "SENHA_HASH": "scrypt$a$b"}
        )

    def test_Carrega_as_credenciais_do_env(self):
        hash_da_senha = credenciais.gerar_hash(SENHA)
        self.env.write_text(f"USUARIO=ana\nSENHA_HASH={hash_da_senha}\n", encoding="utf-8")
        cred = credenciais.Credenciais.do_env(self.env)
        self.assertEqual(cred.usuario, "ana")
        self.assertTrue(cred.verificar("ana", SENHA))

    def test_Sem_arquivo_ou_sem_as_chaves_explica_como_criar(self):
        sem_hash = Path(self._pasta.name) / "sem-hash.env"
        sem_hash.write_text("USUARIO=ana\n", encoding="utf-8")
        for caminho in (self.env, sem_hash):  # o primeiro nem existe
            with self.subTest(caminho=caminho.name), self.assertRaises(credenciais.CredenciaisAusentes) as contexto:
                credenciais.Credenciais.do_env(caminho)
            self.assertIn(".env.example", str(contexto.exception))
            self.assertIn("scripts.gerar_hash", str(contexto.exception))

    def test_O_servidor_recusa_subir_sem_a_configuracao_de_login(self):
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            codigo = servidor.main([
                "--porta", "0", "--env", str(self.env),
                "--solicitacoes", str(Path(self._pasta.name) / "solicitacoes.json"),
            ])
        self.assertEqual(codigo, 1)
        self.assertIn("gerar_hash", erro.getvalue())


class ScriptGerarHashTest(unittest.TestCase):
    def test_Imprime_a_linha_que_o_servidor_aceita(self):
        saida = io.StringIO()
        with mock.patch("getpass.getpass", side_effect=[SENHA, SENHA]), contextlib.redirect_stdout(saida):
            self.assertEqual(gerar_hash.main(), 0)
        chave, _, valor = saida.getvalue().strip().partition("=")
        self.assertEqual(chave, "SENHA_HASH")
        self.assertTrue(credenciais.Credenciais("ana", valor).verificar("ana", SENHA))

    def test_Recusa_senhas_diferentes_vazia_ou_grande_demais(self):
        for respostas in ([SENHA, "outra"], ["", ""], ["x" * 101, "x" * 101]):
            erro = io.StringIO()
            with (
                self.subTest(respostas=[len(r) for r in respostas]),
                mock.patch("getpass.getpass", side_effect=respostas),
                contextlib.redirect_stderr(erro),
                contextlib.redirect_stdout(io.StringIO()) as saida,
            ):
                self.assertEqual(gerar_hash.main(), 1)
            self.assertEqual(saida.getvalue(), "")
            self.assertIn("Erro:", erro.getvalue())


class EnvForaDoGitTest(unittest.TestCase):
    def test_O_env_e_ignorado_e_o_exemplo_nao_tem_valores(self):
        if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
            self.skipTest("git não encontrado")
        ignorado = subprocess.run(["git", "check-ignore", ".env"], cwd=RAIZ, capture_output=True)
        self.assertEqual(ignorado.returncode, 0)
        exemplo = credenciais.carregar_env(RAIZ / ".env.example")
        self.assertEqual(exemplo, {credenciais.CHAVE_USUARIO: "", credenciais.CHAVE_HASH: ""})
