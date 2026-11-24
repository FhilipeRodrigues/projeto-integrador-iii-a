# PRD: Consulta de servidores municipais para apoio à análise de aposentadoria (TCM-GO)

- **Data:** 2026-11-16
- **Status:** aprovado (2026-11-16). **Revisão 2026-11-18** (RF-01 alterado, RF-02 e RF-09 ajustados, RF-15 a RF-18 e RNF-07 novos): aprovada pelo estudante em 2026-11-18. **Revisão 2026-11-24** (RF-19 novo, aba "Regras"): pedida e escopo confirmado pelo estudante em 2026-11-24.

## Problema
Na Secretaria de Atos de Pessoal do TCM-GO, a análise de aposentadorias exige consultar a situação funcional de servidores de vários municípios (idade, tempo de serviço, órgão, remuneração e condições especiais). Hoje essa consulta depende de procurar as informações em fontes separadas, o que é lento e sujeito a erro. A proposta do Projeto Integrador III-A pede um protótipo de consulta de informações em arquitetura cliente-servidor, com comunicação protegida, validado com um representante da instituição (Juliana, chefe direta do estudante).

O protótipo usa uma base **fictícia** (10 municípios, cerca de 50 servidores), pois não deve expor dados reais do TCM-GO.

## Objetivos e métrica de sucesso
- Permitir localizar um servidor por nome e ver sua ficha completa — medido por: encontrar qualquer um dos servidores da base e abrir a ficha em até 3 interações a partir da tela inicial.
- Demonstrar comunicação cliente-servidor protegida — medido por: cliente recusa servidor sem certificado da CA local e aceita o servidor legítimo (RF-14).
- Validar o protótipo com a instituição — medido por: demonstração realizada à Juliana antes de 26/11/2026, com considerações registradas (RP-02).
- Cumprir os entregáveis da disciplina — medido por: itens RP-01 a RP-06 enviados até os prazos.

## Usuários
- **Analista da Secretaria de Atos de Pessoal (representado pela Juliana):** precisa consultar rápido a ficha de um servidor, às vezes sem lembrar a grafia exata do nome, e restringir a busca a um município.
- **Avaliador (professor):** precisa ver, no código e no vídeo, a comunicação cliente-servidor e o mecanismo de segurança funcionando.

## Histórias de usuário
- Como analista, quero digitar parte do nome de um servidor, sem me preocupar com acentos ou maiúsculas, para encontrá-lo mesmo sem saber a grafia exata. (RF-03, RF-05, RF-06)
- Como analista, quero restringir a busca a um município, para reduzir a lista quando há nomes parecidos. (RF-04)
- Como analista, quero abrir a ficha do servidor escolhido, para ver os dados necessários à análise de aposentadoria. (RF-02, RF-07, RF-08)
- Como analista, quero usar o sistema com vários clientes abertos ao mesmo tempo, para que a consulta de um colega não bloqueie a minha. (RF-11)
- Como avaliador, quero ver que a comunicação é cifrada e que o cliente só confia no servidor legítimo, para verificar o requisito de segurança. (RF-14)
- Como analista, quero abrir o requerimento de aposentadoria de um servidor, conferir os dados dele na consulta e então aprová-lo ou desaprová-lo, e ver essa decisão registrada mesmo depois de reiniciar o sistema. (RF-15 a RF-18)
- Como analista, quero consultar as regras básicas de aposentadoria numa aba da própria janela, para decidir se aprovo ou desaprovo sem sair do sistema. (RF-19)
- Como estudante, quero cumprir as etapas de documentos, demonstração e entregas no prazo. (RP-01 a RP-06)

## Requisitos funcionais
- **RF-01:** O sistema deve dispor de uma base fictícia de 10 municípios e 50 servidores, gerada de forma reproduzível (a mesma geração produz sempre a mesma base). Os 50 primeiros nomes são os 25 masculinos e os 25 femininos mais comuns do Brasil (lista do estudante), cada um usado uma única vez e distribuído aleatoriamente entre os municípios. Cada servidor recebe dois sobrenomes comuns diferentes entre si, sorteados. O sexo do servidor acompanha o nome.
- **RF-02:** A ficha do servidor deve exibir: nome completo, sexo, idade, órgão de atuação, PCD (sim ou não), doença profissional ou acidente de trabalho (sim ou não e, se sim, qual), data de ingresso, data da solicitação, última remuneração e tempo de contribuição. Quando o servidor tiver uma solicitação de aposentadoria (RF-15), a ficha exibe também a situação dela (RF-18).
- **RF-03:** O sistema deve buscar servidores por trecho do nome, ignorando acentos e diferença entre maiúsculas e minúsculas. Com o nome vazio, a busca lista todos os servidores (respeitando o filtro de município, RF-04).
- **RF-04:** O sistema deve permitir filtrar a busca por município. Sem filtro, a busca considera todos os municípios. O filtro combina com o nome. A lista de municípios disponível vem do servidor.
- **RF-05:** O resultado da busca deve ser uma lista com nome e município de cada servidor encontrado. Ao selecionar um item, o sistema exibe a ficha completa (RF-02). Ao abrir, a janela já lista todos os servidores (busca com nome vazio e sem filtro), sem o usuário precisar clicar em "Buscar".
- **RF-06:** Quando a busca não encontrar nenhum servidor, o cliente deve exibir uma mensagem clara de "nenhum resultado", sem erro.
- **RF-07:** O tempo de contribuição deve ser a diferença entre a data da solicitação e a data de ingresso, em anos inteiros completos (parte inteira, sem arredondar para cima). Simplificação aceita.
- **RF-08:** A idade deve ser calculada, em anos completos, a partir da data de nascimento do servidor até a **data da solicitação**, e não armazenada como valor fixo.
- **RF-09:** O sistema não deve calcular nem indicar se o servidor atende ou não aos requisitos de aposentadoria. A ficha traz os dados do servidor, e a situação de uma solicitação (RF-18) é apenas o registro da decisão tomada pelo usuário (RF-17), nunca uma conclusão do sistema.
- **RF-10:** O sistema deve ser dividido em servidor (guarda a base, recebe consultas e devolve resultados) e cliente (interface gráfica de janela, simples, que envia as consultas pela rede e apresenta as respostas de forma organizada).
- **RF-11:** O servidor deve atender mais de um cliente ao mesmo tempo.
- **RF-12:** Se o servidor estiver indisponível ou a conexão cair, o cliente deve informar o problema ao usuário, sem travar nem encerrar.
- **RF-13:** Se o servidor receber uma solicitação inválida, deve responder com erro e continuar atendendo os demais clientes.
- **RF-14:** A comunicação entre cliente e servidor deve ser cifrada. O cliente deve confiar apenas em servidor cujo certificado tenha sido emitido pela Autoridade Certificadora (CA) local do projeto, e deve recusar a conexão e informar o usuário caso contrário.

- **RF-15:** O servidor deve manter 10 solicitações de aposentadoria fictícias, cada uma de um servidor diferente da base, sorteados aleatoriamente entre todos os municípios. O sorteio acontece uma única vez: o resultado é gravado em `data/solicitacoes.json` e reutilizado nas execuções seguintes, até o arquivo ser apagado. Cada solicitação nasce com a situação "Pendente".
- **RF-16:** O cliente deve ter uma aba "Solicitações", ao lado da aba "Consulta". Ela lista as solicitações (número, servidor, município e situação) e, ao selecionar uma, exibe um documento formal fictício de requerimento de aposentadoria, com o número, o município, o órgão, o nome do servidor, a data de ingresso, a data da solicitação e o texto do pedido. O documento não traz os dados que o analista deve conferir na aba "Consulta" (idade, tempo de contribuição, PCD, doença profissional e remuneração) nem indica elegibilidade.
- **RF-17:** O documento deve ter os botões "Aprovar" e "Desaprovar". A decisão é enviada ao servidor e pode ser trocada depois (para repetir a demonstração).
- **RF-18:** A situação de cada solicitação (Pendente, Aprovada ou Desaprovada) deve ser **persistente**: fica gravada em `data/solicitacoes.json`, sobrevive a reiniciar o servidor e aparece na lista de Solicitações, no documento e na ficha do servidor (aba "Consulta").
- **RF-19:** O cliente deve ter uma aba "Regras", depois da aba "Solicitações", com o texto das regras básicas de aposentadoria do servidor público, para o analista consultar ao aprovar ou desaprovar: **regra geral** (idade mínima de 62 anos para mulher e 65 para homem; contribuição mínima de 25 anos para ambos), **PCD por tempo de contribuição** (25 anos para homem e 20 para mulher), **PCD por idade** (60 anos para homem e 55 para mulher, com 15 anos de contribuição) e **doença profissional ou acidente de trabalho** (em caso positivo, aprovação direta). O texto vem do servidor (operação `regras`), é fixo e simplificado, serve de apoio à demonstração e não substitui a legislação. A aba só apresenta o texto: não calcula nem indica se um servidor atende (RF-09 continua valendo).

## Requisitos não funcionais
- **RNF-01 (dados):** A base e a interface não devem conter dados reais de pessoas ou do TCM-GO. A interface deve indicar que os dados são fictícios.
- **RNF-02 (segredos):** As chaves privadas (da CA e do servidor) não devem ser versionadas no repositório.
- **RNF-03 (desempenho):** Em ambiente local, uma busca deve retornar em até 1 segundo.
- **RNF-04 (execução):** O sistema deve rodar em ambiente local, sem hospedagem e sem banco de dados, e ser executado a partir das instruções do README, sem instalar bibliotecas externas além da própria linguagem.
- **RNF-05 (vídeo):** A interface deve ser legível em gravação de tela, com fonte de pelo menos 12 pt.
- **RNF-06 (reprodutibilidade):** Os certificados devem poder ser gerados novamente por script, seguindo o README.
- **RNF-07 (integridade do arquivo):** A gravação de `data/solicitacoes.json` não pode deixá-lo corrompido nem permitir que duas decisões simultâneas se percam. O arquivo não é versionado (é estado da execução); o servidor o cria sozinho se não existir e recusa subir se ele estiver inválido.

## Requisitos de processo
- **RP-01:** Carta de Início das Atividades, Termo de Formalização do Convênio e Termo de Participação e Responsabilidade devem ser assinados por gov.br e enviados na Plataforma A até 23/11/2026, 23h59. A Carta é assinada pelo estudante e pelo professor. Os dois termos, pelo estudante e pela Juliana.
- **RP-02:** A demonstração à Juliana deve ocorrer antes de 26/11/2026, e as considerações ou sugestões recebidas devem ser registradas por escrito.
- **RP-03:** O relatório técnico deve ser entregue em PDF, com até 5 páginas (sem capa e referências), em Arial 12 pt, espaçamento simples e margens de 2,5 cm (superior e inferior) e 3 cm (laterais), com as seções: identificação da instituição, problema, solução, resultados (com capturas de tela e descrição da demonstração) e considerações finais.
- **RP-04:** O código-fonte deve ser entregue em repositório ou arquivo compactado, com instruções básicas de execução.
- **RP-05:** O vídeo de até 10 minutos deve mostrar a aplicação, as funcionalidades e a comunicação cliente-servidor, com link acessível (Google Drive ou YouTube não listado).
- **RP-06:** Relatório, código e documentos devem ser enviados no campo "Entregáveis do PI", e o vídeo no campo "Vídeo de Apresentação do PI", até 07/12/2026, 23h59.

## Fora de escopo
- Autenticação e perfis de usuário (melhoria futura).
- Indicação de elegibilidade à aposentadoria ou qualquer regra previdenciária.
- Banco de dados, hospedagem e implantação definitiva na infraestrutura do TCM-GO.
- Cadastro, edição ou exclusão de servidores pelo cliente. A base de servidores é somente leitura; o cliente só registra a decisão das solicitações (RF-17).
- Autenticação de quem aprova ou desaprova: qualquer cliente que confie na CA do projeto pode decidir (protótipo fictício).
- Dados reais de servidores e integração com sistemas do TCM-GO.
- Interface web ou em linha de comando como cliente principal.
- Demonstração com o cliente em outro computador.
- Termo de cessão de voz e imagem.

## Questões abertas
- [x] Idade (RF-08): calculada na data da solicitação. Resolvido em 2026-11-16.
- [x] Tempo de contribuição (RF-07): anos inteiros. Resolvido em 2026-11-16.
- [x] Campos da ficha (RF-02): confirmados pelo estudante em 2026-11-16. Falta apenas validar com a Juliana na demonstração.
- [ ] A Carta de Início não tem linha de assinatura do estudante, mas a proposta exige a assinatura dele. Confirmar com o professor como assinar. — não bloqueante
- [ ] Data e horário da demonstração à Juliana, antes de 26/11. — não bloqueante
