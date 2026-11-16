# language: pt
Funcionalidade: Busca de servidores por nome e município
  Para achar um servidor sem saber a grafia exata
  Como analista da Secretaria de Atos de Pessoal
  Quero buscar por trecho do nome e, se quiser, por município

  Contexto:
    Dado uma base com "João Batista Silva" e "Maria da Conceição Alves" em Anápolis
    E "Joana Dark Lima" e "Maria Conceição Rocha" em Rio Verde

  @RF-03 @fluxo
  Esquema do Cenário: Buscar ignorando acento e maiúsculas
    Quando busco por <digitado>
    Então o resultado inclui <encontrado>

    Exemplos:
      | digitado   | encontrado                 |
      | "joao"     | "João Batista Silva"       |
      | "JOÃO"     | "João Batista Silva"       |
      | "conceicao"| "Maria da Conceição Alves" |
      | "batista"  | "João Batista Silva"       |
      | "  maria " | "Maria da Conceição Alves" |

  @RF-03 @fluxo
  Cenário: Buscar por um trecho que aparece em municípios diferentes
    Quando busco por "maria" sem filtrar município
    Então o resultado traz "Maria da Conceição Alves" de Anápolis
    E o resultado traz "Maria Conceição Rocha" de Rio Verde

  @RF-03 @fluxo
  Cenário: O resultado vem em ordem alfabética
    Quando busco por "jo" sem filtrar município
    Então os nomes aparecem em ordem alfabética, sem considerar acentos

  @RF-03 @fluxo
  Cenário: Nome vazio lista todos os servidores
    Quando busco com o nome vazio e sem filtrar município
    Então o resultado traz todos os servidores da base

  @RF-03 @fluxo
  Cenário: Nenhum servidor combina com o trecho
    Quando busco por "zzz" sem filtrar município
    Então o resultado é uma lista vazia

  @RF-04 @fluxo
  Cenário: Filtrar a busca por município
    Quando busco por "maria" no município "Rio Verde"
    Então o resultado traz apenas "Maria Conceição Rocha"

  @RF-04 @fluxo
  Cenário: Nome vazio com município lista todos os servidores do município
    Quando busco com o nome vazio no município "Anápolis"
    Então o resultado traz apenas os servidores de Anápolis

  @RF-04 @fluxo
  Cenário: Listar os municípios disponíveis
    Quando peço a lista de municípios
    Então recebo "Anápolis" e "Rio Verde" em ordem alfabética, sem repetição
