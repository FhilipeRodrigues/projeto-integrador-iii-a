# Check Spec: Consulta de servidores municipais (TCM-GO)

- **Data:** 2026-11-18 (2ª rodada, após a revisão que criou as tasks 13 a 16; a 1ª rodada, de 2026-11-16, aprovou as tasks 01 a 12)
- **Veredito:** aprovado
- **Arquivos conferidos:** `prd.md`, `techspec.md`, `tasks.md`, `tasks/01-base-ficticia` a `tasks/16-aprovar-desaprovar` (16 arquivos `.md` e 16 `.feature`)

Os cruzamentos de IDs (RF, RNF, tags, dependências, índice) foram feitos por script sobre os arquivos inteiros, e não só pelo `tasks.md`.

## Bloqueantes

Nenhum no estado final. A rodada achou 2, ambos corrigidos antes do veredito (a correção foi feita pelo autor da revisão, não por esta skill):

| # | Achado | Correção |
|---|---|---|
| 1 | PRD e TechSpec diziam "aguardando aprovação" na revisão de 2026-11-18 | Estudante aprovou em 2026-11-18; as duas linhas de status foram atualizadas |
| 9 | O TechSpec só dizia "sem migração" para a base antiga. A revisão regenera `servidores.json` e cria `solicitacoes.json`, e regenerar a base depois de gravar solicitações faria elas apontarem para outros servidores | Seção "Revisão 2026-11-18" ganhou "Migração e reversão" e o campo `municipio` em cada solicitação, conferido ao carregar |

As demais verificações bloqueantes passaram:

| # | Resultado |
|---|---|
| 2 | As 2 questões abertas do PRD são `não bloqueante` |
| 3 | Os 18 RF e os 7 RNF do PRD aparecem na tabela de rastreio do TechSpec |
| 4 | Todo RF e RNF tem ao menos uma task e um cenário com a tag correspondente (RF-07 e RF-08 estão em "Esquema do Cenário" na task 02) |
| 5 | Nenhuma task cita requisito inexistente. Os requisitos de cada task coincidem com as tags dos seus cenários |
| 6 | Cada task tem exatamente um `.feature`, com `# language: pt` e um só `Funcionalidade:` |
| 7 | `depende` só aponta para tasks anteriores existentes, sem ciclo (13 depende de 01; 14 de 06 e 13; 15 de 10, 11 e 14; 16 de 14 e 15) |
| 8 | `python -m unittest`, `python -m compileall` e `.claude/quality.json` existem. Ver aviso A |
| 13 | Os cenários das tasks 13 a 16 têm exatamente uma tag de camada e uma de requisito |

## Avisos

- **[#8] A.** `git check-ignore data/solicitacoes.json` só passa depois que a task 14 acrescenta a linha ao `.gitignore`. Antes disso o comando falha, o que é esperado.
- **[#10] B. Task 16 é a maior.** Reúne servidor (`decidir`), cliente, botões, ficha e 12 cenários, em cerca de 8 arquivos. Tem um só comportamento (decidir e ver a decisão), mas se estourar o contexto, dividir em "decidir no servidor e persistir" e "botões e situação na ficha".
- **[#10] C. Task 14 tem 11 cenários** e a task 15 mexe no arquivo da janela inteira. A 15 deve mover a tela atual para a aba e rodar os testes antes de acrescentar a nova aba (já está na task).
- **[#12] D.** Os `.feature` das tasks 14 e 16 citam os códigos de erro `NAO_ENCONTRADO`, `REQUISICAO_INVALIDA` e `ERRO_INTERNO`, o `.gitignore` e o nome do arquivo. É o contrato do TechSpec, como nas tasks 06 e 07, e fica aceitável.
- **[#10] E.** As tasks 13 a 16 alteram testes das tasks 01 a 12 (nomes da base, lista exata de campos da ficha, janela em abas). Isso é esperado, e a `execute-task` roda a suíte inteira.
- **[#2] F. Pendências do estudante, fora do código:** como assinar a Carta pelo estudante e marcar a data da demonstração à Juliana.

## Cobertura

| Requisito | Tasks | Cenários (13 a 16 contados por tag) |
|---|---|---|
| RF-01 | 01, 13 | 4 + 7 |
| RF-02 | 02, 06, 10 | task 16 mostra a situação na ficha, sob o RF-18 |
| RF-09 | 02, 06, 10, 16 | 1 na task 16 |
| RF-12 | 05, 11, 15, 16 | 1 na 15 e 1 na 16 |
| RF-15 | 14 | 5 |
| RF-16 | 14, 15 | 3 na 14 e 7 na 15 |
| RF-17 | 16 | 5 |
| RF-18 | 16 | 3 |
| RNF-07 | 14, 16 | 2 na 14 e 2 na 16 |
