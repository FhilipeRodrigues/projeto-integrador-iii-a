---
status: feita
requisitos: [RF-10, RF-12, RF-14]
depende: ["01", "04"]
---

# 05. Canal seguro e lista de municípios

**Objetivo:** estabelecer a comunicação cliente-servidor sobre TCP com TLS, em que o cliente só confia na CA do projeto, já devolvendo a lista de municípios como primeira operação.

**Aceitação:** [05-canal-seguro-municipios.feature](05-canal-seguro-municipios.feature)

**Arquivos prováveis:** `consulta/protocolo.py` (uma linha JSON, limites), `consulta/servidor.py` (contexto TLS, `accept`, uma thread por conexão, log, operação `municipios`), `consulta/cliente.py` (`ClienteRede`, erros de rede tratados), `tests/test_protocolo.py`, `tests/test_integracao_tls.py`.

**Fora de escopo:** operações `buscar` e `ficha` (task 06), erros do protocolo (task 07), concorrência medida (task 08), janela (tasks 09 a 11).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
