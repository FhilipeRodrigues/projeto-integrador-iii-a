# language: pt
Funcionalidade: Base fictícia reproduzível
  Para demonstrar o sistema sem expor dados reais do TCM-GO
  Como estudante responsável pelo protótipo
  Quero uma base de servidores fictícios, sempre igual e validada

  @RF-01 @fluxo
  Cenário: Gerar a base com 10 municípios e 50 servidores
    Quando gero a base fictícia
    Então a base tem 10 municípios
    E cada município tem 5 servidores
    E todos os servidores têm um número de identificação diferente

  @RF-01 @fluxo
  Cenário: A mesma geração produz sempre a mesma base
    Quando gero a base fictícia duas vezes
    Então os dois arquivos gerados são idênticos

  @RF-01 @fluxo
  Cenário: A base serve para demonstrar a busca
    Quando gero a base fictícia
    Então há pelo menos 3 nomes com acento
    E há pelo menos 2 nomes que contêm o mesmo trecho em municípios diferentes
    E há servidores com PCD e servidores com doença profissional ou acidente de trabalho

  @RNF-01 @fluxo
  Cenário: A base é marcada como fictícia
    Quando carrego a base
    Então ela está identificada como fictícia

  @RF-01 @fluxo
  Esquema do Cenário: Recusar uma base com dados inválidos
    Dado uma base em que <problema>
    Quando tento carregar a base
    Então o carregamento é recusado com uma mensagem que aponta o servidor e o campo com problema

    Exemplos:
      | problema                                            |
      | um servidor ingressou antes de completar 18 anos    |
      | a data da solicitação é anterior ao ingresso        |
      | dois servidores têm o mesmo número de identificação |
      | o sexo não é "F" nem "M"                            |
      | falta o município de um servidor                    |
