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

## Próximos passos

1. **Estudante:**
   - Assinar a Carta por gov.br e enviar ao professor pelo Teams, perguntando como assinar pelo aluno se faltar a linha.
   - Depois que o professor assinar, enviar os dois termos à Juliana para ela preencher os dados dela e assinar.
   - Marcar a data da demonstração à Juliana (questão aberta do PRD).
2. **Claude:** `create-techspec` → `create-tasks` → `check-spec` → `execute-task` (uma task por contexto). O TechSpec define o protocolo, o formato dos dados, o TLS com CA local e a estrutura do projeto.
3. Antes da demonstração, validar com a Juliana os campos da ficha.

## Referências

- PRD: `docs/specs/2026-11-16-consulta-servidores-tcmgo/prd.md`.
- Dados pessoais e do TCM-GO: `dados-pessoais.local.md` (não versionado).
- Documentos preenchidos: `documentos-preenchidos/` (não versionado). Script de preenchimento e venv ficaram no scratchpad da sessão, e podem ser refeitos.
- Proposta (seção 4): interface gráfica não é exigida, mas é permitida.
