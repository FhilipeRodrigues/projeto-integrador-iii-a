"""Gera data/servidores.json: 10 municípios de Goiás e 50 servidores FICTÍCIOS.

A semente é fixa, então a mesma versão do Python produz sempre o mesmo arquivo.
Os 50 nomes mais comuns do Brasil aparecem uma vez cada, com dois sobrenomes comuns
sorteados; as combinações podem coincidir por acaso com pessoas reais.

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
# Os 25 nomes femininos e os 25 masculinos mais comuns do Brasil (lista do estudante).
# Cada um aparece uma vez na base.
NOMES_F = [
    "Maria", "Ana", "Helena", "Francisca", "Antônia", "Adriana", "Márcia",
    "Juliana", "Isabel", "Beatriz", "Catarina", "Vitória", "Sofia", "Laura",
    "Fernanda", "Patrícia", "Júlia", "Cecília", "Maitê", "Alice", "Aurora",
    "Antonella", "Ísis", "Heloísa", "Luísa",
]
NOMES_M = [
    "José", "João", "Antônio", "Francisco", "Pedro", "Carlos", "Lucas", "Luiz",
    "Paulo", "Gabriel", "Marcos", "Davi", "Rafael", "Luís", "Daniel", "Miguel",
    "Gustavo", "Felipe", "Guilherme", "Eduardo", "Arthur", "Heitor", "Matheus",
    "Henrique", "Samuel",
]
# Pares que diferem só pela terminação: ficam em municípios diferentes.
PARES_PARECIDOS = [("Antônio", "Antônia"), ("Francisco", "Francisca")]
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


def _distribuicao_valida(primeiros):
    """Cada município (blocos de 5) mistura os sexos, e nomes parecidos não dividem município."""
    blocos = [primeiros[i:i + SERVIDORES_POR_MUNICIPIO]
              for i in range(0, len(primeiros), SERVIDORES_POR_MUNICIPIO)]
    for bloco in blocos:
        sexos = {sexo for _, sexo in bloco}
        if sexos != {"F", "M"}:
            return False
        nomes = {nome for nome, _ in bloco}
        if any(a in nomes and b in nomes for a, b in PARES_PARECIDOS):
            return False
    return True


def _sortear_primeiros_nomes(rng):
    """Embaralha os 50 nomes até a distribuição pelos municípios ser válida (determinístico)."""
    primeiros = [(nome, "F") for nome in NOMES_F] + [(nome, "M") for nome in NOMES_M]
    while True:
        rng.shuffle(primeiros)
        if _distribuicao_valida(primeiros):
            return primeiros


def _novo_servidor(rng, numero, municipio, primeiro, sexo):
    sobrenome1, sobrenome2 = rng.sample(SOBRENOMES, 2)
    nome = f"{primeiro} {sobrenome1} {sobrenome2}"

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
    primeiros = _sortear_primeiros_nomes(rng)
    servidores = []
    for municipio in MUNICIPIOS:
        for _ in range(SERVIDORES_POR_MUNICIPIO):
            primeiro, sexo = primeiros[len(servidores)]
            servidores.append(_novo_servidor(rng, len(servidores) + 1, municipio, primeiro, sexo))
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
