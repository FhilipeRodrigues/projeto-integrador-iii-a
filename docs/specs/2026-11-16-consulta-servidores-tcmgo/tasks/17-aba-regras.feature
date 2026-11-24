# language: pt
Funcionalidade: Aba de regras de aposentadoria
  Para decidir se aprovo ou desaprovo uma solicitação
  Como analista da Secretaria de Atos de Pessoal
  Quero consultar as regras básicas de aposentadoria na própria janela

  Contexto:
    Dado que o servidor está no ar
    E a janela do cliente está aberta

  @RF-19 @fluxo
  Cenário: O servidor entrega as regras
    Quando o cliente pede as regras ao servidor
    Então recebe os blocos "Regra geral", "Pessoa com deficiência (PCD)" e "Doença profissional ou acidente de trabalho"
    E a regra geral traz 62 anos (mulher) e 65 anos (homem) de idade e 25 anos de contribuição para ambos
    E o PCD por tempo traz 25 anos (homem) e 20 anos (mulher)
    E o PCD por idade traz 60 anos (homem) e 55 anos (mulher) com 15 anos de contribuição
    E a doença profissional ou acidente de trabalho traz "aprovação direta"

  @RF-19 @fluxo
  Cenário: A operação só devolve texto
    Quando o cliente pede as regras ao servidor
    Então a resposta não depende de nenhum servidor nem solicitação
    E não traz campo de elegibilidade nem de resultado

  @RF-19 @ui
  Cenário: A janela tem a aba Regras depois de Solicitações
    Então vejo as abas "Consulta", "Solicitações" e "Regras", nessa ordem
    E a aba "Consulta" é a que está aberta

  @RF-19 @ui
  Cenário: A aba Regras mostra o texto
    Quando abro a aba "Regras"
    Então vejo os três blocos com as regras, em fonte de pelo menos 12 pt
    E o texto não pode ser editado
    E o rodapé diz que o texto é simplificado e não substitui a legislação

  @RF-09 @RF-19 @ui
  Cenário: A aba não indica elegibilidade
    Quando abro a aba "Regras"
    Então não há botão nem campo que calcule se um servidor atende às regras

  @RF-12 @ui
  Cenário: Falha de rede na aba Regras
    Dado que o servidor está fora do ar
    Quando abro a aba "Regras"
    Então vejo uma mensagem clara sobre a falha
    E a janela continua aberta
    Quando o servidor volta e abro a aba "Regras" de novo
    Então vejo o texto das regras
