import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk

from consulta import base, cliente, dominio, interface
from scripts import gerar_certificados
from tests.test_integracao_tls import _openssl, servidor_no_ar

RAIZ = Path(__file__).resolve().parent.parent
SERVIDORES = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]


class ClienteFalso:
    """Responde como o servidor, a partir da base, sem rede nem certificados."""

    def municipios(self):
        return dominio.listar_municipios(SERVIDORES)

    def buscar(self, nome, municipio=None):
        return dominio.buscar(SERVIDORES, nome, municipio)


def _percorrer(widget):
    yield widget
    for filho in widget.winfo_children():
        yield from _percorrer(filho)


class JanelaBase(unittest.TestCase):
    cliente_de_rede = ClienteFalso

    def setUp(self):
        try:
            self.raiz = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"sem ambiente gráfico: {erro}")
        self.raiz.withdraw()
        self.addCleanup(self.raiz.destroy)
        self.janela = interface.JanelaConsulta(self.raiz, self.cliente_de_rede())
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


class InterfaceBuscaTest(JanelaBase):
    def test_A_janela_avisa_que_os_dados_sao_ficticios(self):
        textos = [str(w.cget("text")) for w in _percorrer(self.raiz) if "text" in w.keys()]
        self.assertIn("Dados fictícios, para demonstração", textos)

    def test_Os_municipios_aparecem_para_escolha(self):
        seletor = self.janela._seletor
        self.assertEqual(seletor.get(), "Todos os municípios")
        municipios = list(seletor.cget("values"))[1:]
        self.assertEqual(len(municipios), 10)
        self.assertEqual(municipios, sorted(municipios, key=dominio.normalizar))

    def test_Buscar_por_trecho_do_nome(self):
        self.buscar("conceicao")
        linhas = self.linhas()
        self.assertTrue(linhas)
        for nome, municipio in linhas:
            self.assertIn("conceicao", dominio.normalizar(nome))
            self.assertTrue(municipio)

    def test_Buscar_com_a_tecla_Enter(self):
        self.janela._nome.set("joao")
        entrada = next(w for w in _percorrer(self.raiz) if isinstance(w, ttk.Entry))
        self.raiz.deiconify()  # o foco só chega ao campo com a janela visível
        entrada.focus_force()
        self.raiz.update()
        entrada.event_generate("<Return>")
        self.esperar()
        esperado = {s["nome"] for s in dominio.buscar(SERVIDORES, "joao")}
        self.assertTrue(esperado)
        self.assertEqual({nome for nome, _ in self.linhas()}, esperado)

    def test_Buscar_dentro_de_um_municipio(self):
        self.buscar("joana")
        self.assertGreater(len({municipio for _, municipio in self.linhas()}), 1)
        self.buscar("joana", "Anápolis")
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
        self.buscar("joao")
        self.assertEqual(self.janela._situacao.get(), "sem rede")


class InterfaceIntegracaoTest(unittest.TestCase):
    @unittest.skipUnless(_openssl(), "openssl não encontrado; veja a mensagem do script")
    def test_A_lista_corresponde_ao_que_o_servidor_tem(self):
        try:
            raiz = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f"sem ambiente gráfico: {erro}")
        raiz.withdraw()
        self.addCleanup(raiz.destroy)
        with tempfile.TemporaryDirectory() as tmp:
            certs = gerar_certificados.gerar_certificados(Path(tmp) / "certs")
            with servidor_no_ar(SERVIDORES, certs) as (srv, _):
                rede = cliente.ClienteRede("127.0.0.1", srv.porta, certs / "ca.crt")
                janela = interface.JanelaConsulta(raiz, rede)
                janela._nome.set("joao")
                janela.buscar()
                limite = time.monotonic() + 10
                while janela.aguardando() and time.monotonic() < limite:
                    raiz.update()
                    time.sleep(0.01)
                raiz.update()
                do_servidor = [(s["nome"], s["municipio"]) for s in rede.buscar("joao")]
                na_janela = [
                    tuple(janela._lista.item(i, "values")) for i in janela._lista.get_children()
                ]
        self.assertTrue(do_servidor)
        self.assertEqual(na_janela, do_servidor)


if __name__ == "__main__":
    unittest.main()
