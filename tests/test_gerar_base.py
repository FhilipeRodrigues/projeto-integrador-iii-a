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

    def _primeiros(self):
        return [s["nome"].split()[0] for s in self.dados["servidores"]]

    def test_Cada_um_dos_50_nomes_aparece_uma_vez(self):
        primeiros = self._primeiros()
        self.assertEqual(sorted(primeiros), sorted(gerar_base.NOMES_M + gerar_base.NOMES_F))
        self.assertEqual(len(gerar_base.NOMES_M), 25)
        self.assertEqual(len(gerar_base.NOMES_F), 25)

    def test_O_sexo_acompanha_o_nome(self):
        for servidor in self.dados["servidores"]:
            esperado = "M" if servidor["nome"].split()[0] in gerar_base.NOMES_M else "F"
            self.assertEqual(servidor["sexo"], esperado, servidor["nome"])

    def test_Dois_sobrenomes_diferentes_entre_si(self):
        for servidor in self.dados["servidores"]:
            partes = servidor["nome"].split()
            self.assertEqual(len(partes), 3, servidor["nome"])
            self.assertNotEqual(partes[1], partes[2], servidor["nome"])

    def test_Nomes_parecidos_em_municipios_diferentes(self):
        municipio = {s["nome"].split()[0]: s["municipio"] for s in self.dados["servidores"]}
        for a, b in gerar_base.PARES_PARECIDOS:
            self.assertNotEqual(municipio[a], municipio[b], f"{a} e {b}")

    def test_Os_nomes_ficam_distribuidos_entre_os_municipios(self):
        sexos = {}
        for servidor in self.dados["servidores"]:
            sexos.setdefault(servidor["municipio"], set()).add(servidor["sexo"])
        self.assertEqual(len(sexos), 10)
        for municipio, conjunto in sexos.items():
            self.assertEqual(conjunto, {"F", "M"}, municipio)

    def test_O_nome_usado_no_README_existe_na_base_e_no_README(self):
        self.assertTrue(any("maria" in nome.lower() for nome in self._primeiros()))
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn("`maria`", readme)
        self.assertNotIn("`joana`", readme)

    def test_a_base_versionada_e_a_que_o_gerador_produz(self):
        versionada = RAIZ / "data" / "servidores.json"
        self.assertTrue(versionada.exists(), "rode: python scripts/gerar_base.py")
        self.assertEqual(versionada.read_bytes(), self.destino.read_bytes())


if __name__ == "__main__":
    unittest.main()
