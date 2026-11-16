---
status: pendente
requisitos: [RF-04, RF-05, RF-06, RNF-01, RNF-05]
depende: ["06"]
---

# 09. Interface: busca e lista

**Objetivo:** abrir a janela, carregar os municípios, buscar por nome e município e mostrar a lista de resultados, com a faixa de dados fictícios e fonte legível.

**Aceitação:** [09-interface-busca.feature](09-interface-busca.feature)

**Arquivos prováveis:** `consulta/interface.py` (janela `ttk`, `Combobox`, `Treeview`, faixa de aviso, rede em thread de trabalho com `queue.Queue` e `after()`; recebe o `ClienteRede` por parâmetro), `tests/test_interface.py`.

**Fora de escopo:** painel da ficha (task 10), mensagens de falha de rede e de certificado (task 11).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- UI: abrir a janela com o servidor no ar, percorrer os cenários e registrar uma captura de tela (vai para o relatório).
