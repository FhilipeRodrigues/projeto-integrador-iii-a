import re
import tempfile
import unittest
from pathlib import Path

from consulta import base
from scripts import gerar_base

RAIZ = Path(__file__).resolve().parent.parent


class GerarBaseTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.destino = Path(self.pasta.name) / "servidores.json"
        gerar_base.escrever_base(self.destino)
        self.dados = base.carregar(self.destino)

    def test_gerar_a_base_com_10_municipios_e_50_servidores(self):
        servidores = self.dados["servidores"]
        por_municipio = {}
        for servidor in servidores:
            por_municipio.setdefault(servidor["municipio"], []).append(servidor)
        self.assertEqual(len(por_municipio), 10)
        for municipio, lista in por_municipio.items():
            self.assertEqual(len(lista), 5, municipio)
        ids = [servidor["id"] for servidor in servidores]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)

    def test_a_mesma_geracao_produz_sempre_a_mesma_base(self):
        outro = Path(self.pasta.name) / "outra.json"
        gerar_base.escrever_base(outro)
        self.assertEqual(self.destino.read_bytes(), outro.read_bytes())

    def test_a_base_serve_para_demonstrar_a_busca(self):
        servidores = self.dados["servidores"]
        com_acento = [s for s in servidores if re.search(r"[^\x00-\x7f]", s["nome"])]
        self.assertGreaterEqual(len(com_acento), 3)

        municipios_por_palavra = {}
        for servidor in servidores:
            for palavra in servidor["nome"].split():
                municipios_por_palavra.setdefault(palavra, set()).add(servidor["municipio"])
        compartilhadas = [p for p, m in municipios_por_palavra.items() if len(m) >= 2]
        self.assertGreaterEqual(len(compartilhadas), 2)

        self.assertTrue(any(s["pcd"] for s in servidores))
        self.assertTrue(any(s["doenca_profissional"] for s in servidores))

    def test_a_base_versionada_e_a_que_o_gerador_produz(self):
        versionada = RAIZ / "data" / "servidores.json"
        self.assertTrue(versionada.exists(), "rode: python scripts/gerar_base.py")
        self.assertEqual(versionada.read_bytes(), self.destino.read_bytes())


if __name__ == "__main__":
    unittest.main()
