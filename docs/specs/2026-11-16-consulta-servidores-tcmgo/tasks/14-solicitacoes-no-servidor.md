---
status: feita
requisitos: [RF-15, RF-16, RNF-07]
depende: ["06", "13"]
---

# 14. Solicitações de aposentadoria no servidor

**Objetivo:** o servidor sorteia uma vez 10 solicitações fictícias (uma por município), grava em `data/solicitacoes.json` e as entrega pela rede, listadas e como documento.

**Aceitação:** [14-solicitacoes-no-servidor.feature](14-solicitacoes-no-servidor.feature)

**Arquivos prováveis:** `consulta/solicitacoes.py` (novo), `consulta/dominio.py` (`montar_documento`), `consulta/servidor.py` (operações `solicitacoes` e `documento`, opção `--solicitacoes`), `consulta/cliente.py`, `.gitignore`, `tests/test_solicitacoes.py` (novo), `tests/test_integracao_tls.py`.

**Fora de escopo:** aprovar e desaprovar (task 16), a aba na janela (task 15). Nesta task toda solicitação fica "pendente".

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- `git check-ignore data/solicitacoes.json`
