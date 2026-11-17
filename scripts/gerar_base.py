"""Gera data/servidores.json: 10 municípios de Goiás e 50 servidores FICTÍCIOS.

A semente é fixa, então a mesma versão do Python produz sempre o mesmo arquivo.
Os nomes são combinações aleatórias de nomes e sobrenomes comuns e podem coincidir
por acaso com pessoas reais.

Uso: python scripts/gerar_base.py [destino]
"""

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 2026
SERVIDORES_POR_MUNICIPIO = 5
DATA_SOLICITACAO_BASE = date(2026, 9, 1)
DESTINO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "servidores.json"

MUNICIPIOS = [
    "Anápolis", "Goiânia", "Aparecida de Goiânia", "Rio Verde", "Luziânia",
    "Águas Lindas de Goiás", "Valparaíso de Goiás", "Trindade", "Formosa", "Itumbiara",
]
ORGAOS = [
    "Secretaria Municipal de Educação",
    "Secretaria Municipal de Saúde",
    "Secretaria Municipal de Administração",
    "Secretaria Municipal de Obras",
    "Secretaria Municipal de Assistência Social",
]
NOMES_F = [
    "Maria", "Ana", "Conceição", "Luíza", "Aparecida", "Joana", "Sebastiana",
    "Helena", "Márcia", "Rita", "Teresa", "Fátima",
]
NOMES_M = [
    "José", "João", "Antônio", "Francisco", "Carlos", "Paulo", "Geraldo",
    "Raimundo", "Sebastião", "Luiz", "Marcos", "Valdemar",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Alves", "Ferreira",
    "Rodrigues", "Gonçalves", "Barbosa", "Ribeiro", "Carvalho", "Lima", "Araújo",
]
DOENCAS = [
    "Lesão por esforço repetitivo (LER/DORT)",
    "Perda auditiva ocupacional",
    "Acidente de trabalho com fratura no punho",
]


def _data_iso(dia: date) -> str:
    return dia.isoformat()


def _novo_servidor(rng, numero, municipio, nomes_usados):
    sexo = rng.choice(["F", "M"])
    while True:
        primeiro = rng.choice(NOMES_F if sexo == "F" else NOMES_M)
        nome = f"{primeiro} {rng.choice(SOBRENOMES)} {rng.choice(SOBRENOMES)}"
        if nome not in nomes_usados:
            nomes_usados.add(nome)
            break

    # Dia de nascimento até 28 evita o caso de 29/02 e garante 18 anos no ingresso.
    nascimento = date(rng.randint(1958, 1990), rng.randint(1, 12), rng.randint(1, 28))
    solicitacao = DATA_SOLICITACAO_BASE + timedelta(days=rng.randint(0, 60))
    primeiro_dia = date(nascimento.year + 18, nascimento.month, nascimento.day)
    ultimo_dia = solicitacao - timedelta(days=365)
    ingresso = primeiro_dia + timedelta(days=rng.randint(0, (ultimo_dia - primeiro_dia).days))

    return {
        "id": numero,
        "nome": nome,
        "sexo": sexo,
        "data_nascimento": _data_iso(nascimento),
        "municipio": municipio,
        "orgao": rng.choice(ORGAOS),
        "pcd": numero % 8 == 3,
        "doenca_profissional": DOENCAS[numero % len(DOENCAS)] if numero % 11 == 5 else None,
        "data_ingresso": _data_iso(ingresso),
        "data_solicitacao": _data_iso(solicitacao),
        "ultima_remuneracao_centavos": rng.randint(2000, 12000) * 100,
    }


def gerar_base() -> dict:
    """Monta a base em memória, de forma determinística."""
    rng = random.Random(SEMENTE)
    nomes_usados = set()
    servidores = []
    for municipio in MUNICIPIOS:
        for _ in range(SERVIDORES_POR_MUNICIPIO):
            servidores.append(_novo_servidor(rng, len(servidores) + 1, municipio, nomes_usados))
    return {"ficticio": True, "servidores": servidores}


def escrever_base(destino) -> None:
    """Grava a base em UTF-8 com quebra de linha \\n, igual em qualquer sistema."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(gerar_base(), ensure_ascii=False, indent=2) + "\n"
    with open(destino, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(texto)


if __name__ == "__main__":
    alvo = Path(sys.argv[1]) if len(sys.argv) > 1 else DESTINO_PADRAO
    escrever_base(alvo)
    print(f"Base fictícia gravada em {alvo}")
