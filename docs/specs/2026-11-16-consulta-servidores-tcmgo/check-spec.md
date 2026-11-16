# Check Spec: Consulta de servidores municipais (TCM-GO)

- **Data:** 2026-11-16
- **Veredito:** aprovado
- **Arquivos conferidos:** `prd.md`, `techspec.md`, `tasks.md`, `tasks/01-base-ficticia` a `tasks/12-readme-execucao` (12 arquivos `.md` e 12 `.feature`)

Os cruzamentos de IDs (RF, RNF, tags, dependências, índice) foram feitos por script sobre os arquivos inteiros, e não só pelo `tasks.md`.

## Bloqueantes

Nenhum. As 9 verificações bloqueantes passaram, mais a de tags (#13):

| # | Resultado |
|---|---|
| 1 | PRD e TechSpec com status `aprovado (2026-11-16)` |
| 2 | As 2 questões abertas do PRD são `não bloqueante` (assinatura da Carta pelo estudante; data da demonstração) |
| 3 | Os 14 RF e os 6 RNF do PRD aparecem na tabela de rastreio do TechSpec |
| 4 | Todo RF tem ao menos uma task e um cenário com `@RF-NN` (ver cobertura) |
| 5 | Nenhuma task cita RF ou RNF inexistente. Os requisitos de cada task coincidem com as tags dos cenários e com o índice |
| 6 | Cada task tem exatamente um `.feature`, com `# language: pt` e um só `Funcionalidade:`. Os links apontam para o arquivo certo |
| 7 | `depende` só aponta para tasks anteriores existentes, sem ciclo |
| 8 | Os comandos existem: `python -m unittest`, `python -m compileall` e `git check-ignore` funcionam nesta máquina. Ver aviso A |
| 9 | O TechSpec declara "sem dados existentes e sem migração" |
| 13 | Os 69 cenários têm exatamente uma tag de camada e uma tag de requisito |

## Avisos

- **[#8] A. Os comandos de validação ainda não têm onde rodar.**
  - Não há `pyproject.toml`, `package.json` nem `.claude/quality.json`.
  - As pastas `consulta/`, `scripts/` e `tests/` ainda não existem, então `compileall` e `unittest discover -s tests` falham até a task 01 criá-las.
  - A task 01 cria as três, então não bloqueia.
  - O agente `task-reviewer` lê os checks do `.claude/quality.json`. Sem esse arquivo, ele não terá o que rodar. Sugiro criá-lo na task 01 com os dois comandos de teste e de sintaxe.
- **[#10] B. Task 05 é a maior.** Reúne protocolo, servidor TLS, cliente, log e 7 cenários, em cerca de 5 arquivos. Cabe em um contexto, mas é o ponto de maior risco. Se estourar, dividir em "canal TLS e operação `municipios`" e "recusa de certificado e log".
- **[#10] C. Task 09 tem 9 cenários**, a maior contagem. Tem um só comportamento (buscar e listar), então não é problema, só um sinal de que o contexto vai ficar cheio.
- **[#11] D. RNF-04 só é verificado na task 12.** O teste de imports e o README ficam no fim. Se algum import externo entrar antes, só será pego lá. Opcional: mover o teste de imports para a task 01.
- **[#12] E. Detalhe de protocolo em cenários.** A task 07 cita "JSON" e os códigos `REQUISICAO_INVALIDA`, `OPERACAO_DESCONHECIDA`, `NAO_ENCONTRADO`. É o contrato definido no TechSpec e fica aceitável. Não há seletor, nome de função nem classe em nenhum `.feature`.
- **[#2] F. Pendências do estudante, fora do código.** Como assinar a Carta pelo estudante e marcar a data da demonstração à Juliana (prazo antes de 26/11). Não travam as tasks.

## Cobertura

| Requisito | Tasks | Cenários |
|---|---|---|
| RF-01 | 01 | 4 |
| RF-02 | 02, 06, 10 | 7 |
| RF-03 | 03, 06 | 8 |
| RF-04 | 03, 06, 09 | 6 |
| RF-05 | 09, 10 | 7 |
| RF-06 | 09 | 1 |
| RF-07 | 02 | 1 (esquema com 3 exemplos) |
| RF-08 | 02 | 1 (esquema com 5 exemplos) |
| RF-09 | 02, 06, 10 | 3 |
| RF-10 | 05, 06 | 2 |
| RF-11 | 08 | 3 |
| RF-12 | 05, 11 | 6 |
| RF-13 | 07 | 5 |
| RF-14 | 04, 05, 11 | 11 |
| RNF-01 | 01, 09 | 2 |
| RNF-02 | 04 | 1 |
| RNF-03 | 08 | 1 |
| RNF-04 | 12 | 6 |
| RNF-05 | 09 | 1 |
| RNF-06 | 04 | 2 |

Requisitos de processo RP-01 a RP-06: fora das tasks de código por decisão do estudante (RP-04 coberto pela task 12). O relatório e o roteiro do vídeo ficam para depois do sistema pronto.
