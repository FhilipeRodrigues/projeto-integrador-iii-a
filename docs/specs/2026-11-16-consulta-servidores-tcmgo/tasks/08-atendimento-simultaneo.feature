# language: pt
Funcionalidade: Atendimento simultâneo de clientes
  Para que a consulta de um colega não atrase a minha
  Como analista da Secretaria de Atos de Pessoal
  Quero que vários clientes usem o servidor ao mesmo tempo

  Contexto:
    Dado que o servidor está no ar com a base fictícia e o canal seguro

  @RF-11 @fluxo
  Cenário: Dois clientes consultam ao mesmo tempo
    Quando dois clientes fazem buscas diferentes ao mesmo tempo
    Então cada cliente recebe a resposta da própria busca

  @RF-11 @fluxo
  Cenário: Muitos clientes consultam ao mesmo tempo
    Quando 10 clientes fazem buscas ao mesmo tempo
    Então os 10 recebem resposta correta

  @RF-11 @fluxo
  Cenário: Um cliente lento não bloqueia os outros
    Dado um cliente que abriu a conexão e ainda não terminou o aperto de mão
    Quando outro cliente faz uma busca
    Então o outro cliente recebe a resposta sem esperar o primeiro

  @RNF-03 @fluxo
  Cenário: A busca responde em até 1 segundo
    Quando o cliente faz uma busca em ambiente local
    Então a resposta chega em até 1 segundo, contando a conexão e o aperto de mão
