---
status: feita
requisitos: [RF-14, RNF-02, RNF-06]
depende: []
---

# 04. Certificados da CA local

**Objetivo:** gerar, por script, uma CA local e o certificado do servidor assinado por ela, compatíveis com a verificação estrita do Python, sem versionar as chaves.

**Aceitação:** [04-certificados-ca-local.feature](04-certificados-ca-local.feature)

**Arquivos prováveis:** `scripts/gerar_certificados.py`, `.gitignore` (acrescentar `certs/`), `tests/test_certificados.py`.

**Fora de escopo:** uso dos certificados pelo servidor e pelo cliente (task 05).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- `git check-ignore certs/servidor.key certs/ca.key`
