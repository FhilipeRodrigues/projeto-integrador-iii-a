import copy
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from consulta import base
from scripts import gerar_base


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.valida = gerar_base.gerar_base()

    def _gravar(self, dados):
        caminho = Path(self.pasta.name) / "base.json"
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        return caminho

    def test_a_base_e_marcada_como_ficticia(self):
        carregada = base.carregar(self._gravar(self.valida))
        self.assertIs(carregada["ficticio"], True)

    def test_recusar_base_sem_a_marca_de_ficticia(self):
        dados = copy.deepcopy(self.valida)
        dados["ficticio"] = False
        with self.assertRaisesRegex(base.BaseInvalida, "fictícia"):
            base.carregar(self._gravar(dados))

    def test_recusar_uma_base_com_dados_invalidos(self):
        def ingresso_antes_dos_18(s):
            s["data_ingresso"] = s["data_nascimento"]

        def solicitacao_antes_do_ingresso(s):
            ingresso = date.fromisoformat(s["data_ingresso"])
            s["data_solicitacao"] = (ingresso - timedelta(days=1)).isoformat()

        def id_repetido(s):
            s["id"] = 1

        def sexo_invalido(s):
            s["sexo"] = "X"

        def sem_municipio(s):
            del s["municipio"]

        casos = [
            ("um servidor ingressou antes de completar 18 anos", ingresso_antes_dos_18, "data_ingresso"),
            ("a data da solicitação é anterior ao ingresso", solicitacao_antes_do_ingresso, "data_solicitacao"),
            ("dois servidores têm o mesmo número de identificação", id_repetido, "'id'"),
            ("o sexo não é F nem M", sexo_invalido, "sexo"),
            ("falta o município de um servidor", sem_municipio, "municipio"),
        ]
        for problema, alterar, campo in casos:
            with self.subTest(problema):
                dados = copy.deepcopy(self.valida)
                alterar(dados["servidores"][1])  # o segundo servidor, id 2
                with self.assertRaises(base.BaseInvalida) as contexto:
                    base.carregar(self._gravar(dados))
                mensagem = str(contexto.exception)
                self.assertIn("servidor 2", mensagem)
                self.assertIn(campo, mensagem)

    def test_ingresso_exatamente_aos_18_anos_e_aceito_e_um_dia_antes_e_recusado(self):
        dados = copy.deepcopy(self.valida)
        servidor = dados["servidores"][0]
        servidor["data_nascimento"] = "1980-05-10"
        servidor["data_ingresso"] = "1998-05-10"
        base.carregar(self._gravar(dados))
        servidor["data_ingresso"] = "1998-05-09"
        with self.assertRaisesRegex(base.BaseInvalida, "data_ingresso"):
            base.carregar(self._gravar(dados))

    def test_recusar_data_inexistente_e_arquivo_ausente(self):
        dados = copy.deepcopy(self.valida)
        dados["servidores"][0]["data_nascimento"] = "1970-02-30"
        with self.assertRaisesRegex(base.BaseInvalida, "data_nascimento"):
            base.carregar(self._gravar(dados))
        with self.assertRaisesRegex(base.BaseInvalida, "não foi possível ler"):
            base.carregar(Path(self.pasta.name) / "nao-existe.json")


if __name__ == "__main__":
    unittest.main()
