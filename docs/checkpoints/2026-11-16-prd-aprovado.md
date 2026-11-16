# Checkpoint: PRD aprovado e documentos preenchidos (16/11/2026)

Complementa [2026-11-13-planejamento-inicial.md](2026-11-13-planejamento-inicial.md). Onde houver conflito, vale este.

## Progresso

- Documentos preenchidos do lado do estudante, em `documentos-preenchidos/` (não versionado): Carta de Início, Termo de Formalização (Word) e Termo de Participação e Responsabilidade (PDF). Campos da Juliana em branco, de propósito.
- PRD aprovado: [prd.md](../specs/2026-11-16-consulta-servidores-tcmgo/prd.md) (14 RF, 6 RNF, 6 RP).
- Código: nada escrito ainda.

## Decisões novas (confirmadas pelo estudante)

| Tema | Decisão | Por quê |
|---|---|---|
| Interface do cliente | **Interface gráfica (Tkinter)**, no lugar da linha de comando | A proposta permite CLI, mas não exige. O estudante quer algo mais apresentável no vídeo e quer aprender Tkinter |
| Resultado da busca | Lista (nome e município), depois ficha ao selecionar | Cobre grafia parcial |
| Elegibilidade | Não indicar; só exibir os dados | Evita regra previdenciária |
| Demonstração | Tudo na máquina do estudante, ambiente local | Proposta permite; menos risco |
| Concorrência | Servidor atende vários clientes ao mesmo tempo | Custa pouco e aparece bem no vídeo |
| Idade | Em anos completos, até a **data da solicitação** | Coerente com o tempo de contribuição |
| Tempo de contribuição | Anos inteiros (parte inteira) | Simplificação aceita |
| Campos da ficha | Confirmados pelo estudante; falta validar com a Juliana na demo | A proposta pede definir em conjunto com a instituição |
| Carta de Início | Proposta exige assinatura do aluno **e** do professor, mas o modelo só tem linha do professor | Resolver com o professor |
| Termos para a Juliana | Só enviar **depois** que o professor assinar a Carta | Decisão do estudante |

## Prazos

Sem mudança. Documentos assinados até **23/11 23h59**, demonstração à Juliana **antes de 26/11**, entrega final **07/12 23h59**.

## Atualização do fim do dia (16/11/2026)

- **Carta de Início: concluída.** O estudante assinou por gov.br e o professor devolveu a versão definitiva, com as duas assinaturas, em uma página: `documentos-preenchidos/Carta_de_Inicio_das_Atividades_-_assinado_7985.pdf`. A assinatura do aluno pôde ser posta em qualquer lugar do PDF, então a questão aberta da Carta está resolvida. Foi apagada a versão intermediária (só com a assinatura do aluno).
- **Termos: plano mudou.** Os termos que o estudante assinou tinham os campos da Juliana em branco, e o Termo de Formalização em PDF não permite digitar nada. Novo fluxo, sem assinatura antes de os campos estarem completos:
  1. O estudante envia à Juliana os arquivos **sem assinatura**, na pasta `documentos-preenchidos/para-juliana/`: o Termo de Formalização em Word e o Termo de Participação em PDF preenchível.
  2. Ela preenche os campos dela e devolve, sem assinar.
  3. O estudante confere, converte o Word para PDF e assina de novo os dois, por gov.br.
  4. Ela assina, pelo `assinador.iti.br`, o arquivo que o estudante enviar.
  5. O estudante anexa tudo na Plataforma A até 23/11, 23h59.
- Os PDFs dos termos que o estudante já assinou (`*_preenchido_assinado.pdf`) ficam obsoletos e não devem ser enviados.
- Detalhe estético na Carta definitiva: sobrou um trecho sublinhado ("__________") depois do nome do professor. Já está assinada, então foi deixado como está.

## Próximos passos

1. **Estudante:**
   - Enviar os termos sem assinatura à Juliana e seguir o fluxo acima.
   - Marcar a data da demonstração à Juliana (questão aberta do PRD).
2. **Claude:** `create-techspec` → `create-tasks` → `check-spec` → `execute-task` (uma task por contexto). O TechSpec define o protocolo, o formato dos dados, o TLS com CA local e a estrutura do projeto.
3. Antes da demonstração, validar com a Juliana os campos da ficha.

## Como retomar (inclusive em outra máquina)

1. **Branch:** o trabalho está na `docs/spec-consulta-servidores-tcmgo`. Em outra máquina só existe depois do `git push` dessa branch.
2. **Ler antes de agir:** este checkpoint e `docs/specs/2026-11-16-consulta-servidores-tcmgo/` (`prd.md`, `techspec.md`, `tasks.md`, `check-spec.md`, status `aprovado`).
3. **Começar o código:** `/clear` e depois a skill `execute-task` pela **task 01** (`tasks/01-base-ficticia.md`). Uma task por contexto. A task 01 também deve criar o `.claude/quality.json` com os comandos de teste e de sintaxe.
4. **Ambiente necessário:** Python 3.10 ou superior (a máquina atual tem 3.15.0), Tkinter e o executável `openssl` no PATH (no Windows, o do Git for Windows serve). Nada de bibliotecas externas no sistema.
5. **O que não está no repositório** (`.gitignore`) e precisa ser refeito ou levado à mão em outra máquina:
   - `dados-pessoais.local.md` (dados do estudante, do TCM-GO e da vigência);
   - `documentos-preenchidos/` (Carta assinada e termos). O script que preencheu os documentos ficou no scratchpad da sessão e tinha dados pessoais fixos, então não foi versionado. Se for preciso preencher de novo, escrever outro;
   - os PDFs da proposta e do material das disciplinas, e a memória local do Claude (`~/.claude/projects/...`). As decisões que importam estão neste checkpoint e na spec.
6. **Fora do código, em paralelo:** termos com a Juliana (fluxo acima, prazo 23/11) e a demonstração a ela antes de 26/11.
7. **Convenções:** commits em Conventional Commits, sem assinatura de IA. Integração por PR, que o estudante revisa e mergeia. Sem merge, rebase nem force push pelo Claude.

## Referências

- PRD: `docs/specs/2026-11-16-consulta-servidores-tcmgo/prd.md`.
- Dados pessoais e do TCM-GO: `dados-pessoais.local.md` (não versionado).
- Documentos preenchidos: `documentos-preenchidos/` (não versionado). Script de preenchimento e venv ficaram no scratchpad da sessão, e podem ser refeitos.
- Proposta (seção 4): interface gráfica não é exigida, mas é permitida.
