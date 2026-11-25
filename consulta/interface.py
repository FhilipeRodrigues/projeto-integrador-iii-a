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
SELECIONE_SERVIDOR = "Selecione um servidor da lista para ver a ficha."
# (chave da ficha, rótulo), na ordem de exibição, duas por linha.
CAMPOS_DA_FICHA = (
    ("nome", "Nome completo"), ("municipio", "Município"),
    ("sexo", "Sexo"), ("idade", "Idade"),
    ("orgao", "Órgão de atuação"), ("pcd", "PCD"),
    ("doenca_profissional", "Doença profissional ou acidente de trabalho"),
    ("data_ingresso", "Data de ingresso"),
    ("data_solicitacao", "Data da solicitação"),
    ("ultima_remuneracao_centavos", "Última remuneração"),
    ("tempo_contribuicao_anos", "Tempo de contribuição"),
    ("situacao_solicitacao", "Situação da solicitação"),
)
_SEXOS = {"F": "Feminino", "M": "Masculino"}
ABA_CONSULTA = "Consulta"
ABA_SOLICITACOES = "Solicitações"
ABA_REGRAS = "Regras"
RODAPE_REGRAS = "Texto simplificado, de apoio à demonstração. Não substitui a legislação."
SELECIONE_SOLICITACAO = "Selecione uma solicitação da lista para ver o documento."
RODAPE_DOCUMENTO = "Documento fictício, para demonstração"
ROTULOS_SITUACAO = {"pendente": "Pendente", "aprovada": "Aprovada", "desaprovada": "Desaprovada"}
SEM_SOLICITACAO = "Nenhuma solicitação"
INFORME_CREDENCIAIS = "Informe usuário e senha."
COR_ERRO = "#a00000"


def _data_br(iso: str) -> str:
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


def _dinheiro_br(centavos: int) -> str:
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def _anos(quantidade: int) -> str:
    return f"{quantidade} ano" if quantidade == 1 else f"{quantidade} anos"


def formatar_ficha(ficha: dict) -> dict:
    """Valores da ficha como aparecem na janela (formato brasileiro, Sim/Não)."""
    doenca = ficha["doenca_profissional"]
    return {
        "nome": ficha["nome"],
        "municipio": ficha["municipio"],
        "sexo": _SEXOS.get(ficha["sexo"], ficha["sexo"]),
        "idade": _anos(ficha["idade"]),
        "orgao": ficha["orgao"],
        "pcd": "Sim" if ficha["pcd"] else "Não",
        "doenca_profissional": f"Sim: {doenca}" if doenca else "Não",
        "data_ingresso": _data_br(ficha["data_ingresso"]),
        "data_solicitacao": _data_br(ficha["data_solicitacao"]),
        "ultima_remuneracao_centavos": _dinheiro_br(ficha["ultima_remuneracao_centavos"]),
        "tempo_contribuicao_anos": _anos(ficha["tempo_contribuicao_anos"]),
        "situacao_solicitacao": _rotulo_da_situacao(ficha["situacao_solicitacao"]),
    }


def _rotulo_da_situacao(situacao) -> str:
    return SEM_SOLICITACAO if situacao is None else ROTULOS_SITUACAO.get(situacao, situacao)


def _situacao_do_documento(dados: dict) -> str:
    """Linha "Situação: Aprovada em 23/11/2026 às 14:05" (sem data enquanto pendente)."""
    situacao = f"Situação: {_rotulo_da_situacao(dados['situacao'])}"
    if dados["decidida_em"] is not None:
        data, hora = dados["decidida_em"].split("T")
        situacao += f" em {_data_br(data)} às {hora[:5]}"
    return situacao + "\n"


def formatar_documento(dados: dict) -> tuple:
    """Requerimento como aparece na janela: texto e etiqueta alternados, prontos para o Text.

    Só usa os campos do documento formal; o texto concorda com o sexo do servidor (RF-16).
    """
    feminino = dados["sexo"] == "F"
    artigo, lotado, ingressado = (
        ("a servidora", "lotada", "ingressada") if feminino else ("o servidor", "lotado", "ingressado")
    )
    municipio = dados["municipio"]
    corpo = (
        f"Ao Setor de Pessoal da Prefeitura Municipal de {municipio}.\n\n"
        f"Requer {artigo} {dados['servidor_nome']}, {lotado} em {dados['orgao']} e {ingressado} "
        f"em {_data_br(dados['data_ingresso'])}, a concessão de aposentadoria voluntária "
        "e a análise do ato pelo TCM-GO.\n\n"
        "Nestes termos, pede deferimento.\n\n"
        f"{municipio}, {_data_br(dados['data_solicitacao'])}.\n\n"
        f"______________________________\n{dados['servidor_nome']}\n"
    )
    return (
        f"Requerimento de aposentadoria\nNº {dados['numero']}\n", "titulo",
        _situacao_do_documento(dados), "situacao",
        corpo, "",
    )


class DialogoCredenciais(tk.Toplevel):
    """Pede usuário e senha (a senha aparece mascarada). Com `usuario_fixo`, o usuário só é exibido."""

    def __init__(self, pai, titulo, instrucao, rotulo_confirmar, ao_confirmar, ao_cancelar,
                 usuario_fixo=None):
        super().__init__(pai)
        self.title(titulo)
        self.resizable(False, False)
        self._ao_confirmar = ao_confirmar
        self._ao_cancelar = ao_cancelar
        self._ocupado = False
        self.mensagem = tk.StringVar(master=self)

        quadro = ttk.Frame(self, padding=16)
        quadro.grid(sticky="nsew")
        quadro.columnconfigure(1, weight=1)
        ttk.Label(quadro, text=instrucao, wraplength=380).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        ttk.Label(quadro, text="Usuário").grid(row=1, column=0, sticky="w", pady=4)
        self.campo_usuario = ttk.Entry(quadro, width=28)
        self.campo_usuario.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=4)
        ttk.Label(quadro, text="Senha").grid(row=2, column=0, sticky="w", pady=4)
        self.campo_senha = ttk.Entry(quadro, width=28, show="*")
        self.campo_senha.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=4)
        ttk.Label(quadro, textvariable=self.mensagem, foreground=COR_ERRO, wraplength=380).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )
        botoes = ttk.Frame(quadro)
        botoes.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        self.botao_confirmar = ttk.Button(botoes, text=rotulo_confirmar, command=self.confirmar)
        self.botao_confirmar.grid(row=0, column=0, padx=(0, 12))
        self.botao_cancelar = ttk.Button(botoes, text="Cancelar", command=self.cancelar)
        self.botao_cancelar.grid(row=0, column=1)

        if usuario_fixo is not None:
            self.campo_usuario.insert(0, usuario_fixo)
            self.campo_usuario.state(["readonly"])
        self.bind("<Return>", lambda _evento: self.confirmar())
        self.bind("<Escape>", lambda _evento: self.cancelar())
        self.protocol("WM_DELETE_WINDOW", self.cancelar)
        (self.campo_senha if usuario_fixo is not None else self.campo_usuario).focus_set()

    def confirmar(self) -> None:
        if self._ocupado:
            return
        usuario, senha = self.campo_usuario.get(), self.campo_senha.get()
        if not usuario or not senha:
            self.mensagem.set(INFORME_CREDENCIAIS)
            return
        self.mensagem.set("")
        self._definir_ocupado(True)
        self._ao_confirmar(usuario, senha)

    def cancelar(self) -> None:
        if not self._ocupado:  # uma consulta em andamento não pode ser desfeita
            self._ao_cancelar()

    def liberar(self) -> None:
        """A tentativa terminou sem sucesso: limpa a senha e deixa tentar de novo."""
        self.campo_senha.delete(0, "end")
        self._definir_ocupado(False)
        self.campo_senha.focus_set()

    def _definir_ocupado(self, ocupado: bool) -> None:
        self._ocupado = ocupado
        for botao in (self.botao_confirmar, self.botao_cancelar):
            botao.state(["disabled" if ocupado else "!disabled"])


class JanelaConsulta:
    """Sem `usuario`, a janela fica oculta até o login ser aceito pelo servidor."""

    def __init__(self, raiz: tk.Tk, cliente_rede, usuario=None):
        self._raiz = raiz
        self._cliente = cliente_rede
        self._fila = queue.Queue()
        self._em_andamento = 0
        self._busca_atual = 0
        self._ficha_atual = 0
        self._lista_atual = 0
        self._documento_atual = 0
        self._decidindo = False
        self._usuario = usuario
        self._dialogo = None
        self._regras_atual = 0
        self._regras_carregadas = False
        self._municipios_carregados = False

        raiz.title(TITULO)
        raiz.minsize(760, 700)
        self._configurar_fontes()
        self._montar()
        self._agendamento = raiz.after(INTERVALO_FILA_MS, self._drenar_fila)
        raiz.bind("<Destroy>", self._ao_destruir)
        if usuario is None:
            raiz.withdraw()
            self._pedir_login()
        else:
            self.buscar()  # nome vazio e todos os municípios: a lista já abre cheia; carrega o filtro junto

    def aguardando(self) -> bool:
        """Há consulta de rede em andamento ou resultado ainda não aplicado à janela."""
        return self._em_andamento > 0

    def buscar(self) -> None:
        if self._botao_buscar.instate(["disabled"]):
            return  # já há uma busca em andamento (Enter no campo não passa pelo botão)
        nome = self._nome.get()
        escolhido = self._municipio.get()
        municipio = None if escolhido == TODOS_OS_MUNICIPIOS else escolhido
        self._busca_atual += 1
        numero = self._busca_atual
        self._limpar_ficha()
        self._botao_buscar.state(["disabled"])
        if not self._municipios_carregados:
            self._carregar_municipios(silencioso=True)  # o servidor pode ter voltado
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
        raiz.rowconfigure(1, weight=1)

        ttk.Label(raiz, text=AVISO_FICTICIO, style="Aviso.TLabel", padding=8).grid(
            row=0, column=0, sticky="ew"
        )
        self._abas = ttk.Notebook(raiz)
        self._abas.grid(row=1, column=0, sticky="nsew")
        self._montar_consulta()
        self._montar_solicitacoes()
        self._montar_regras()
        self._abas.bind("<<NotebookTabChanged>>", self._ao_trocar_aba)

    def _montar_consulta(self) -> None:
        raiz = ttk.Frame(self._abas)
        raiz.columnconfigure(0, weight=1)
        raiz.rowconfigure(1, weight=1)
        self._aba_consulta = raiz
        self._abas.add(raiz, text=ABA_CONSULTA)

        formulario = ttk.Frame(raiz, padding=(12, 12, 12, 6))
        formulario.grid(row=0, column=0, sticky="ew")
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
        self._botao_buscar = ttk.Button(formulario, text="Buscar", command=self.buscar)
        self._botao_buscar.grid(row=1, column=3, sticky="e", padx=(12, 0))

        corpo = ttk.Frame(raiz, padding=(12, 0))
        corpo.grid(row=1, column=0, sticky="nsew")
        corpo.columnconfigure(0, weight=1)
        corpo.rowconfigure(0, weight=1)
        self._lista = ttk.Treeview(
            corpo, columns=("nome", "municipio"), show="headings", selectmode="browse", height=6
        )
        self._lista.heading("nome", text="Nome")
        self._lista.heading("municipio", text="Município")
        self._lista.column("nome", width=360, anchor="w")
        self._lista.column("municipio", width=200, anchor="w")
        self._lista.grid(row=0, column=0, sticky="nsew")
        barra = ttk.Scrollbar(corpo, orient="vertical", command=self._lista.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self._lista.configure(yscrollcommand=barra.set)
        self._lista.bind("<<TreeviewSelect>>", self._ao_selecionar)

        moldura = ttk.LabelFrame(raiz, text="Ficha do servidor", padding=12)
        moldura.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 0))
        moldura.columnconfigure((1, 3), weight=1, uniform="valor")
        self._dica_ficha = ttk.Label(moldura, text=SELECIONE_SERVIDOR)
        self._dica_ficha.grid(row=0, column=0, columnspan=4, sticky="w")
        self._campos_ficha = ttk.Frame(moldura)
        self._campos_ficha.grid(row=0, column=0, columnspan=4, sticky="ew")
        self._campos_ficha.columnconfigure((1, 3), weight=1, uniform="valor")
        self._valores_ficha = {}
        for posicao, (chave, rotulo) in enumerate(CAMPOS_DA_FICHA):
            linha, lado = divmod(posicao, 2)
            ttk.Label(self._campos_ficha, text=rotulo, wraplength=160, foreground="#555555").grid(
                row=linha, column=lado * 2, sticky="nw", padx=(0 if lado == 0 else 16, 8), pady=2
            )
            variavel = tk.StringVar()
            self._valores_ficha[chave] = variavel
            ttk.Label(self._campos_ficha, textvariable=variavel, wraplength=190).grid(
                row=linha, column=lado * 2 + 1, sticky="nw", pady=2
            )
        self._campos_ficha.grid_remove()

        self._situacao = tk.StringVar()
        ttk.Label(raiz, textvariable=self._situacao, padding=(12, 8)).grid(
            row=3, column=0, sticky="ew"
        )

    def _montar_solicitacoes(self) -> None:
        raiz = ttk.Frame(self._abas)
        raiz.columnconfigure(0, weight=1)
        raiz.rowconfigure(1, weight=1)
        self._aba_solicitacoes = raiz
        self._abas.add(raiz, text=ABA_SOLICITACOES)

        corpo = ttk.Frame(raiz, padding=(12, 12, 12, 0))
        corpo.grid(row=0, column=0, sticky="ew")
        corpo.columnconfigure(0, weight=1)
        self._lista_solicitacoes = ttk.Treeview(
            corpo, columns=("numero", "servidor", "municipio", "situacao"),
            show="headings", selectmode="browse", height=5,
        )
        for coluna, titulo, largura in (
            ("numero", "Número", 145), ("servidor", "Servidor", 235),
            ("municipio", "Município", 190), ("situacao", "Situação", 125),
        ):
            self._lista_solicitacoes.heading(coluna, text=titulo)
            self._lista_solicitacoes.column(coluna, width=largura, anchor="w")
        self._lista_solicitacoes.grid(row=0, column=0, sticky="ew")
        barra = ttk.Scrollbar(corpo, orient="vertical", command=self._lista_solicitacoes.yview)
        barra.grid(row=0, column=1, sticky="ns")
        self._lista_solicitacoes.configure(yscrollcommand=barra.set)
        self._lista_solicitacoes.bind("<<TreeviewSelect>>", self._ao_selecionar_solicitacao)

        moldura = ttk.LabelFrame(raiz, text="Documento", padding=8)
        moldura.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8, 0))
        moldura.columnconfigure(0, weight=1)
        moldura.rowconfigure(0, weight=1)
        fonte = tkfont.nametofont("TkDefaultFont")  # o Text usaria a fonte de largura fixa
        self._documento = tk.Text(
            moldura, wrap="word", height=17, width=60, padx=16, pady=8, relief="flat",
            background="#ffffff", foreground="#000000", state="disabled", cursor="arrow",
            font=fonte, spacing2=2,
        )
        self._documento.grid(row=0, column=0, sticky="nsew")
        rolagem = ttk.Scrollbar(moldura, orient="vertical", command=self._documento.yview)
        rolagem.grid(row=0, column=1, sticky="ns")
        self._documento.configure(yscrollcommand=rolagem.set)
        self._documento.tag_configure(
            "titulo", justify="center", spacing3=6,
            font=tkfont.Font(root=self._raiz, family=fonte.actual("family"),
                             size=TAMANHO_FONTE_PT + 4, weight="bold"),
        )
        self._documento.tag_configure(
            "situacao", justify="center", spacing3=12,
            font=tkfont.Font(root=self._raiz, family=fonte.actual("family"),
                             size=TAMANHO_FONTE_PT, weight="bold"),
        )
        self._documento.tag_configure("centro", justify="center")
        self._escrever_documento(SELECIONE_SOLICITACAO, "centro")
        # Fora do Text, para o aviso nunca sair da vista quando o documento for longo.
        ttk.Label(moldura, text=RODAPE_DOCUMENTO, foreground="#555555", anchor="center").grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )

        decisao = ttk.Frame(raiz, padding=(12, 8, 12, 0))
        decisao.grid(row=2, column=0, sticky="e")
        self._botao_aprovar = ttk.Button(
            decisao, text="Aprovar", command=lambda: self.decidir("aprovada")
        )
        self._botao_aprovar.grid(row=0, column=0, padx=(0, 12))
        self._botao_desaprovar = ttk.Button(
            decisao, text="Desaprovar", command=lambda: self.decidir("desaprovada")
        )
        self._botao_desaprovar.grid(row=0, column=1)
        self._atualizar_botoes()

        self._situacao_solicitacoes = tk.StringVar()
        ttk.Label(raiz, textvariable=self._situacao_solicitacoes, padding=(12, 8)).grid(
            row=3, column=0, sticky="ew"
        )

    def _montar_regras(self) -> None:
        raiz = ttk.Frame(self._abas)
        raiz.columnconfigure(0, weight=1)
        raiz.rowconfigure(0, weight=1)
        self._aba_regras = raiz
        self._abas.add(raiz, text=ABA_REGRAS)

        moldura = ttk.LabelFrame(raiz, text="Regras básicas", padding=8)
        moldura.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 0))
        moldura.columnconfigure(0, weight=1)
        moldura.rowconfigure(0, weight=1)
        fonte = tkfont.nametofont("TkDefaultFont")
        self._texto_regras = tk.Text(
            moldura, wrap="word", height=17, width=60, padx=16, pady=8, relief="flat",
            background="#ffffff", foreground="#000000", state="disabled", cursor="arrow",
            font=fonte, spacing2=2,
        )
        self._texto_regras.grid(row=0, column=0, sticky="nsew")
        rolagem = ttk.Scrollbar(moldura, orient="vertical", command=self._texto_regras.yview)
        rolagem.grid(row=0, column=1, sticky="ns")
        self._texto_regras.configure(yscrollcommand=rolagem.set)
        self._texto_regras.tag_configure(
            "bloco", spacing1=12, spacing3=4,
            font=tkfont.Font(root=self._raiz, family=fonte.actual("family"),
                             size=TAMANHO_FONTE_PT + 2, weight="bold"),
        )
        self._texto_regras.tag_configure("linha", lmargin1=12, lmargin2=28, spacing3=4)
        ttk.Label(moldura, text=RODAPE_REGRAS, foreground="#555555", anchor="center").grid(
            row=1, column=0, sticky="ew", pady=(6, 0)
        )

        self._situacao_regras = tk.StringVar()
        ttk.Label(raiz, textvariable=self._situacao_regras, padding=(12, 8)).grid(
            row=1, column=0, sticky="ew"
        )

    def _carregar_regras(self) -> None:
        """Pede o texto uma vez; se a rede falhar, a próxima abertura da aba tenta de novo."""
        if self._regras_carregadas:
            return
        self._regras_atual += 1
        numero = self._regras_atual
        self._executar(
            self._cliente.regras,
            lambda blocos, erro: self._mostrar_regras(numero, blocos, erro),
        )

    def _mostrar_regras(self, numero, blocos, erro) -> None:
        if numero != self._regras_atual:
            return  # uma consulta mais nova já foi pedida
        if erro is not None:
            self._mostrar_erro(erro, self._situacao_regras)
            return
        self._texto_regras.configure(state="normal")
        self._texto_regras.delete("1.0", "end")
        for bloco in blocos:
            self._texto_regras.insert("end", bloco["titulo"] + "\n", "bloco")
            for linha in bloco["linhas"]:
                self._texto_regras.insert("end", "• " + linha + "\n", "linha")
        self._texto_regras.configure(state="disabled")
        self._regras_carregadas = True
        self._situacao_regras.set("")

    def _ao_trocar_aba(self, _evento) -> None:
        aba = self._abas.select()
        if aba == str(self._aba_solicitacoes):
            self._carregar_solicitacoes()
        elif aba == str(self._aba_regras):
            self._carregar_regras()
        elif self._lista.selection():
            self._ao_selecionar(None)  # a decisão pode ter mudado a situação na ficha aberta

    def _carregar_solicitacoes(self) -> None:
        self._lista_atual += 1
        numero = self._lista_atual
        self._executar(
            self._cliente.solicitacoes,
            lambda itens, erro: self._mostrar_solicitacoes(numero, itens, erro),
        )

    def _mostrar_solicitacoes(self, numero, itens, erro) -> None:
        if numero != self._lista_atual:
            return  # uma consulta mais nova da lista já foi pedida
        selecionada = self._lista_solicitacoes.selection()
        self._lista_solicitacoes.delete(*self._lista_solicitacoes.get_children())
        if erro is not None:
            self._limpar_documento()
            self._mostrar_erro(erro, self._situacao_solicitacoes)
            return
        for item in itens:
            self._lista_solicitacoes.insert(
                "", "end", iid=str(item["id"]),
                values=(item["numero"], item["servidor_nome"], item["municipio"],
                        ROTULOS_SITUACAO.get(item["situacao"], item["situacao"])),
            )
        self._situacao_solicitacoes.set(f"{len(itens)} solicitação(ões)")
        if selecionada and self._lista_solicitacoes.exists(selecionada[0]):
            self._lista_solicitacoes.selection_set(selecionada[0])
        else:
            self._limpar_documento()
        self._atualizar_botoes()

    def _ao_selecionar_solicitacao(self, _evento) -> None:
        selecionadas = self._lista_solicitacoes.selection()
        if not selecionadas:
            return
        identificacao = int(selecionadas[0])
        self._atualizar_botoes()
        self._documento_atual += 1
        numero = self._documento_atual
        self._executar(
            lambda: self._cliente.documento(identificacao),
            lambda dados, erro: self._mostrar_documento(numero, dados, erro),
        )

    def _mostrar_documento(self, numero, dados, erro) -> None:
        if numero != self._documento_atual:
            return  # outra seleção ou uma nova lista já aconteceu
        if erro is not None:
            self._limpar_documento()  # não deixa na tela o documento de outra linha
            self._mostrar_erro(erro, self._situacao_solicitacoes)
            return
        self._situacao_solicitacoes.set(
            f"{len(self._lista_solicitacoes.get_children())} solicitação(ões)"
        )
        self._escrever_documento(*formatar_documento(dados))

    def _pedir_login(self) -> None:
        self._dialogo = DialogoCredenciais(
            self._raiz, "Entrar", "Informe seu usuário e senha para entrar.", "Entrar",
            ao_confirmar=self._entrar, ao_cancelar=self._sair,
        )

    def _sair(self) -> None:
        self._raiz.destroy()

    def _entrar(self, usuario: str, senha: str) -> None:
        self._executar(
            lambda: self._cliente.login(usuario, senha),
            lambda _dados, erro: self._concluir_login(usuario, erro),
        )

    def _concluir_login(self, usuario, erro) -> None:
        if erro is not None:
            self._rejeitar_credencial(erro)
            return
        self._usuario = usuario
        self._fechar_dialogo()
        self._raiz.deiconify()
        self.buscar()

    def decidir(self, decisao: str) -> None:
        """Pede a senha de novo; o servidor a confere e então aprova ou desaprova (a última vale)."""
        selecionadas = self._lista_solicitacoes.selection()
        if not selecionadas or self._decidindo or self._dialogo is not None:
            return
        identificacao = int(selecionadas[0])
        verbo = "aprovar" if decisao == "aprovada" else "desaprovar"
        self._dialogo = DialogoCredenciais(
            self._raiz, "Confirmar senha", f"Confirme sua senha para {verbo} a solicitação.",
            "Confirmar",
            ao_confirmar=lambda usuario, senha: self._confirmar_decisao(
                identificacao, decisao, usuario, senha
            ),
            ao_cancelar=self._fechar_dialogo, usuario_fixo=self._usuario,
        )
        self._dialogo.transient(self._raiz)
        self._atualizar_botoes()

    def _confirmar_decisao(self, identificacao, decisao, usuario, senha) -> None:
        self._decidindo = True
        self._executar(
            lambda: self._cliente.decidir(identificacao, decisao, usuario, senha),
            self._concluir_decisao,
        )

    def _concluir_decisao(self, documento, erro) -> None:
        if isinstance(erro, rede.CredenciaisInvalidas):
            self._decidindo = False
            self._rejeitar_credencial(erro)  # a confirmação segue aberta, para tentar de novo
            return
        self._fechar_dialogo()
        self._mostrar_decisao(documento, erro)

    def _rejeitar_credencial(self, erro) -> None:
        self._mostrar_erro(erro, self._dialogo.mensagem)
        self._dialogo.liberar()

    def _fechar_dialogo(self) -> None:
        self._dialogo.destroy()
        self._dialogo = None
        self._atualizar_botoes()

    def _mostrar_decisao(self, documento, erro) -> None:
        self._decidindo = False
        self._atualizar_botoes()
        if erro is not None:
            self._mostrar_erro(erro, self._situacao_solicitacoes)  # a tela segue como estava
            return
        identificacao = str(documento["id"])
        if self._lista_solicitacoes.exists(identificacao):
            self._lista_solicitacoes.set(
                identificacao, "situacao", _rotulo_da_situacao(documento["situacao"])
            )
        if self._lista_solicitacoes.selection() == (identificacao,):
            self._documento_atual += 1  # um documento antigo ainda a caminho não pode sobrescrever
            self._escrever_documento(*formatar_documento(documento))
        self._situacao_solicitacoes.set(
            f"{len(self._lista_solicitacoes.get_children())} solicitação(ões)"
        )

    def _atualizar_botoes(self) -> None:
        pronto = (
            bool(self._lista_solicitacoes.selection())
            and not self._decidindo
            and self._dialogo is None
        )
        for botao in (self._botao_aprovar, self._botao_desaprovar):
            botao.state(["!disabled" if pronto else "disabled"])

    def _limpar_documento(self) -> None:
        self._documento_atual += 1  # descarta o documento que ainda esteja a caminho
        self._escrever_documento(SELECIONE_SOLICITACAO, "centro")
        self._atualizar_botoes()

    def _escrever_documento(self, *partes) -> None:
        """`partes` alternam texto e a etiqueta de formatação (ou "") dele."""
        self._documento.configure(state="normal")
        self._documento.delete("1.0", "end")
        for texto, etiqueta in zip(partes[::2], partes[1::2]):
            self._documento.insert("end", texto, etiqueta)
        self._documento.configure(state="disabled")

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

    def _carregar_municipios(self, silencioso=False) -> None:
        """Pede os municípios; `silencioso` não avisa da falha (a busca que o acompanha avisa)."""
        self._executar(
            self._cliente.municipios,
            lambda municipios, erro: self._mostrar_municipios(municipios, erro, silencioso),
        )

    def _mostrar_municipios(self, municipios, erro, silencioso=False) -> None:
        if erro is not None:
            if not silencioso:
                self._mostrar_erro(erro)
            return
        self._municipios_carregados = True
        self._seletor.configure(values=[TODOS_OS_MUNICIPIOS, *municipios])

    def _mostrar_resultados(self, numero, servidores, erro) -> None:
        if numero != self._busca_atual:
            return  # uma busca mais nova já foi pedida
        self._botao_buscar.state(["!disabled"])
        self._lista.delete(*self._lista.get_children())
        if erro is not None:
            self._mostrar_erro(erro)
            return
        for servidor in servidores:
            self._lista.insert(
                "", "end", iid=str(servidor["id"]), values=(servidor["nome"], servidor["municipio"])
            )
        self._situacao.set(SEM_RESULTADO if not servidores else f"{len(servidores)} servidor(es) encontrado(s)")

    def _ao_selecionar(self, _evento) -> None:
        selecionados = self._lista.selection()
        if not selecionados:
            return
        identificacao = int(selecionados[0])
        self._ficha_atual += 1
        numero = self._ficha_atual
        self._executar(
            lambda: self._cliente.ficha(identificacao),
            lambda ficha, erro: self._mostrar_ficha(numero, ficha, erro),
        )

    def _mostrar_ficha(self, numero, ficha, erro) -> None:
        if numero != self._ficha_atual:
            return  # outra seleção ou uma nova busca já aconteceu
        if erro is not None:
            self._mostrar_erro(erro)
            return
        for chave, valor in formatar_ficha(ficha).items():
            self._valores_ficha[chave].set(valor)
        self._dica_ficha.grid_remove()
        self._campos_ficha.grid()

    def _limpar_ficha(self) -> None:
        self._ficha_atual += 1  # descarta a ficha que ainda esteja a caminho
        for variavel in self._valores_ficha.values():
            variavel.set("")
        self._campos_ficha.grid_remove()
        self._dica_ficha.grid()

    def _mostrar_erro(self, erro, destino=None) -> None:
        destino = self._situacao if destino is None else destino
        if isinstance(erro, rede.ErroDeRede):
            destino.set(str(erro))
        else:
            traceback.print_exception(erro)  # a causa vai ao terminal; a janela mostra só o aviso
            destino.set("Erro inesperado ao consultar o servidor.")


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
