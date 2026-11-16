# language: pt
Funcionalidade: Buscar servidores na janela
  Para encontrar um servidor rapidamente durante a análise
  Como analista da Secretaria de Atos de Pessoal
  Quero digitar parte do nome, escolher o município e ver a lista

  @RNF-01 @ui
  Cenário: A janela avisa que os dados são fictícios
    Quando abro a janela
    Então vejo a faixa "Dados fictícios, para demonstração"

  @RF-04 @ui
  Cenário: Os municípios aparecem para escolha
    Quando abro a janela
    Então o seletor de município mostra "Todos os municípios" selecionado
    E mostra os 10 municípios em ordem alfabética

  @RF-05 @ui
  Cenário: Buscar por trecho do nome
    Dado que a janela está aberta
    Quando digito "conceicao" e clico em "Buscar"
    Então vejo uma lista com o nome e o município de cada servidor encontrado

  @RF-05 @ui
  Cenário: Buscar com a tecla Enter
    Dado que a janela está aberta
    Quando digito "maria" e aperto Enter
    Então a busca é feita e a lista é atualizada

  @RF-04 @ui
  Cenário: Buscar dentro de um município
    Dado que a janela está aberta
    Quando digito "maria", escolho o município "Anápolis" e busco
    Então todos os servidores da lista são de Anápolis

  @RF-05 @ui
  Cenário: Buscar com o nome vazio
    Dado que a janela está aberta
    Quando deixo o nome em branco e clico em "Buscar"
    Então vejo todos os servidores do município escolhido, ou os 50, se for "Todos os municípios"

  @RF-06 @ui
  Cenário: Nenhum servidor encontrado
    Dado que a janela está aberta
    Quando busco por "zzz"
    Então vejo a mensagem "Nenhum servidor encontrado"
    E não vejo mensagem de erro

  @RNF-05 @ui
  Cenário: A janela é legível em gravação de tela
    Quando abro a janela
    Então todos os textos usam fonte de pelo menos 12 pt

  @RF-05 @integracao
  Cenário: A lista corresponde ao que o servidor tem
    Dado que o servidor real está no ar com a base fictícia
    Quando busco por "joao" na janela
    Então a lista mostra exatamente os servidores que a busca do servidor devolve para "joao"
