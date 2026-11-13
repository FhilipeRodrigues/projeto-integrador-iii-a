# Checkpoint: planejamento inicial do PI III-A (13/11/2026)

Resumo completo da proposta: [Resumo-Proposta-PI-III-A.md](../../Resumo-Proposta-PI-III-A.md).

## Progresso

- Proposta lida e resumida (requisitos, entregáveis, prazos, critérios).
- Material das disciplinas lido por busca de termos. Mecanismo de segurança definido a partir dele.
- Modelos de documentos localizados na Plataforma A e baixados (Carta de Início e Termo de Formalização do Convênio).
- Nenhum código escrito ainda. Nenhum documento preenchido ainda.

## Decisões (todas confirmadas pelo estudante)

| Tema | Decisão | Por quê |
|---|---|---|
| Instituição | TCM-GO (Tribunal de Contas dos Municípios do Estado de Goiás) | O estudante trabalha na Secretaria de Atos de Pessoal (análise de aposentadorias) |
| Representante | Juliana (chefe direta) | Assina o Termo de Formalização do Convênio |
| Equipe | Individual | O estudante e a Juliana assinam |
| Solução | Consulta de servidores municipais, apoio à análise de aposentadoria | Necessidade real da secretaria |
| Escopo de dados | 10 municípios, cerca de 50 servidores **fictícios** | Evita LGPD e trabalho excessivo; a proposta pede simplicidade |
| Base de dados | Arquivo JSON gerado por script com **semente fixa** | Reproduzível, sem banco de dados (não exigido) |
| Linguagem | Python | `socket` e `ssl` na biblioteca padrão |
| Arquitetura | Cliente-servidor sobre TCP, interface em linha de comando | Exigido pela proposta |
| Segurança | **TLS com CA local** (a CA assina o certificado do servidor; o cliente confia na CA) | O material das disciplinas trata de SSL/TLS, certificados e Autoridade Certificadora |
| Consulta | Busca por **nome, sem acento e sem diferenciar maiúsculas**, com **filtro por município** | Definido pelo estudante |
| Autenticação de usuário | **Fora do escopo** (não incluir) | A proposta manda evitar complexidade. Registrar como melhoria futura |
| Assinatura dos documentos | Assinatura digital **gov.br (E-GOV)**, indicada nos modelos | Gratuita. Não reutilizar o certificado do TCM (credencial de trabalho) |
| Voz e Imagem | Dispensado | Só necessário se terceiros aparecerem em voz ou vídeo no vídeo demonstrativo |

### Campos de cada servidor na ficha

1. Nome completo
2. Sexo
3. Idade (calculada a partir da data de nascimento)
4. Órgão de atuação
5. PCD (sim ou não)
6. Doença profissional ou acidente de trabalho (se sim, qual)
7. Data de ingresso
8. **Data da solicitação** (campo novo)
9. Última remuneração

**Tempo de contribuição** = data da solicitação menos data de ingresso, **em anos** (simplificação aceita).

## Prazos

| Data | O quê |
|---|---|
| **23/11/2026, 23h59** | Enviar na Plataforma A: Termo de Formalização, Carta de Início e Termo de Participação e Responsabilidade (assinados) |
| **26/11/2026, 19h** | 3ª aula síncrona (ajustes finais). Demonstração à Juliana deve ocorrer **antes** |
| **07/12/2026, 23h59** | Entrega final: relatório PDF (até 5 páginas), código com instruções, vídeo (até 10 min), documentos |

### Fluxo dos documentos (diagrama da plataforma)

1. Estudante preenche e assina a **Carta de Início** e envia ao professor pelo Teams.
2. Professor confere e assina a Carta.
3. Estudante entra em contato com a instituição (feito: TCM-GO, Juliana).
4. Estudante preenche e assina o **Termo de Formalização do Convênio** e envia à Juliana.
5. Juliana assina o Termo.
6. Estudante anexa os documentos na Plataforma A.

## Problemas encontrados nos modelos

- O **Termo de Convênio** veio preenchido de outro projeto: concedente "Programa de Gerontologia Social da PUC Goiás" e disciplina "Lazer e Recreação...". Trocar por TCM-GO e Projeto Integrador III-A.
- A **Carta** tem "2023" fixo na data. Trocar por 2026.
- Falta baixar o **Termo de Participação e Responsabilidade** (em "Documentos dos Estudantes" na Plataforma A).
- Os dados pessoais do estudante estão num arquivo **local e não versionado**: `dados-pessoais.local.md`. Em outra máquina, informe-os de novo.

## Próximos passos

1. **Pendências do estudante:**
   - Baixar o Termo de Participação e Responsabilidade.
   - Fornecer nome oficial, CNPJ e endereço do TCM-GO, e nome e cargo da Juliana.
   - Confirmar a vigência do Termo (sugestão: 12/10/2026 a 07/12/2026) e o nome exato da Escola.
   - Conferir o nível da conta gov.br (prata ou ouro) e se a Juliana tem conta compatível.
   - Ler a página "Como fazer a Assinatura Digital dos Documentos" na plataforma.
2. **Claude:** preencher os três documentos em Word, prontos para assinar.
3. **Estudante:** enviar a Carta ao professor pelo Teams e o Termo à Juliana, **antes de 23/11**.
4. **Spec-Driven:** `create-prd` → `create-techspec` → `create-tasks` → `check-spec` → `execute-task`. O PRD deve incluir os entregáveis (relatório, vídeo, documentos) como requisitos de processo.
5. **Antes do código:** marcar a demonstração com a Juliana, antes de 26/11.

## Referências

- Proposta: `Proposta.pdf` (não versionado, está na pasta local).
- Material das disciplinas (PDFs, não versionados). Trechos usados:
  - "Tipos comuns de invasão": HTTPS, SSL/TLS, certificados e Autoridade Certificadora.
  - "Redes - políticas de segurança, criptografia...": chave privada e pública, RSA, hash e assinatura digital.
  - "Processos para sistemas distribuídos": cliente/servidor sobre TCP/IP.
  - "A legislação da segurança da informação no Brasil": LGPD, usada para justificar TLS e base fictícia.
- Plataforma A: `pucgoiasgraduacao.grupoa.education`, página "Orientações para Atividades Extensionistas".
