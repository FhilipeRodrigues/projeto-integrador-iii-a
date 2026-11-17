"""Janela Tkinter: busca de servidores por nome e município, com a lista de resultados.

Uso: python -m consulta.interface [--host 127.0.0.1] [--porta 8443] [--ca certs/ca.crt]

A janela nunca chama a rede: cada consulta roda numa thread de trabalho, que devolve o
resultado por uma `queue.Queue` consultada com `after()` (o Tk não é seguro para threads).
"""

import argparse
import queue
import threading
import tkinter as tk
import traceback
from tkinter import font as tkfont
from tkinter import ttk

from consulta import cliente as rede

TITULO = "Consulta de servidores municipais"
AVISO_FICTICIO = "Dados fictícios, para demonstração"
TODOS_OS_MUNICIPIOS = "Todos os municípios"
SEM_RESULTADO = "Nenhum servidor encontrado"
TAMANHO_FONTE_PT = 12
INTERVALO_FILA_MS = 50
_FONTES_PADRAO = ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkFixedFont")


class JanelaConsulta:
    def __init__(self, raiz: tk.Tk, cliente_rede):
        self._raiz = raiz
        self._cliente = cliente_rede
        self._fila = queue.Queue()
        self._em_andamento = 0
        self._busca_atual = 0

        raiz.title(TITULO)
        raiz.minsize(640, 420)
        self._configurar_fontes()
        self._montar()
        self._agendamento = raiz.after(INTERVALO_FILA_MS, self._drenar_fila)
        raiz.bind("<Destroy>", self._ao_destruir)
        self._executar(self._cliente.municipios, self._mostrar_municipios)

    def aguardando(self) -> bool:
        """Há consulta de rede em andamento ou resultado ainda não aplicado à janela."""
        return self._em_andamento > 0

    def buscar(self) -> None:
        nome = self._nome.get()
        escolhido = self._municipio.get()
        municipio = None if escolhido == TODOS_OS_MUNICIPIOS else escolhido
        self._busca_atual += 1
        numero = self._busca_atual
        self._executar(
            lambda: self._cliente.buscar(nome, municipio),
            lambda resultado, erro: self._mostrar_resultados(numero, resultado, erro),
        )

    def _configurar_fontes(self) -> None:
        for nome in _FONTES_PADRAO:
            tkfont.nametofont(nome).configure(size=TAMANHO_FONTE_PT)
        estilo = ttk.Style(self._raiz)
        estilo.configure("Treeview", rowheight=30)
        estilo.configure("Aviso.TLabel", background="#fff3cd", foreground="#4d3b00", anchor="center")

    def _montar(self) -> None:
        raiz = self._raiz
        raiz.columnconfigure(0, weight=1)
        raiz.rowconfigure(2, weight=1)

        ttk.Label(raiz, text=AVISO_FICTICIO, style="Aviso.TLabel", padding=8).grid(
            row=0, column=0, sticky="ew"
        )

        formulario = ttk.Frame(raiz, padding=(12, 12, 12, 6))
        formulario.grid(row=1, column=0, sticky="ew")
        formulario.columnconfigure(1, weight=1)
        ttk.Label(formulario, text="Nome").grid(row=0, column=0, sticky="w")
        ttk.Label(formulario, text="Município").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self._nome = tk.StringVar()
        entrada = ttk.Entry(formulario, textvariable=self._nome)
        entrada.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 12))
        entrada.bind("<Return>", lambda _evento: self.buscar())
        entrada.bind("<KP_Enter>", lambda _evento: self.buscar())
        entrada.focus_set()
        self._municipio = tk.StringVar(value=TODOS_OS_MUNICIPIOS)
        self._seletor = ttk.Combobox(
            formulario, textvariable=self._municipio, values=[TODOS_OS_MUNICIPIOS],
            state="readonly", width=24,
        )
        self._seletor.grid(row=1, column=2, sticky="ew")
        ttk.Button(formulario, text="Buscar", command=self.buscar).grid(
            row=1, column=3, sticky="e", padx=(12, 0)
        )

        corpo = ttk.Frame(raiz, padding=(12, 0))
        corpo.grid(row=2, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=1)
        corpo.rowconfigure(0, weight=1)
        self._lista = ttk.Treeview(
            corpo, columns=("nome", "municipio"), show="headings", selectmode="browse"
        )
        self._lista.heading("nome", text="Nome")
        self._lista.heading("municipio", text="Município")
        self._lista.column("nome", width=360, anchor="w")
        self._lista.column("municipio", width=200, anchor="w")
        self._lista.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(corpo, orient="vertical", command=self._lista.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self._lista.configure(yscrollcommand=barra.set)

        self._situacao = tk.StringVar()
        ttk.Label(raiz, textvariable=self._situacao, padding=(12, 8)).grid(
            row=3, column=0, sticky="ew"
        )

    def _executar(self, trabalho, ao_concluir) -> None:
        """Roda `trabalho` numa thread; `ao_concluir(resultado, erro)` roda na thread da janela."""
        self._em_andamento += 1

        def rodar():
            try:
                saida = (trabalho(), None)
            except Exception as erro:  # a thread nunca derruba a janela
                saida = (None, erro)
            self._fila.put((ao_concluir, saida))

        threading.Thread(target=rodar, daemon=True).start()

    def _drenar_fila(self) -> None:
        while True:
            try:
                ao_concluir, (resultado, erro) = self._fila.get_nowait()
            except queue.Empty:
                break
            self._em_andamento -= 1
            ao_concluir(resultado, erro)
        self._agendamento = self._raiz.after(INTERVALO_FILA_MS, self._drenar_fila)

    def _ao_destruir(self, evento) -> None:
        if evento.widget is self._raiz:
            self._raiz.after_cancel(self._agendamento)

    def _mostrar_municipios(self, municipios, erro) -> None:
        if erro is not None:
            self._mostrar_erro(erro)
            return
        self._seletor.configure(values=[TODOS_OS_MUNICIPIOS, *municipios])

    def _mostrar_resultados(self, numero, servidores, erro) -> None:
        if numero != self._busca_atual:
            return  # uma busca mais nova já foi pedida
        if erro is not None:
            self._mostrar_erro(erro)
            return
        self._lista.delete(*self._lista.get_children())
        for servidor in servidores:
            self._lista.insert(
                "", "end", iid=str(servidor["id"]), values=(servidor["nome"], servidor["municipio"])
            )
        self._situacao.set(SEM_RESULTADO if not servidores else f"{len(servidores)} servidor(es) encontrado(s)")

    def _mostrar_erro(self, erro) -> None:
        # O tratamento detalhado de falhas de rede e de certificado é da task 11.
        if isinstance(erro, rede.ErroDeRede):
            self._situacao.set(str(erro))
        else:
            traceback.print_exception(erro)  # a causa vai ao terminal; a janela mostra só o aviso
            self._situacao.set("Erro inesperado ao consultar o servidor.")


def main(argumentos=None) -> int:
    analisador = argparse.ArgumentParser(description="Janela de consulta de servidores.")
    analisador.add_argument("--host", default=rede.HOST_PADRAO)
    analisador.add_argument("--porta", type=int, default=rede.PORTA_PADRAO)
    analisador.add_argument("--ca", default=str(rede.CA_PADRAO), help="certificado da CA do projeto")
    opcoes = analisador.parse_args(argumentos)

    raiz = tk.Tk()
    JanelaConsulta(raiz, rede.ClienteRede(opcoes.host, opcoes.porta, opcoes.ca))
    raiz.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
