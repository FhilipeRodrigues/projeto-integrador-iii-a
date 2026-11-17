import unittest
from datetime import date

from consulta import dominio

CAMPOS_DA_FICHA = {
    "id", "nome", "municipio", "sexo", "idade", "orgao", "pcd",
    "doenca_profissional", "data_ingresso", "data_solicitacao",
    "ultima_remuneracao_centavos", "tempo_contribuicao_anos",
}


def servidor(**alteracoes):
    base = {
        "id": 1,
        "nome": "Maria da Conceição Alves",
        "sexo": "F",
        "data_nascimento": "1968-04-12",
        "municipio": "Anápolis",
        "orgao": "Secretaria Municipal de Educação",
        "pcd": False,
        "doenca_profissional": None,
        "data_ingresso": "1994-03-01",
        "data_solicitacao": "2026-09-15",
        "ultima_remuneracao_centavos": 485000,
    }
    base.update(alteracoes)
    return base


class IdadeTest(unittest.TestCase):
    def test_idade_em_anos_completos_na_data_da_solicitacao(self):
        exemplos = [
            ("1968-04-12", "2026-09-15", 58),  # aniversário já passou no ano
            ("1968-09-15", "2026-09-15", 58),  # aniversário no próprio dia
            ("1968-09-16", "2026-09-15", 57),  # véspera do aniversário
            ("1968-02-29", "2026-02-28", 57),  # 29/02 em ano sem 29/02
            ("1968-02-29", "2026-03-01", 58),  # dia seguinte
        ]
        for nascimento, solicitacao, esperada in exemplos:
            with self.subTest(nascimento=nascimento, solicitacao=solicitacao):
                ficha = dominio.montar_ficha(
                    servidor(data_nascimento=nascimento, data_solicitacao=solicitacao)
                )
                self.assertEqual(ficha["idade"], esperada)


class TempoDeContribuicaoTest(unittest.TestCase):
    def test_tempo_de_contribuicao_em_anos_inteiros(self):
        exemplos = [
            ("1994-03-01", "2026-09-15", 32),  # 32 anos e 6 meses
            ("1994-09-15", "2026-09-15", 32),  # completa no próprio dia
            ("1994-09-16", "2026-09-15", 31),  # falta um dia
        ]
        for ingresso, solicitacao, esperado in exemplos:
            with self.subTest(ingresso=ingresso, solicitacao=solicitacao):
                ficha = dominio.montar_ficha(
                    servidor(data_ingresso=ingresso, data_solicitacao=solicitacao)
                )
                self.assertEqual(ficha["tempo_contribuicao_anos"], esperado)


class FichaTest(unittest.TestCase):
    def test_a_ficha_traz_todos_os_campos_necessarios(self):
        ficha = dominio.montar_ficha(servidor())
        self.assertEqual(
            ficha,
            {
                "id": 1,
                "nome": "Maria da Conceição Alves",
                "municipio": "Anápolis",
                "sexo": "F",
                "idade": 58,
                "orgao": "Secretaria Municipal de Educação",
                "pcd": False,
                "doenca_profissional": None,
                "data_ingresso": "1994-03-01",
                "data_solicitacao": "2026-09-15",
                "ultima_remuneracao_centavos": 485000,
                "tempo_contribuicao_anos": 32,
            },
        )

    def test_doenca_profissional_vazia_significa_que_nao_ha(self):
        ficha = dominio.montar_ficha(servidor(doenca_profissional=None))
        self.assertIsNone(ficha["doenca_profissional"])

    def test_doenca_profissional_informada_traz_qual_e(self):
        ficha = dominio.montar_ficha(servidor(doenca_profissional="Tendinite ocupacional"))
        self.assertEqual(ficha["doenca_profissional"], "Tendinite ocupacional")

    def test_a_ficha_nao_revela_nascimento_nem_indica_elegibilidade(self):
        ficha = dominio.montar_ficha(servidor())
        self.assertEqual(set(ficha), CAMPOS_DA_FICHA)
        self.assertNotIn("1968-04-12", repr(ficha))
        self.assertFalse(
            [campo for campo in ficha if "nasc" in campo or "elegi" in campo or "aposent" in campo]
        )

    def test_a_ficha_nao_altera_o_registro_da_base(self):
        registro = servidor()
        copia = dict(registro)
        dominio.montar_ficha(registro)
        self.assertEqual(registro, copia)


class AnosCompletosTest(unittest.TestCase):
    def test_29_de_fevereiro_conta_como_anterior_a_1_de_marco(self):
        self.assertEqual(dominio.anos_completos(date(1968, 2, 29), date(2026, 2, 28)), 57)
        self.assertEqual(dominio.anos_completos(date(1968, 2, 29), date(2026, 3, 1)), 58)


if __name__ == "__main__":
    unittest.main()
