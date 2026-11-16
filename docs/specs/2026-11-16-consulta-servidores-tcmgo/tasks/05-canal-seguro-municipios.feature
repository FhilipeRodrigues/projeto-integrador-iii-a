# language: pt
Funcionalidade: Canal seguro entre cliente e servidor
  Para que as consultas não possam ser lidas nem desviadas na rede
  Como avaliador do projeto e como analista
  Quero que cliente e servidor conversem por uma conexão cifrada e autenticada

  Contexto:
    Dado que gerei os certificados da CA do projeto
    E o servidor está no ar com o certificado assinado por essa CA

  @RF-10 @fluxo
  Cenário: O cliente obtém a lista de municípios pelo servidor
    Quando o cliente pede a lista de municípios
    Então recebe os 10 municípios da base em ordem alfabética

  @RF-14 @fluxo
  Cenário: A comunicação é cifrada com TLS
    Quando o cliente pede a lista de municípios
    Então a conexão usou TLS na versão 1.2 ou superior
    E o servidor registrou no terminal a hora, o endereço do cliente, a versão do TLS e a operação pedida

  @RF-14 @fluxo
  Cenário: O log do servidor não mostra dados das fichas
    Quando o cliente pede a lista de municípios
    Então o registro do servidor não contém nomes de servidores nem remunerações

  @RF-14 @fluxo
  Cenário: O cliente recusa um servidor com certificado de outra CA
    Dado um servidor que usa um certificado emitido por outra CA
    Quando o cliente tenta pedir a lista de municípios a esse servidor
    Então a conexão é recusada
    E o cliente informa que o certificado do servidor não é confiável

  @RF-14 @fluxo
  Cenário: O cliente recusa um servidor cujo certificado não vale para o endereço usado
    Dado que o cliente se conecta pelo nome "outro.exemplo"
    Quando o cliente tenta pedir a lista de municípios
    Então a conexão é recusada
    E o cliente informa que o certificado não corresponde ao endereço

  @RF-12 @fluxo
  Cenário: O servidor está parado
    Dado que o servidor foi encerrado
    Quando o cliente pede a lista de municípios
    Então o cliente informa que não conseguiu conectar ao servidor
    E o cliente não encerra com erro inesperado

  @RF-14 @fluxo
  Cenário: O servidor não inicia sem os certificados
    Dado que a pasta de certificados está vazia
    Quando tento iniciar o servidor
    Então o servidor não inicia
    E mostra uma mensagem que manda executar o script de certificados
