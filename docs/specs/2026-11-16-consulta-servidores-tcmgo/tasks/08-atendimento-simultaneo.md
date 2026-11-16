---
status: pendente
requisitos: [RF-11, RNF-03]
depende: ["06"]
---

# 08. Atendimento simultâneo

**Objetivo:** garantir que o servidor atenda vários clientes ao mesmo tempo, sem que um cliente lento bloqueie os demais, e que a busca responda em até 1 segundo.

**Aceitação:** [08-atendimento-simultaneo.feature](08-atendimento-simultaneo.feature)

**Arquivos prováveis:** `consulta/servidor.py` (o handshake TLS acontece na thread da conexão), `tests/test_integracao_tls.py`.

**Fora de escopo:** limite de conexões simultâneas e fila (não previstos no PRD).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
