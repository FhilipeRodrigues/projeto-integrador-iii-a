# language: pt
Funcionalidade: Solicitações de aposentadoria no servidor
  Para que o analista tenha requerimentos fictícios a analisar
  Como estudante que apresenta o protótipo
  Quero que o servidor sorteie e entregue 10 solicitações

  Contexto:
    Dado que o servidor está no ar com a base fictícia e o canal seguro

  @RF-15 @fluxo
  Cenário: Primeira execução sorteia e grava 10 solicitações
    Dado que o arquivo de solicitações não existe
    Quando o servidor inicia
    Então o arquivo de solicitações é criado com 10 solicitações

  @RF-15 @fluxo
  Cenário: Uma solicitação por município, de servidores diferentes
    Quando o servidor inicia sem arquivo de solicitações
    Então as 10 solicitações são de 10 municípios diferentes
    E cada uma é de um servidor que existe na base e trabalha naquele município
    E nenhum servidor aparece em duas solicitações

  @RF-15 @fluxo
  Cenário: Toda solicitação nasce pendente
    Quando o servidor inicia sem arquivo de solicitações
    Então as 10 solicitações estão com a situação "pendente"
    E os números vão de "REQ-2026-0001" a "REQ-2026-0010"

  @RF-15 @fluxo
  Cenário: Reiniciar o servidor reutiliza o mesmo sorteio
    Dado que o servidor já gravou as 10 solicitações
    Quando o servidor é reiniciado
    Então as solicitações são exatamente as mesmas

  @RF-15 @fluxo
  Cenário: Apagar o arquivo sorteia de novo
    Dado que o servidor já gravou as 10 solicitações
    Quando o arquivo é apagado e o servidor reiniciado
    Então o arquivo é criado outra vez com 10 solicitações

  @RF-16 @fluxo
  Cenário: Listar as solicitações pela rede
    Quando o cliente pede a lista de solicitações
    Então recebe 10 itens com número, nome do servidor, município e situação, ordenados pelo número

  @RF-16 @fluxo
  Cenário: Abrir o documento de uma solicitação
    Dado que o cliente recebeu a lista de solicitações
    Quando o cliente pede o documento da primeira
    Então recebe número, situação, município, órgão, nome do servidor, sexo, data de ingresso e data da solicitação

  @RF-16 @fluxo
  Cenário: O documento não expõe dados que o analista confere na consulta
    Quando o cliente pede o documento de qualquer solicitação
    Então a resposta não contém data de nascimento, idade, tempo de contribuição, PCD, doença profissional nem remuneração
    E a resposta não contém nenhuma indicação de aptidão para aposentadoria

  @RF-16 @fluxo
  Cenário: Documento de solicitação inexistente
    Quando o cliente pede o documento de uma solicitação que não existe
    Então recebe o erro "NAO_ENCONTRADO"
    E o servidor continua atendendo

  @RNF-07 @fluxo
  Cenário: Arquivo de solicitações inválido impede o servidor de subir
    Dado um arquivo de solicitações que cita um servidor que não existe na base
    Quando o servidor tenta iniciar
    Então ele não sobe
    E informa qual solicitação e qual campo estão inválidos

  @RNF-07 @fluxo
  Cenário: O arquivo de solicitações não vai para o repositório
    Então "data/solicitacoes.json" está no .gitignore
