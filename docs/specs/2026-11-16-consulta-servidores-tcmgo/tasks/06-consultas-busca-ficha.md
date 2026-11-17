---
status: feita
requisitos: [RF-02, RF-03, RF-04, RF-09, RF-10]
depende: ["02", "03", "05"]
---

# 06. Consultas de busca e ficha pelo canal

**Objetivo:** o cliente busca servidores (por trecho do nome e município) e abre a ficha de um deles pelo canal seguro, com os cálculos feitos no servidor.

**Aceitação:** [06-consultas-busca-ficha.feature](06-consultas-busca-ficha.feature)

**Arquivos prováveis:** `consulta/servidor.py` (operações `buscar` e `ficha`), `consulta/cliente.py` (métodos `buscar` e `ficha`), `consulta/protocolo.py`, `tests/test_integracao_tls.py`.

**Fora de escopo:** respostas de erro do protocolo (task 07), simultaneidade (task 08), janela (tasks 09 a 11).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
