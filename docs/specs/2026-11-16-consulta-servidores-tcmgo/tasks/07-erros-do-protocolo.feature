# language: pt
Funcionalidade: Erros do protocolo
  Para que um pedido malformado não derrube o atendimento
  Como analista e como avaliador do projeto
  Quero respostas de erro claras e um servidor que continua funcionando

  Contexto:
    Dado que o servidor está no ar com a base fictícia e o canal seguro

  @RF-13 @fluxo
  Esquema do Cenário: Recusar um pedido inválido com o código de erro certo
    Quando um cliente envia <pedido>
    Então a resposta é um erro com o código <codigo>
    E a mensagem de erro é compreensível e não mostra detalhes internos

    Exemplos:
      | pedido                                         | codigo                |
      | um texto que não é JSON                        | "REQUISICAO_INVALIDA" |
      | um JSON que não é um objeto                    | "REQUISICAO_INVALIDA" |
      | uma busca sem o campo "nome"                   | "REQUISICAO_INVALIDA" |
      | uma busca com "nome" que não é texto           | "REQUISICAO_INVALIDA" |
      | uma busca com nome de mais de 100 caracteres   | "REQUISICAO_INVALIDA" |
      | uma busca com um município que não existe      | "REQUISICAO_INVALIDA" |
      | um pedido de ficha com identificação não numérica | "REQUISICAO_INVALIDA" |
      | uma operação chamada "apagar"                  | "OPERACAO_DESCONHECIDA" |
      | um pedido de ficha de um servidor inexistente  | "NAO_ENCONTRADO"      |

  @RF-13 @fluxo
  Cenário: Recusar uma linha grande demais
    Quando um cliente envia uma linha com mais de 64 KiB
    Então a resposta é um erro "REQUISICAO_INVALIDA"
    E o servidor não carrega a linha inteira na memória

  @RF-13 @fluxo
  Cenário: O servidor continua atendendo depois de um erro
    Dado que um cliente enviou um pedido inválido e recebeu o erro
    Quando outro cliente faz uma busca válida
    Então recebe a lista de resultados normalmente

  @RF-13 @fluxo
  Cenário: Falha inesperada no atendimento de uma conexão
    Dado que ocorre uma falha inesperada ao atender um pedido
    Quando o cliente recebe a resposta
    Então o código é "ERRO_INTERNO" com uma mensagem genérica
    E o servidor continua no ar para as próximas conexões

  @RF-13 @fluxo
  Cenário: Cliente que conecta e não envia nada
    Dado um cliente que abre a conexão e não envia nenhum pedido
    Quando passam 5 segundos
    Então o servidor encerra essa conexão
    E os outros clientes continuam sendo atendidos nesse intervalo
