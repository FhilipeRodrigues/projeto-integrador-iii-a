# language: pt
Funcionalidade: Consultar servidores pelo servidor
  Para analisar a aposentadoria de um servidor
  Como analista da Secretaria de Atos de Pessoal
  Quero buscar servidores e abrir a ficha pelo cliente

  Contexto:
    Dado que o servidor está no ar com a base fictícia e o canal seguro

  @RF-03 @fluxo
  Cenário: Buscar por trecho do nome
    Quando o cliente busca por "conceicao"
    Então recebe uma lista com identificação, nome e município de cada servidor encontrado
    E todos os nomes da lista contêm "conceição", sem diferenciar acento nem maiúsculas

  @RF-04 @fluxo
  Cenário: Buscar dentro de um município
    Quando o cliente busca por "maria" no município "Anápolis"
    Então todos os servidores da lista são de Anápolis

  @RF-03 @fluxo
  Cenário: Buscar com o nome vazio
    Quando o cliente busca com o nome vazio e sem município
    Então recebe os 50 servidores da base

  @RF-03 @fluxo
  Cenário: Buscar sem encontrar ninguém
    Quando o cliente busca por "zzz"
    Então recebe uma lista vazia, sem erro

  @RF-02 @fluxo
  Cenário: Abrir a ficha de um servidor da lista
    Dado que o cliente buscou "maria" e recebeu a lista
    Quando o cliente pede a ficha do primeiro servidor da lista
    Então a ficha traz nome, município, sexo, idade, órgão de atuação, PCD, doença profissional ou acidente de trabalho, data de ingresso, data da solicitação, última remuneração e tempo de contribuição

  @RF-02 @fluxo
  Cenário: Idade e tempo de contribuição vêm calculados pelo servidor
    Dado um servidor nascido em 1968-04-12, que ingressou em 1994-03-01 e solicitou em 2026-09-15
    Quando o cliente pede a ficha dele
    Então a idade é 58 anos
    E o tempo de contribuição é 32 anos

  @RF-09 @fluxo
  Cenário: A ficha pela rede não expõe a data de nascimento nem elegibilidade
    Quando o cliente pede a ficha de qualquer servidor
    Então a resposta não contém a data de nascimento
    E a resposta não contém nenhuma indicação de aptidão para aposentadoria

  @RF-10 @fluxo
  Cenário: Cliente e servidor são programas separados
    Dado que o servidor roda em um programa e o cliente em outro
    Quando o cliente faz uma busca
    Então a resposta chega pela rede e não por acesso direto ao arquivo da base
