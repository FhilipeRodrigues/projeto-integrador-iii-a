"""Carrega e valida a base de servidores (data/servidores.json)."""

import json
import re
from datetime import date
from pathlib import Path

from consulta.dominio import anos_completos

IDADE_MINIMA_INGRESSO = 18
_FORMATO_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")


class BaseInvalida(ValueError):
    """A base não pode ser usada; a mensagem aponta o servidor e o campo."""


def _erro(posicao, servidor, campo, motivo):
    ident = servidor.get("id", "?") if isinstance(servidor, dict) else "?"
    return BaseInvalida(f"servidor {posicao} (id {ident}), campo '{campo}': {motivo}")


def _texto(posicao, servidor, campo):
    valor = servidor.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise _erro(posicao, servidor, campo, "obrigatório, texto não vazio")
    return valor


def _data(posicao, servidor, campo):
    valor = servidor.get(campo)
    if not isinstance(valor, str) or not _FORMATO_DATA.fullmatch(valor):
        raise _erro(posicao, servidor, campo, "data esperada no formato AAAA-MM-DD")
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise _erro(posicao, servidor, campo, "data inexistente") from None


def _validar_servidor(posicao, servidor, ids_vistos):
    if not isinstance(servidor, dict):
        raise _erro(posicao, servidor, "(registro)", "esperado um objeto")

    ident = servidor.get("id")
    if not isinstance(ident, int) or isinstance(ident, bool):
        raise _erro(posicao, servidor, "id", "obrigatório, número inteiro")
    if ident in ids_vistos:
        raise _erro(posicao, servidor, "id", "número de identificação repetido")
    ids_vistos.add(ident)

    _texto(posicao, servidor, "nome")
    _texto(posicao, servidor, "municipio")
    _texto(posicao, servidor, "orgao")
    if servidor.get("sexo") not in ("F", "M"):
        raise _erro(posicao, servidor, "sexo", "deve ser 'F' ou 'M'")
    if not isinstance(servidor.get("pcd"), bool):
        raise _erro(posicao, servidor, "pcd", "obrigatório, verdadeiro ou falso")
    doenca = servidor.get("doenca_profissional")
    if doenca is not None and (not isinstance(doenca, str) or not doenca.strip()):
        raise _erro(posicao, servidor, "doenca_profissional", "null ou texto não vazio")
    remuneracao = servidor.get("ultima_remuneracao_centavos")
    if (
        not isinstance(remuneracao, int)
        or isinstance(remuneracao, bool)
        or remuneracao < 0
    ):
        raise _erro(
            posicao, servidor, "ultima_remuneracao_centavos", "inteiro de centavos, não negativo"
        )

    nascimento = _data(posicao, servidor, "data_nascimento")
    ingresso = _data(posicao, servidor, "data_ingresso")
    solicitacao = _data(posicao, servidor, "data_solicitacao")
    if anos_completos(nascimento, ingresso) < IDADE_MINIMA_INGRESSO:
        raise _erro(
            posicao, servidor, "data_ingresso",
            f"servidor ingressou com menos de {IDADE_MINIMA_INGRESSO} anos",
        )
    if solicitacao < ingresso:
        raise _erro(posicao, servidor, "data_solicitacao", "anterior à data de ingresso")


def carregar(caminho):
    """Lê a base e devolve o dicionário validado. Levanta BaseInvalida se houver problema."""
    try:
        with open(Path(caminho), encoding="utf-8") as arquivo:
            base = json.load(arquivo)
    except OSError as erro:
        raise BaseInvalida(f"não foi possível ler a base: {erro}") from erro
    except json.JSONDecodeError as erro:
        raise BaseInvalida(f"a base não é um JSON válido: {erro}") from erro

    if not isinstance(base, dict):
        raise BaseInvalida("a base deve ser um objeto JSON")
    if base.get("ficticio") is not True:
        raise BaseInvalida("a base deve estar marcada como fictícia ('ficticio': true)")
    servidores = base.get("servidores")
    if not isinstance(servidores, list) or not servidores:
        raise BaseInvalida("a base deve ter uma lista 'servidores' não vazia")

    ids_vistos = set()
    for posicao, servidor in enumerate(servidores, start=1):
        _validar_servidor(posicao, servidor, ids_vistos)
    return base
