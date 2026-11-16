# language: pt
Funcionalidade: Certificados da Autoridade Certificadora local
  Para que o cliente confie apenas no servidor legítimo do projeto
  Como estudante responsável pela segurança do protótipo
  Quero gerar a CA e o certificado do servidor por script

  @RF-14 @fluxo
  Cenário: Gerar a CA e o certificado do servidor
    Quando executo o script de certificados
    Então são criados o certificado da CA, o certificado do servidor e a chave privada de cada um

  @RF-14 @fluxo
  Cenário: O certificado do servidor é assinado pela CA do projeto
    Dado que gerei os certificados
    Quando verifico o certificado do servidor contra o certificado da CA
    Então a verificação é aprovada

  @RF-14 @fluxo
  Cenário: O certificado vale para o endereço local
    Dado que gerei os certificados
    Então o certificado do servidor é válido para "localhost" e para "127.0.0.1"

  @RF-14 @fluxo
  Cenário: Os certificados atendem à verificação estrita do Python
    Dado que gerei os certificados
    Quando um cliente que confia só na CA do projeto se conecta a um servidor TLS que usa esse certificado
    Então o aperto de mão termina com sucesso

  @RNF-06 @fluxo
  Cenário: Gerar de novo em outra pasta
    Quando executo o script de certificados escolhendo outra pasta de destino
    Então os arquivos são criados nessa pasta
    E o certificado dessa pasta não é aceito pela CA da pasta padrão

  @RNF-02 @fluxo
  Cenário: As chaves privadas não vão para o repositório
    Dado que gerei os certificados na pasta padrão
    Então o git ignora a chave privada da CA
    E o git ignora a chave privada do servidor

  @RNF-06 @fluxo
  Cenário: Falta o programa que gera os certificados
    Dado que o programa "openssl" não está disponível
    Quando executo o script de certificados
    Então vejo uma mensagem que explica o que falta e como obtê-lo
    E nenhum arquivo parcial é deixado na pasta de destino
