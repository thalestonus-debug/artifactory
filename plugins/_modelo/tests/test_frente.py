import importlib.util
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
caminho = RAIZ / "skills" / "nome-da-skill" / "scripts" / "exemplo.py"
spec = importlib.util.spec_from_file_location("exemplo", caminho)
exemplo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exemplo)


class TestExemplo(unittest.TestCase):
    def test_processar(self):
        self.assertEqual(exemplo.processar({"a": 1}), {"recebido": {"a": 1}})


if __name__ == "__main__":
    unittest.main()
