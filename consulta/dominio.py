"""Regras de domínio: normalização, busca, cálculos e montagem da ficha."""

from datetime import date


def anos_completos(inicio: date, fim: date) -> int:
    """Anos inteiros completos entre duas datas (parte inteira, sem arredondar)."""
    anos = fim.year - inicio.year
    if (fim.month, fim.day) < (inicio.month, inicio.day):
        anos -= 1
    return anos
