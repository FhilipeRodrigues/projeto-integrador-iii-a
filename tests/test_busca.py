import unittest

from consulta import dominio

BASE = [
    {"id": 1, "nome": "João Batista Silva", "municipio": "Anápolis"},
    {"id": 2, "nome": "Maria da Conceição Alves", "municipio": "Anápolis"},
    {"id": 3, "nome": "Joana Dark Lima", "municipio": "Rio Verde"},
    {"id": 4, "nome": "Maria Conceição Rocha", "municipio": "Rio Verde"},
]


def nomes(resultado):
    return [r["nome"] for r in resultado]


class BuscaPorNomeTest(unittest.TestCase):
    def test_buscar_ignorando_acento_e_maiusculas(self):
        exemplos = [
            ("joao", "João Batista Silva"),
            ("JOÃO", "João Batista Silva"),
            ("conceicao", "Maria da Conceição Alves"),
            ("batista", "João Batista Silva"),
            ("  maria ", "Maria da Conceição Alves"),
        ]
        for digitado, encontrado in exemplos:
            with self.subTest(digitado=digitado):
                self.assertIn(encontrado, nomes(dominio.buscar(BASE, digitado)))

    def test_buscar_por_um_trecho_que_aparece_em_municipios_diferentes(self):
        resultado = dominio.buscar(BASE, "maria")
        self.assertIn(
            {"id": 2, "nome": "Maria da Conceição Alves", "municipio": "Anápolis"}, resultado
        )
        self.assertIn(
            {"id": 4, "nome": "Maria Conceição Rocha", "municipio": "Rio Verde"}, resultado
        )

    def test_o_resultado_vem_em_ordem_alfabetica_sem_considerar_acentos(self):
        base = BASE + [{"id": 5, "nome": "Joaquim Álvaro", "municipio": "Anápolis"}]
        self.assertEqual(
            nomes(dominio.buscar(base, "jo")),
            ["Joana Dark Lima", "João Batista Silva", "Joaquim Álvaro"],
        )

    def test_nomes_iguais_saem_em_ordem_de_id(self):
        base = [
            {"id": 9, "nome": "Ana Souza", "municipio": "Anápolis"},
            {"id": 2, "nome": "ANA SOUZA", "municipio": "Rio Verde"},
        ]
        self.assertEqual([r["id"] for r in dominio.buscar(base, "ana")], [2, 9])

    def test_nome_vazio_lista_todos_os_servidores(self):
        self.assertEqual(len(dominio.buscar(BASE, "")), len(BASE))

    def test_nenhum_servidor_combina_com_o_trecho(self):
        self.assertEqual(dominio.buscar(BASE, "zzz"), [])

    def test_o_resultado_traz_so_id_nome_e_municipio(self):
        base = [dict(BASE[0], data_nascimento="1970-01-01")]
        self.assertEqual(
            dominio.buscar(base, ""),
            [{"id": 1, "nome": "João Batista Silva", "municipio": "Anápolis"}],
        )


class BuscaPorMunicipioTest(unittest.TestCase):
    def test_filtrar_a_busca_por_municipio(self):
        self.assertEqual(nomes(dominio.buscar(BASE, "maria", "Rio Verde")), ["Maria Conceição Rocha"])

    def test_nome_vazio_com_municipio_lista_todos_os_servidores_do_municipio(self):
        resultado = dominio.buscar(BASE, "", "Anápolis")
        self.assertEqual({r["municipio"] for r in resultado}, {"Anápolis"})
        self.assertEqual(len(resultado), 2)

    def test_listar_os_municipios_disponiveis(self):
        self.assertEqual(dominio.listar_municipios(BASE), ["Anápolis", "Rio Verde"])

    def test_municipios_em_ordem_alfabetica_sem_considerar_acentos(self):
        base = BASE + [{"id": 5, "nome": "X", "municipio": "Aparecida"}]
        self.assertEqual(
            dominio.listar_municipios(base), ["Anápolis", "Aparecida", "Rio Verde"]
        )


class NormalizarTest(unittest.TestCase):
    def test_remove_acento_maiuscula_e_espacos_nas_pontas(self):
        self.assertEqual(dominio.normalizar("  JOÃO Conceição "), "joao conceicao")


if __name__ == "__main__":
    unittest.main()
