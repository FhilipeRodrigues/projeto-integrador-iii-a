"""Enquadramento das mensagens: um objeto JSON em UTF-8 por linha, até 64 KiB."""

import json

LIMITE_LINHA = 64 * 1024


class ProtocoloErro(ValueError):
    """A mensagem recebida não cumpre o formato do protocolo."""


def ler_mensagem(arquivo) -> dict:
    """Lê uma linha de um arquivo binário (ex.: `soquete.makefile('rb')`) e a decodifica."""
    linha = arquivo.readline(LIMITE_LINHA + 1)
    if not linha:
        raise ProtocoloErro("a conexão foi encerrada sem enviar mensagem")
    if len(linha) > LIMITE_LINHA or not linha.endswith(b"\n"):
        raise ProtocoloErro("a mensagem é grande demais ou está incompleta")
    try:
        mensagem = json.loads(linha.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ProtocoloErro("a mensagem não é um JSON válido") from erro
    if not isinstance(mensagem, dict):
        raise ProtocoloErro("a mensagem deve ser um objeto JSON")
    return mensagem


def escrever_mensagem(soquete, mensagem: dict) -> None:
    """Envia `mensagem` como uma linha JSON."""
    soquete.sendall(json.dumps(mensagem, ensure_ascii=False).encode("utf-8") + b"\n")
