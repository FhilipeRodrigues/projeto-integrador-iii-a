---
status: feita
requisitos: [RF-12, RF-16]
depende: ["10", "11", "14"]
---

# 15. Aba "Solicitações" na janela

**Objetivo:** a janela ganha duas abas, "Consulta" (como é hoje) e "Solicitações", que lista os requerimentos e mostra o documento formal do selecionado.

**Aceitação:** [15-aba-solicitacoes.feature](15-aba-solicitacoes.feature)

**Arquivos prováveis:** `consulta/interface.py`, `tests/test_interface.py`.

**Ordem sugerida:** primeiro mover a tela atual para a aba "Consulta" e rodar os testes da interface sem mudar nada neles; só depois acrescentar a aba "Solicitações".

**Fora de escopo:** os botões Aprovar e Desaprovar e a situação na ficha (task 16).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- abrir a janela de verdade e tirar captura de tela da aba nova
