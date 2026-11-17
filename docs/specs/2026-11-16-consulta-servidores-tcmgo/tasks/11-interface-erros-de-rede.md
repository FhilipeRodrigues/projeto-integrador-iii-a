---
status: feita
requisitos: [RF-12, RF-14]
depende: ["09"]
---

# 11. Interface: erros de rede e de certificado

**Objetivo:** quando o servidor está fora do ar, lento ou com certificado não confiável, a janela explica o problema, continua responsiva e volta a funcionar quando o servidor voltar.

**Aceitação:** [11-interface-erros-de-rede.feature](11-interface-erros-de-rede.feature)

**Arquivos prováveis:** `consulta/interface.py` (área de mensagem, nova tentativa de carregar municípios, bloqueio do botão durante a consulta), `consulta/cliente.py` (tipos de erro), `tests/test_interface.py`, `tests/test_integracao_tls.py`.

**Fora de escopo:** erros do protocolo (task 07, que só trata o lado do servidor).

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- UI: com o servidor parado e depois com o servidor de certificado falso, registrar a captura de tela da mensagem (evidência do RF-14 para o vídeo).
