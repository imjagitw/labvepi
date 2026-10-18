import csv
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from etl.base import id_estavel, Resultado, NAMESPACE_LABVEPI


class TestEtlBase(unittest.TestCase):
    def test_id_estavel_idempotente(self):
        id1 = id_estavel("morcegos", "M01")
        id2 = id_estavel("morcegos", "M01")
        self.assertEqual(id1, id2)
        
        # Valida que é um UUID válido
        parsed = uuid.UUID(id1)
        self.assertEqual(parsed.version, 5)

    def test_id_estavel_distingue_planilhas_e_chaves(self):
        id_morcego = id_estavel("morcegos", 1)
        id_ave = id_estavel("aves", 1)
        self.assertNotEqual(id_morcego, id_ave)

        id_chave1 = id_estavel("morcegos", "M01")
        id_chave2 = id_estavel("morcegos", "M02")
        self.assertNotEqual(id_chave1, id_chave2)

    def test_id_estavel_limpa_espacos(self):
        id_trim = id_estavel("morcegos", "  M01  ")
        id_clean = id_estavel("morcegos", "M01")
        self.assertEqual(id_trim, id_clean)

    def test_resultado_ids_autoincrementais(self):
        res = Resultado()
        self.assertEqual(res.proximo_id_animal(), 1)
        self.assertEqual(res.proximo_id_animal(), 2)
        self.assertEqual(res.proximo_id_amostra(), 1)
        self.assertEqual(res.proximo_id_amostra(), 2)
        self.assertEqual(res.proximo_id_exame(), 1)
        self.assertEqual(res.proximo_id_exame(), 2)

    def test_resultado_salvar(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = Resultado()
            res.animais.append({"animal_id": "M01", "nome_comum": "Morcego"})
            res.amostras.append({"amostra_id": "AMS01", "animal_id": "M01"})
            res.exames.append({"exame_id": "EX01", "amostra_id": "AMS01", "resultado": "Positivo"})
            res.problema(linha=2, coluna="peso", valor="duvidoso", motivo="não interpretável")

            contagens = res.salvar(tmpdir)
            self.assertEqual(contagens["animais"], 1)
            self.assertEqual(contagens["amostras"], 1)
            self.assertEqual(contagens["exames"], 1)
            self.assertEqual(contagens["problemas"], 1)

            p_dir = Path(tmpdir)
            self.assertTrue((p_dir / "animais.jsonl").exists())
            self.assertTrue((p_dir / "amostras.jsonl").exists())
            self.assertTrue((p_dir / "exames.jsonl").exists())
            self.assertTrue((p_dir / "problemas.csv").exists())

            # Validar conteúdo do jsonl
            with open(p_dir / "animais.jsonl", encoding="utf-8") as f:
                linha = json.loads(f.readline())
                self.assertEqual(linha["animal_id"], "M01")

            # Validar conteúdo do csv de problemas
            with open(p_dir / "problemas.csv", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                linhas = list(reader)
                self.assertEqual(len(linhas), 1)
                self.assertEqual(linhas[0]["linha"], "2")
                self.assertEqual(linhas[0]["coluna"], "peso")
                self.assertEqual(linhas[0]["valor"], "duvidoso")
                self.assertEqual(linhas[0]["motivo"], "não interpretável")


if __name__ == "__main__":
    unittest.main()
