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


class TestCasosReais(unittest.TestCase):
    """Casos que surgiram no uso real: viagem que termina em outra cidade e carro próprio."""

    def test_destino_final_diferente_e_comeca_na_origem(self):
        p = plano.montar_plano({
            "origem": "Salvador", "data_inicio": "2027-01-30", "viajantes": 3,
            "destino_final": "São Paulo",
            "destinos": [{"cidade": "Salvador", "noites": 6}, {"cidade": "Itacaré", "noites": 2},
                         {"cidade": "Caravelas", "noites": 1}],
        })
        self.assertEqual([(t["de"], t["para"], t["data"]) for t in p["trechos"]], [
            ("Salvador", "Itacaré", "2027-02-05"),
            ("Itacaré", "Caravelas", "2027-02-07"),
            ("Caravelas", "São Paulo", "2027-02-08"),
        ])
        self.assertEqual(p["data_fim"], "2027-02-08")

    def test_carro_proprio_sem_onibus_nem_aviao(self):
        cot = {
            "viajantes": 3,
            "trechos": [{"id": "T1", "de": "A", "para": "B", "carro": {"distancia_km": 110, "pedagio": 10, "duracao_h": 2}}],
            "carro_proprio": {"consumo_km_l": 11, "preco_combustivel": 6.0},
            "estadias": [{"id": "H1", "cidade": "B", "noites": 1, "airbnb": {"preco_total": 300}}],
        }
        r = cen.calcular(cot)
        self.assertEqual(list(r["transporte"]), ["carro"])
        self.assertEqual(r["transporte_indisponivel"], {})
        self.assertAlmostEqual(r["transporte"]["carro"]["total"], 60 + 10)
        self.assertEqual(list(r["hospedagem"]), ["airbnb"])
        md = cen.markdown(r)
        self.assertIn("Carro próprio", md)
        self.assertNotIn("Ônibus", md)
        self.assertEqual(r["combinacoes"][0]["total"], 370)


esc = carregar("cotar-hospedagem/scripts/escolher.py")


class TestEscolher(unittest.TestCase):
    def test_mediana_prioridade_e_sem_historico(self):
        r = esc.escolher({
            "preferencias": {"bairros_prioritarios": ["Graca"], "nota_min": 4.7, "avaliacoes_min": 10},
            "anuncios": [
                {"nome": "caro", "bairro": "Barra", "preco_total": 10000, "nota": 5, "avaliacoes": 50},
                {"nome": "barra ok", "bairro": "Barra", "preco_total": 6000, "nota": 4.8, "avaliacoes": 60},
                {"nome": "graca ok", "bairro": "Graça", "preco_total": 7000, "nota": 4.9, "avaliacoes": 30},
                {"nome": "graca nova", "bairro": "Graça", "preco_total": 4600, "nota": None, "avaliacoes": 0},
                {"nome": "nota baixa", "bairro": "Barra", "preco_total": 5000, "nota": 4.2, "avaliacoes": 40},
                {"nome": "outra data", "bairro": "Graça", "preco_total": 100, "nota": 5, "avaliacoes": 99,
                 "datas_exatas": False},
                {"nome": "media", "bairro": "Barra", "preco_total": 8000, "nota": 4.9, "avaliacoes": 20},
            ],
        })
        self.assertEqual(r["mediana"], 6500)  # ignora a de outra data
        self.assertEqual([a["nome"] for a in r["recomendados"]], ["barra ok"])
        self.assertEqual([a["nome"] for a in r["sem_historico"]], ["graca nova"])
        self.assertEqual(r["descartados"], 4)

    def test_teto_relativo_e_prioridade_primeiro(self):
        r = esc.escolher({
            "preferencias": {"bairros_prioritarios": ["Graça"], "teto_relativo_mediana": 1.2, "avaliacoes_min": 1},
            "anuncios": [
                {"nome": "a", "bairro": "Barra", "preco_total": 100, "nota": 5, "avaliacoes": 3},
                {"nome": "b", "bairro": "graça", "preco_total": 115, "nota": 5, "avaliacoes": 3},
                {"nome": "c", "bairro": "Barra", "preco_total": 120, "nota": 5, "avaliacoes": 3},
            ],
        })
        self.assertEqual([a["nome"] for a in r["recomendados"]], ["b", "a", "c"])  # teto = 115 × 1,2 = 138
        self.assertEqual(r["recomendados"][0]["vs_mediana_pct"], 0)


hor = carregar("planejar-viagem/scripts/horarios.py")


class TestHorarios(unittest.TestCase):
    def test_chegada_com_fator_e_avisos(self):
        r = hor.calcular({"fator": 1.2, "trechos": [
            {"id": "T1", "para": "BH", "saida": "2027-01-28T19:00", "duracao_h": 7.9},
            {"id": "T2", "para": "VdC", "saida": "2027-01-29T03:00", "duracao_h": 1},
        ]})
        self.assertEqual(r["trechos"][0]["chegada"], "2027-01-29T04:30")  # 9,48 h → arredonda p/ 5 min
        self.assertEqual(r["trechos"][0]["chegada_txt"], "sex 29/01 04:30")
        self.assertEqual(len(r["avisos"]), 3)  # madrugada T1, T2 sai antes de chegar, madrugada T2
