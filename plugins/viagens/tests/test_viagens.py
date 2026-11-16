"""Testes do plugin viagens. Rodar da raiz: python3 -m unittest discover -s plugins/viagens/tests"""
import importlib.util
import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def carregar(rel):
    caminho = RAIZ / "skills" / rel
    spec = importlib.util.spec_from_file_location(caminho.stem, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


plano = carregar("planejar-viagem/scripts/plano.py")
lt = carregar("cotar-transporte/scripts/links_transporte.py")
lh = carregar("cotar-hospedagem/scripts/links_hospedagem.py")
cen = carregar("comparar-cenarios/scripts/cenarios.py")
EXEMPLOS = RAIZ / "exemplos"


class TestPlano(unittest.TestCase):
    def test_exemplo_divide_noites_e_volta(self):
        p = plano.montar_plano(json.loads((EXEMPLOS / "viagem.json").read_text()))
        self.assertEqual([e["noites"] for e in p["estadias"]], [3, 3])
        self.assertEqual([(t["de"], t["para"]) for t in p["trechos"]],
                         [("São Paulo", "Rio de Janeiro"), ("Rio de Janeiro", "Paraty"), ("Paraty", "São Paulo")])
        self.assertEqual(p["data_fim"], "2026-12-24")
        self.assertEqual(p["dias"], 7)

    def test_resto_vai_para_os_primeiros(self):
        p = plano.montar_plano({"origem": "A", "data_inicio": "2026-01-01", "dias": 6,
                                "destinos": ["B", "C"]})
        self.assertEqual([e["noites"] for e in p["estadias"]], [3, 2])

    def test_noites_fixas_e_livres(self):
        p = plano.montar_plano({"origem": "A", "data_inicio": "2026-01-01", "dias": 8,
                                "destinos": [{"cidade": "B", "noites": 5}, {"cidade": "C"}]})
        self.assertEqual([e["noites"] for e in p["estadias"]], [5, 2])

    def test_sem_retorno(self):
        p = plano.montar_plano({"origem": "A", "data_inicio": "2026-01-01", "dias": 3,
                                "retornar_origem": False, "destinos": ["B"]})
        self.assertEqual(len(p["trechos"]), 1)

    def test_erros(self):
        with self.assertRaises(plano.ErroPlano):
            plano.montar_plano({"origem": "A", "data_inicio": "2026-01-01", "destinos": ["B"]})
        with self.assertRaises(plano.ErroPlano):
            plano.montar_plano({"origem": "A", "data_inicio": "2026-01-01", "dias": 3,
                                "destinos": [{"cidade": "B", "noites": 5}, {"cidade": "C"}]})
        with self.assertRaises(plano.ErroPlano):
            plano.montar_plano({"origem": "A", "data_inicio": "01/01/2026", "dias": 3, "destinos": ["B"]})


class TestLinks(unittest.TestCase):
    def setUp(self):
        self.p = plano.montar_plano(json.loads((EXEMPLOS / "viagem.json").read_text()))

    def test_transporte(self):
        self.p["iata"] = {"São Paulo": "sao", "Rio de Janeiro": "rio"}
        self.p["uf"] = {"São Paulo": "sp", "Rio de Janeiro": "rj"}
        r = lt.gerar(self.p)
        t1 = r["trechos"][0]
        self.assertEqual(t1["aviao"]["kayak"], "https://www.kayak.com.br/flights/SAO-RIO/2026-12-18/2adults")
        self.assertEqual(t1["onibus"]["clickbus"],
                         "https://www.clickbus.com.br/onibus/sao-paulo-sp/rio-de-janeiro-rj?departureDate=2026-12-18")
        self.assertNotIn("kayak", r["trechos"][1]["aviao"])
        self.assertIn("2026-12-24", r["aluguel_carro"]["kayak_carros"])

    def test_hospedagem(self):
        r = lh.gerar(self.p)["estadias"][0]
        self.assertTrue(r["airbnb"].startswith("https://www.airbnb.com.br/s/Rio-de-Janeiro/homes?"))
        self.assertIn("checkin=2026-12-18", r["booking"])
        self.assertIn("group_adults=2", r["booking"])


class TestCenarios(unittest.TestCase):
    def setUp(self):
        self.cot = json.loads((EXEMPLOS / "cotacoes.json").read_text())

    def test_custo_carro(self):
        c = cen.custo_carro(self.cot["trechos"], self.cot["aluguel_carro"])
        # 150*7+120 + 990/11*6.3 + 130 + 25*7
        self.assertAlmostEqual(c["total"], 1170 + 567 + 130 + 175)

    def test_combinacoes_ordenadas_e_fallback(self):
        r = cen.calcular(self.cot)
        totais = [c["total"] for c in r["combinacoes"]]
        self.assertEqual(totais, sorted(totais))
        self.assertEqual(r["combinacoes"][0]["total"], 860 + 2330)
        self.assertEqual(r["transporte"]["aviao"]["escolhas"], {"T1": "aviao", "T2": "onibus", "T3": "onibus"})
        self.assertNotIn("misto", r["transporte"])  # idêntico ao ônibus neste exemplo

    def test_misto_quando_diferente(self):
        self.cot["trechos"][0]["aviao"]["preco_por_pessoa"] = 50
        self.cot["trechos"][0]["aviao"]["extras_por_pessoa"] = 0
        self.cot["trechos"][2]["aviao"] = {"preco_por_pessoa": 900, "duracao_h": 3}
        r = cen.calcular(self.cot)
        self.assertEqual(r["transporte"]["misto"]["escolhas"],
                         {"T1": "aviao", "T2": "onibus", "T3": "onibus"})

    def test_carro_indisponivel_sem_aluguel(self):
        del self.cot["aluguel_carro"]
        r = cen.calcular(self.cot)
        self.assertIn("carro", r["transporte_indisponivel"])
        self.assertIn("indisponível", cen.markdown(r))


if __name__ == "__main__":
    unittest.main()
