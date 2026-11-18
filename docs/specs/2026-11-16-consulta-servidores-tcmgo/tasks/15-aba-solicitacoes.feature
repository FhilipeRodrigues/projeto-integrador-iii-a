# language: pt
Funcionalidade: Aba de solicitações na janela
  Para analisar um requerimento de aposentadoria
  Como analista da Secretaria de Atos de Pessoal
  Quero ver a lista de solicitações e abrir o documento de cada uma

  Contexto:
    Dado que o servidor está no ar com 10 solicitações
    E a janela do cliente está aberta

  @RF-16 @ui
  Cenário: A janela tem as abas Consulta e Solicitações
    Então vejo as abas "Consulta" e "Solicitações"
    E a aba "Consulta" é a que está aberta, com o mesmo comportamento de antes

  @RF-16 @ui
  Cenário: A aba Solicitações lista os requerimentos
    Quando abro a aba "Solicitações"
    Então vejo 10 linhas com número, servidor, município e situação
    E todas estão com a situação "Pendente"

  @RF-16 @ui
  Cenário: Selecionar uma solicitação mostra o documento formal
    Quando seleciono a primeira solicitação da lista
    Então vejo um documento com o título "Requerimento de aposentadoria" e o número da solicitação
    E vejo o município, o órgão, o nome do servidor, a data de ingresso e a data da solicitação
    E vejo o pedido de aposentadoria voluntária e a assinatura do servidor

  @RF-16 @ui
  Cenário: O texto concorda com o sexo do servidor
    Quando seleciono a solicitação de uma servidora
    Então o texto diz "a servidora"
    Quando seleciono a solicitação de um servidor
    Então o texto diz "o servidor"

  @RF-16 @ui
  Cenário: O documento deixa os dados da análise para a consulta
    Quando seleciono qualquer solicitação
    Então o documento não mostra idade, tempo de contribuição, PCD, doença profissional nem remuneração
    E não indica se o servidor pode ou não se aposentar

  @RF-16 @ui
  Cenário: O documento é legível e avisa que é fictício
    Quando seleciono qualquer solicitação
    Então o texto do documento usa fonte de pelo menos 12 pt
    E o rodapé diz "Documento fictício, para demonstração"

  @RF-16 @ui
  Cenário: Trocar de aba não perde a consulta
    Dado que busquei "maria" e abri uma ficha na aba "Consulta"
    Quando abro a aba "Solicitações" e volto à aba "Consulta"
    Então a busca, a lista e a ficha continuam como estavam

  @RF-12 @ui
  Cenário: Falha de rede na aba Solicitações
    Dado que o servidor está fora do ar
    Quando abro a aba "Solicitações"
    Então vejo uma mensagem clara sobre a falha
    E a janela continua aberta e responde ao teclado e ao mouse
