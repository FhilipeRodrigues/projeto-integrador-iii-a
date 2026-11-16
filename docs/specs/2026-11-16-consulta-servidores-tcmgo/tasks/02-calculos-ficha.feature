# language: pt
Funcionalidade: Cálculos da ficha do servidor
  Para apoiar a análise de aposentadoria com números corretos
  Como analista da Secretaria de Atos de Pessoal
  Quero idade e tempo de contribuição calculados até a data da solicitação

  @RF-08 @fluxo
  Esquema do Cenário: Idade em anos completos na data da solicitação
    Dado um servidor nascido em <nascimento>
    Quando a data da solicitação é <solicitacao>
    Então a idade é <idade> anos

    Exemplos:
      | nascimento | solicitacao | idade | situação                              |
      | 1968-04-12 | 2026-09-15  | 58    | aniversário já passou no ano          |
      | 1968-09-15 | 2026-09-15  | 58    | aniversário no próprio dia            |
      | 1968-09-16 | 2026-09-15  | 57    | véspera do aniversário                |
      | 1968-02-29 | 2026-02-28  | 57    | nascido em 29/02, ano sem 29/02       |
      | 1968-02-29 | 2026-03-01  | 58    | nascido em 29/02, dia seguinte        |

  @RF-07 @fluxo
  Esquema do Cenário: Tempo de contribuição em anos inteiros
    Dado um servidor que ingressou em <ingresso>
    Quando a data da solicitação é <solicitacao>
    Então o tempo de contribuição é <anos> anos

    Exemplos:
      | ingresso   | solicitacao | anos | situação                          |
      | 1994-03-01 | 2026-09-15  | 32   | passaram 32 anos e 6 meses         |
      | 1994-09-15 | 2026-09-15  | 32   | completa 32 anos no próprio dia    |
      | 1994-09-16 | 2026-09-15  | 31   | falta um dia para completar 32     |

  @RF-02 @fluxo
  Cenário: A ficha traz todos os campos necessários
    Dado um servidor da base
    Quando monto a ficha dele
    Então a ficha traz nome, município, sexo, idade, órgão de atuação, PCD, doença profissional ou acidente de trabalho, data de ingresso, data da solicitação, última remuneração e tempo de contribuição

  @RF-02 @fluxo
  Esquema do Cenário: Doença profissional ou acidente de trabalho na ficha
    Dado um servidor cuja doença profissional ou acidente de trabalho é <registro>
    Quando monto a ficha dele
    Então a ficha informa <resultado>

    Exemplos:
      | registro                  | resultado                       |
      | vazio                     | que não há doença nem acidente  |
      | "Tendinite ocupacional"   | que há, e qual é: "Tendinite ocupacional" |

  @RF-09 @fluxo
  Cenário: A ficha não revela a data de nascimento nem indica elegibilidade
    Dado um servidor da base
    Quando monto a ficha dele
    Então a ficha não contém a data de nascimento
    E a ficha não contém nenhuma indicação de aptidão para aposentadoria
