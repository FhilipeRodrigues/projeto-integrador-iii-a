---
status: pendente
requisitos: [RF-01]
depende: ["01"]
---

# 13. Nomes mais variados na base fictícia

**Objetivo:** a base passa a usar os 25 nomes masculinos e os 25 femininos mais comuns do Brasil (lista do estudante em `nomes-comuns.txt`), cada um uma vez, com dois sobrenomes diferentes sorteados.

**Aceitação:** [13-nomes-da-base.feature](13-nomes-da-base.feature)

**Arquivos prováveis:** `scripts/gerar_base.py`, `data/servidores.json` (regenerado), `tests/test_gerar_base.py`, `README.md` (o exemplo `joana` vira `maria`), testes que dependam de nomes da base real.

**Notas:**
- As listas de nomes ficam no script. "Sofia / Sophia" entra como "Sofia".
- A mudança altera todos os dados sorteados da base, então capturas de tela e textos que citam nomes antigos precisam ser revistos (o `resumo-do-projeto` e as capturas são regenerados no fim das tasks 13 a 16).

**Fora de escopo:** solicitações (tasks 14 a 16), mudança no número de servidores ou municípios.

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
