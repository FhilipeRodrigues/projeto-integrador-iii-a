"""Regras de domínio: normalização, busca, cálculos e montagem da ficha."""

import unicodedata
from datetime import date


def normalizar(texto: str) -> str:
    """Texto sem acento, sem diferença de maiúsculas e sem espaços nas pontas."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_marcas = "".join(c for c in decomposto if not unicodedata.combining(c))
    return sem_marcas.casefold().strip()


def buscar(servidores: list, nome: str, municipio: str | None = None) -> list:
    """Servidores cujo nome contém o trecho, em ordem alfabética sem acentos.

    Nome vazio não filtra por nome; município None não filtra por município.
    """
    trecho = normalizar(nome)
    encontrados = [
        s for s in servidores
        if trecho in normalizar(s["nome"]) and (municipio is None or s["municipio"] == municipio)
    ]
    encontrados.sort(key=lambda s: (normalizar(s["nome"]), s["id"]))
    return [{"id": s["id"], "nome": s["nome"], "municipio": s["municipio"]} for s in encontrados]


def listar_municipios(servidores: list) -> list:
    """Municípios da base, sem repetição, em ordem alfabética sem acentos."""
    return sorted({s["municipio"] for s in servidores}, key=normalizar)


def anos_completos(inicio: date, fim: date) -> int:
    """Anos inteiros completos entre duas datas (parte inteira, sem arredondar)."""
    anos = fim.year - inicio.year
    if (fim.month, fim.day) < (inicio.month, inicio.day):
        anos -= 1
    return anos


def montar_ficha(servidor: dict) -> dict:
    """Ficha enviada ao cliente: idade e tempo calculados até a data da solicitação.

    A data de nascimento não entra na ficha, e não há campo de elegibilidade.
    """
    solicitacao = date.fromisoformat(servidor["data_solicitacao"])
    return {
        "id": servidor["id"],
        "nome": servidor["nome"],
        "municipio": servidor["municipio"],
        "sexo": servidor["sexo"],
        "idade": anos_completos(date.fromisoformat(servidor["data_nascimento"]), solicitacao),
        "orgao": servidor["orgao"],
        "pcd": servidor["pcd"],
        "doenca_profissional": servidor["doenca_profissional"],
        "data_ingresso": servidor["data_ingresso"],
        "data_solicitacao": servidor["data_solicitacao"],
        "ultima_remuneracao_centavos": servidor["ultima_remuneracao_centavos"],
        "tempo_contribuicao_anos": anos_completos(
            date.fromisoformat(servidor["data_ingresso"]), solicitacao
        ),
    }
