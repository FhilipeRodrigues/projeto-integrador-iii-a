import contextlib
import gc
import socket
import ssl
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk
from unittest import mock

from consulta import base, cliente, dominio, interface, regras, solicitacoes
from scripts import gerar_certificados
from tests.test_integracao_tls import SENHA, USUARIO, _openssl, servidor_no_ar, servidor_no_ar_em

RAIZ = Path(__file__).resolve().parent.parent
SERVIDORES = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]
# Dois servidores achados pela busca "pereira", sem fixar ids que dependem do sorteio da base.
ID_A, ID_B = [s["id"] for s in dominio.buscar(SERVIDORES, "pereira")][:2]


class ClienteFalso:
    """Responde como o servidor, a partir da base, sem rede nem certificados."""

    def __init__(self):
        self._pedidos = solicitacoes.Solicitacoes(SERVIDORES)

    def municipios(self):
        return dominio.listar_municipios(SERVIDORES)

    def buscar(self, nome, municipio=None):
        return dominio.buscar(SERVIDORES, nome, municipio)

    def ficha(self, identificacao):
        servidor = next(s for s in SERVIDORES if s["id"] == identificacao)
        return dominio.montar_ficha(servidor, self._pedidos.situacao_do_servidor(identificacao))

    def solicitacoes(self):
        return self._pedidos.listar()

    def documento(self, identificacao):
        pedido = self._pedidos.obter(identificacao)
        servidor = next(s for s in SERVIDORES if s["id"] == pedido["servidor_id"])
        return dominio.montar_documento(servidor, pedido)

    def login(self, usuario, senha):
        self._conferir(usuario, senha)
        return {"usuario": usuario}

    @staticmethod
    def _conferir(usuario, senha):
        if (usuario, senha) != (USUARIO, SENHA):
            raise cliente.CredenciaisInvalidas("Usuário ou senha inválidos.")

    def decidir(self, identificacao, decisao, usuario, senha):
        self._conferir(usuario, senha)
        pedido = self._pedidos.decidir(identificacao, decisao)
        servidor = next(s for s in SERVIDORES if s["id"] == pedido["servidor_id"])
        return dominio.montar_documento(servidor, pedido)

    def regras(self):
        return regras.listar()


def _destruir(raiz):
    """Fecha a janela e recolhe o lixo aqui, na thread principal.

    Sem isso o coletor de ciclos roda numa thread de trabalho e finaliza variáveis do Tk
    de janelas já fechadas: cada uma espera ~1 s pela thread principal e atrasa a consulta
    do teste seguinte além do limite de 5 s.
    """
    raiz.destroy()
    gc.collect()


def _percorrer(widget):
    yield widget
    for filho in widget.winfo_children():
        yield from _percorrer(filho)


class JanelaBase(unittest.TestCase):
    cliente_de_rede = ClienteFalso
    usuario_inicial = USUARIO  # None faz a janela abrir pelo login

    def setUp(self):
        try:
            self.raiz = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"sem ambiente gráfico: {erro}")
        self.raiz.withdraw()
        self.addCleanup(_destruir, self.raiz)
        self.addCleanup(setattr, self, "janela", None)  # roda antes: solta a janela para o coletor
        self.janela = interface.JanelaConsulta(self.raiz, self.cliente_de_rede(), self.usuario_inicial)
        self.esperar()

    def esperar(self):
        limite = time.monotonic() + 5
        while self.janela.aguardando():
            self.assertLess(time.monotonic(), limite, "a janela não concluiu a consulta")
            self.raiz.update()
            time.sleep(0.01)
        self.raiz.update()

    def buscar(self, nome, municipio=interface.TODOS_OS_MUNICIPIOS):
        self.janela._nome.set(nome)
        self.janela._municipio.set(municipio)
        self.janela.buscar()
        self.esperar()

    def linhas(self):
        return [self.janela._lista.item(i, "values") for i in self.janela._lista.get_children()]

    def abrir_aba(self, aba=None):
        self.janela._abas.select(aba or self.janela._aba_solicitacoes)
        self.raiz.update()  # entrega o evento de troca de aba, que pede a lista
        self.esperar()

    def linhas_solicitacoes(self):
        lista = self.janela._lista_solicitacoes
        return [lista.item(i, "values") for i in lista.get_children()]


class InterfaceBuscaTest(JanelaBase):
    def test_A_janela_avisa_que_os_dados_sao_ficticios(self):
        textos = [str(w.cget("text")) for w in _percorrer(self.raiz) if "text" in w.keys()]
        self.assertIn("Dados fictícios, para demonstração", textos)

    def test_A_janela_abre_com_todos_os_servidores_listados(self):
        linhas = self.linhas()
        self.assertEqual(len(linhas), len(SERVIDORES))
        self.assertEqual(linhas, [(s["nome"], s["municipio"]) for s in dominio.buscar(SERVIDORES, "")])
        self.assertEqual(self.janela._situacao.get(), f"{len(SERVIDORES)} servidor(es) encontrado(s)")
        self.assertEqual(self.janela._nome.get(), "")
        self.assertFalse(self.janela._botao_buscar.instate(["disabled"]))

    def test_Os_municipios_aparecem_para_escolha(self):
        seletor = self.janela._seletor
        self.assertEqual(seletor.get(), "Todos os municípios")
        municipios = list(seletor.cget("values"))[1:]
        self.assertEqual(len(municipios), 10)
        self.assertEqual(municipios, sorted(municipios, key=dominio.normalizar))

    def test_Buscar_por_trecho_do_nome(self):
        self.buscar("pereira")
        linhas = self.linhas()
        self.assertTrue(linhas)
        for nome, municipio in linhas:
            self.assertIn("pereira", dominio.normalizar(nome))
            self.assertTrue(municipio)

    def test_Buscar_com_a_tecla_Enter(self):
        self.janela._nome.set("pereira")
        entrada = next(w for w in _percorrer(self.raiz) if isinstance(w, ttk.Entry))
        self.raiz.deiconify()  # o foco só chega ao campo com a janela visível
        entrada.focus_force()
        self.raiz.update()
        entrada.event_generate("<Return>")
        self.esperar()
        esperado = {s["nome"] for s in dominio.buscar(SERVIDORES, "pereira")}
        self.assertTrue(esperado)
        self.assertEqual({nome for nome, _ in self.linhas()}, esperado)

    def test_Buscar_dentro_de_um_municipio(self):
        self.buscar("lima")
        self.assertGreater(len({municipio for _, municipio in self.linhas()}), 1)
        self.buscar("lima", "Anápolis")
        linhas = self.linhas()
        self.assertTrue(linhas)
        self.assertEqual({municipio for _, municipio in linhas}, {"Anápolis"})

    def test_Buscar_com_o_nome_vazio(self):
        self.buscar("")
        self.assertEqual(len(self.linhas()), 50)
        self.buscar("", "Anápolis")
        self.assertEqual(
            len(self.linhas()), len([s for s in SERVIDORES if s["municipio"] == "Anápolis"])
        )

    def test_Nenhum_servidor_encontrado(self):
        self.buscar("zzz")
        self.assertEqual(self.linhas(), [])
        self.assertEqual(self.janela._situacao.get(), "Nenhum servidor encontrado")

    def test_A_janela_e_legivel_em_gravacao_de_tela(self):
        estilo = ttk.Style(self.raiz)
        for widget in _percorrer(self.raiz):
            if isinstance(widget, ttk.Treeview):
                nomes = [estilo.lookup("Treeview", "font"), estilo.lookup("Treeview.Heading", "font")]
            else:
                proprio = str(widget.cget("font")) if "font" in widget.keys() else ""
                nomes = [proprio or estilo.lookup(widget.winfo_class(), "font")]
            for nome in nomes:
                fonte = tkfont.Font(root=self.raiz, font=nome or "TkDefaultFont")
                self.assertGreaterEqual(fonte.actual("size"), 12, f"{widget} usa a fonte {nome!r}")

    def test_Uma_falha_da_consulta_nao_derruba_a_janela(self):
        class Quebrado(ClienteFalso):
            def buscar(self, nome, municipio=None):
                raise cliente.ErroDeRede("sem rede")

        self.janela._cliente = Quebrado()
        self.buscar("pereira")
        self.assertEqual(self.janela._situacao.get(), "sem rede")


class InterfaceFichaTest(JanelaBase):
    def selecionar(self, identificacao):
        self.janela._lista.selection_set(str(identificacao))
        self.raiz.update()  # entrega o evento de seleção, que pede a ficha
        self.esperar()

    def ficha(self):
        return {c: v.get() for c, v in self.janela._valores_ficha.items()}

    def ficha_visivel(self):
        return self.janela._campos_ficha.winfo_manager() == "grid"

    def com_servidor(self, **campos):
        servidor = dict(SERVIDORES[0], id=9001, nome="Fulano de Teste", **campos)

        class Isolado(ClienteFalso):
            def buscar(self, nome, municipio=None):
                return dominio.buscar([servidor], nome, municipio)

            def ficha(self, identificacao):
                return dominio.montar_ficha(servidor)

        self.janela._cliente = Isolado()
        self.buscar("fulano")
        self.selecionar(9001)
        return self.ficha()

    def test_Selecionar_um_servidor_mostra_a_ficha(self):
        self.buscar("pereira")
        self.selecionar(ID_A)
        servidor = next(s for s in SERVIDORES if s["id"] == ID_A)
        rotulos = [str(w.cget("text")) for w in _percorrer(self.janela._campos_ficha)
                   if isinstance(w, ttk.Label)]
        for _, rotulo in interface.CAMPOS_DA_FICHA:
            self.assertIn(rotulo, rotulos)
        self.assertEqual(len(self.ficha()), 12)
        self.assertTrue(all(self.ficha().values()))
        self.assertEqual(self.ficha()["nome"], servidor["nome"])
        self.assertEqual(self.ficha()["municipio"], servidor["municipio"])
        self.assertTrue(self.ficha_visivel())

    def test_Os_valores_aparecem_em_formato_brasileiro(self):
        ficha = self.com_servidor(
            data_ingresso="1994-03-01", data_solicitacao="2026-09-15",
            ultima_remuneracao_centavos=485000,
        )
        self.assertEqual(ficha["data_ingresso"], "01/03/1994")
        self.assertEqual(ficha["data_solicitacao"], "15/09/2026")
        self.assertEqual(ficha["ultima_remuneracao_centavos"], "R$ 4.850,00")
        self.assertEqual(ficha["tempo_contribuicao_anos"], "32 anos")

    def test_Remuneracao_com_milhar_e_centavos(self):
        self.assertEqual(interface._dinheiro_br(123456789), "R$ 1.234.567,89")
        self.assertEqual(interface._dinheiro_br(5), "R$ 0,05")

    def test_PCD_e_doenca_profissional_ou_acidente_de_trabalho(self):
        ficha = self.com_servidor(pcd=False, doenca_profissional=None)
        self.assertEqual((ficha["pcd"], ficha["doenca_profissional"]), ("Não", "Não"))
        ficha = self.com_servidor(pcd=True, doenca_profissional="Tendinite ocupacional")
        self.assertEqual(
            (ficha["pcd"], ficha["doenca_profissional"]), ("Sim", "Sim: Tendinite ocupacional")
        )

    def test_Selecionar_outro_servidor_atualiza_a_ficha(self):
        self.buscar("pereira")
        self.selecionar(ID_A)
        primeira = self.ficha()
        self.selecionar(ID_B)
        self.assertNotEqual(self.ficha()["nome"], primeira["nome"])
        self.assertEqual(self.ficha()["nome"], next(s["nome"] for s in SERVIDORES if s["id"] == ID_B))

    def test_Uma_nova_busca_limpa_a_ficha(self):
        self.buscar("pereira")
        self.selecionar(ID_A)
        self.assertTrue(self.ficha_visivel())
        self.buscar("lima")
        self.assertFalse(self.ficha_visivel())
        self.assertFalse(any(self.ficha().values()))
        self.selecionar(self.janela._lista.get_children()[0])
        self.assertTrue(self.ficha_visivel())

    def test_Ficha_que_chega_depois_de_nova_busca_e_descartada(self):
        self.buscar("pereira")
        self.janela._lista.selection_set(str(ID_A))
        self.raiz.update()  # dispara o pedido da ficha, sem esperar a resposta
        self.janela._nome.set("lima")
        self.janela.buscar()
        self.esperar()
        self.assertFalse(self.ficha_visivel())

    def test_A_ficha_nao_indica_elegibilidade_nem_mostra_a_data_de_nascimento(self):
        self.buscar("pereira")
        self.selecionar(ID_A)
        servidor = next(s for s in SERVIDORES if s["id"] == ID_A)
        textos = [str(w.cget("text")) for w in _percorrer(self.raiz) if "text" in w.keys()]
        textos += [v for v in self.ficha().values()]
        junto = " ".join(textos).casefold()
        for proibido in ("aposent", "elegib", "apto", "nascimento"):
            self.assertNotIn(proibido, junto)
        self.assertNotIn(interface._data_br(servidor["data_nascimento"]), junto)


class InterfaceAbaSolicitacoesTest(JanelaBase):
    def selecionar(self, identificacao):
        self.janela._lista_solicitacoes.selection_set(str(identificacao))
        self.raiz.update()
        self.esperar()

    def texto(self):
        return self.janela._documento.get("1.0", "end")

    def solicitacao_do_sexo(self, sexo):
        for item in self.janela._cliente.solicitacoes():
            documento = self.janela._cliente.documento(item["id"])
            if documento["sexo"] == sexo:
                return documento
        self.fail(f"nenhuma solicitação com sexo {sexo}")

    def test_A_janela_tem_as_abas_Consulta_Solicitacoes_e_Regras(self):
        abas = self.janela._abas
        self.assertEqual(
            [abas.tab(a, "text") for a in abas.tabs()], ["Consulta", "Solicitações", "Regras"]
        )
        self.assertEqual(abas.select(), str(self.janela._aba_consulta))

    def test_A_aba_Solicitacoes_lista_os_requerimentos(self):
        self.abrir_aba()
        linhas = self.linhas_solicitacoes()
        self.assertEqual(len(linhas), 10)
        for numero, servidor, municipio, situacao in linhas:
            self.assertRegex(numero, r"^REQ-2026-\d{4}$")
            self.assertTrue(servidor and municipio)
            self.assertEqual(situacao, "Pendente")

    def test_Selecionar_uma_solicitacao_mostra_o_documento_formal(self):
        self.abrir_aba()
        primeira = self.janela._lista_solicitacoes.get_children()[0]
        self.selecionar(primeira)
        dados = self.janela._cliente.documento(int(primeira))
        texto = self.texto()
        self.assertTrue(texto.startswith("Requerimento de aposentadoria\n"))
        for esperado in (
            dados["numero"], dados["municipio"], dados["orgao"], dados["servidor_nome"],
            interface._data_br(dados["data_ingresso"]),
            interface._data_br(dados["data_solicitacao"]),
            "aposentadoria voluntária", "______",
        ):
            self.assertIn(esperado, texto)
        # a assinatura é a linha do nome, logo abaixo do traço
        self.assertIn(f"______\n{dados['servidor_nome']}", texto)

    def test_O_texto_concorda_com_o_sexo_do_servidor(self):
        self.abrir_aba()
        servidora = self.solicitacao_do_sexo("F")
        self.selecionar(servidora["id"])
        self.assertIn("a servidora", self.texto())
        self.assertNotIn("o servidor ", self.texto())
        servidor = self.solicitacao_do_sexo("M")
        self.selecionar(servidor["id"])
        self.assertIn("o servidor", self.texto())
        self.assertNotIn("a servidora", self.texto())

    def test_O_documento_deixa_os_dados_da_analise_para_a_consulta(self):
        self.abrir_aba()
        for item in self.janela._cliente.solicitacoes():
            self.selecionar(item["id"])
            texto = self.texto().casefold()
            for proibido in (r"\bidade\b", "contribui", r"\bpcd\b", "doença", "remunera",
                             "elegib", r"\bapto\b", r"pode se aposentar", "requisitos"):
                self.assertNotRegex(texto, proibido)

    def test_O_documento_e_legivel_e_avisa_que_e_ficticio(self):
        self.abrir_aba()
        self.selecionar(self.janela._lista_solicitacoes.get_children()[0])
        rotulos = [str(w.cget("text")) for w in _percorrer(self.janela._aba_solicitacoes)
                   if isinstance(w, ttk.Label)]
        self.assertIn("Documento fictício, para demonstração", rotulos)
        documento = self.janela._documento
        fontes = [documento.cget("font"), documento.tag_cget("titulo", "font")]
        for nome in fontes:
            self.assertGreaterEqual(tkfont.Font(root=self.raiz, font=nome).actual("size"), 12)

    def test_Trocar_de_aba_nao_perde_a_consulta(self):
        self.buscar("maria")
        self.janela._lista.selection_set(self.janela._lista.get_children()[0])
        self.raiz.update()
        self.esperar()
        antes = (self.linhas(), self.janela._situacao.get(),
                 {c: v.get() for c, v in self.janela._valores_ficha.items()})
        self.assertTrue(antes[0] and all(antes[2].values()))
        self.abrir_aba()
        self.abrir_aba(self.janela._aba_consulta)
        depois = (self.linhas(), self.janela._situacao.get(),
                  {c: v.get() for c, v in self.janela._valores_ficha.items()})
        self.assertEqual(depois, antes)
        self.assertEqual(self.janela._nome.get(), "maria")
        self.assertEqual(self.janela._lista.selection(), (self.janela._lista.get_children()[0],))

    def test_Documento_que_chega_depois_de_outra_selecao_e_descartado(self):
        self.abrir_aba()
        a, b = self.janela._lista_solicitacoes.get_children()[:2]
        liberar = threading.Event()
        original = self.janela._cliente.documento

        def lento(identificacao):
            if identificacao == int(a):
                liberar.wait(5)
            return original(identificacao)

        self.janela._cliente.documento = lento
        self.janela._lista_solicitacoes.selection_set(a)
        self.raiz.update()  # pede o documento de a, que demora
        self.janela._lista_solicitacoes.selection_set(b)
        self.raiz.update()
        liberar.set()
        self.esperar()
        self.assertIn(original(int(b))["numero"], self.texto())

    def test_Documento_em_voo_nao_reaparece_apos_falha_ao_recarregar_a_lista(self):
        self.abrir_aba()
        a = self.janela._lista_solicitacoes.get_children()[0]
        liberar = threading.Event()
        original = self.janela._cliente.documento

        def lento(identificacao):
            liberar.wait(5)
            return original(identificacao)

        self.janela._cliente.documento = lento
        self.janela._lista_solicitacoes.selection_set(a)
        self.raiz.update()
        self.janela._cliente = ClienteParado()
        self.janela._abas.select(self.janela._aba_consulta)
        self.raiz.update()
        self.janela._abas.select(self.janela._aba_solicitacoes)  # a lista falha e invalida o documento
        self.raiz.update()
        time.sleep(0.2)
        self.raiz.update()
        liberar.set()
        self.esperar()
        self.assertNotIn("Requerimento de aposentadoria", self.texto())
        self.assertEqual(self.janela._situacao_solicitacoes.get(), MSG_PARADO)

    def test_Lista_antiga_que_chega_depois_da_nova_e_descartada(self):
        self.abrir_aba()
        liberar = threading.Event()
        original = self.janela._cliente.solicitacoes
        chamadas = []

        def lenta():
            chamadas.append(1)
            if len(chamadas) == 1:
                liberar.wait(5)
                return original()[:3]  # resposta velha, com outro conteúdo
            return original()

        self.janela._cliente.solicitacoes = lenta
        self.janela._abas.select(self.janela._aba_consulta)
        self.raiz.update()
        self.janela._abas.select(self.janela._aba_solicitacoes)
        self.raiz.update()
        self.janela._abas.select(self.janela._aba_consulta)
        self.raiz.update()
        self.janela._abas.select(self.janela._aba_solicitacoes)
        self.raiz.update()
        liberar.set()
        self.esperar()
        self.assertEqual(len(self.linhas_solicitacoes()), 10)

    def test_Reabrir_a_aba_atualiza_a_lista_sem_perder_a_selecao(self):
        self.abrir_aba()
        escolhida = self.janela._lista_solicitacoes.get_children()[2]
        self.selecionar(escolhida)
        self.abrir_aba(self.janela._aba_consulta)
        self.abrir_aba()
        self.assertEqual(len(self.linhas_solicitacoes()), 10)
        self.assertEqual(self.janela._lista_solicitacoes.selection(), (escolhida,))


MSG_PARADO = "Não foi possível conectar ao servidor. Verifique se ele está em execução."
MSG_NAO_CONFIAVEL = "Servidor não confiável: o certificado não foi emitido pela CA do projeto."


class ClienteParado(ClienteFalso):
    def municipios(self):
        raise cliente.ErroDeRede(MSG_PARADO)

    def buscar(self, nome, municipio=None):
        raise cliente.ErroDeRede(MSG_PARADO)

    def solicitacoes(self):
        raise cliente.ErroDeRede(MSG_PARADO)

    def documento(self, identificacao):
        raise cliente.ErroDeRede(MSG_PARADO)

    def login(self, usuario, senha):
        raise cliente.ErroDeRede(MSG_PARADO)

    def decidir(self, identificacao, decisao, usuario, senha):
        raise cliente.ErroDeRede(MSG_PARADO)

    def regras(self):
        raise cliente.ErroDeRede(MSG_PARADO)


class InterfaceServidorParadoTest(JanelaBase):
    cliente_de_rede = ClienteParado

    def test_O_servidor_esta_parado_ao_abrir_a_janela(self):
        self.assertEqual(self.janela._situacao.get(), MSG_PARADO)
        self.assertEqual(tuple(self.janela._seletor.cget("values")), (interface.TODOS_OS_MUNICIPIOS,))

    def test_O_servidor_esta_parado_ao_buscar(self):
        self.buscar("maria")
        self.assertEqual(self.janela._situacao.get(), MSG_PARADO)
        self.assertEqual(self.linhas(), [])
        self.assertTrue(self.janela._botao_buscar.instate(["!disabled"]))  # janela utilizável

    def test_Falha_de_rede_na_aba_Solicitacoes(self):
        self.abrir_aba()
        self.assertEqual(self.janela._situacao_solicitacoes.get(), MSG_PARADO)
        self.assertEqual(self.linhas_solicitacoes(), [])
        # a janela segue viva: troca de aba e atende de novo assim que o servidor volta
        self.abrir_aba(self.janela._aba_consulta)
        self.janela._cliente = ClienteFalso()
        self.buscar("pereira")
        self.assertTrue(self.linhas())
        self.abrir_aba()
        self.assertEqual(len(self.linhas_solicitacoes()), 10)
        self.assertNotEqual(self.janela._situacao_solicitacoes.get(), MSG_PARADO)

    def test_O_servidor_volta_a_funcionar_sem_reiniciar_a_janela(self):
        self.janela._cliente = ClienteFalso()
        self.buscar("pereira")
        self.assertTrue(self.linhas())
        self.assertGreater(len(self.janela._seletor.cget("values")), 1)


class InterfaceDecisaoTest(JanelaBase):
    def setUp(self):
        super().setUp()
        self.abrir_aba()
        self.pedidos = self.janela._cliente._pedidos

    def selecionar(self, identificacao):
        self.janela._lista_solicitacoes.selection_set(str(identificacao))
        self.raiz.update()
        self.esperar()

    def decidir(self, botao, senha=SENHA):
        botao.invoke()
        self.confirmar(senha)

    def confirmar(self, senha=SENHA):
        dialogo = self.janela._dialogo
        dialogo.campo_senha.insert(0, senha)
        dialogo.confirmar()
        self.esperar()

    def texto(self):
        return self.janela._documento.get("1.0", "end")

    def situacao_na_lista(self, identificacao):
        return self.janela._lista_solicitacoes.set(str(identificacao), "situacao")

    def ficha_do_servidor_da(self, identificacao):
        """Na aba Consulta: busca o servidor da solicitação, abre a ficha e devolve a situação."""
        servidor_id = self.pedidos.obter(identificacao)["servidor_id"]
        nome = next(s["nome"] for s in SERVIDORES if s["id"] == servidor_id)
        self.abrir_aba(self.janela._aba_consulta)
        self.buscar(nome)
        self.janela._lista.selection_set(str(servidor_id))
        self.raiz.update()
        self.esperar()
        return self.janela._valores_ficha["situacao_solicitacao"].get()

    def test_Os_botoes_so_valem_com_uma_solicitacao_selecionada(self):
        botoes = (self.janela._botao_aprovar, self.janela._botao_desaprovar)
        self.assertEqual([b.cget("text") for b in botoes], ["Aprovar", "Desaprovar"])
        self.assertTrue(all(b.instate(["disabled"]) for b in botoes))
        self.selecionar(1)
        self.assertTrue(all(b.instate(["!disabled"]) for b in botoes))

    def test_Aprovar_uma_solicitacao(self):
        self.selecionar(1)
        self.assertIn("Situação: Pendente", self.texto())
        self.decidir(self.janela._botao_aprovar)
        decidida_em = self.pedidos.obter(1)["decidida_em"]
        data, hora = decidida_em.split("T")
        self.assertIn(f"Situação: Aprovada em {interface._data_br(data)} às {hora[:5]}", self.texto())
        self.assertEqual(self.situacao_na_lista(1), "Aprovada")
        self.assertEqual(self.situacao_na_lista(2), "Pendente")
        self.assertTrue(self.janela._botao_aprovar.instate(["!disabled"]))  # a decisão é reversível

    def test_Desaprovar_uma_solicitacao(self):
        self.selecionar(2)
        self.decidir(self.janela._botao_desaprovar)
        self.assertRegex(self.texto(), r"Situação: Desaprovada em \d\d/\d\d/\d{4} às \d\d:\d\d")
        self.assertEqual(self.situacao_na_lista(2), "Desaprovada")

    def test_Trocar_a_decisao(self):
        self.selecionar(1)
        self.decidir(self.janela._botao_aprovar)
        self.decidir(self.janela._botao_desaprovar)
        self.assertIn("Situação: Desaprovada", self.texto())
        self.assertNotIn("Situação: Aprovada", self.texto())
        self.assertEqual(self.situacao_na_lista(1), "Desaprovada")
        self.assertEqual(self.pedidos.obter(1)["situacao"], "desaprovada")

    def test_A_decisao_continua_ao_recarregar_a_lista(self):
        self.selecionar(1)
        self.decidir(self.janela._botao_aprovar)
        self.abrir_aba(self.janela._aba_consulta)
        self.abrir_aba()
        self.assertEqual(self.situacao_na_lista(1), "Aprovada")

    def test_A_situacao_aparece_na_ficha_do_servidor(self):
        self.selecionar(1)
        self.decidir(self.janela._botao_aprovar)
        self.assertEqual(self.ficha_do_servidor_da(1), "Aprovada")

    def test_Servidor_sem_solicitacao_na_ficha(self):
        com_solicitacao = {self.pedidos.obter(n)["servidor_id"] for n in range(1, 11)}
        sem = next(s for s in SERVIDORES if s["id"] not in com_solicitacao)
        self.abrir_aba(self.janela._aba_consulta)
        self.buscar(sem["nome"])
        self.janela._lista.selection_set(str(sem["id"]))
        self.raiz.update()
        self.esperar()
        self.assertEqual(
            self.janela._valores_ficha["situacao_solicitacao"].get(), "Nenhuma solicitação"
        )

    def test_Fluxo_da_demonstracao(self):
        self.selecionar(1)
        self.assertEqual(self.ficha_do_servidor_da(1), "Pendente")
        self.abrir_aba()
        self.decidir(self.janela._botao_aprovar)
        self.abrir_aba(self.janela._aba_consulta)  # a ficha já aberta se atualiza ao voltar
        self.assertEqual(self.janela._valores_ficha["situacao_solicitacao"].get(), "Aprovada")

    def test_Servidor_fora_do_ar_na_hora_de_decidir(self):
        self.selecionar(1)
        antes = self.texto()
        self.janela._cliente = ClienteParado()
        self.decidir(self.janela._botao_aprovar)
        self.assertEqual(self.janela._situacao_solicitacoes.get(), MSG_PARADO)
        self.assertEqual(self.situacao_na_lista(1), "Pendente")
        self.assertEqual(self.texto(), antes)
        self.assertEqual(self.pedidos.obter(1)["situacao"], "pendente")
        self.assertTrue(self.janela._botao_aprovar.instate(["!disabled"]))  # dá para tentar de novo

    def test_Documento_antigo_em_voo_nao_apaga_a_decisao(self):
        liberar = threading.Event()
        original = self.janela._cliente.documento

        def lento(identificacao):
            documento = original(identificacao)  # fotografia de antes da decisão
            liberar.wait(5)
            return documento

        self.janela._cliente.documento = lento
        self.janela._lista_solicitacoes.selection_set("1")
        self.raiz.update()
        self.janela.decidir("aprovada")
        self.janela._dialogo.campo_senha.insert(0, SENHA)
        self.janela._dialogo.confirmar()
        limite = time.monotonic() + 5
        while self.janela._decidindo and time.monotonic() < limite:
            self.raiz.update()
            time.sleep(0.01)
        liberar.set()
        self.esperar()
        self.assertIn("Situação: Aprovada", self.texto())

    def test_Aprovar_pede_a_senha_antes_de_enviar(self):
        self.selecionar(1)
        self.janela._botao_aprovar.invoke()
        self.raiz.update()
        dialogo = self.janela._dialogo
        self.assertIsNotNone(dialogo)
        self.assertEqual(dialogo.campo_usuario.get(), USUARIO)
        self.assertTrue(dialogo.campo_usuario.instate(["readonly"]))
        self.assertEqual(str(dialogo.campo_senha.cget("show")), "*")
        self.assertEqual(self.pedidos.obter(1)["situacao"], "pendente")
        for botao in (self.janela._botao_aprovar, self.janela._botao_desaprovar):
            self.assertTrue(botao.instate(["disabled"]))
        self.confirmar()
        self.assertIsNone(self.janela._dialogo)
        self.assertEqual(self.situacao_na_lista(1), "Aprovada")
        self.assertTrue(self.janela._botao_aprovar.instate(["!disabled"]))

    def test_Desaprovar_tambem_pede_a_senha(self):
        self.selecionar(1)
        self.decidir(self.janela._botao_desaprovar)
        self.assertEqual(self.pedidos.obter(1)["situacao"], "desaprovada")

    def test_Senha_errada_mantem_a_confirmacao_e_nao_grava(self):
        self.selecionar(1)
        self.decidir(self.janela._botao_aprovar, senha="errada")
        dialogo = self.janela._dialogo
        self.assertIsNotNone(dialogo)
        self.assertEqual(dialogo.mensagem.get(), "Usuário ou senha inválidos.")
        self.assertEqual(dialogo.campo_senha.get(), "")
        self.assertEqual(self.pedidos.obter(1)["situacao"], "pendente")
        self.assertEqual(self.situacao_na_lista(1), "Pendente")
        self.assertTrue(dialogo.botao_confirmar.instate(["!disabled"]))
        self.confirmar()  # tenta de novo, na mesma confirmação, com a senha certa
        self.assertIsNone(self.janela._dialogo)
        self.assertEqual(self.pedidos.obter(1)["situacao"], "aprovada")

    def test_Cancelar_a_confirmacao_nao_grava_e_libera_os_botoes(self):
        self.selecionar(1)
        self.janela._botao_aprovar.invoke()
        self.janela._dialogo.cancelar()
        self.assertIsNone(self.janela._dialogo)
        self.assertEqual(self.pedidos.obter(1)["situacao"], "pendente")
        self.assertTrue(self.janela._botao_aprovar.instate(["!disabled"]))

    def test_Com_a_confirmacao_aberta_outro_clique_nao_abre_outra(self):
        self.selecionar(1)
        self.janela._botao_aprovar.invoke()
        primeira = self.janela._dialogo
        self.janela.decidir("desaprovada")
        self.assertIs(self.janela._dialogo, primeira)

    def test_Confirmar_sem_senha_nao_chama_o_servidor(self):
        self.selecionar(1)
        self.janela._botao_aprovar.invoke()
        self.janela._dialogo.confirmar()
        self.assertFalse(self.janela.aguardando())
        self.assertEqual(self.janela._dialogo.mensagem.get(), interface.INFORME_CREDENCIAIS)

    def test_Sem_selecao_decidir_nao_faz_nada(self):
        self.janela.decidir("aprovada")
        self.assertIsNone(self.janela._dialogo)
        self.esperar()
        self.assertEqual({i["situacao"] for i in self.pedidos.listar()}, {"pendente"})


class InterfaceLoginTest(JanelaBase):
    usuario_inicial = None

    def entrar(self, usuario=USUARIO, senha=SENHA):
        dialogo = self.janela._dialogo
        dialogo.campo_usuario.insert(0, usuario)
        dialogo.campo_senha.insert(0, senha)
        dialogo.confirmar()
        self.esperar()

    def test_A_janela_abre_pelo_login_sem_mostrar_dados(self):
        dialogo = self.janela._dialogo
        self.assertIsNotNone(dialogo)
        self.assertEqual(self.raiz.state(), "withdrawn")
        self.assertEqual(str(dialogo.campo_senha.cget("show")), "*")
        self.assertEqual(self.linhas(), [])  # nenhuma consulta antes do login
        rotulos = {w.cget("text") for w in _percorrer(dialogo) if isinstance(w, ttk.Label)}
        self.assertLessEqual({"Usuário", "Senha"}, rotulos)

    def test_Credencial_certa_mostra_a_janela_com_a_lista(self):
        self.entrar()
        self.assertIsNone(self.janela._dialogo)
        self.assertEqual(self.raiz.state(), "normal")
        self.assertTrue(self.linhas())
        self.assertEqual(self.janela._usuario, USUARIO)

    def test_Credencial_errada_fica_no_login_com_a_mesma_mensagem(self):
        for usuario, senha in (("outro", SENHA), (USUARIO, "errada")):
            with self.subTest(usuario=usuario):
                dialogo = self.janela._dialogo
                dialogo.campo_usuario.delete(0, "end")
                self.entrar(usuario, senha)
                self.assertIs(self.janela._dialogo, dialogo)
                self.assertEqual(dialogo.mensagem.get(), "Usuário ou senha inválidos.")
                self.assertEqual(dialogo.campo_senha.get(), "")
                self.assertEqual(self.raiz.state(), "withdrawn")
                self.assertEqual(self.linhas(), [])

    def test_Campos_vazios_nao_chamam_o_servidor(self):
        self.janela._dialogo.confirmar()
        self.assertFalse(self.janela.aguardando())
        self.assertEqual(self.janela._dialogo.mensagem.get(), interface.INFORME_CREDENCIAIS)

    def test_Cancelar_o_login_encerra_o_programa(self):
        with mock.patch.object(self.raiz, "destroy") as destruir:
            self.janela._dialogo.cancelar()
        destruir.assert_called_once_with()


class InterfaceLoginServidorParadoTest(JanelaBase):
    cliente_de_rede = ClienteParado
    usuario_inicial = None

    def test_Servidor_fora_do_ar_avisa_no_login_e_deixa_tentar_de_novo(self):
        dialogo = self.janela._dialogo
        dialogo.campo_usuario.insert(0, USUARIO)
        dialogo.campo_senha.insert(0, SENHA)
        dialogo.confirmar()
        self.esperar()
        self.assertIs(self.janela._dialogo, dialogo)
        self.assertEqual(dialogo.mensagem.get(), MSG_PARADO)
        self.assertEqual(self.raiz.state(), "withdrawn")
        self.janela._cliente = ClienteFalso()  # o servidor voltou
        dialogo.campo_senha.insert(0, SENHA)
        dialogo.confirmar()
        self.esperar()
        self.assertIsNone(self.janela._dialogo)
        self.assertEqual(self.raiz.state(), "normal")


class InterfaceConsultaLentaTest(JanelaBase):
    def test_A_janela_continua_responsiva_durante_uma_consulta_lenta(self):
        liberar = threading.Event()

        class Lento(ClienteFalso):
            def buscar(self, nome, municipio=None):
                liberar.wait(5)
                return super().buscar(nome, municipio)

        self.janela._cliente = Lento()
        self.janela._nome.set("pereira")
        self.janela.buscar()
        self.assertTrue(self.janela._botao_buscar.instate(["disabled"]))
        self.janela.buscar()  # Enter no campo durante a consulta é ignorado
        for _ in range(5):
            self.raiz.update()  # a janela atende eventos enquanto espera
        self.assertTrue(self.janela._botao_buscar.instate(["disabled"]))
        liberar.set()
        self.esperar()
        self.assertTrue(self.janela._botao_buscar.instate(["!disabled"]))
        self.assertTrue(self.linhas())


class ClienteContador(ClienteFalso):
    """Conta quantas vezes o texto das regras foi pedido ao servidor."""

    def __init__(self):
        super().__init__()
        self.pedidos_de_regras = 0

    def regras(self):
        self.pedidos_de_regras += 1
        return super().regras()


class InterfaceAbaRegrasTest(JanelaBase):
    cliente_de_rede = ClienteContador

    def texto(self):
        return self.janela._texto_regras.get("1.0", "end")

    def test_A_aba_Regras_mostra_os_tres_blocos(self):
        self.abrir_aba(self.janela._aba_regras)
        texto = self.texto()
        for bloco in regras.listar():
            self.assertIn(bloco["titulo"], texto)
            for linha in bloco["linhas"]:
                self.assertIn(linha, texto)
        self.assertEqual(self.janela._situacao_regras.get(), "")

    def test_O_texto_nao_pode_ser_editado(self):
        self.abrir_aba(self.janela._aba_regras)
        self.assertEqual(str(self.janela._texto_regras.cget("state")), "disabled")

    def test_O_texto_e_legivel_e_o_rodape_avisa_que_e_simplificado(self):
        texto = self.janela._texto_regras
        for nome in (texto.cget("font"), texto.tag_cget("bloco", "font")):
            self.assertGreaterEqual(tkfont.Font(root=self.raiz, font=nome).actual("size"), 12)
        rotulos = [str(w.cget("text")) for w in _percorrer(self.raiz) if "text" in w.keys()]
        self.assertIn(interface.RODAPE_REGRAS, rotulos)
        self.assertIn("simplificado", interface.RODAPE_REGRAS)
        self.assertIn("Não substitui a legislação", interface.RODAPE_REGRAS)

    def test_A_aba_nao_tem_botao_que_calcule_elegibilidade(self):
        botoes = [w for w in _percorrer(self.janela._aba_regras) if isinstance(w, ttk.Button)]
        self.assertEqual(botoes, [])

    def test_Abrir_a_aba_de_novo_nao_pede_o_texto_outra_vez(self):
        self.abrir_aba(self.janela._aba_regras)
        self.abrir_aba(self.janela._aba_consulta)
        self.abrir_aba(self.janela._aba_regras)
        self.assertEqual(self.janela._cliente.pedidos_de_regras, 1)

    def test_Abrir_a_aba_Regras_nao_refaz_a_ficha_da_consulta(self):
        self.buscar("pereira")
        self.janela._lista.selection_set(str(ID_A))
        self.raiz.update()
        self.esperar()
        fichas = []
        original = self.janela._cliente.ficha
        self.janela._cliente.ficha = lambda i: (fichas.append(i), original(i))[1]
        self.abrir_aba(self.janela._aba_regras)
        self.assertEqual(fichas, [])

    def test_A_aba_Consulta_continua_como_estava(self):
        self.buscar("pereira")
        antes = self.linhas()
        self.abrir_aba(self.janela._aba_regras)
        self.abrir_aba(self.janela._aba_consulta)
        self.assertEqual(self.linhas(), antes)


class InterfaceAbaRegrasServidorParadoTest(JanelaBase):
    cliente_de_rede = ClienteParado

    def test_Falha_de_rede_avisa_e_a_proxima_abertura_tenta_de_novo(self):
        self.abrir_aba(self.janela._aba_regras)
        self.assertEqual(self.janela._situacao_regras.get(), MSG_PARADO)
        self.assertEqual(self.janela._texto_regras.get("1.0", "end").strip(), "")
        self.janela._cliente = ClienteFalso()  # o servidor voltou
        self.abrir_aba(self.janela._aba_consulta)
        self.abrir_aba(self.janela._aba_regras)
        self.assertIn("Regra geral", self.janela._texto_regras.get("1.0", "end"))
        self.assertEqual(self.janela._situacao_regras.get(), "")


@unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
class InterfaceErrosDeRedeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        raiz = Path(cls._tmp.name)
        cls.certs = gerar_certificados.gerar_certificados(raiz / "certs")
        cls.certs_de_outra_ca = gerar_certificados.gerar_certificados(raiz / "outra")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def abrir(self, porta):
        try:
            raiz = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"sem ambiente gráfico: {erro}")
        raiz.withdraw()
        self.addCleanup(_destruir, raiz)
        rede = cliente.ClienteRede("127.0.0.1", porta, self.certs / "ca.crt")
        janela = interface.JanelaConsulta(raiz, rede, USUARIO)
        self.esperar(janela)
        return janela

    def esperar(self, janela):
        limite = time.monotonic() + 10
        while janela.aguardando() and time.monotonic() < limite:
            janela._raiz.update()
            time.sleep(0.01)
        janela._raiz.update()

    def buscar(self, janela, nome):
        janela._nome.set(nome)
        janela.buscar()
        self.esperar(janela)

    def test_A_conexao_cai_no_meio_da_consulta(self):
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.load_cert_chain(self.certs / "servidor.crt", self.certs / "servidor.key")
        escuta = socket.create_server(("127.0.0.1", 0))
        self.addCleanup(escuta.close)

        def fechar_sem_responder():
            while True:
                try:
                    bruto, _ = escuta.accept()
                except OSError:
                    return  # a escuta foi fechada
                try:
                    with contexto.wrap_socket(bruto, server_side=True) as seguro:
                        with seguro.makefile("rb") as arquivo:
                            arquivo.readline()
                except OSError:
                    pass

        threading.Thread(target=fechar_sem_responder, daemon=True).start()
        janela = self.abrir(escuta.getsockname()[1])
        self.buscar(janela, "maria")
        self.assertEqual(janela._situacao.get(), cliente.CONEXAO_INTERROMPIDA)
        self.assertEqual(janela._lista.get_children(), ())
        self.assertTrue(janela._botao_buscar.instate(["!disabled"]))  # pode buscar de novo

    def test_O_servidor_volta_ao_ar_e_os_municipios_aparecem(self):
        with socket.create_server(("127.0.0.1", 0)) as livre:
            porta = livre.getsockname()[1]
        janela = self.abrir(porta)
        self.assertEqual(janela._situacao.get(), MSG_PARADO)
        self.assertEqual(len(janela._seletor.cget("values")), 1)
        with servidor_no_ar_em(SERVIDORES, self.certs, porta):
            self.buscar(janela, "pereira")
        self.assertTrue(janela._lista.get_children())
        self.assertGreater(len(janela._seletor.cget("values")), 1)

    def test_O_servidor_tem_certificado_de_outra_CA(self):
        with servidor_no_ar(SERVIDORES, self.certs_de_outra_ca) as (srv, linhas):
            janela = self.abrir(srv.porta)
            self.assertEqual(janela._situacao.get(), MSG_NAO_CONFIAVEL)
            self.buscar(janela, "maria")
            self.assertEqual(janela._situacao.get(), MSG_NAO_CONFIAVEL)
            self.assertEqual(janela._lista.get_children(), ())
        # A janela não envia nada a um servidor não confiável: nenhuma busca chegou a ele.
        self.assertFalse([linha for linha in linhas if "op=buscar" in linha])


class InterfaceIntegracaoTest(unittest.TestCase):
    @contextlib.contextmanager
    def janela_no_ar(self, usuario=USUARIO):
        """Janela real ligada ao servidor real (TLS) com a base fictícia."""
        try:
            raiz = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"sem ambiente gráfico: {erro}")
        raiz.withdraw()
        self.addCleanup(_destruir, raiz)
        with tempfile.TemporaryDirectory() as tmp:
            certs = gerar_certificados.gerar_certificados(Path(tmp) / "certs")
            with servidor_no_ar(SERVIDORES, certs) as (srv, _):
                rede = cliente.ClienteRede("127.0.0.1", srv.porta, certs / "ca.crt")
                janela = interface.JanelaConsulta(raiz, rede, usuario)

                def esperar():
                    limite = time.monotonic() + 10
                    while janela.aguardando() and time.monotonic() < limite:
                        raiz.update()
                        time.sleep(0.01)
                    raiz.update()

                esperar()  # a janela já abre com a lista de todos os servidores
                yield janela, rede, esperar

    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_A_lista_corresponde_ao_que_o_servidor_tem(self):
        with self.janela_no_ar() as (janela, rede, esperar):
            janela._nome.set("pereira")
            janela.buscar()
            esperar()
            do_servidor = [(s["nome"], s["municipio"]) for s in rede.buscar("pereira")]
            na_janela = [
                tuple(janela._lista.item(i, "values")) for i in janela._lista.get_children()
            ]
        self.assertTrue(do_servidor)
        self.assertEqual(na_janela, do_servidor)

    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_A_ficha_da_janela_corresponde_ao_servidor(self):
        with self.janela_no_ar() as (janela, rede, esperar):
            raiz_update = janela._raiz.update
            janela._nome.set("pereira")
            janela.buscar()
            esperar()
            identificacao = janela._lista.get_children()[0]
            janela._lista.selection_set(identificacao)
            raiz_update()  # entrega o evento de seleção, que pede a ficha
            esperar()
            do_servidor = interface.formatar_ficha(rede.ficha(int(identificacao)))
            na_janela = {c: v.get() for c, v in janela._valores_ficha.items()}
        self.assertEqual(na_janela, do_servidor)
        self.assertTrue(all(na_janela.values()))

    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_A_aba_Solicitacoes_corresponde_ao_servidor(self):
        with self.janela_no_ar() as (janela, rede, esperar):
            janela._abas.select(janela._aba_solicitacoes)
            janela._raiz.update()
            esperar()
            do_servidor = rede.solicitacoes()
            na_janela = [
                tuple(janela._lista_solicitacoes.item(i, "values"))
                for i in janela._lista_solicitacoes.get_children()
            ]
            primeira = do_servidor[0]
            janela._lista_solicitacoes.selection_set(str(primeira["id"]))
            janela._raiz.update()
            esperar()
            texto = janela._documento.get("1.0", "end")
            documento = rede.documento(primeira["id"])
        self.assertEqual(len(do_servidor), 10)
        self.assertEqual(
            na_janela,
            [(s["numero"], s["servidor_nome"], s["municipio"], "Pendente") for s in do_servidor],
        )
        self.assertIn(documento["numero"], texto)
        self.assertIn(documento["servidor_nome"], texto)
        self.assertIn(documento["orgao"], texto)

    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_Aprovar_na_janela_chega_ao_servidor_e_volta_na_ficha(self):
        with self.janela_no_ar() as (janela, rede, esperar):
            janela._abas.select(janela._aba_solicitacoes)
            janela._raiz.update()
            esperar()
            primeira = rede.solicitacoes()[0]
            janela._lista_solicitacoes.selection_set(str(primeira["id"]))
            janela._raiz.update()
            esperar()
            janela._botao_aprovar.invoke()
            janela._dialogo.campo_senha.insert(0, SENHA)
            janela._dialogo.confirmar()
            esperar()
            no_servidor = rede.documento(primeira["id"])
            na_lista = janela._lista_solicitacoes.set(str(primeira["id"]), "situacao")
            texto = janela._documento.get("1.0", "end")
            servidor_id = next(
                s["id"] for s in SERVIDORES
                if s["nome"] == primeira["servidor_nome"] and s["municipio"] == primeira["municipio"]
            )
            ficha_no_servidor = rede.ficha(servidor_id)["situacao_solicitacao"]
            janela._abas.select(janela._aba_consulta)
            janela._nome.set(primeira["servidor_nome"])
            janela.buscar()
            esperar()
            janela._lista.selection_set(str(servidor_id))
            janela._raiz.update()
            esperar()
            na_ficha = janela._valores_ficha["situacao_solicitacao"].get()
        self.assertEqual(no_servidor["situacao"], "aprovada")
        self.assertEqual(ficha_no_servidor, "aprovada")
        self.assertEqual((na_lista, na_ficha), ("Aprovada", "Aprovada"))
        data, hora = no_servidor["decidida_em"].split("T")
        self.assertIn(f"Situação: Aprovada em {interface._data_br(data)} às {hora[:5]}", texto)

    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_Login_pela_rede_recusa_a_senha_errada_e_aceita_a_certa(self):
        with self.janela_no_ar(usuario=None) as (janela, rede, esperar):
            dialogo = janela._dialogo
            dialogo.campo_usuario.insert(0, USUARIO)
            dialogo.campo_senha.insert(0, "errada")
            dialogo.confirmar()
            esperar()
            recusado = (dialogo.mensagem.get(), janela._raiz.state(), len(janela._lista.get_children()))
            dialogo.campo_senha.insert(0, SENHA)
            dialogo.confirmar()
            esperar()
            aceito = (janela._dialogo, janela._raiz.state(), len(janela._lista.get_children()))
        self.assertEqual(recusado, ("Usuário ou senha inválidos.", "withdrawn", 0))
        self.assertIsNone(aceito[0])
        self.assertEqual(aceito[1], "normal")
        self.assertGreater(aceito[2], 0)


if __name__ == "__main__":
    unittest.main()
