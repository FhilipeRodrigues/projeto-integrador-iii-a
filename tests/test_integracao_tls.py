import contextlib
import io
import json
import socket
import ssl
import tempfile
import threading
import time
import unittest
from concurrent import futures
from pathlib import Path
from unittest import mock

from consulta import base, cliente, credenciais, dominio, regras, servidor, solicitacoes
from scripts import gerar_certificados

RAIZ = Path(__file__).resolve().parent.parent
USUARIO, SENHA = "analista", "senha-de-teste"
CREDENCIAIS = credenciais.Credenciais(USUARIO, credenciais.gerar_hash(SENHA))
CRED = {"usuario": USUARIO, "senha": SENHA}


def _openssl():
    try:
        return gerar_certificados.localizar_openssl()
    except gerar_certificados.OpenSslAusente:
        return None


@contextlib.contextmanager
def servidor_no_ar_em(servidores, pasta_certs, porta, pedidos=None, atraso_falha_s=0, conta=None):
    """Sobe o servidor na `porta` dada (0 = livre); devolve (servidor, linhas de log)."""
    linhas = []
    srv = servidor.Servidor(
        servidores, pasta_certs, "127.0.0.1", porta, log=linhas.append, pedidos=pedidos,
        credenciais=CREDENCIAIS if conta is None else conta, atraso_falha_s=atraso_falha_s,
    )
    srv.iniciar()
    fio = threading.Thread(target=srv.servir)
    fio.start()
    try:
        yield srv, linhas
    finally:
        srv.parar()
        fio.join(timeout=5)


def servidor_no_ar(servidores, pasta_certs, pedidos=None, atraso_falha_s=0, conta=None):
    """Sobe o servidor numa porta livre; devolve (servidor, linhas de log)."""
    return servidor_no_ar_em(servidores, pasta_certs, 0, pedidos, atraso_falha_s, conta)


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
        self.assertIn("Servidor não confiável", str(contexto.exception))

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
                servidor.Servidor(self.servidores, vazia, "127.0.0.1", 0, credenciais=CREDENCIAIS)
            self.assertIn("gerar_certificados.py", str(contexto.exception))

            env = Path(vazia) / ".env"
            env.write_text(f"USUARIO={USUARIO}\nSENHA_HASH={credenciais.gerar_hash(SENHA)}\n", encoding="utf-8")
            erro = io.StringIO()
            with contextlib.redirect_stderr(erro):
                codigo = servidor.main([
                    "--certs", vazia, "--porta", "0", "--env", str(env),
                    "--solicitacoes", str(Path(vazia) / "solicitacoes.json"),
                ])
        self.assertEqual(codigo, 1)
        self.assertIn("gerar_certificados.py", erro.getvalue())

    def test_Buscar_por_trecho_do_nome(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            lista = self._cliente(srv).buscar("pereira")
        self.assertTrue(lista)
        for item in lista:
            self.assertEqual(set(item), {"id", "nome", "municipio"})
            self.assertIn("pereira", dominio.normalizar(item["nome"]))

    def _com_marias(self):
        """Renomeia três servidores para o cenário ter várias "Maria" em Anápolis e Goiânia."""
        base_com_marias = [dict(s) for s in self.servidores]
        for indice, nome in ((0, "Maria Alves Lima"), (1, "Ana Maria Souza"), (5, "Maria Pereira")):
            base_com_marias[indice]["nome"] = nome
        return base_com_marias

    def test_Buscar_dentro_de_um_municipio(self):
        with servidor_no_ar(self._com_marias(), self.certs) as (srv, _):
            lista = self._cliente(srv).buscar("maria", "Anápolis")
        self.assertTrue(lista)
        self.assertEqual([i["id"] for i in lista], [2, 1])  # ordem alfabética; Goiânia (id 6) fica de fora

    def test_Buscar_com_o_nome_vazio(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            self.assertEqual(len(self._cliente(srv).buscar("")), 50)

    def test_Buscar_sem_encontrar_ninguem(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            self.assertEqual(self._cliente(srv).buscar("zzz"), [])

    def test_Abrir_a_ficha_de_um_servidor_da_lista(self):
        with servidor_no_ar(self._com_marias(), self.certs) as (srv, _):
            c = self._cliente(srv)
            primeiro = c.buscar("maria")[0]
            ficha = c.ficha(primeiro["id"])
        self.assertEqual(ficha["id"], primeiro["id"])
        self.assertEqual(
            set(ficha),
            {"id", "nome", "municipio", "sexo", "idade", "orgao", "pcd", "doenca_profissional",
             "data_ingresso", "data_solicitacao", "ultima_remuneracao_centavos",
             "tempo_contribuicao_anos", "situacao_solicitacao"},
        )

    def test_Idade_e_tempo_de_contribuicao_vem_calculados_pelo_servidor(self):
        modelo = dict(self.servidores[0], id=1, data_nascimento="1968-04-12",
                      data_ingresso="1994-03-01", data_solicitacao="2026-09-15")
        with servidor_no_ar([modelo], self.certs) as (srv, _):
            ficha = self._cliente(srv).ficha(1)
        self.assertEqual(ficha["idade"], 58)
        self.assertEqual(ficha["tempo_contribuicao_anos"], 32)

    def test_A_ficha_pela_rede_nao_expoe_nascimento_nem_elegibilidade(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            resposta = self._cliente(srv).consultar({"op": "ficha", "id": self.servidores[0]["id"]})
        texto = str(resposta).lower()
        self.assertNotIn("nascimento", texto)
        self.assertNotIn(self.servidores[0]["data_nascimento"], texto)
        for palavra in ("elegib", "apto", "aposent"):
            self.assertNotIn(palavra, texto)

    def test_Cliente_e_servidor_sao_programas_separados(self):
        # O cliente só recebe a base pela rede: ClienteRede não importa nem abre a base.
        self.assertFalse(hasattr(cliente, "base"))
        with servidor_no_ar(self.servidores, self.certs) as (srv, linhas):
            with mock.patch("builtins.open", side_effect=AssertionError("acesso direto a arquivo")):
                lista = self._cliente(srv).buscar("")
            self.assertEqual(len(lista), 50)
            self.assertTrue(self._esperar(linhas))
        self.assertIn("op=buscar", linhas[0])

    def _bruto(self, srv, dados):
        """Envia bytes crus pelo canal TLS e devolve a resposta decodificada (ou None se vazia)."""
        contexto = ssl.create_default_context(cafile=str(self.certs / "ca.crt"))
        with socket.create_connection(("127.0.0.1", srv.porta), timeout=5) as bruto:
            with contexto.wrap_socket(bruto, server_hostname="127.0.0.1") as seguro:
                seguro.sendall(dados)
                with seguro.makefile("rb") as leitor:
                    linha = leitor.readline()
        return json.loads(linha) if linha else None

    def _pedido(self, requisicao):
        return json.dumps(requisicao).encode("utf-8") + b"\n"

    def _confere_erro(self, resposta, codigo):
        self.assertFalse(resposta["ok"])
        self.assertEqual(resposta["erro"]["codigo"], codigo)
        mensagem = resposta["erro"]["mensagem"]
        self.assertTrue(mensagem.strip())
        for interno in ("Traceback", "File \"", "Error:", ".py", "Exception"):
            self.assertNotIn(interno, mensagem)

    def test_Recusar_um_pedido_invalido_com_o_codigo_de_erro_certo(self):
        invalido, desconhecida = "REQUISICAO_INVALIDA", "OPERACAO_DESCONHECIDA"
        casos = [
            ("um texto que não é JSON", b"isto nao e json\n", invalido),
            ("um JSON que não é um objeto", b"[1, 2]\n", invalido),
            ("uma busca sem o campo nome", self._pedido({"op": "buscar"}), invalido),
            ("nome que não é texto", self._pedido({"op": "buscar", "nome": 123}), invalido),
            ("nome com mais de 100 caracteres",
             self._pedido({"op": "buscar", "nome": "a" * 101}), invalido),
            ("município que não existe",
             self._pedido({"op": "buscar", "nome": "", "municipio": "Nárnia"}), invalido),
            ("município que não é texto",
             self._pedido({"op": "buscar", "nome": "", "municipio": 7}), invalido),
            ("ficha com identificação não numérica",
             self._pedido({"op": "ficha", "id": "abc"}), invalido),
            ("ficha com identificação booleana",
             self._pedido({"op": "ficha", "id": True}), invalido),
            ("ficha sem identificação", self._pedido({"op": "ficha"}), invalido),
            ("pedido sem operação", self._pedido({"nome": "x"}), invalido),
            ("operação que não é texto", self._pedido({"op": ["buscar"]}), invalido),
            ("operação apagar", self._pedido({"op": "apagar"}), desconhecida),
            ("ficha de servidor inexistente",
             self._pedido({"op": "ficha", "id": 999999}), "NAO_ENCONTRADO"),
        ]
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            for descricao, pedido, codigo in casos:
                with self.subTest(descricao):
                    self._confere_erro(self._bruto(srv, pedido), codigo)

    def test_Nome_com_exatamente_100_caracteres_e_aceito(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            resposta = self._bruto(srv, self._pedido({"op": "buscar", "nome": "a" * 100}))
        self.assertTrue(resposta["ok"])

    def test_Recusar_uma_linha_grande_demais(self):
        grande = b'{"op": "buscar", "nome": "' + b"a" * (100 * 1024) + b'"}\n'
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            self._confere_erro(self._bruto(srv, grande), "REQUISICAO_INVALIDA")

    def test_O_servidor_continua_atendendo_depois_de_um_erro(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            self._confere_erro(self._bruto(srv, b"lixo\n"), "REQUISICAO_INVALIDA")
            self.assertEqual(len(self._cliente(srv).buscar("")), 50)

    def test_Falha_inesperada_no_atendimento_de_uma_conexao(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, linhas):
            with mock.patch("consulta.servidor.dominio.buscar",
                            side_effect=RuntimeError("segredo interno")):
                resposta = self._bruto(srv, self._pedido({"op": "buscar", "nome": ""}))
            self._confere_erro(resposta, "ERRO_INTERNO")
            self.assertNotIn("segredo interno", resposta["erro"]["mensagem"])
            self.assertEqual(len(self._cliente(srv).buscar("")), 50)
        self.assertIn("ERRO_INTERNO", "\n".join(linhas))

    def test_O_timeout_de_conexao_e_de_5_segundos(self):
        self.assertEqual(servidor.TIMEOUT_S, 5)

    def test_Cliente_que_conecta_e_nao_envia_nada(self):
        contexto = ssl.create_default_context(cafile=str(self.certs / "ca.crt"))
        with mock.patch.object(servidor, "TIMEOUT_S", 1):
            with servidor_no_ar(self.servidores, self.certs) as (srv, _):
                with socket.create_connection(("127.0.0.1", srv.porta), timeout=4) as bruto:
                    with contexto.wrap_socket(bruto, server_hostname="127.0.0.1") as ocioso:
                        # Enquanto o cliente ocioso espera, outro é atendido normalmente.
                        self.assertEqual(len(self._cliente(srv).buscar("")), 50)
                        try:
                            recebido = ocioso.recv(1)
                        except (ssl.SSLError, ConnectionError):
                            recebido = b""  # conexão encerrada pelo servidor
                self.assertEqual(recebido, b"")  # servidor encerrou; o recv não estourou o prazo de 4 s

    def _buscas_simultaneas(self, srv, termos):
        """Dispara uma busca por termo, todas liberadas juntas; devolve os resultados na ordem."""
        largada = threading.Barrier(len(termos))

        def buscar(termo):
            largada.wait(timeout=5)
            return self._cliente(srv).buscar(termo)

        with futures.ThreadPoolExecutor(max_workers=len(termos)) as piscina:
            return [f.result(timeout=10) for f in [piscina.submit(buscar, t) for t in termos]]

    def test_Dois_clientes_consultam_ao_mesmo_tempo(self):
        termos = [self.servidores[0]["nome"].split()[0], self.servidores[1]["nome"].split()[-1]]
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            resultados = self._buscas_simultaneas(srv, termos)
        for termo, lista in zip(termos, resultados):
            esperado = dominio.buscar(self.servidores, termo, None)
            self.assertTrue(esperado)
            self.assertEqual(lista, esperado)

    def test_Muitos_clientes_consultam_ao_mesmo_tempo(self):
        termos = [s["nome"].split()[0] for s in self.servidores[:10]]
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            resultados = self._buscas_simultaneas(srv, termos)
        self.assertEqual(len(resultados), 10)
        for termo, lista in zip(termos, resultados):
            esperado = dominio.buscar(self.servidores, termo, None)
            self.assertTrue(esperado)
            self.assertEqual(lista, esperado)

    def test_Um_cliente_lento_nao_bloqueia_os_outros(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            # Conexão aberta, sem iniciar o aperto de mão TLS: ocupa a thread dela, só.
            with socket.create_connection(("127.0.0.1", srv.porta), timeout=5):
                time.sleep(0.2)  # dá tempo de o servidor aceitar a conexão lenta
                inicio = time.perf_counter()
                lista = self._cliente(srv).buscar("")
                decorrido = time.perf_counter() - inicio
        self.assertEqual(len(lista), 50)
        self.assertLess(decorrido, servidor.TIMEOUT_S / 2)  # não esperou o prazo do cliente lento

    def test_A_busca_responde_em_ate_1_segundo(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            tempos = []
            for _ in range(3):  # a menor de 3 amostras evita falha por oscilação da máquina
                inicio = time.perf_counter()
                lista = self._cliente(srv).buscar("")  # conexão + aperto de mão + busca + resposta
                tempos.append(time.perf_counter() - inicio)
        self.assertEqual(len(lista), 50)
        self.assertLessEqual(min(tempos), 1.0)

    @staticmethod
    def _esperar(linhas, segundos=5):
        """O log é escrito pela thread de atendimento, depois da resposta."""
        evento = threading.Event()
        for _ in range(int(segundos * 20)):
            if linhas:
                return True
            evento.wait(0.05)
        return bool(linhas)




@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class SolicitacoesPelaRedeTest(unittest.TestCase):
    CAMPOS_DO_DOCUMENTO = {
        "id", "numero", "situacao", "decidida_em", "municipio", "orgao", "servidor_nome",
        "sexo", "data_ingresso", "data_solicitacao",
    }

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.certs = gerar_certificados.gerar_certificados(Path(cls._tmp.name) / "certs")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _no_ar(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores)
        return servidor_no_ar(self.servidores, self.certs, pedidos)

    def _cliente(self, srv):
        return cliente.ClienteRede("127.0.0.1", srv.porta, self.certs / "ca.crt")

    def test_Listar_as_solicitacoes_pela_rede(self):
        with self._no_ar() as (srv, _):
            lista = self._cliente(srv).solicitacoes()
        self.assertEqual(len(lista), 10)
        for item in lista:
            self.assertEqual(set(item), {"id", "numero", "servidor_nome", "municipio", "situacao"})
        self.assertEqual([i["numero"] for i in lista], sorted(i["numero"] for i in lista))

    def test_Abrir_o_documento_de_uma_solicitacao(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            primeira = c.solicitacoes()[0]
            documento = c.documento(primeira["id"])
        self.assertEqual(set(documento), self.CAMPOS_DO_DOCUMENTO)
        self.assertEqual(documento["numero"], primeira["numero"])
        self.assertEqual(documento["servidor_nome"], primeira["servidor_nome"])
        self.assertEqual(documento["municipio"], primeira["municipio"])
        self.assertEqual(documento["situacao"], "pendente")

    def test_O_documento_nao_expoe_dados_que_o_analista_confere_na_consulta(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            brutos = [
                json.dumps(c.documento(item["id"]), ensure_ascii=False) for item in c.solicitacoes()
            ]
        for bruto in brutos:
            for vedado in ("nascimento", "idade", "contribuicao", "pcd", "doenca", "remuneracao",
                           "apto", "elegivel", "elegibilidade"):
                self.assertNotIn(vedado, bruto)

    def test_Documento_de_solicitacao_inexistente(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            resposta = c.consultar({"op": "documento", "id": 999})
            depois = c.solicitacoes()
        self.assertFalse(resposta["ok"])
        self.assertEqual(resposta["erro"]["codigo"], "NAO_ENCONTRADO")
        self.assertEqual(len(depois), 10)  # o servidor continua atendendo

    def test_Documento_com_identificacao_invalida(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            for invalido in ("1", None, 1.5, True):
                resposta = c.consultar({"op": "documento", "id": invalido})
                self.assertEqual(resposta["erro"]["codigo"], "REQUISICAO_INVALIDA")
            resposta = c.consultar({"op": "documento"})
        self.assertEqual(resposta["erro"]["codigo"], "REQUISICAO_INVALIDA")

    def test_O_log_nao_mostra_nomes_de_servidores(self):
        with self._no_ar() as (srv, linhas):
            c = self._cliente(srv)
            for item in c.solicitacoes():
                c.documento(item["id"])
            limite = time.monotonic() + 5
            while len(linhas) < 11 and time.monotonic() < limite:
                time.sleep(0.01)
        registro = "\n".join(linhas)
        self.assertIn("op=solicitacoes", registro)
        self.assertIn("op=documento", registro)
        for servidor_da_base in self.servidores:
            self.assertNotIn(servidor_da_base["nome"], registro)


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class DecisaoPelaRedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.certs = gerar_certificados.gerar_certificados(Path(cls._tmp.name) / "certs")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.arquivo = Path(self._pasta.name) / "solicitacoes.json"

    def _no_ar(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.arquivo)
        return servidor_no_ar(self.servidores, self.certs, pedidos)

    def _cliente(self, srv):
        return cliente.ClienteRede("127.0.0.1", srv.porta, self.certs / "ca.crt")

    def test_Aprovar_e_desaprovar_devolvem_o_documento_atualizado(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            primeira, segunda = c.solicitacoes()[:2]
            aprovada = c.decidir(primeira["id"], "aprovada", USUARIO, SENHA)
            desaprovada = c.decidir(segunda["id"], "desaprovada", USUARIO, SENHA)
            lista = {i["id"]: i["situacao"] for i in c.solicitacoes()}
            relida = c.documento(primeira["id"])
        self.assertEqual(set(aprovada), SolicitacoesPelaRedeTest.CAMPOS_DO_DOCUMENTO)
        self.assertEqual((aprovada["situacao"], desaprovada["situacao"]), ("aprovada", "desaprovada"))
        self.assertRegex(aprovada["decidida_em"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$")
        self.assertEqual(relida, aprovada)
        self.assertEqual(lista[primeira["id"]], "aprovada")
        self.assertEqual(lista[segunda["id"]], "desaprovada")

    def test_Trocar_a_decisao(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ident = c.solicitacoes()[0]["id"]
            c.decidir(ident, "aprovada", USUARIO, SENHA)
            trocada = c.decidir(ident, "desaprovada", USUARIO, SENHA)
        self.assertEqual(trocada["situacao"], "desaprovada")

    def test_A_decisao_sobrevive_a_reiniciar_o_servidor(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ids = [i["id"] for i in c.solicitacoes()]
            c.decidir(ids[0], "aprovada", USUARIO, SENHA)
            c.decidir(ids[1], "desaprovada", USUARIO, SENHA)
        with self._no_ar() as (srv, _):  # outro servidor no ar, mesmo arquivo
            situacoes = [i["situacao"] for i in self._cliente(srv).solicitacoes()]
        self.assertEqual(situacoes, ["aprovada", "desaprovada"] + ["pendente"] * 8)

    def test_A_ficha_mostra_a_situacao_da_solicitacao_do_servidor(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.arquivo)
        com_solicitacao = pedidos.obter(1)["servidor_id"]
        sem_solicitacao = next(
            s["id"] for s in self.servidores
            if pedidos.situacao_do_servidor(s["id"]) is None
        )
        with servidor_no_ar(self.servidores, self.certs, pedidos) as (srv, _):
            c = self._cliente(srv)
            antes = c.ficha(com_solicitacao)["situacao_solicitacao"]
            c.decidir(1, "aprovada", USUARIO, SENHA)
            depois = c.ficha(com_solicitacao)["situacao_solicitacao"]
            sem = c.ficha(sem_solicitacao)["situacao_solicitacao"]
        self.assertEqual((antes, depois, sem), ("pendente", "aprovada", None))

    def test_A_situacao_registra_a_decisao_e_nao_indica_aptidao(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            c.decidir(c.solicitacoes()[0]["id"], "aprovada", USUARIO, SENHA)
            brutos = [json.dumps(c.documento(i["id"])).lower() for i in c.solicitacoes()]
            situacoes = {i["situacao"] for i in c.solicitacoes()}
        for bruto in brutos:
            for vedado in ("apto", "elegib", "pode se aposentar"):
                self.assertNotIn(vedado, bruto)
        self.assertLessEqual(situacoes, {"pendente", "aprovada", "desaprovada"})

    def test_Decisao_com_dados_invalidos(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ident = c.solicitacoes()[0]["id"]
            for decisao in ("pendente", "APROVADA", "", None, 1, ["aprovada"]):
                resposta = c.consultar({"op": "decidir", **CRED, "id": ident, "decisao": decisao})
                self.assertEqual(resposta["erro"]["codigo"], "REQUISICAO_INVALIDA")
            for invalido in ("1", None, 1.5, True):
                resposta = c.consultar({"op": "decidir", **CRED, "id": invalido, "decisao": "aprovada"})
                self.assertEqual(resposta["erro"]["codigo"], "REQUISICAO_INVALIDA")
            resposta = c.consultar({"op": "decidir", **CRED, "decisao": "aprovada"})
            self.assertEqual(resposta["erro"]["codigo"], "REQUISICAO_INVALIDA")
            resposta = c.consultar({"op": "decidir", **CRED, "id": 999, "decisao": "aprovada"})
            self.assertEqual(resposta["erro"]["codigo"], "NAO_ENCONTRADO")
            depois = c.solicitacoes()  # o servidor continua atendendo
        self.assertEqual({i["situacao"] for i in depois}, {"pendente"})

    def test_Duas_decisoes_ao_mesmo_tempo_ficam_registradas(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ids = [i["id"] for i in c.solicitacoes()]
            with futures.ThreadPoolExecutor(max_workers=len(ids)) as pool:
                respostas = list(pool.map(
                    lambda n: c.consultar({"op": "decidir", **CRED, "id": ids[n],
                                           "decisao": "aprovada" if n % 2 else "desaprovada"}),
                    range(len(ids)),
                ))
            lista = c.solicitacoes()
        self.assertTrue(all(r["ok"] for r in respostas))
        self.assertEqual(
            [i["situacao"] for i in lista],
            ["desaprovada" if n % 2 == 0 else "aprovada" for n in range(len(ids))],
        )
        reaberto = solicitacoes.Solicitacoes(self.servidores, self.arquivo)  # o arquivo segue válido
        self.assertEqual([i["situacao"] for i in reaberto.listar()], [i["situacao"] for i in lista])

    def test_Falha_ao_gravar_devolve_erro_interno_e_mantem_a_situacao(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ident = c.solicitacoes()[0]["id"]
            with mock.patch("consulta.solicitacoes.os.replace", side_effect=OSError("disco cheio")):
                resposta = c.consultar({"op": "decidir", **CRED, "id": ident, "decisao": "aprovada"})
            depois = c.solicitacoes()[0]["situacao"]
            de_novo = c.decidir(ident, "aprovada", USUARIO, SENHA)  # o servidor segue atendendo
        self.assertEqual(resposta["erro"]["codigo"], "ERRO_INTERNO")
        self.assertNotIn("disco cheio", resposta["erro"]["mensagem"])
        self.assertEqual(depois, "pendente")
        self.assertEqual(de_novo["situacao"], "aprovada")

    def test_O_log_registra_a_decisao_sem_nomes(self):
        with self._no_ar() as (srv, linhas):
            c = self._cliente(srv)
            c.decidir(c.solicitacoes()[0]["id"], "aprovada", USUARIO, SENHA)
            limite = time.monotonic() + 5
            while len(linhas) < 2 and time.monotonic() < limite:
                time.sleep(0.01)
        registro = "\n".join(linhas)
        self.assertIn("op=decidir resultado=ok", registro)
        for servidor_da_base in self.servidores:
            self.assertNotIn(servidor_da_base["nome"], registro)


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class LoginPelaRedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.certs = gerar_certificados.gerar_certificados(Path(cls._tmp.name) / "certs")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.arquivo = Path(self._pasta.name) / "solicitacoes.json"

    def _no_ar(self, atraso_falha_s=0):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.arquivo)
        return servidor_no_ar(self.servidores, self.certs, pedidos, atraso_falha_s)

    def _cliente(self, srv):
        return cliente.ClienteRede("127.0.0.1", srv.porta, self.certs / "ca.crt")

    def test_Login_com_a_credencial_certa(self):
        with self._no_ar() as (srv, _):
            self.assertEqual(self._cliente(srv).login(USUARIO, SENHA), {"usuario": USUARIO})

    def test_Qualquer_outra_credencial_falha_do_mesmo_jeito(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            respostas = [
                c.consultar({"op": "login", "usuario": usuario, "senha": senha})
                for usuario, senha in (("outro", SENHA), (USUARIO, "errada"), ("outro", "errada"))
            ]
            with self.assertRaises(cliente.CredenciaisInvalidas) as contexto:
                c.login(USUARIO, "errada")
        for resposta in respostas:
            self.assertEqual(resposta, respostas[0])
            self.assertEqual(resposta["erro"]["codigo"], "CREDENCIAIS_INVALIDAS")
            self.assertEqual(resposta["erro"]["mensagem"], "Usuário ou senha inválidos.")
        self.assertEqual(str(contexto.exception), "Usuário ou senha inválidos.")

    def test_Credencial_malformada_e_requisicao_invalida(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            pedidos = [
                {"op": "login"},
                {"op": "login", "usuario": USUARIO},
                {"op": "login", "usuario": USUARIO, "senha": 123},
                {"op": "login", "usuario": None, "senha": SENHA},
                {"op": "login", "usuario": USUARIO, "senha": ""},
                {"op": "login", "usuario": USUARIO, "senha": "x" * 101},
            ]
            codigos = [c.consultar(pedido)["erro"]["codigo"] for pedido in pedidos]
            depois = c.login(USUARIO, SENHA)  # o servidor segue atendendo
        self.assertEqual(set(codigos), {"REQUISICAO_INVALIDA"})
        self.assertEqual(depois, {"usuario": USUARIO})

    def test_Decidir_sem_a_credencial_certa_nao_grava(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ident = c.solicitacoes()[0]["id"]
            sem = c.consultar({"op": "decidir", "id": ident, "decisao": "aprovada"})
            errada = c.consultar({"op": "decidir", "id": ident, "decisao": "aprovada",
                                  "usuario": USUARIO, "senha": "errada"})
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.decidir(ident, "aprovada", "outro", SENHA)
            pendente = c.solicitacoes()[0]["situacao"]
            certa = c.decidir(ident, "aprovada", USUARIO, SENHA)
        self.assertEqual(sem["erro"]["codigo"], "REQUISICAO_INVALIDA")
        self.assertEqual(errada["erro"]["codigo"], "CREDENCIAIS_INVALIDAS")
        self.assertEqual(pendente, "pendente")
        self.assertEqual(certa["situacao"], "aprovada")

    def test_A_credencial_e_conferida_antes_do_id(self):
        with self._no_ar() as (srv, _):
            resposta = self._cliente(srv).consultar({
                "op": "decidir", "id": 999, "decisao": "aprovada",
                "usuario": USUARIO, "senha": "errada",
            })
        self.assertEqual(resposta["erro"]["codigo"], "CREDENCIAIS_INVALIDAS")

    def test_Cada_falha_espera_a_pausa_e_o_acerto_nao(self):
        with self._no_ar(atraso_falha_s=0.3) as (srv, _):
            c = self._cliente(srv)
            inicio = time.monotonic()
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.login(USUARIO, "errada")
            falha = time.monotonic() - inicio
            inicio = time.monotonic()
            c.login(USUARIO, SENHA)
            acerto = time.monotonic() - inicio
        self.assertGreaterEqual(falha, 0.3)
        self.assertLess(acerto, 0.3)

    def test_O_log_registra_o_resultado_sem_usuario_nem_senha(self):
        with self._no_ar() as (srv, linhas):
            c = self._cliente(srv)
            c.login(USUARIO, SENHA)
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.login(USUARIO, "senha-errada-no-log")
            limite = time.monotonic() + 5
            while len(linhas) < 2 and time.monotonic() < limite:
                time.sleep(0.01)
        registro = "\n".join(linhas)
        self.assertIn("op=login resultado=ok", registro)
        self.assertIn("op=login resultado=erro:CREDENCIAIS_INVALIDAS", registro)
        for segredo in (USUARIO, SENHA, "senha-errada-no-log"):
            self.assertNotIn(segredo, registro)


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class CriarContaPelaRedeTest(unittest.TestCase):
    NOVO_USUARIO, NOVA_SENHA = "ana", "senha-nova-123"

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.certs = gerar_certificados.gerar_certificados(Path(cls._tmp.name) / "certs")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def setUp(self):
        self._pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self._pasta.cleanup)
        self.env = Path(self._pasta.name) / ".env"

    def _no_ar(self):
        conta = credenciais.Credenciais.do_env(self.env)
        pedidos = solicitacoes.Solicitacoes(self.servidores, Path(self._pasta.name) / "solicitacoes.json")
        return servidor_no_ar(self.servidores, self.certs, pedidos, conta=conta)

    def _cliente(self, srv):
        return cliente.ClienteRede("127.0.0.1", srv.porta, self.certs / "ca.crt")

    def test_Sem_conta_o_login_falha_como_qualquer_credencial_errada(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            sem_conta = c.consultar({"op": "login", **CRED})
            errada = c.consultar({"op": "login", "usuario": "x", "senha": "y"})
        self.assertEqual(sem_conta, errada)
        self.assertEqual(sem_conta["erro"]["codigo"], "CREDENCIAIS_INVALIDAS")
        self.assertEqual(sem_conta["erro"]["mensagem"], "Usuário ou senha inválidos.")

    def test_Criar_a_conta_grava_o_env_e_libera_o_login(self):
        with self._no_ar() as (srv, linhas):
            c = self._cliente(srv)
            criada = c.criar_conta(self.NOVO_USUARIO, self.NOVA_SENHA)
            entrou = c.login(self.NOVO_USUARIO, self.NOVA_SENHA)
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.login(self.NOVO_USUARIO, "senha-errada")
        self.assertEqual(criada, {"usuario": self.NOVO_USUARIO})
        self.assertEqual(entrou, {"usuario": self.NOVO_USUARIO})
        gravado = self.env.read_text(encoding="utf-8")
        self.assertIn(f"USUARIO={self.NOVO_USUARIO}", gravado)
        self.assertIn("SENHA_HASH=scrypt$", gravado)
        self.assertNotIn(self.NOVA_SENHA, gravado)
        registro = "\n".join(linhas)
        self.assertIn("op=criar_conta resultado=ok", registro)
        for segredo in (self.NOVO_USUARIO, self.NOVA_SENHA, "scrypt$"):
            self.assertNotIn(segredo, registro)

    def test_A_conta_sobrevive_ao_reinicio_do_servidor(self):
        with self._no_ar() as (srv, _):
            self._cliente(srv).criar_conta(self.NOVO_USUARIO, self.NOVA_SENHA)
        with self._no_ar() as (srv, _):  # lê o .env gravado
            self.assertEqual(
                self._cliente(srv).login(self.NOVO_USUARIO, self.NOVA_SENHA),
                {"usuario": self.NOVO_USUARIO},
            )

    def test_So_se_cria_a_conta_uma_vez(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            c.criar_conta(self.NOVO_USUARIO, self.NOVA_SENHA)
            segunda = c.consultar({"op": "criar_conta", "usuario": "outro", "senha": "outra-senha"})
            with self.assertRaises(cliente.ContaJaExiste) as contexto:
                c.criar_conta("outro", "outra-senha")
            original = c.login(self.NOVO_USUARIO, self.NOVA_SENHA)
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.login("outro", "outra-senha")
        self.assertEqual(segunda["erro"]["codigo"], "CONTA_JA_EXISTE")
        self.assertEqual(str(contexto.exception), "Já existe uma conta cadastrada. Entre com ela.")
        self.assertEqual(original, {"usuario": self.NOVO_USUARIO})

    def test_Dados_invalidos_dao_requisicao_invalida_e_nao_gravam(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            pedidos = [
                {"op": "criar_conta"},
                {"op": "criar_conta", "usuario": "ana"},
                {"op": "criar_conta", "usuario": "ana", "senha": 123},
                {"op": "criar_conta", "usuario": None, "senha": self.NOVA_SENHA},
                {"op": "criar_conta", "usuario": " ana", "senha": self.NOVA_SENHA},
                {"op": "criar_conta", "usuario": "ana", "senha": "abc"},
                {"op": "criar_conta", "usuario": "ana", "senha": "x" * 101},
            ]
            codigos = [c.consultar(pedido)["erro"]["codigo"] for pedido in pedidos]
            with self.assertRaises(cliente.DadosDeContaInvalidos) as contexto:
                c.criar_conta("ana", "abc")
            c.criar_conta(self.NOVO_USUARIO, self.NOVA_SENHA)  # o servidor segue atendendo
        self.assertEqual(set(codigos), {"REQUISICAO_INVALIDA"})
        self.assertEqual(str(contexto.exception), "Dados inválidos: a senha deve ter de 4 a 100 caracteres.")

    def test_Falha_ao_gravar_o_env_vira_erro_interno_e_nao_cria_a_conta(self):
        with self._no_ar() as (srv, linhas):
            c = self._cliente(srv)
            with mock.patch("consulta.credenciais.os.replace", side_effect=PermissionError):
                resposta = c.consultar({"op": "criar_conta", "usuario": "ana", "senha": self.NOVA_SENHA})
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.login("ana", self.NOVA_SENHA)
        self.assertEqual(resposta["erro"]["codigo"], "ERRO_INTERNO")
        self.assertFalse(self.env.exists())
        self.assertIn("op=criar_conta falha_ao_gravar (PermissionError)", "\n".join(linhas))

    def test_Sem_conta_decidir_e_recusado_e_nada_e_gravado(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            ident = c.solicitacoes()[0]["id"]
            with self.assertRaises(cliente.CredenciaisInvalidas):
                c.decidir(ident, "aprovada", **{"usuario": USUARIO, "senha": SENHA})
            self.assertEqual(c.solicitacoes()[0]["situacao"], "pendente")


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class RegrasPelaRedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.certs = gerar_certificados.gerar_certificados(Path(cls._tmp.name) / "certs")
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _no_ar(self):
        return servidor_no_ar(self.servidores, self.certs, solicitacoes.Solicitacoes(self.servidores))

    def _cliente(self, srv):
        return cliente.ClienteRede("127.0.0.1", srv.porta, self.certs / "ca.crt")

    def test_O_cliente_recebe_as_regras_pela_rede(self):
        with self._no_ar() as (srv, _):
            recebidas = self._cliente(srv).regras()
        self.assertEqual(recebidas, regras.listar())

    def test_A_resposta_e_a_mesma_para_todo_cliente_e_a_qualquer_hora(self):
        with self._no_ar() as (srv, _):
            c = self._cliente(srv)
            primeira = c.regras()
            c.decidir(c.solicitacoes()[0]["id"], "aprovada", USUARIO, SENHA)  # decidir não muda o texto
            self.assertEqual(c.regras(), primeira)

    def test_Parametros_extras_sao_ignorados(self):
        with self._no_ar() as (srv, _):
            resposta = self._cliente(srv).consultar({"op": "regras", "id": 1, "nome": "x"})
        self.assertTrue(resposta["ok"])
        self.assertEqual(resposta["dados"], regras.listar())

    def test_O_log_registra_a_operacao(self):
        with self._no_ar() as (srv, linhas):
            self._cliente(srv).regras()
            limite = time.monotonic() + 5
            while len(linhas) < 1 and time.monotonic() < limite:
                time.sleep(0.01)
        self.assertIn("op=regras resultado=ok", "\n".join(linhas))


if __name__ == "__main__":
    unittest.main()
