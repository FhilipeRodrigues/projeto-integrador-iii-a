# language: pt
Funcionalidade: Base fictícia com nomes comuns variados
  Para que a demonstração tenha buscas variadas e realistas
  Como estudante que apresenta o protótipo
  Quero que a base use os nomes mais comuns do Brasil, bem distribuídos

  Contexto:
    Dado a base fictícia gerada pelo script

  @RF-01 @fluxo
  Cenário: Cada um dos 50 nomes aparece uma vez
    Então há 25 servidores com nome masculino da lista e 25 com nome feminino da lista
    E cada nome da lista aparece como primeiro nome de exatamente um servidor

  @RF-01 @fluxo
  Cenário: O sexo acompanha o nome
    Então todo servidor com nome da lista masculina tem sexo "M"
    E todo servidor com nome da lista feminina tem sexo "F"

  @RF-01 @fluxo
  Cenário: Dois sobrenomes diferentes entre si
    Então todo servidor tem exatamente dois sobrenomes
    E os dois sobrenomes de cada servidor são diferentes

  @RF-01 @fluxo
  Cenário: Nomes parecidos em municípios diferentes
    Então "Antônio" e "Antônia" trabalham em municípios diferentes
    E "Francisco" e "Francisca" trabalham em municípios diferentes

  @RF-01 @fluxo
  Cenário: Os nomes ficam distribuídos entre os 10 municípios
    Então cada município tem 5 servidores
    E nenhum município concentra só nomes masculinos nem só femininos

  @RF-01 @fluxo
  Cenário: A geração continua reproduzível e a base continua válida
    Quando o script gera a base duas vezes
    Então os dois arquivos são idênticos byte a byte
    E a base passa na validação, com 10 municípios e 50 servidores

  @RF-01 @fluxo
  Cenário: O nome usado no README existe na base
    Quando busco por "maria" na base gerada
    Então encontro pelo menos um servidor
    E o README orienta a buscar por "maria"
