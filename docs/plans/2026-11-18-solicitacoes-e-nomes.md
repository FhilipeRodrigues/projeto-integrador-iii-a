# Plano: nomes variados, aba Solicitações e aprovar/desaprovar (18/11/2026)

**Status:** spec revisada, aguardando aprovação do estudante. Nenhum código alterado.

## Objetivo
Três melhorias pedidas pelo estudante para o vídeo do PI III-A:
1. Base com os 50 nomes mais comuns do Brasil (`nomes-comuns.txt`), cada um uma vez, com dois sobrenomes sorteados.
2. Aba "Solicitações" com 10 requerimentos formais fictícios, sorteados uma vez e gravados em arquivo.
3. Botões Aprovar e Desaprovar no documento, com situação persistente também na ficha da consulta.

## Decisões do estudante (18/11/2026)
- Sorteio das solicitações: **uma vez, gravado em `data/solicitacoes.json`**, reutilizado até apagar o arquivo.
- Persistência da situação: **no mesmo arquivo**.
- Processo: **atualizar a spec em fluxo curto** e executar uma task por contexto.

## Passos
| Task | O quê | Requisitos |
|---|---|---|
| 13 | Nomes da base (gerador, base regenerada, README com `maria`) | RF-01 |
| 14 | Solicitações no servidor (sorteio, arquivo, operações `solicitacoes` e `documento`) | RF-15, RF-16, RNF-07 |
| 15 | Aba "Solicitações" e documento formal na janela | RF-12, RF-16 |
| 16 | Operação `decidir`, botões, situação na lista, no documento e na ficha | RF-09, RF-12, RF-17, RF-18, RNF-07 |

## Arquivos afetados
`scripts/gerar_base.py`, `data/servidores.json`, `consulta/solicitacoes.py` (novo), `consulta/dominio.py`, `consulta/servidor.py`, `consulta/cliente.py`, `consulta/interface.py`, `.gitignore`, `README.md`, testes correspondentes. Spec: `docs/specs/2026-11-16-consulta-servidores-tcmgo/` (PRD, TechSpec, tasks 13 a 16).

## Critério de validação
`python -m unittest discover -s tests -v` e `python -m compileall -q consulta scripts tests` sem falhas nem warnings novos; `git check-ignore data/solicitacoes.json`; fluxo completo aberto na janela real e capturas de tela; reiniciar o servidor mantém as decisões.

## Depois das tasks
Regenerar as capturas e o `docs/resumo/resumo-do-projeto.pdf` (nomes mudam), e atualizar o checkpoint.
