# Tasks: Consulta de servidores municipais (TCM-GO)

PRD: [prd.md](prd.md) · TechSpec: [techspec.md](techspec.md)

| # | Task | RF / RNF | Depende | Status |
|---|---|---|---|---|
| 01 | [Base fictícia reproduzível](tasks/01-base-ficticia.md) | RF-01, RNF-01 | — | feita |
| 02 | [Cálculos da ficha](tasks/02-calculos-ficha.md) | RF-02, RF-07, RF-08, RF-09 | 01 | feita |
| 03 | [Busca de servidores](tasks/03-busca-servidores.md) | RF-03, RF-04 | 01 | feita |
| 04 | [Certificados da CA local](tasks/04-certificados-ca-local.md) | RF-14, RNF-02, RNF-06 | — | pendente |
| 05 | [Canal seguro e lista de municípios](tasks/05-canal-seguro-municipios.md) | RF-10, RF-12, RF-14 | 01, 04 | pendente |
| 06 | [Consultas de busca e ficha pelo canal](tasks/06-consultas-busca-ficha.md) | RF-02, RF-03, RF-04, RF-09, RF-10 | 02, 03, 05 | pendente |
| 07 | [Erros do protocolo](tasks/07-erros-do-protocolo.md) | RF-13 | 06 | pendente |
| 08 | [Atendimento simultâneo](tasks/08-atendimento-simultaneo.md) | RF-11, RNF-03 | 06 | pendente |
| 09 | [Interface: busca e lista](tasks/09-interface-busca.md) | RF-04, RF-05, RF-06, RNF-01, RNF-05 | 06 | pendente |
| 10 | [Interface: ficha do servidor](tasks/10-interface-ficha.md) | RF-02, RF-05, RF-09 | 09 | pendente |
| 11 | [Interface: erros de rede e de certificado](tasks/11-interface-erros-de-rede.md) | RF-12, RF-14 | 09 | pendente |
| 12 | [README e execução em pasta limpa](tasks/12-readme-execucao.md) | RNF-04 | 10, 11 | pendente |

**Ordem sugerida de execução:** 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12. As tasks 02, 03 e 04 não dependem entre si.

**Cobertura:** todo RF do PRD (RF-01 a RF-14) aparece em pelo menos uma task e em pelo menos um cenário. Os RNF-01 a RNF-06 também.

## Comandos de validação do projeto

- `python -m unittest discover -s tests -v`
- `python -m compileall -q consulta scripts tests`
- `git check-ignore certs/servidor.key certs/ca.key` (tasks que mexem em certificados)

Não há linter configurado. Tags de camada: `@fluxo` (dado, regra e rede, sem tela), `@ui` (o que se vê na janela), `@integracao` (janela e servidor reais juntos). Como o projeto é Tkinter e não web nem Mongo, a `execute-task` faz o QA de `@ui` com a janela e captura de tela, e o de `@fluxo` com os testes de unidade e de integração.

## Requisitos de processo fora das tasks de código

Estes itens não têm `.feature`, porque a verificação é manual. Ficam registrados aqui e no checkpoint:

| RP | O quê | Quem | Prazo |
|---|---|---|---|
| RP-01 | Assinar e enviar Carta, Termo de Formalização e Termo de Participação | Estudante, Juliana e professor | 23/11/2026, 23h59 |
| RP-02 | Demonstração à Juliana e registro das considerações | Estudante | antes de 26/11/2026 |
| RP-03 | Relatório técnico em PDF (até 5 páginas, Arial 12 pt, margens 2,5 e 3 cm) | Estudante, com apoio do Claude | 07/12/2026 |
| RP-04 | Código com instruções de execução | Coberto pela task 12 | 07/12/2026 |
| RP-05 | Vídeo de até 10 minutos, com a comunicação cliente-servidor | Estudante | 07/12/2026 |
| RP-06 | Envio nos dois campos da Plataforma A | Estudante | 07/12/2026, 23h59 |

O relatório (RP-03) e o roteiro do vídeo (RP-05) dependem do sistema pronto e das capturas de tela da task 10. Depois da task 12, vale uma checklist própria para esses dois.
