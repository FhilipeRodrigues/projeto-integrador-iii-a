---
status: pendente
requisitos: [RF-03, RF-04]
depende: ["01"]
---

# 03. Busca de servidores

**Objetivo:** buscar servidores por trecho do nome, sem acento e sem diferenciar maiúsculas, com filtro opcional por município e lista de municípios.

**Aceitação:** [03-busca-servidores.feature](03-busca-servidores.feature)

**Arquivos prováveis:** `consulta/dominio.py` (`normalizar`, `buscar`, `listar_municipios`), `tests/test_dominio.py` (ou `tests/test_busca.py`).

**Fora de escopo:** cálculos da ficha (task 02), protocolo e rede (tasks 05 a 07).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
