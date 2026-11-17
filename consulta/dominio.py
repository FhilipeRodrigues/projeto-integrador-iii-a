"""Regras de domínio: normalização, busca, cálculos e montagem da ficha."""

from datetime import date


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
