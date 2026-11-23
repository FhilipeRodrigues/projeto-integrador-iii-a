"""Solicitações de aposentadoria fictícias: sorteadas uma vez e gravadas em arquivo.

O arquivo (`data/solicitacoes.json`) é estado da execução, não é versionado. O servidor o cria
sozinho se não existir e recusa subir se ele estiver inválido (RF-15, RNF-07).
"""

import json
import os
import random
import tempfile
from datetime import datetime
from pathlib import Path

ANO_DO_NUMERO = 2026
SITUACAO_INICIAL = "pendente"
SITUACOES = ("pendente", "aprovada", "desaprovada")
FORMATO_DECISAO = "%Y-%m-%dT%H:%M:%S"


class SolicitacoesInvalidas(ValueError):
    """O arquivo de solicitações não pode ser usado; a mensagem aponta a solicitação e o campo."""


def _erro(posicao, solicitacao, campo, motivo):
    ident = solicitacao.get("id", "?") if isinstance(solicitacao, dict) else "?"
    return SolicitacoesInvalidas(f"solicitação {posicao} (id {ident}), campo '{campo}': {motivo}")


def _numero(ident: int) -> str:
    return f"REQ-{ANO_DO_NUMERO}-{ident:04d}"


def _sortear(servidores: list) -> list:
    """Uma solicitação por município, de um servidor sorteado entre os dele, em ordem sorteada."""
    sorteador = random.SystemRandom()
    por_municipio = {}
    for servidor in servidores:
        por_municipio.setdefault(servidor["municipio"], []).append(servidor)
    escolhidos = [sorteador.choice(lotados) for lotados in por_municipio.values()]
    sorteador.shuffle(escolhidos)
    return [
        {
            "id": ident,
            "numero": _numero(ident),
            "servidor_id": servidor["id"],
            "municipio": servidor["municipio"],
            "situacao": SITUACAO_INICIAL,
            "decidida_em": None,
        }
        for ident, servidor in enumerate(escolhidos, start=1)
    ]


def _validar(solicitacao, posicao, servidores_por_id, ids_vistos, servidores_vistos):
    if not isinstance(solicitacao, dict):
        raise _erro(posicao, solicitacao, "(registro)", "esperado um objeto")

    ident = solicitacao.get("id")
    if not isinstance(ident, int) or isinstance(ident, bool):
        raise _erro(posicao, solicitacao, "id", "obrigatório, número inteiro")
    if ident in ids_vistos:
        raise _erro(posicao, solicitacao, "id", "número de identificação repetido")
    ids_vistos.add(ident)

    if solicitacao.get("numero") != _numero(ident):
        raise _erro(posicao, solicitacao, "numero", f"esperado '{_numero(ident)}'")

    servidor_id = solicitacao.get("servidor_id")
    servidor = servidores_por_id.get(servidor_id) if type(servidor_id) is int else None
    if servidor is None:
        raise _erro(posicao, solicitacao, "servidor_id", "servidor inexistente na base")
    if servidor_id in servidores_vistos:
        raise _erro(posicao, solicitacao, "servidor_id", "servidor em mais de uma solicitação")
    servidores_vistos.add(servidor_id)
    if solicitacao.get("municipio") != servidor["municipio"]:
        raise _erro(
            posicao, solicitacao, "municipio",
            f"o servidor {servidor_id} trabalha em '{servidor['municipio']}'",
        )

    situacao = solicitacao.get("situacao")
    if situacao not in SITUACOES:
        raise _erro(posicao, solicitacao, "situacao", f"deve ser uma de {', '.join(SITUACOES)}")
    decidida_em = solicitacao.get("decidida_em")
    if situacao == SITUACAO_INICIAL:
        if decidida_em is not None:
            raise _erro(posicao, solicitacao, "decidida_em", "deve ser null enquanto pendente")
        return
    try:
        if not isinstance(decidida_em, str):
            raise ValueError
        datetime.strptime(decidida_em, FORMATO_DECISAO)
    except ValueError:
        raise _erro(
            posicao, solicitacao, "decidida_em", "data e hora esperadas como AAAA-MM-DDTHH:MM:SS"
        ) from None


class Solicitacoes:
    """As solicitações da execução. Sem `caminho`, ficam só em memória (testes)."""

    def __init__(self, servidores: list, caminho=None):
        self._servidores = {s["id"]: s for s in servidores}
        self._caminho = Path(caminho) if caminho is not None else None
        if self._caminho is not None and self._caminho.exists():
            self._itens = self._carregar()
        else:
            self._itens = _sortear(servidores)
            if self._caminho is not None:
                self._gravar()

    def listar(self) -> list:
        """Resumo de cada solicitação, ordenado pelo número."""
        return [
            {
                "id": s["id"],
                "numero": s["numero"],
                "servidor_nome": self._servidores[s["servidor_id"]]["nome"],
                "municipio": s["municipio"],
                "situacao": s["situacao"],
            }
            for s in self._itens
        ]

    def obter(self, ident: int):
        """A solicitação (cópia) ou None se não existir."""
        for s in self._itens:
            if s["id"] == ident:
                return dict(s)
        return None

    def _carregar(self) -> list:
        try:
            with open(self._caminho, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except OSError as erro:
            raise SolicitacoesInvalidas(f"não foi possível ler as solicitações: {erro}") from erro
        except json.JSONDecodeError as erro:
            raise SolicitacoesInvalidas(f"as solicitações não são um JSON válido: {erro}") from erro

        if not isinstance(conteudo, dict):
            raise SolicitacoesInvalidas("o arquivo de solicitações deve ser um objeto JSON")
        if conteudo.get("ficticio") is not True:
            raise SolicitacoesInvalidas("o arquivo deve estar marcado como fictício ('ficticio': true)")
        itens = conteudo.get("solicitacoes")
        if not isinstance(itens, list) or not itens:
            raise SolicitacoesInvalidas("o arquivo deve ter uma lista 'solicitacoes' não vazia")

        ids_vistos, servidores_vistos = set(), set()
        for posicao, item in enumerate(itens, start=1):
            _validar(item, posicao, self._servidores, ids_vistos, servidores_vistos)
        return sorted(itens, key=lambda s: s["id"])

    def _gravar(self) -> None:
        """Grava por arquivo temporário e troca atômica: nunca deixa o arquivo pela metade."""
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        descritor, temporario = tempfile.mkstemp(
            dir=self._caminho.parent, prefix=self._caminho.name, suffix=".tmp"
        )
        try:
            with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
                json.dump({"ficticio": True, "solicitacoes": self._itens}, arquivo,
                          ensure_ascii=False, indent=2)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, self._caminho)
        except BaseException:
            Path(temporario).unlink(missing_ok=True)
            raise
