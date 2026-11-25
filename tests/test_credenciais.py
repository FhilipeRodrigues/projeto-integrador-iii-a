import contextlib
import io
import subprocess
import tempfile
import threading
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

    def test_Arquivo_ausente_ou_com_valores_vazios_vale_como_sem_conta(self):
        vazio = Path(self._pasta.name) / "vazio.env"
        vazio.write_text("# modelo\nUSUARIO=\nSENHA_HASH=\n", encoding="utf-8")
        for caminho in (self.env, vazio):  # o primeiro nem existe
            with self.subTest(caminho=caminho.name):
                cred = credenciais.Credenciais.do_env(caminho)
                self.assertFalse(cred.configurada)
                self.assertFalse(cred.verificar("ana", SENHA))

    def test_Hash_faltando_ou_malformado_explica_como_corrigir(self):
        for conteudo in ("USUARIO=ana\n", "USUARIO=ana\nSENHA_HASH=lixo\n", "SENHA_HASH=scrypt$ab$cd\n"):
            caminho = Path(self._pasta.name) / "invalido.env"
            caminho.write_text(conteudo, encoding="utf-8")
            with self.subTest(conteudo=conteudo), self.assertRaises(credenciais.CredenciaisAusentes) as contexto:
                credenciais.Credenciais.do_env(caminho)
            self.assertIn(".env.example", str(contexto.exception))
            self.assertIn("scripts.gerar_hash", str(contexto.exception))

    def test_O_servidor_sobe_sem_conta_e_avisa(self):
        saida = io.StringIO()
        with (
            mock.patch.object(servidor, "Servidor") as falso,
            contextlib.redirect_stdout(saida),
        ):
            falso.return_value.porta = 8443
            falso.return_value.servir.side_effect = KeyboardInterrupt
            codigo = servidor.main([
                "--env", str(self.env),
                "--solicitacoes", str(Path(self._pasta.name) / "solicitacoes.json"),
            ])
        self.assertEqual(codigo, 0)
        self.assertFalse(falso.call_args.kwargs["credenciais"].configurada)
        self.assertIn("Criar conta", saida.getvalue())

    def test_O_servidor_recusa_subir_com_o_env_corrompido(self):
        self.env.write_text("USUARIO=ana\nSENHA_HASH=lixo\n", encoding="utf-8")
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            codigo = servidor.main([
                "--porta", "0", "--env", str(self.env),
                "--solicitacoes", str(Path(self._pasta.name) / "solicitacoes.json"),
            ])
        self.assertEqual(codigo, 1)
        self.assertIn("gerar_hash", erro.getvalue())


class CriarContaTest(unittest.TestCase):
    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.env = Path(self._pasta.name) / ".env"

    def _sem_conta(self):
        return credenciais.Credenciais.do_env(self.env)

    def test_Criar_grava_o_env_com_hash_sem_a_senha_e_ativa_a_conta(self):
        cred = self._sem_conta()
        cred.criar("ana", SENHA)
        self.assertTrue(cred.configurada)
        self.assertEqual(cred.usuario, "ana")
        self.assertTrue(cred.verificar("ana", SENHA))
        self.assertFalse(cred.verificar("ana", SENHA + "x"))
        gravado = credenciais.carregar_env(self.env)
        self.assertEqual(gravado[credenciais.CHAVE_USUARIO], "ana")
        self.assertTrue(gravado[credenciais.CHAVE_HASH].startswith("scrypt$"))
        self.assertNotIn(SENHA, self.env.read_text(encoding="utf-8"))
        self.assertEqual([p.name for p in self.env.parent.iterdir()], [".env"])  # sem temporário

    def test_Um_novo_servidor_aceita_o_env_gravado(self):
        self._sem_conta().criar("ana", SENHA)
        depois = credenciais.Credenciais.do_env(self.env)
        self.assertTrue(depois.configurada)
        self.assertTrue(depois.verificar("ana", SENHA))

    def test_So_se_cria_a_conta_uma_vez(self):
        cred = self._sem_conta()
        cred.criar("ana", SENHA)
        antes = self.env.read_bytes()
        with self.assertRaises(credenciais.ContaJaExiste):
            cred.criar("outro", "outra-senha")
        self.assertEqual(self.env.read_bytes(), antes)
        self.assertTrue(cred.verificar("ana", SENHA))
        self.assertFalse(cred.verificar("outro", "outra-senha"))

    def test_Uma_conta_vinda_do_env_tambem_recusa_criar_outra(self):
        self.env.write_text(f"USUARIO=ana\nSENHA_HASH={credenciais.gerar_hash(SENHA)}\n", encoding="utf-8")
        with self.assertRaises(credenciais.ContaJaExiste):
            credenciais.Credenciais.do_env(self.env).criar("outro", "outra-senha")

    def test_Dados_fora_das_regras_nao_criam_nada(self):
        invalidos = [
            (None, SENHA), ("ana", None), ("ana", 1234), ("", SENHA), (" ana", SENHA), ("ana ", SENHA),
            ("ana\n", SENHA), ("a" * 101, SENHA), ("ana", "abc"), ("ana", ""), ("ana", "x" * 101),
        ]
        for usuario, senha in invalidos:
            cred = self._sem_conta()
            with self.subTest(usuario=usuario, senha=senha), self.assertRaises(credenciais.DadosDeContaInvalidos):
                cred.criar(usuario, senha)
            self.assertFalse(cred.configurada)
            self.assertFalse(self.env.exists())

    def test_Limites_aceitos(self):
        for usuario, senha in (("a", "abcd"), ("a" * 100, "x" * 100), ("Ana Maria", "çãõ-1234")):
            with self.subTest(usuario=usuario[:10]):
                cred = self._sem_conta()
                cred.criar(usuario, senha)
                self.assertTrue(credenciais.Credenciais.do_env(self.env).verificar(usuario, senha))
                self.env.unlink()

    def test_Falha_ao_gravar_nao_ativa_a_conta_nem_deixa_temporario(self):
        cred = self._sem_conta()
        with mock.patch("consulta.credenciais.os.replace", side_effect=PermissionError), self.assertRaises(OSError):
            cred.criar("ana", SENHA)
        self.assertFalse(cred.configurada)
        self.assertEqual(list(self.env.parent.iterdir()), [])
        cred.criar("ana", SENHA)  # a mesma instância ainda pode criar quando o disco voltar
        self.assertTrue(cred.verificar("ana", SENHA))

    def test_Sem_caminho_a_conta_vale_so_na_memoria(self):
        cred = credenciais.Credenciais()
        cred.criar("ana", SENHA)
        self.assertTrue(cred.verificar("ana", SENHA))

    def test_Sem_conta_o_scrypt_roda_e_a_verificacao_falha(self):
        cred = self._sem_conta()
        with mock.patch("consulta.credenciais._derivar", wraps=credenciais._derivar) as derivar:
            self.assertFalse(cred.verificar("ana", SENHA))
        derivar.assert_called_once()

    def test_Criacoes_simultaneas_deixam_uma_unica_conta(self):
        cred = self._sem_conta()
        resultados = []

        def tentar(numero):
            try:
                cred.criar(f"usuario{numero}", SENHA)
                resultados.append("criada")
            except credenciais.ContaJaExiste:
                resultados.append("recusada")

        fios = [threading.Thread(target=tentar, args=(n,)) for n in range(6)]
        for fio in fios:
            fio.start()
        for fio in fios:
            fio.join()
        self.assertEqual(sorted(resultados), ["criada"] + ["recusada"] * 5)
        self.assertEqual(credenciais.carregar_env(self.env)["USUARIO"], cred.usuario)


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
