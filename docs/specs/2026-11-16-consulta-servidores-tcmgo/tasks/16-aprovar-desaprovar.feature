# language: pt
Funcionalidade: Aprovar ou desaprovar uma solicitação
  Para registrar a análise do requerimento de aposentadoria
  Como analista da Secretaria de Atos de Pessoal
  Quero decidir pelo próprio documento e ver a decisão onde eu consultar o servidor

  Contexto:
    Dado que o servidor está no ar com 10 solicitações pendentes
    E a janela do cliente está aberta na aba "Solicitações"

  @RF-17 @ui
  Cenário: Aprovar uma solicitação
    Dado que selecionei uma solicitação pendente
    Quando clico em "Aprovar"
    Então o documento mostra a situação "Aprovada" e a data e hora da decisão
    E a linha dela na lista mostra "Aprovada"

  @RF-17 @ui
  Cenário: Desaprovar uma solicitação
    Dado que selecionei uma solicitação pendente
    Quando clico em "Desaprovar"
    Então o documento mostra a situação "Desaprovada" e a data e hora da decisão
    E a linha dela na lista mostra "Desaprovada"

  @RF-17 @ui
  Cenário: Trocar a decisão
    Dado que aprovei uma solicitação
    Quando clico em "Desaprovar" nela
    Então a situação passa a "Desaprovada"
    E a decisão anterior deixa de valer

  @RF-18 @integracao
  Cenário: A decisão sobrevive a reiniciar o servidor
    Dado que aprovei uma solicitação e desaprovei outra
    Quando o servidor é parado e iniciado de novo e a janela consulta a lista
    Então a primeira continua "Aprovada" e a segunda continua "Desaprovada"
    E as demais continuam "Pendente"

  @RF-18 @ui
  Cenário: A situação aparece na ficha do servidor
    Dado que aprovei a solicitação de um servidor
    Quando busco esse servidor na aba "Consulta" e abro a ficha
    Então a ficha mostra "Situação da solicitação: Aprovada"

  @RF-18 @ui
  Cenário: Servidor sem solicitação
    Quando abro na aba "Consulta" a ficha de um servidor que não tem solicitação
    Então a ficha mostra "Situação da solicitação: Nenhuma solicitação"

  @RF-09 @fluxo
  Cenário: A situação registra a decisão do usuário, não uma conclusão do sistema
    Quando o cliente pede a ficha e o documento de qualquer servidor com solicitação
    Então nenhuma resposta contém indicação de aptidão para aposentadoria
    E a situação é uma das três: "pendente", "aprovada" ou "desaprovada"

  @RF-17 @fluxo
  Cenário: Decisão com dados inválidos
    Quando o cliente envia uma decisão diferente de "aprovada" e "desaprovada"
    Então recebe o erro "REQUISICAO_INVALIDA"
    Quando o cliente decide uma solicitação que não existe
    Então recebe o erro "NAO_ENCONTRADO"
    E a situação das solicitações não muda
    E o servidor continua atendendo

  @RNF-07 @fluxo
  Cenário: Duas decisões ao mesmo tempo não se perdem nem corrompem o arquivo
    Quando dois clientes decidem solicitações diferentes ao mesmo tempo
    Então as duas decisões ficam registradas
    E o arquivo de solicitações continua válido ao ser recarregado

  @RNF-07 @fluxo
  Cenário: Falha ao gravar não muda a situação
    Dado que o arquivo de solicitações não pode ser gravado
    Quando o cliente decide uma solicitação
    Então recebe o erro "ERRO_INTERNO"
    E a situação da solicitação continua a anterior

  @RF-12 @ui
  Cenário: Servidor cai na hora de decidir
    Dado que selecionei uma solicitação pendente e o servidor saiu do ar
    Quando clico em "Aprovar"
    Então vejo uma mensagem clara sobre a falha
    E a situação na tela continua "Pendente"
    E a janela continua aberta

  @RF-17 @integracao
  Cenário: Fluxo da demonstração
    Dado que abri a solicitação de uma servidora na aba "Solicitações"
    Quando vou à aba "Consulta", busco o nome dela e abro a ficha
    Então vejo os dados dela e a situação "Pendente"
    Quando volto à aba "Solicitações" e clico em "Aprovar"
    E volto à aba "Consulta" e abro a ficha de novo
    Então a ficha mostra a situação "Aprovada"
