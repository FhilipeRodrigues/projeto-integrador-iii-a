---
status: pendente
requisitos: [RF-02, RF-05, RF-09]
depende: ["09"]
---

# 10. Interface: ficha do servidor

**Objetivo:** ao selecionar um servidor da lista, mostrar a ficha completa e bem formatada.

**Aceitação:** [10-interface-ficha.feature](10-interface-ficha.feature)

**Arquivos prováveis:** `consulta/interface.py` (painel da ficha e formatação de datas, valores e Sim/Não), `tests/test_interface.py`.

**Fora de escopo:** erros de rede ao pedir a ficha (task 11).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- UI: abrir uma ficha com doença profissional e outra sem, e registrar a captura de tela (vai para o relatório).
