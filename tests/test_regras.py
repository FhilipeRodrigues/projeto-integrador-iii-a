import unittest

from consulta import regras


def _texto(blocos):
    return " ".join(linha for bloco in blocos for linha in bloco["linhas"])


class RegrasTest(unittest.TestCase):
    def test_Tem_os_tres_blocos_na_ordem(self):
        titulos = [bloco["titulo"] for bloco in regras.listar()]
        self.assertEqual(
            titulos,
            ["Regra geral", "Pessoa com deficiência (PCD)", "Doença profissional ou acidente de trabalho"],
        )

    def test_Regra_geral(self):
        geral = regras.listar()[0]["linhas"]
        self.assertEqual(len(geral), 2)
        self.assertIn("62 anos, se mulher; 65 anos, se homem", geral[0])
        self.assertIn("25 anos, para ambos", geral[1])

    def test_PCD_por_tempo_e_por_idade(self):
        por_tempo, por_idade = regras.listar()[1]["linhas"]
        self.assertIn("tempo de contribuição: 25 anos, se homem; 20 anos, se mulher", por_tempo)
        self.assertIn("60 anos, se homem; 55 anos, se mulher", por_idade)
        self.assertIn("15 anos de contribuição", por_idade)

    def test_Doenca_profissional_e_aprovacao_direta(self):
        self.assertIn("aprovação é direta", _texto(regras.listar()[2:]))

    def test_So_tem_titulo_e_linhas_de_texto(self):
        for bloco in regras.listar():
            self.assertEqual(set(bloco), {"titulo", "linhas"})
            self.assertIsInstance(bloco["titulo"], str)
            self.assertTrue(bloco["linhas"])
            self.assertTrue(all(isinstance(linha, str) for linha in bloco["linhas"]))

    def test_Quem_recebe_o_texto_nao_altera_o_original(self):
        recebido = regras.listar()
        recebido[0]["linhas"].append("alterada")
        recebido.pop()
        self.assertEqual(len(regras.listar()), 3)
        self.assertNotIn("alterada", _texto(regras.listar()))


if __name__ == "__main__":
    unittest.main()
