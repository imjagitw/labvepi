import unittest
from etl.base import Resultado
from etl.morcegos import eh_sim, processar_linha_morcego
from src.models.Animal.enums.Sexo import Sexo
from src.models.Animal.enums.StatusVital import StatusVital
from src.models.Amostra.enums.MaterialBiologico import MaterialBiologico


class TestETLMorcegos(unittest.TestCase):
    def test_eh_sim(self):
        self.assertTrue(eh_sim("Sim"))
        self.assertTrue(eh_sim("SIM"))
        self.assertTrue(eh_sim("sim (diluído)"))
        self.assertTrue(eh_sim("+"))
        self.assertTrue(eh_sim("positivo"))
        self.assertFalse(eh_sim("Não"))
        self.assertFalse(eh_sim("-"))
        self.assertFalse(eh_sim(None))
        self.assertFalse(eh_sim(""))

    def test_processar_linha_morcego_completa(self):
        res = Resultado()
        row = {
            "identificação": "M05",
            "espécie": "artibeus lineatus",
            "peso": 0.005,
            "sexo": "M",
            "sangue": "SIM (Diluído)",
            "fezes": "-",
            "enema": "-",
            "papel filtro": "SIM",
            "esfregaço": "SIM",
            "herpes": "SIM",
            "aimes": "-",
            "covid o": "SIM",
            "covid r": "-",
            "obs": "Foram coletados pulmão, coração e fígado",
        }

        processar_linha_morcego(
            row_dict=row,
            n_linha=11,
            sheet_name="Teresina",
            data_coleta_padrao="2022-01-28",
            res=res,
        )

        # 1 animal
        self.assertEqual(len(res.animais), 1)
        animal = res.animais[0]
        self.assertEqual(animal["_id"], 1)
        self.assertEqual(animal["animal_id"], "M05")
        self.assertEqual(animal["nome_comum"], "Morcego-de-linha-branca")
        self.assertEqual(animal["nome_cientifico"], "Platyrrhinus lineatus")
        self.assertEqual(animal["sexo"], Sexo.MACHO.value)
        self.assertEqual(animal["peso"], 0.005)
        self.assertEqual(animal["status_vital"], StatusVital.VIVO.value)

        # Amostras: Sangue, Papel Filtro, Esfregaço, Swab Oral, Pulmão, Coração, Fígado = 7 amostras
        self.assertEqual(len(res.amostras), 7)
        self.assertEqual(res.amostras[0]["_id"], 1)
        self.assertEqual(res.amostras[0]["animal_id"], "M05")
        self.assertEqual(res.amostras[0]["amostra_id"], "M05-SG")
        materiais = [a["material_biologico"] for a in res.amostras]
        self.assertIn(MaterialBiologico.SANGUE.value, materiais)
        self.assertIn(MaterialBiologico.PAPEL_FILTRO.value, materiais)
        self.assertIn(MaterialBiologico.ESFREGACO_SANGUINEO.value, materiais)
        self.assertIn(MaterialBiologico.SWAB_ORAL.value, materiais)
        self.assertIn(MaterialBiologico.PULMAO.value, materiais)
        self.assertIn(MaterialBiologico.CORACAO.value, materiais)
        self.assertIn(MaterialBiologico.FIGADO.value, materiais)

        # Exames: Herpes, Covid Oral = 2 exames
        self.assertEqual(len(res.exames), 2)
        self.assertEqual(res.exames[0]["_id"], 1)
        self.assertEqual(res.exames[0]["amostra_id"], "M05-SG")
        exame_ids = [e["exame_id"] for e in res.exames]
        self.assertIn("M05-HERPES", exame_ids)
        self.assertIn("M05-COVIDO", exame_ids)

        # Sem problemas registrados nessa linha
        self.assertEqual(len(res.problemas), 0)

    def test_processar_linha_morcego_com_problema_de_especie(self):
        res = Resultado()
        row = {
            "identificação": "M01",
            "espécie": "-",
            "peso": "-",
            "sexo": "-",
            "sangue": "-",
            "obs": "Óbito no transporte",
        }

        processar_linha_morcego(
            row_dict=row,
            n_linha=7,
            sheet_name="Floriano",
            data_coleta_padrao="2022-01-01",
            res=res,
        )

        self.assertEqual(len(res.animais), 1)
        animal = res.animais[0]
        self.assertEqual(animal["_id"], 1)
        self.assertEqual(animal["animal_id"], "M01")
        self.assertEqual(animal["status_vital"], StatusVital.MORTO.value)
        self.assertEqual(animal["nome_comum"], "Não informado")

        # Deve haver 1 problema registrado para espécie
        self.assertEqual(len(res.problemas), 1)
        self.assertEqual(res.problemas[0].coluna, "Espécie")
        self.assertIn("Floriano", res.problemas[0].motivo)


if __name__ == "__main__":
    unittest.main()
