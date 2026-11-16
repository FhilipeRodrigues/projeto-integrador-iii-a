---
status: pendente
requisitos: [RF-13]
depende: ["06"]
---

# 07. Erros do protocolo

**Objetivo:** responder com erro claro a qualquer solicitação inválida, sem derrubar o servidor nem afetar os outros clientes.

**Aceitação:** [07-erros-do-protocolo.feature](07-erros-do-protocolo.feature)

**Arquivos prováveis:** `consulta/protocolo.py` (validação, códigos de erro, limite de 64 KiB, timeout de 5 s), `consulta/servidor.py` (despacho e `ERRO_INTERNO`), `tests/test_protocolo.py`, `tests/test_integracao_tls.py`.

**Fora de escopo:** exibição dos erros na janela (task 11).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
