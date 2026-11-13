# Projeto Integrador III-A: resumo da proposta

PUC Goiás – CEAD – Escola Politécnica e de Artes | Análise e Desenvolvimento de Sistemas | Prof. Thalles Bruno G. N. dos Santos | Goiânia, 2026

Fonte: `Proposta.pdf`. Anotações feitas em 13/11/2026.

## 1. Visão geral

Projeto **extensionista**: deve ser feito para uma **instituição real** (pública, privada ou ONG).

**Objetivo:** criar uma aplicação simples de **consulta de informações**, com arquitetura **cliente-servidor** e **segurança básica na comunicação**, que resolva uma necessidade real da instituição escolhida.

## 2. Prazos

| Data | Atividade | Situação (em 13/11/2026) |
|---|---|---|
| 26/10/2026, 19h | 1ª aula síncrona: apresentação do projeto | Passou |
| 07/11/2026, 11h | 2ª aula síncrona: ajustes | Passou |
| **26/11/2026, 19h** | 3ª aula síncrona: ajustes finais | **Em 13 dias** |
| **07/12/2026, 23h59** | **Entrega do Projeto Integrador** | **Em 24 dias** |

## 3. Requisitos

### A) Contexto institucional
- Selecionar uma instituição pública, privada ou ONG.
- Fazer um levantamento simplificado das necessidades, por contato com um representante.
- Identificar uma necessidade que uma aplicação de consulta de informações resolva.
- Definir com a instituição quais informações serão disponibilizadas.

### B) Desenvolvimento da aplicação
- **Servidor:** armazena ou disponibiliza as informações, recebe as solicitações do cliente, processa e devolve as informações correspondentes.
- **Cliente:** o usuário faz consultas ao servidor, as solicitações são enviadas por comunicação em rede, e as informações recebidas são apresentadas de forma organizada.
- A interface pode ser em **linha de comando**; interface gráfica não é exigida.
- **Banco de dados não é exigido.** As informações podem ficar em arquivos ou em estruturas da linguagem escolhida.
- Execução e demonstração podem ser em ambiente local, sem hospedagem.

### C) Segurança da informação
- Proteger a comunicação cliente-servidor com uma **biblioteca ou recurso de segurança existente**. O PDF não cita qual; TLS/SSL é o candidato natural.
- Evitar a exposição de informações sensíveis da instituição.

### D) Validação na instituição
- Apresentar a aplicação a um representante da instituição e fazer uma demonstração.
- **Registrar as considerações e sugestões** recebidas.
- Não é necessária implantação definitiva: basta um protótipo funcional.

## 4. Entregáveis

Todos obrigatórios. Cada aluno deve enviar os seus arquivos; quem não enviar recebe nota zero, mesmo que o restante do grupo tenha enviado.

1. **Relatório técnico em PDF, até 5 páginas** (sem capa e referências). Formato: Arial 12pt, espaçamento simples, margens de 2,5 cm (superior e inferior) e 3 cm (laterais). Seções:
   - Identificação da instituição: nome, área de atuação e breve descrição das atividades.
   - Problema identificado: necessidade apresentada pela instituição e justificativa da solução.
   - Solução desenvolvida: funcionalidades, arquitetura cliente-servidor e mecanismo de segurança.
   - Resultados: evidências do funcionamento (capturas de tela) e descrição da demonstração feita à instituição.
   - Considerações finais: resultados alcançados, dificuldades encontradas e possíveis melhorias.
2. **Código-fonte** em repositório ou arquivo compactado, com **instruções básicas de execução**.
3. **Vídeo de até 10 minutos** mostrando a aplicação, as funcionalidades e a comunicação cliente-servidor. Link acessível (Google Drive ou YouTube não listado).
4. **Evidência da atividade extensionista:**
   - Carta de Início das Atividades, preenchida e assinada pelo aluno (ou grupo) e pelo professor.
   - Termo de Formalização de Convênio, preenchido e assinado pelo aluno (ou grupo) e por um representante da instituição.

Envio: o PDF prevê dois campos de upload, "Entregáveis do PI" (relatório, código, documentos) e "Vídeo de Apresentação do PI" (obrigatório).

## 5. Critérios de avaliação

- Funcionamento da solução.
- Aplicação dos conceitos estudados no módulo.
- **Comprovação da interação com a instituição.**
- Priorizar a necessidade identificada e **evitar funcionalidades desnecessárias ou complexidade técnica excessiva**.
- A proposta admite que nem tudo está definido e incentiva a criatividade do aluno.

## 6. Pontos em aberto (a decidir)

Decisões necessárias antes de escrever o PRD.

| # | Ponto | Observação | Decisão |
|---|---|---|---|
| 1 | Instituição | Há contato com algum representante? É o maior risco do cronograma: o Termo de Convênio precisa de assinatura externa e a demonstração precisa ocorrer antes de 07/12. | |
| 2 | Individual ou em grupo | Define a divisão de trabalho e quem assina os documentos. | |
| 3 | Necessidade concreta | Que informação será consultada e por quem. | |
| 4 | Linguagem e stack | O PDF não impõe nenhuma. Python tem `socket` e `ssl` na biblioteca padrão. | |
| 5 | Protocolo da consulta | Sockets TCP com protocolo próprio ou HTTP. "Comunicação em rede" favorece sockets. | |
| 6 | Mecanismo de segurança | TLS (certificado autoassinado serve para protótipo). Conferir o que as disciplinas do módulo ensinaram. | |
| 7 | Dados sensíveis | Quais dados são públicos e quais são sensíveis; usar dados de exemplo ou anonimizados. | |
| 8 | Material das disciplinas e Plano de Ensino | O PDF manda consultá-los; ainda não foram fornecidos. | |
| 9 | Modelos dos documentos | Carta de Início das Atividades e Termo de Formalização de Convênio. | |

## 7. Organização no Spec-Driven

- **PRD:** requisitos funcionais vêm dos itens A a D. Os entregáveis (relatório, vídeo, documentos) entram como requisitos de processo, para o rastreio não deixar nenhum de fora.
- **TechSpec:** protocolo cliente-servidor, formato dos dados (por exemplo JSON ou CSV), TLS, tratamento de erros e estrutura do projeto.
- **Tasks:** servidor, cliente, TLS, dados de exemplo, testes e README de execução; depois relatório e roteiro do vídeo.
- **Fora do código:** contato com a instituição, assinaturas, demonstração e registro do feedback. Não são tasks de código, mas precisam de datas no plano.
