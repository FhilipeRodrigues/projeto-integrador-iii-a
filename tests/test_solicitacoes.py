import contextlib
import io
import json
import tempfile
import unittest
from concurrent import futures
from datetime import datetime
from pathlib import Path
from unittest import mock

from consulta import base, dominio, servidor, solicitacoes

RAIZ = Path(__file__).resolve().parent.parent


class SolicitacoesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidores = base.carregar(RAIZ / "data" / "servidores.json")["servidores"]
        cls.por_id = {s["id"]: s for s in cls.servidores}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.caminho = Path(self._tmp.name) / "solicitacoes.json"

    def _gravado(self):
        return json.loads(self.caminho.read_text(encoding="utf-8"))

    def _escrever(self, conteudo):
        self.caminho.write_text(json.dumps(conteudo, ensure_ascii=False), encoding="utf-8")

    def _arquivo_valido(self):
        self.caminho.unlink(missing_ok=True)
        solicitacoes.Solicitacoes(self.servidores, self.caminho)
        return self._gravado()

    def _recusa(self, conteudo, *trechos):
        self._escrever(conteudo)
        with self.assertRaises(solicitacoes.SolicitacoesInvalidas) as contexto:
            solicitacoes.Solicitacoes(self.servidores, self.caminho)
        for trecho in trechos:
            self.assertIn(trecho, str(contexto.exception))

    def test_Primeira_execucao_sorteia_e_grava_10_solicitacoes(self):
        self.assertFalse(self.caminho.exists())
        solicitacoes.Solicitacoes(self.servidores, self.caminho)
        conteudo = self._gravado()
        self.assertIs(conteudo["ficticio"], True)
        self.assertEqual(len(conteudo["solicitacoes"]), 10)

    def test_Uma_solicitacao_por_municipio_de_servidores_diferentes(self):
        itens = self._arquivo_valido()["solicitacoes"]
        self.assertEqual(len({i["municipio"] for i in itens}), 10)
        self.assertEqual(len({i["servidor_id"] for i in itens}), 10)
        for item in itens:
            self.assertEqual(self.por_id[item["servidor_id"]]["municipio"], item["municipio"])

    def test_Toda_solicitacao_nasce_pendente(self):
        itens = self._arquivo_valido()["solicitacoes"]
        self.assertEqual({i["situacao"] for i in itens}, {"pendente"})
        self.assertEqual({i["decidida_em"] for i in itens}, {None})
        self.assertEqual(
            [i["numero"] for i in sorted(itens, key=lambda i: i["id"])],
            [f"REQ-2026-{n:04d}" for n in range(1, 11)],
        )

    def test_Reiniciar_o_servidor_reutiliza_o_mesmo_sorteio(self):
        primeira = solicitacoes.Solicitacoes(self.servidores, self.caminho).listar()
        bytes_gravados = self.caminho.read_bytes()
        segunda = solicitacoes.Solicitacoes(self.servidores, self.caminho).listar()
        self.assertEqual(primeira, segunda)
        self.assertEqual(self.caminho.read_bytes(), bytes_gravados)

    def test_Apagar_o_arquivo_sorteia_de_novo(self):
        solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.caminho.unlink()
        solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.assertEqual(len(self._gravado()["solicitacoes"]), 10)

    def test_O_sorteio_varia_entre_execucoes(self):
        sorteios = {
            tuple(s["servidor_nome"] for s in solicitacoes.Solicitacoes(self.servidores).listar())
            for _ in range(5)
        }
        self.assertGreater(len(sorteios), 1)

    def test_Listar_traz_o_resumo_ordenado_pelo_numero(self):
        lista = solicitacoes.Solicitacoes(self.servidores, self.caminho).listar()
        self.assertEqual(len(lista), 10)
        self.assertEqual([i["numero"] for i in lista], sorted(i["numero"] for i in lista))
        for item in lista:
            self.assertEqual(set(item), {"id", "numero", "servidor_nome", "municipio", "situacao"})

    def test_Obter_devolve_copia_ou_nada(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores)
        primeira = pedidos.obter(1)
        primeira["situacao"] = "aprovada"
        self.assertEqual(pedidos.obter(1)["situacao"], "pendente")
        self.assertIsNone(pedidos.obter(999))

    def test_O_documento_tem_so_os_campos_do_requerimento(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores)
        solicitacao = pedidos.obter(1)
        documento = dominio.montar_documento(self.por_id[solicitacao["servidor_id"]], solicitacao)
        self.assertEqual(
            set(documento),
            {"id", "numero", "situacao", "decidida_em", "municipio", "orgao", "servidor_nome",
             "sexo", "data_ingresso", "data_solicitacao"},
        )

    def test_Aprovar_e_desaprovar_registram_a_situacao_e_a_hora(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        aprovada = pedidos.decidir(1, "aprovada")
        desaprovada = pedidos.decidir(2, "desaprovada")
        self.assertEqual((aprovada["situacao"], desaprovada["situacao"]), ("aprovada", "desaprovada"))
        for decidida in (aprovada, desaprovada):
            datetime.strptime(decidida["decidida_em"], solicitacoes.FORMATO_DECISAO)
        situacoes = [i["situacao"] for i in pedidos.listar()]
        self.assertEqual(situacoes, ["aprovada", "desaprovada"] + ["pendente"] * 8)

    def test_Trocar_a_decisao_a_ultima_vale(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        pedidos.decidir(1, "aprovada")
        pedidos.decidir(1, "desaprovada")
        self.assertEqual(pedidos.obter(1)["situacao"], "desaprovada")
        self.assertEqual(self._gravado()["solicitacoes"][0]["situacao"], "desaprovada")

    def test_A_decisao_sobrevive_a_reiniciar(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        pedidos.decidir(3, "aprovada")
        pedidos.decidir(4, "desaprovada")
        depois = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        situacoes = {i["id"]: i["situacao"] for i in depois.listar()}
        self.assertEqual(situacoes[3], "aprovada")
        self.assertEqual(situacoes[4], "desaprovada")
        self.assertEqual({v for k, v in situacoes.items() if k not in (3, 4)}, {"pendente"})
        self.assertEqual(depois.obter(3)["decidida_em"], pedidos.obter(3)["decidida_em"])

    def test_Decisao_invalida_ou_solicitacao_inexistente_nao_muda_nada(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        antes = self.caminho.read_bytes()
        for invalida in ("pendente", "talvez", None, 1, ["aprovada"]):
            with self.assertRaises(ValueError):
                pedidos.decidir(1, invalida)
        self.assertIsNone(pedidos.decidir(999, "aprovada"))
        self.assertEqual(self.caminho.read_bytes(), antes)
        self.assertEqual({i["situacao"] for i in pedidos.listar()}, {"pendente"})

    def test_A_situacao_do_servidor_vem_da_solicitacao_dele(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores)
        servidor_id = pedidos.obter(1)["servidor_id"]
        self.assertEqual(pedidos.situacao_do_servidor(servidor_id), "pendente")
        pedidos.decidir(1, "aprovada")
        self.assertEqual(pedidos.situacao_do_servidor(servidor_id), "aprovada")
        sem = next(s["id"] for s in self.servidores if s["id"] not in
                   {i["servidor_id"] for i in (pedidos.obter(n) for n in range(1, 11))})
        self.assertIsNone(pedidos.situacao_do_servidor(sem))

    def test_Duas_decisoes_ao_mesmo_tempo_nao_se_perdem_nem_corrompem_o_arquivo(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        saida = futures.ThreadPoolExecutor(max_workers=10)
        with saida:
            for resultado in saida.map(
                lambda n: pedidos.decidir(n, "aprovada" if n % 2 else "desaprovada"), range(1, 11)
            ):
                self.assertIsNotNone(resultado)
        esperado = {n: "aprovada" if n % 2 else "desaprovada" for n in range(1, 11)}
        for origem in (pedidos, solicitacoes.Solicitacoes(self.servidores, self.caminho)):
            self.assertEqual({i["id"]: i["situacao"] for i in origem.listar()}, esperado)
        self.assertEqual([p.name for p in self.caminho.parent.iterdir()], [self.caminho.name])

    def test_Falha_ao_gravar_a_decisao_mantem_a_situacao_anterior(self):
        pedidos = solicitacoes.Solicitacoes(self.servidores, self.caminho)
        pedidos.decidir(1, "aprovada")
        antes = self.caminho.read_bytes()
        with mock.patch("consulta.solicitacoes.os.replace", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                pedidos.decidir(1, "desaprovada")
        self.assertEqual(pedidos.obter(1)["situacao"], "aprovada")
        self.assertEqual(self.caminho.read_bytes(), antes)
        self.assertEqual([p.name for p in self.caminho.parent.iterdir()], [self.caminho.name])

    def test_Arquivo_com_servidor_inexistente_e_recusado_com_solicitacao_e_campo(self):
        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][2]["servidor_id"] = 9999
        self._recusa(conteudo, "solicitação 3", "servidor_id")

    def test_Arquivo_com_municipio_diferente_do_servidor_e_recusado(self):
        conteudo = self._arquivo_valido()
        item = conteudo["solicitacoes"][0]
        item["municipio"] = next(
            s["municipio"] for s in self.servidores if s["municipio"] != item["municipio"]
        )
        self._recusa(conteudo, "solicitação 1", "municipio")

    def test_Arquivo_com_servidor_repetido_e_recusado(self):
        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][1]["servidor_id"] = conteudo["solicitacoes"][0]["servidor_id"]
        conteudo["solicitacoes"][1]["municipio"] = conteudo["solicitacoes"][0]["municipio"]
        self._recusa(conteudo, "solicitação 2", "servidor_id")

    def test_Arquivo_com_situacao_ou_decisao_incoerente_e_recusado(self):
        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][0]["situacao"] = "talvez"
        self._recusa(conteudo, "solicitação 1", "situacao")

        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][0]["situacao"] = "aprovada"
        self._recusa(conteudo, "decidida_em")

        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][0]["decidida_em"] = "2026-11-18T10:00:00"
        self._recusa(conteudo, "decidida_em")

    def test_Arquivo_com_id_repetido_ou_numero_trocado_e_recusado(self):
        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][1]["id"] = conteudo["solicitacoes"][0]["id"]
        self._recusa(conteudo, "solicitação 2", "id")

        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][0]["numero"] = "REQ-2026-0099"
        self._recusa(conteudo, "numero")

    def test_Arquivo_com_estrutura_errada_e_recusado(self):
        self._recusa(["não é objeto"], "objeto JSON")
        self._recusa({"ficticio": False, "solicitacoes": []}, "ficticio")
        self._recusa({"ficticio": True, "solicitacoes": []}, "solicitacoes")
        self.caminho.write_text("{ não é json", encoding="utf-8")
        with self.assertRaises(solicitacoes.SolicitacoesInvalidas) as contexto:
            solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.assertIn("JSON", str(contexto.exception))

    def test_Arquivo_invalido_nao_e_sobrescrito(self):
        self.caminho.write_text("{ não é json", encoding="utf-8")
        with self.assertRaises(solicitacoes.SolicitacoesInvalidas):
            solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.assertEqual(self.caminho.read_text(encoding="utf-8"), "{ não é json")

    def test_A_gravacao_nao_deixa_arquivo_temporario(self):
        solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.assertEqual([p.name for p in self.caminho.parent.iterdir()], [self.caminho.name])

    def test_Falha_na_gravacao_nao_deixa_lixo_nem_arquivo_pela_metade(self):
        with mock.patch("consulta.solicitacoes.os.replace", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                solicitacoes.Solicitacoes(self.servidores, self.caminho)
        self.assertEqual(list(self.caminho.parent.iterdir()), [])

    def test_O_servidor_nao_sobe_com_arquivo_de_solicitacoes_invalido(self):
        conteudo = self._arquivo_valido()
        conteudo["solicitacoes"][2]["servidor_id"] = 9999
        self._escrever(conteudo)
        erro = io.StringIO()
        with contextlib.redirect_stderr(erro):
            codigo = servidor.main(["--solicitacoes", str(self.caminho), "--porta", "0"])
        self.assertEqual(codigo, 1)
        self.assertIn("solicitação 3", erro.getvalue())
        self.assertIn("servidor_id", erro.getvalue())

    def test_O_arquivo_de_solicitacoes_nao_vai_para_o_repositorio(self):
        ignorado = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("data/solicitacoes.json", ignorado)


if __name__ == "__main__":
    unittest.main()
