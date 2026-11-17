---
status: feita
requisitos: [RF-01, RNF-01]
depende: []
---

# 01. Base fictícia reproduzível

**Objetivo:** gerar e carregar uma base fictícia de 10 municípios e 50 servidores, sempre igual na mesma versão do Python, e recusar uma base inválida.

**Aceitação:** [01-base-ficticia.feature](01-base-ficticia.feature)

**Arquivos prováveis:** `scripts/gerar_base.py`, `data/servidores.json`, `consulta/__init__.py`, `consulta/base.py`, `tests/test_gerar_base.py`, `tests/test_base.py`.

**Fora de escopo:** busca e cálculo de idade (tasks 02 e 03), rede e interface.

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
