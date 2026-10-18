import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from etl.carregar import (
    BANCO_AUTORIZADO,
    executar_carga,
    validar_documentos,
    verificar_integridade_vinculos,
    persistir_lote_mongodb,
)


class TestEtlCarregar(unittest.TestCase):
    def setUp(self):
        self.animal_valido = {
            "_id": 1,
            "id": 1,
            "animal_id": "M01",
            "codigo_lab": "M01",
            "classe": "Mamífero",
            "nome_comum": "Molossus sp.",
            "nome_cientifico": "Molossus sp.",
            "sexo": "Macho",
            "peso": 0.015,
            "faixa_etaria": "Não Informado",
            "orgao_origem": "UFPI",
            "local_origem": "Teresina/PI",
            "regime_vida": "Vida livre",
            "status_vital": "Vivo",
        }

        self.amostra_valida = {
            "_id": 1,
            "id": 1,
            "amostra_id": "M01-SG",
            "animal_id": "M01",
            "codigo_lab": "M01-SG",
            "material_biologico": "Sangue",
            "status_amostra": "Disponível",
            "data_coleta_amostra": "2022-01-28",
            "local_coleta_amostra": "Teresina/PI",
        }

        self.exame_valido = {
            "_id": 1,
            "id": 1,
            "exame_id": "M01-HERPES",
            "amostra_id": "M01-SG",
            "tipo_exame": "Herpesviridae",
            "resultado": "Aguardando Resultado",
            "teste_laboratorial": "PCR",
            "data_realizacao": "2022-01-28",
        }

    def test_validar_documentos_sucesso(self):
        animais, amostras, exames, erros = validar_documentos(
            [self.animal_valido], [self.amostra_valida], [self.exame_valido]
        )
        self.assertEqual(len(animais), 1)
        self.assertEqual(len(amostras), 1)
        self.assertEqual(len(exames), 1)
        self.assertEqual(len(erros), 0)

    def test_validar_documentos_detecta_erros(self):
        animal_invalido = {"_id": "x"}  # Faltam campos essenciais
        animais, amostras, exames, erros = validar_documentos([animal_invalido], [], [])
        self.assertEqual(len(animais), 0)
        self.assertEqual(len(erros), 1)
        self.assertEqual(erros[0]["entidade"], "Animal")

    def test_verificar_integridade_vinculos_valida(self):
        animais, amostras, exames, erros = verificar_integridade_vinculos(
            [self.animal_valido], [self.amostra_valida], [self.exame_valido]
        )
        self.assertEqual(len(animais), 1)
        self.assertEqual(len(amostras), 1)
        self.assertEqual(len(exames), 1)
        self.assertEqual(len(erros), 0)

    def test_verificar_integridade_vinculos_detecta_orfaos(self):
        # Amostra referenciando animal inexistente
        amostra_orfa = dict(self.amostra_valida)
        amostra_orfa["animal_id"] = "ANIMAL_INEXISTENTE"

        # Exame referenciando amostra inexistente
        exame_orfao = dict(self.exame_valido)
        exame_orfao["amostra_id"] = "AMOSTRA_INEXISTENTE"

        animais, amostras, exames, erros = verificar_integridade_vinculos(
            [self.animal_valido], [amostra_orfa], [exame_orfao]
        )
        self.assertEqual(len(animais), 1)
        self.assertEqual(len(amostras), 0)  # Rejeitada
        self.assertEqual(len(exames), 0)    # Rejeitado
        self.assertEqual(len(erros), 2)

    def test_seguranca_banco_nao_autorizado(self):
        with self.assertRaises(ValueError) as ctx:
            executar_carga("etl/saida/morcegos", banco="pibit_app")
        self.assertIn("exclusivamente contra o banco 'pibit_app_dev'", str(ctx.exception))

    def test_persistir_lote_mongodb_chama_upsert(self):
        mock_db = MagicMock()
        mock_db.animais.update_one = MagicMock()
        mock_db.amostras.update_one = MagicMock()
        mock_db.exames.update_one = MagicMock()

        cont_a, cont_am, cont_ex = persistir_lote_mongodb(
            [self.animal_valido], [self.amostra_valida], [self.exame_valido], mock_db
        )

        self.assertEqual(cont_a, 1)
        self.assertEqual(cont_am, 1)
        self.assertEqual(cont_ex, 1)

        mock_db.animais.update_one.assert_called_once_with(
            {"_id": 1}, {"$set": self.animal_valido}, upsert=True
        )
        mock_db.amostras.update_one.assert_called_once_with(
            {"_id": 1}, {"$set": self.amostra_valida}, upsert=True
        )
        mock_db.exames.update_one.assert_called_once_with(
            {"_id": 1}, {"$set": self.exame_valido}, upsert=True
        )

    def test_validar_documentos_legados_com_defaults_canonicamente(self):
        """Valida que documentos legados emitidos com valores sentinela/padrão pelo ETL são válidos."""
        animal_legado = {
            "animal_id": "LEG_001",
            "classe": "Mamífero",
            "nome_comum": "Bugio-preto",
            "nome_cientifico": "Alouatta caraya",
            "sexo": "Não Informado",
            "peso": "Não aferido",
            "faixa_etaria": "Não Informado",
            "orgao_origem": "NAO INFORMADO",
            "local_origem": "Não informado",
            "regime_vida": "Não informado",
            "status_vital": "Não Informado",
        }
        amostra_legada = {
            "amostra_id": "LEG_AMS_01",
            "animal_id": "LEG_001",
            "material_biologico": "Outro",
            "status_amostra": "Disponível",
            "local_coleta_amostra": "Não informado",
        }

        animais, amostras, exames, erros = validar_documentos([animal_legado], [amostra_legada], [])
        self.assertEqual(len(animais), 1)
        self.assertEqual(len(amostras), 1)
        self.assertEqual(len(erros), 0)


if __name__ == "__main__":
    unittest.main()
