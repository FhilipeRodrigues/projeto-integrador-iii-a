"""Enquadramento das mensagens: um objeto JSON em UTF-8 por linha, até 64 KiB."""

import json

LIMITE_LINHA = 64 * 1024


REQUISICAO_INVALIDA = "REQUISICAO_INVALIDA"
OPERACAO_DESCONHECIDA = "OPERACAO_DESCONHECIDA"
NAO_ENCONTRADO = "NAO_ENCONTRADO"
ERRO_INTERNO = "ERRO_INTERNO"
CREDENCIAIS_INVALIDAS = "CREDENCIAIS_INVALIDAS"
CONTA_JA_EXISTE = "CONTA_JA_EXISTE"


class ProtocoloErro(ValueError):
    """A mensagem recebida não cumpre o formato do protocolo."""


class ConexaoEncerrada(ProtocoloErro):
    """O outro lado fechou o canal antes de enviar a mensagem."""


class LinhaGrandeDemais(ProtocoloErro):
    """A linha passou de `LIMITE_LINHA`; o restante dela ainda está no canal."""


class ErroDeAtendimento(Exception):
    """Pedido que o servidor recusa; vira uma resposta de erro com `codigo` e `mensagem`."""

    def __init__(self, codigo: str, mensagem: str):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


def resposta_erro(codigo: str, mensagem: str) -> dict:
    return {"ok": False, "erro": {"codigo": codigo, "mensagem": mensagem}}


def ler_mensagem(arquivo) -> dict:
    """Lê uma linha de um arquivo binário (ex.: `soquete.makefile('rb')`) e a decodifica."""
    linha = arquivo.readline(LIMITE_LINHA + 1)
    if not linha:
        raise ConexaoEncerrada("a conexão foi encerrada sem enviar mensagem")
    if len(linha) > LIMITE_LINHA:
        raise LinhaGrandeDemais("a mensagem é grande demais")
    if not linha.endswith(b"\n"):
        raise ProtocoloErro("a mensagem está incompleta")
    try:
        mensagem = json.loads(linha.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as erro:
        raise ProtocoloErro("a mensagem não é um JSON válido") from erro
    if not isinstance(mensagem, dict):
        raise ProtocoloErro("a mensagem deve ser um objeto JSON")
    return mensagem


def descartar_excesso(arquivo, limite: int = 2 * LIMITE_LINHA) -> None:
    """Joga fora, em blocos, o resto de uma linha grande demais (até `limite` bytes).

    Fechar o canal com dados não lidos faz o sistema resetar a conexão e a resposta de erro
    pode se perder; descartar em blocos evita isso sem guardar a linha na memória.
    """
    while limite > 0:
        try:
            bloco = arquivo.read1(min(4096, limite))
        except OSError:
            return
        if not bloco or b"\n" in bloco:
            return  # fim da linha (ou do canal): não há mais o que descartar
        limite -= len(bloco)


def escrever_mensagem(soquete, mensagem: dict) -> None:
    """Envia `mensagem` como uma linha JSON."""
    soquete.sendall(json.dumps(mensagem, ensure_ascii=False).encode("utf-8") + b"\n")
