---
status: pendente
requisitos: [RF-02, RF-07, RF-08, RF-09]
depende: ["01"]
---

# 02. Cálculos da ficha

**Objetivo:** calcular idade e tempo de contribuição em anos completos até a data da solicitação e montar a ficha sem data de nascimento nem indicação de elegibilidade.

**Aceitação:** [02-calculos-ficha.feature](02-calculos-ficha.feature)

**Arquivos prováveis:** `consulta/dominio.py` (`anos_completos`, `montar_ficha`), `tests/test_dominio.py`.

**Fora de escopo:** normalização e busca (task 03), operação `ficha` pela rede (task 06).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
