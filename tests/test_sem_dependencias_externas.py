import ast
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PACOTES_DO_PROJETO = {"consulta", "scripts", "tests"}


def importacoes(arquivo: Path):
    """Nome do módulo de cada importação absoluta do arquivo."""
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                yield alias.name.split(".")[0]
        elif isinstance(no, ast.ImportFrom) and no.level == 0:
            yield no.module.split(".")[0]


def _readme() -> str:
    return (RAIZ / "README.md").read_text(encoding="utf-8")


class SemDependenciasExternasTest(unittest.TestCase):
    def test_o_projeto_usa_so_a_biblioteca_padrao_do_python(self):
        arquivos = sorted(
            arquivo
            for pasta in ("consulta", "scripts")
            for arquivo in (RAIZ / pasta).rglob("*.py")
        )
        self.assertTrue(arquivos)
        externas = {
            f"{arquivo.relative_to(RAIZ)}: {modulo}"
            for arquivo in arquivos
            for modulo in importacoes(arquivo)
            if modulo not in sys.stdlib_module_names and modulo not in PACOTES_DO_PROJETO
        }
        self.assertEqual(set(), externas)


class ReadmeTest(unittest.TestCase):
    def test_pre_requisitos_citam_python_tkinter_e_openssl(self):
        texto = _readme()
        self.assertIn("## Pré-requisitos", texto)
        self.assertRegex(texto, r"Python\s*\|\s*3\.\d+")
        self.assertIn("Tkinter", texto)
        self.assertIn("openssl", texto)
        self.assertIn("git-scm.com", texto)  # onde obter o openssl no Windows

    def test_readme_ensina_a_recusa_de_servidor_falso(self):
        texto = _readme()
        self.assertIn("## Demonstração de segurança", texto)
        self.assertIn("python scripts/gerar_certificados.py certs/falso", texto)
        self.assertIn("python -m consulta.servidor --certs certs/falso", texto)
        self.assertIn("recusa", texto.lower())

    def test_readme_avisa_que_os_dados_sao_ficticios(self):
        texto = _readme()
        self.assertIn("fictícios", texto)
        self.assertRegex(texto, r"coincidir por acaso com pessoas reais")

    def test_a_busca_de_exemplo_do_readme_acha_servidores_na_base(self):
        from consulta import base, dominio

        termo = re.search(r"digite `(\w+)`", _readme()).group(1)
        servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]
        self.assertTrue(dominio.buscar(servidores, termo), termo)

    def test_comandos_do_readme_apontam_para_arquivos_existentes(self):
        texto = _readme()
        for script in re.findall(r"python scripts/(\w+\.py)", texto):
            self.assertTrue((RAIZ / "scripts" / script).is_file(), script)
        for modulo in re.findall(r"python -m (consulta\.\w+)", texto):
            self.assertTrue((RAIZ / (modulo.replace(".", "/") + ".py")).is_file(), modulo)


class RepositorioSemSegredosTest(unittest.TestCase):
    def test_o_repositorio_nao_carrega_segredos(self):
        if shutil.which("git") is None or not (RAIZ / ".git").exists():
            self.skipTest("sem git ou fora de um repositório")
        saida = subprocess.run(
            ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        proibidos = [
            arquivo
            for arquivo in saida
            if arquivo.endswith((".key", ".pem", ".crt")) or arquivo.startswith("certs/")
        ]
        self.assertEqual([], proibidos)


if __name__ == "__main__":
    unittest.main()
