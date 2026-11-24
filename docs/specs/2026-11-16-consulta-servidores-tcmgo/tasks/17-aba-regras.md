---
status: feita
requisitos: [RF-09, RF-12, RF-19]
depende: ["14", "15"]
---

# 17. Aba Regras: consulta das regras de aposentadoria

**Objetivo:** o servidor passa a entregar o texto das regras básicas de aposentadoria (operação `regras`) e a janela ganha a aba "Regras", depois de "Solicitações", que apenas o exibe. Sem cálculo e sem indicar elegibilidade.

**Aceitação:** [17-aba-regras.feature](17-aba-regras.feature)

**Arquivos prováveis:** `consulta/regras.py` (o texto, em blocos de título e linhas), `consulta/servidor.py` (operação `regras`), `consulta/cliente.py` (`regras`), `consulta/interface.py` (aba com `Text` somente leitura), `tests/test_regras.py`, `tests/test_integracao_tls.py`, `tests/test_interface.py` (a lista de abas passa a ter três), `README.md` (lista de operações, se houver), `docs/resumo/resumo-do-projeto.html` e `docs/video/roteiro-video.md` (depois, ao regenerar as capturas).

**Notas:** o texto é do estudante e fica fixo no servidor, sem arquivo de configuração. A operação não recebe parâmetros. A aba carrega o texto ao ser aberta pela primeira vez e tenta de novo se a rede falhou. O rodapé avisa que o texto é simplificado e não substitui a legislação. O teste da lista de campos da ficha (RF-09) não muda.

**Validação:**
- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- abrir a janela de verdade, passar pela aba e tirar captura de tela
