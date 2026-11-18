---
status: pendente
requisitos: [RF-09, RF-12, RF-17, RF-18, RNF-07]
depende: ["14", "15"]
---

# 16. Aprovar ou desaprovar, com situação persistente

**Objetivo:** o documento ganha os botões "Aprovar" e "Desaprovar". A decisão vai ao servidor, fica gravada em `data/solicitacoes.json` e aparece na lista, no documento e na ficha do servidor, mesmo depois de reiniciar o servidor.

**Aceitação:** [16-aprovar-desaprovar.feature](16-aprovar-desaprovar.feature)

**Arquivos prováveis:** `consulta/solicitacoes.py` (`decidir`), `consulta/dominio.py` (`montar_ficha` com `situacao_solicitacao`), `consulta/servidor.py` (operação `decidir`), `consulta/cliente.py`, `consulta/interface.py` (botões, atualização da lista e linha "Situação da solicitação" na ficha), `tests/test_solicitacoes.py`, `tests/test_integracao_tls.py`, `tests/test_interface.py`, `README.md` (como zerar as decisões).

**Notas:** a decisão é reversível (a última vale). Não há confirmação em diálogo nem autenticação (decisões do TechSpec). O teste da lista exata de campos da ficha (RF-09) é atualizado com o novo campo.

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- abrir a janela de verdade, fazer o fluxo completo do vídeo e tirar capturas de tela
