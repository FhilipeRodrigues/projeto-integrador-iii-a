# Check Spec: Consulta de servidores municipais (TCM-GO)

- **Data:** 2026-11-25 (3ª rodada, após as revisões que criaram as tasks 17, 18 e 19; a 1ª rodada, de 2026-11-16, aprovou as tasks 01 a 12, e a 2ª, de 2026-11-18, as tasks 13 a 16)
- **Veredito:** aprovado
- **Arquivos conferidos:** `prd.md`, `techspec.md`, `tasks.md`, `tasks/01-base-ficticia` a `tasks/19-criar-conta` (19 arquivos `.md` e 19 `.feature`) e `.claude/quality.json`

Os cruzamentos de IDs (RF, RNF, tags, dependências, índice e status) foram feitos por script sobre os arquivos inteiros, e não só pelo `tasks.md`. As 19 tasks já constam como `feita`: esta rodada confere a spec que as tasks 17 a 19 acrescentaram, que ainda não tinha passado pelo `check-spec`.

## Bloqueantes

Nenhum.

| # | Resultado |
|---|---|
| 1 | PRD e TechSpec estão `aprovado` (2026-11-16), com as revisões de 2026-11-18, 2026-11-24, 2026-11-25 e 2026-11-25b registradas (no TechSpec, depois do aviso A) |
| 2 | As 2 questões abertas do PRD são `não bloqueante` (assinatura da Carta e data da demonstração) |
| 3 | Os 22 RF e os 8 RNF do PRD aparecem na tabela de rastreio do TechSpec, e a tabela não traz ID inexistente |
| 4 | Todo RF e RNF tem ao menos uma task e um cenário com a tag correspondente (RF-07 e RF-08 estão em "Esquema do Cenário" na task 02) |
| 5 | Nenhuma task cita requisito inexistente (ver aviso B sobre o RF-12 na task 18) |
| 6 | As 19 tasks têm exatamente um `.feature`, com `# language: pt` e um só `Funcionalidade:`. Não há `.feature` sem task |
| 7 | `depende` só aponta para tasks anteriores existentes, sem ciclo (17 depende de 14 e 15; 18 de 16 e 17; 19 de 18). O status e a linha de cada task em `tasks.md` coincidem com os arquivos |
| 8 | `python -m unittest discover -s tests -v` e `python -m compileall -q consulta scripts tests` existem em `.claude/quality.json`; `git check-ignore .env` é um comando do git. Ver aviso E |
| 9 | A task 19 não muda o modelo de dados: o `.env` mantém o formato da task 18 (`USUARIO` e `SENHA_HASH`). O TechSpec (revisão 2026-11-25b) descreve a reversão (parar o servidor, apagar `.env` e `data/solicitacoes.json`) e o que vale como "sem conta" (arquivo ausente ou valores vazios) |
| 13 | Todo cenário e todo esquema de cenário das 19 tasks tem exatamente uma tag de camada (`@ui`, `@fluxo` ou `@integracao`) e ao menos uma tag de requisito |

## Avisos

Os avisos A, B e C foram corrigidos na spec depois desta rodada, a pedido do estudante (edição feita fora desta skill), e o cruzamento por script foi refeito sem divergência:

- **[#1] A. TechSpec sem as revisões de 2026-11-25 e 2026-11-25b na linha de status.** Corrigido: a linha `Status` passou a citar as duas revisões.
- **[#5] B. A task 18 usava `@RF-12` num cenário** ("Servidor fora do ar ao entrar") sem o RF-12 no `requisitos`. Corrigido em `tasks/18-login.md` e na linha 18 de `tasks.md`.
- **[#4] C. A "Cobertura" e a "Ordem sugerida" de `tasks.md` estavam desatualizadas** (RF-01 a RF-14, RNF-01 a RNF-06, ordem até a task 16). Corrigido: RF-01 a RF-22, RNF-01 a RNF-08 e ordem até a task 19.
- **[#10] D. Tamanho das tasks 18 e 19.** A 18 tem 14 cenários e a 19 tem 15, cada uma em servidor, cliente e janela (de 8 a 10 arquivos com os testes). Cada uma tem um só comportamento (login; criar a conta), e as duas já foram executadas e passaram na suíte inteira. Em tasks futuras desse porte, dividir em "servidor e cliente" e "janela".
- **[#8] E.** A task 19 escreve a validação com `.venv/Scripts/python.exe -m ...` por causa do Python isolado desta máquina. É equivalente ao `python -m ...` do `quality.json`, mas só vale onde o `.venv` existe.
- **[#12] F.** Os `.feature` das tasks 18 e 19 citam o nome do arquivo `.env`, a chave `SENHA_HASH`, a operação `criar_conta` e os códigos `CREDENCIAIS_INVALIDAS`, `CONTA_JA_EXISTE`, `REQUISICAO_INVALIDA` e `ERRO_INTERNO`. É o contrato do TechSpec, como nas tasks 06 e 07, e fica aceitável.
- **[#11] G. RNF-08 tem forma de verificação** na estratégia de teste das revisões 2026-11-25 e 2026-11-25b: hash, `git check-ignore .env`, log sem segredo, gravação do `.env` sem arquivo pela metade (testes de falha ao gravar e de criações simultâneas). Nada a ajustar.
- **[#2] H. Pendências do estudante, fora do código:** como assinar a Carta pelo estudante e marcar a data da demonstração à Juliana.

## Cobertura

| Requisito | Tasks | Cenários em |
|---|---|---|
| RF-01 | 01, 13 | 01, 13 |
| RF-02 | 02, 06, 10 | 02, 06, 10 |
| RF-03 | 03, 06 | 03, 06 |
| RF-04 | 03, 06, 09 | 03, 06, 09 |
| RF-05 | 09, 10 | 09, 10 |
| RF-06 | 09 | 09 |
| RF-07 | 02 | 02 (esquema) |
| RF-08 | 02 | 02 (esquema) |
| RF-09 | 02, 06, 10, 16, 17 | 02, 06, 10, 16, 17 |
| RF-10 | 05, 06 | 05, 06 |
| RF-11 | 08 | 08 |
| RF-12 | 05, 11, 15, 16, 17, 18 | 05, 11, 15, 16, 17, 18 |
| RF-13 | 07 | 07 |
| RF-14 | 04, 05, 11 | 04, 05, 11 |
| RF-15 | 14 | 14 |
| RF-16 | 14, 15 | 14, 15 |
| RF-17 | 16 | 16 |
| RF-18 | 16 | 16 |
| RF-19 | 17 | 17 |
| RF-20 | 18 | 18 |
| RF-21 | 18 | 18 |
| RF-22 | 19 | 19 |
| RNF-01 | 01, 09 | 01, 09 |
| RNF-02 | 04 | 04 |
| RNF-03 | 08 | 08 |
| RNF-04 | 12 | 12 |
| RNF-05 | 09 | 09 |
| RNF-06 | 04 | 04 |
| RNF-07 | 14, 16 | 14, 16 |
| RNF-08 | 18, 19 | 18, 19 |
