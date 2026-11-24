# Plano: aba Regras (task 17, RF-19)

Pedido do estudante em 24/11/2026. Escopo confirmado: **só consulta** (o sistema não calcula nem indica elegibilidade, RF-09 continua valendo) e **o servidor envia o texto** (operação `regras`).

## Objetivo

Uma aba "Regras" na janela, depois de "Solicitações", com o texto das regras básicas de aposentadoria do servidor público, para o analista consultar ao aprovar ou desaprovar.

## Conteúdo (do estudante)

- **Regra geral:** idade mínima de 62 anos (mulher) e 65 anos (homem); contribuição mínima de 25 anos, para ambos.
- **PCD, por tempo de contribuição:** homem 25 anos, mulher 20 anos.
- **PCD, por idade:** idade mínima de 60 anos (homem) e 55 anos (mulher), com 15 anos de contribuição.
- **Doença profissional ou acidente de trabalho:** em caso positivo, aprovação direta.
- Rodapé: texto simplificado, de apoio à demonstração, que não substitui a legislação.

## Passos

1. Spec: RF-19 no PRD, seção "Revisão 2026-11-24" no TechSpec, task 17 (`.md` e `.feature`) e linha no `tasks.md`. **Feito.**
2. `consulta/regras.py` com o texto em blocos; testes em `tests/test_regras.py`.
3. Operação `regras` em `consulta/servidor.py` e `regras()` em `consulta/cliente.py`; teste de integração por TLS, incluindo o log.
4. Aba "Regras" em `consulta/interface.py` (`Text` somente leitura, fonte de 12 pt ou mais, rodapé, nova tentativa se a rede falhar); testes em `tests/test_interface.py` e ajuste do teste que confere os nomes das abas.
5. Conferir o README (lista de operações) e rodar os checks.
6. Janela real: captura de tela da aba. Depois, no resumo e no roteiro do vídeo: nova captura, operações (sete) e um passo sobre as regras.

## Arquivos afetados

`consulta/regras.py` (novo), `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py`, `tests/test_regras.py` (novo), `tests/test_integracao_tls.py`, `tests/test_interface.py`, `README.md` (se citar as operações), `docs/specs/2026-11-16-consulta-servidores-tcmgo/*`, `docs/resumo/*` e `docs/video/roteiro-video.md` (no fim).

## Validação

- `python -m unittest discover -s tests -v` e `python -m compileall -q consulta scripts tests`, sem falhas nem warnings novos.
- Janela aberta de verdade contra o servidor real, passando pelas três abas, com captura de tela.
- A ficha continua sem campo de elegibilidade (teste existente da lista de campos).
