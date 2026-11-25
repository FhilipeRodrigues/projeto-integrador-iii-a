# language: pt
Funcionalidade: Criar conta pela janela
  Para começar a usar o sistema sem usar o terminal
  Como analista da Secretaria de Atos de Pessoal
  Quero criar meu usuário e minha senha na própria tela de login

  @RF-22 @RNF-08 @fluxo
  Cenário: O servidor sobe sem conta e o login falha
    Dado que não há ".env"
    Quando inicio o servidor
    Então ele sobe e avisa que não há conta
    E o "login" com qualquer credencial responde "CREDENCIAIS_INVALIDAS" com a mensagem "Usuário ou senha inválidos."

  @RF-22 @RNF-08 @fluxo
  Cenário: Criar a conta grava o hash e ativa o login
    Dado um servidor sem conta
    Quando o cliente envia "criar_conta" com usuário e senha válidos
    Então o servidor responde com sucesso e o nome do usuário
    E o ".env" tem USUARIO e um SENHA_HASH que não contém a senha
    E o "login" com essa credencial passa a funcionar
    E o log não contém usuário, senha nem hash

  @RF-22 @fluxo
  Cenário: A conta sobrevive ao reinício do servidor
    Dado que criei a conta
    Quando reinicio o servidor com o mesmo ".env"
    Então o "login" com a mesma credencial funciona

  @RF-22 @fluxo
  Cenário: Só se cria a conta uma vez
    Dado que já existe uma conta
    Quando o cliente envia "criar_conta" com outro usuário e outra senha
    Então o servidor responde "CONTA_JA_EXISTE"
    E o login com a conta original continua funcionando
    E o login com a credencial nova continua falhando

  @RF-22 @fluxo
  Cenário: Dados fora das regras
    Dado um servidor sem conta
    Quando o cliente envia "criar_conta" sem usuário, sem senha, com campo que não é texto, com senha de menos de 4 caracteres, com mais de 100 caracteres ou com usuário com espaço nas pontas
    Então o servidor responde "REQUISICAO_INVALIDA" e nenhum ".env" é gravado

  @RF-22 @RNF-08 @fluxo
  Cenário: Falha ao gravar o ".env" não cria a conta
    Dado um servidor sem conta e um ".env" que não pode ser gravado
    Quando o cliente envia "criar_conta" com dados válidos
    Então o servidor responde "ERRO_INTERNO"
    E o login com essa credencial continua falhando

  @RNF-08 @fluxo
  Cenário: Arquivo ausente ou vazio vale como "sem conta"; hash malformado é recusado
    Dado um ".env" que não existe, ou com USUARIO e SENHA_HASH vazios
    Quando inicio o servidor
    Então ele sobe sem conta
    Dado um ".env" com SENHA_HASH preenchido e malformado
    Quando inicio o servidor
    Então ele recusa subir e explica como corrigir

  @RF-22 @ui
  Cenário: O login oferece "Criar conta"
    Quando abro o cliente
    Então vejo o botão "Criar conta" na tela de login

  @RF-22 @ui
  Cenário: Abrir a criação e cancelar
    Dado que estou no login
    Quando clico em "Criar conta"
    Então vejo os campos "Usuário", "Senha" e "Repita a senha", com as senhas mascaradas
    Quando cancelo
    Então volto ao login

  @RF-22 @ui
  Cenário: Senhas diferentes ou campos vazios barram antes da rede
    Dado que estou na criação de conta
    Quando as duas senhas são diferentes
    Então vejo "As senhas não conferem." e nada é enviado ao servidor
    Quando deixo usuário ou senha vazios
    Então vejo "Informe usuário e senha." e nada é enviado ao servidor

  @RF-22 @ui
  Cenário: Regra da conta recusada pelo servidor
    Dado que estou na criação de conta
    Quando informo uma senha com menos de 4 caracteres e confirmo
    Então vejo a regra enviada pelo servidor ("a senha deve ter de 4 a 100 caracteres") e a tela continua aberta
    E os campos de senha são limpos

  @RF-22 @ui
  Cenário: Conta criada volta ao login
    Dado que estou na criação de conta
    Quando informo usuário, senha e a repetição corretos e confirmo
    Então volto ao login, com o usuário preenchido e a instrução "Conta criada. Entre com ela."
    E a janela principal ainda não aparece

  @RF-22 @ui
  Cenário: Conta já existente
    Dado que o servidor já tem conta
    Quando confirmo a criação de outra
    Então vejo "Já existe uma conta cadastrada. Entre com ela." e a tela de criação continua aberta

  @RF-22 @ui
  Cenário: Servidor fora do ar ao criar
    Dado que o servidor está fora do ar
    Quando confirmo a criação
    Então vejo uma mensagem clara sobre a falha e posso tentar de novo

  @RF-22 @integracao
  Cenário: Fluxo da demonstração
    Dado o servidor real sem ".env"
    Quando tento entrar e vejo a recusa
    E crio a conta pela janela
    E tento entrar com a senha errada
    E depois com a senha certa
    Então a janela principal aparece com a lista de servidores
