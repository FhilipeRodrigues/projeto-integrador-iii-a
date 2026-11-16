# language: pt
Funcionalidade: Ficha do servidor na janela
  Para analisar a situação funcional de um servidor
  Como analista da Secretaria de Atos de Pessoal
  Quero ver a ficha completa ao selecionar o servidor na lista

  Contexto:
    Dado que a janela está aberta e a lista mostra os resultados de uma busca

  @RF-05 @ui
  Cenário: Selecionar um servidor mostra a ficha
    Quando seleciono um servidor da lista
    Então vejo a ficha com: nome completo, município, sexo, idade, órgão de atuação, PCD, doença profissional ou acidente de trabalho, data de ingresso, data da solicitação, última remuneração e tempo de contribuição

  @RF-02 @ui
  Cenário: Os valores aparecem em formato brasileiro
    Dado um servidor que ingressou em 1994-03-01, solicitou em 2026-09-15 e recebe 4850,00
    Quando seleciono esse servidor
    Então a data de ingresso aparece como "01/03/1994"
    E a data da solicitação aparece como "15/09/2026"
    E a última remuneração aparece como "R$ 4.850,00"
    E o tempo de contribuição aparece como "32 anos"

  @RF-02 @ui
  Esquema do Cenário: PCD e doença profissional ou acidente de trabalho
    Dado um servidor com PCD <pcd> e doença profissional ou acidente de trabalho <registro>
    Quando seleciono esse servidor
    Então a ficha mostra PCD como <pcd_exibido>
    E mostra doença profissional ou acidente de trabalho como <doenca_exibida>

    Exemplos:
      | pcd   | registro                | pcd_exibido | doenca_exibida                  |
      | não   | nenhum                  | "Não"       | "Não"                           |
      | sim   | "Tendinite ocupacional" | "Sim"       | "Sim: Tendinite ocupacional"    |

  @RF-05 @ui
  Cenário: Selecionar outro servidor atualiza a ficha
    Dado que a ficha de um servidor está na tela
    Quando seleciono outro servidor da lista
    Então a ficha passa a mostrar os dados do outro servidor

  @RF-05 @ui
  Cenário: Uma nova busca limpa a ficha
    Dado que a ficha de um servidor está na tela
    Quando faço uma nova busca
    Então a ficha some até eu selecionar um servidor da nova lista

  @RF-09 @ui
  Cenário: A ficha não indica elegibilidade nem mostra a data de nascimento
    Quando seleciono um servidor da lista
    Então não vejo nenhuma indicação de aptidão para aposentadoria
    E não vejo a data de nascimento

  @RF-02 @integracao
  Cenário: A ficha da janela corresponde ao servidor
    Dado que o servidor real está no ar com a base fictícia
    Quando seleciono "João" da lista na janela
    Então os valores da ficha são os que o servidor devolve para essa identificação
