# language: pt
Funcionalidade: Login e confirmação da senha ao decidir
  Para que só o analista autorizado registre decisões
  Como analista da Secretaria de Atos de Pessoal
  Quero entrar com usuário e senha e confirmar a senha ao aprovar ou desaprovar

  Contexto:
    Dado que o servidor está no ar com o usuário e o hash da senha no ".env"

  @RF-20 @fluxo
  Cenário: Login com a credencial certa
    Quando o cliente envia "login" com o usuário e a senha corretos
    Então o servidor responde com sucesso e o nome do usuário

  @RF-20 @RNF-08 @fluxo
  Cenário: Qualquer outra credencial falha do mesmo jeito
    Quando o cliente envia "login" com usuário errado e senha certa
    E depois com usuário certo e senha errada
    Então as duas respostas trazem o código "CREDENCIAIS_INVALIDAS" e a mensagem "Usuário ou senha inválidos."
    E cada tentativa errada demora pelo menos a pausa configurada
    E o log não contém o usuário nem a senha

  @RF-20 @fluxo
  Cenário: Credencial malformada
    Quando o cliente envia "login" sem senha, ou com senha que não é texto, ou com mais de 100 caracteres
    Então o servidor responde "REQUISICAO_INVALIDA" e segue atendendo

  @RF-21 @fluxo
  Cenário: Decidir exige a credencial
    Dado uma solicitação pendente
    Quando o cliente envia "decidir" sem credencial ou com a senha errada
    Então o servidor recusa com "CREDENCIAIS_INVALIDAS"
    E a situação da solicitação continua "pendente"
    Quando o cliente envia "decidir" com a credencial certa
    Então a decisão é gravada

  @RF-21 @fluxo
  Cenário: A credencial é conferida antes do id
    Quando o cliente envia "decidir" com a senha errada e um id que não existe
    Então a resposta é "CREDENCIAIS_INVALIDAS" e não "NAO_ENCONTRADO"

  @RNF-08 @fluxo
  Cenário: O hash não é a senha e muda a cada geração
    Quando gero o hash da mesma senha duas vezes
    Então os dois valores são diferentes e nenhum contém a senha
    E ambos validam a senha certa e recusam a errada

  @RNF-08 @fluxo
  Cenário: O servidor não sobe sem a configuração
    Dado que não há ".env" ou que ele não traz o usuário e o hash
    Quando inicio o servidor
    Então ele recusa subir e explica como criar o ".env"
    E o ".env" é ignorado pelo git

  @RF-20 @ui
  Cenário: A janela abre pelo login
    Quando abro o cliente
    Então vejo só a tela de login, com os campos "Usuário" e "Senha"
    E a senha aparece mascarada
    E a janela principal ainda não aparece

  @RF-20 @ui
  Cenário: Entrar com a credencial certa
    Quando informo a credencial correta e confirmo
    Então a janela principal aparece com a lista de servidores

  @RF-20 @ui
  Cenário: Entrar com a credencial errada
    Quando informo usuário ou senha errados e confirmo
    Então vejo "Usuário ou senha inválidos." no login
    E o campo da senha é limpo
    E a janela principal não aparece

  @RF-20 @ui
  Cenário: Cancelar o login
    Quando cancelo o login
    Então o programa encerra

  @RF-21 @ui
  Cenário: Aprovar pede a senha
    Dado que entrei e selecionei uma solicitação pendente
    Quando clico em "Aprovar"
    Então vejo a confirmação da senha, com o usuário logado e a senha mascarada
    Quando informo a senha certa e confirmo
    Então a situação passa a "Aprovada"

  @RF-21 @ui
  Cenário: Senha errada ao decidir
    Dado que clico em "Desaprovar" numa solicitação pendente
    Quando informo a senha errada e confirmo
    Então a confirmação continua aberta com "Usuário ou senha inválidos."
    E a situação da solicitação continua "Pendente"
    Quando cancelo a confirmação
    Então volto à janela principal sem decisão gravada

  @RF-12 @ui
  Cenário: Servidor fora do ar ao entrar
    Dado que o servidor está fora do ar
    Quando informo a credencial e confirmo
    Então vejo uma mensagem clara sobre a falha no login
    E posso tentar de novo quando o servidor voltar
