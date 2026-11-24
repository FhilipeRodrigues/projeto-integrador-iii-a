"""Texto das regras básicas de aposentadoria do servidor público (RF-19).

É só dado para o analista consultar, entregue pela operação `regras`. Nada aqui calcula
nem indica se um servidor atende às regras (RF-09). O texto é simplificado e não substitui
a legislação.
"""

_REGRAS = (
    {
        "titulo": "Regra geral",
        "linhas": (
            "Idade mínima: 62 anos, se mulher; 65 anos, se homem.",
            "Tempo mínimo de contribuição: 25 anos, para ambos.",
        ),
    },
    {
        "titulo": "Pessoa com deficiência (PCD)",
        "linhas": (
            "Por tempo de contribuição: 25 anos, se homem; 20 anos, se mulher.",
            "Por idade: idade mínima de 60 anos, se homem; 55 anos, se mulher, "
            "com 15 anos de contribuição.",
        ),
    },
    {
        "titulo": "Doença profissional ou acidente de trabalho",
        "linhas": ("Em caso positivo, a aprovação é direta.",),
    },
)


def listar() -> list:
    """Blocos `{"titulo", "linhas"}` na ordem de exibição (cópia: quem recebe não altera o original)."""
    return [{"titulo": bloco["titulo"], "linhas": list(bloco["linhas"])} for bloco in _REGRAS]
