# language: pt
Funcionalidade: Erros de rede e de certificado na janela
  Para saber o que houve quando a consulta não funciona
  Como analista da Secretaria de Atos de Pessoal
  Quero mensagens claras e uma janela que continua utilizável

  @RF-12 @ui
  Cenário: O servidor está parado ao buscar
    Dado que a janela está aberta e o servidor foi encerrado
    Quando busco por "maria"
    Então vejo a mensagem "Não foi possível conectar ao servidor. Verifique se ele está em execução."
    E a janela continua aberta e utilizável

  @RF-12 @ui
  Cenário: O servidor está parado ao abrir a janela
    Dado que o servidor está encerrado
    Quando abro a janela
    Então vejo a mensagem de que não foi possível conectar ao servidor
    E o seletor de município mostra apenas "Todos os municípios"

  @RF-12 @ui
  Cenário: A janela continua responsiva durante uma consulta lenta
    Dado um servidor que demora 3 segundos para responder
    Quando clico em "Buscar"
    Então o botão "Buscar" fica desabilitado e a janela continua respondendo a cliques e ao redimensionamento
    E quando a resposta chega, o botão volta a ficar habilitado

  @RF-12 @ui
  Cenário: A conexão cai no meio da consulta
    Dado um servidor que fecha a conexão sem responder
    Quando busco por "maria"
    Então vejo uma mensagem de que a conexão foi interrompida
    E posso buscar de novo

  @RF-12 @integracao
  Cenário: O servidor volta a funcionar sem reiniciar a janela
    Dado que a janela está aberta e o servidor estava parado
    Quando o servidor volta ao ar e eu busco por "maria"
    Então vejo a lista de resultados
    E os municípios passam a aparecer no seletor

  @RF-14 @integracao
  Cenário: O servidor tem certificado de outra CA
    Dado um servidor no ar que usa um certificado emitido por outra CA
    Quando abro a janela e busco por "maria"
    Então vejo a mensagem "Servidor não confiável: o certificado não foi emitido pela CA do projeto."
    E nenhuma lista de servidores é exibida

  @RF-14 @integracao
  Cenário: A janela não envia nada a um servidor não confiável
    Dado um servidor no ar que usa um certificado emitido por outra CA
    Quando busco por "maria"
    Então o servidor não recebe o conteúdo da busca
