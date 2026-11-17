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

from consulta import base, cliente, dominio, servidor
from scripts import gerar_certificados

RAIZ = Path(__file__).resolve().parent.parent


def _openssl():
    try:
        return gerar_certificados.localizar_openssl()
    except gerar_certificados.OpenSslAusente:
        return None


@contextlib.contextmanager
def servidor_no_ar_em(servidores, pasta_certs, porta):
    """Sobe o servidor na `porta` dada (0 = livre); devolve (servidor, linhas de log)."""
    linhas = []
    srv = servidor.Servidor(servidores, pasta_certs, "127.0.0.1", porta, log=linhas.append)
    srv.iniciar()
    fio = threading.Thread(target=srv.servir)
    fio.start()
    try:
        yield srv, linhas
    finally:
        srv.parar()
        fio.join(timeout=5)


def servidor_no_ar(servidores, pasta_certs):
    """Sobe o servidor numa porta livre; devolve (servidor, linhas de log)."""
    return servidor_no_ar_em(servidores, pasta_certs, 0)


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
                servidor.Servidor(self.servidores, vazia, "127.0.0.1", 0)
            self.assertIn("gerar_certificados.py", str(contexto.exception))

            erro = io.StringIO()
            with contextlib.redirect_stderr(erro):
                codigo = servidor.main(["--certs", vazia, "--porta", "0"])
        self.assertEqual(codigo, 1)
        self.assertIn("gerar_certificados.py", erro.getvalue())

    def test_Buscar_por_trecho_do_nome(self):
        with servidor_no_ar(self.servidores, self.certs) as (srv, _):
            lista = self._cliente(srv).buscar("conceicao")
        self.assertTrue(lista)
        for item in lista:
            self.assertEqual(set(item), {"id", "nome", "municipio"})
            self.assertIn("conceicao", dominio.normalizar(item["nome"]))

    def _com_marias(self):
        """A base fictícia atual não tem nenhuma "Maria": renomeia três para o cenário."""
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
             "tempo_contribuicao_anos"},
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


if __name__ == "__main__":
    unittest.main()
