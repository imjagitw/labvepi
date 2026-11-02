import unittest
from fastapi.testclient import TestClient
from src.main import app

class TestCentralizedControllers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_animal_controller_not_found_returns_404(self):
        res = self.client.get("/animal/ANIMAL_INEXISTENTE_999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())
        self.assertIn("não encontrado", res.json()["detail"].lower())

    def test_animal_controller_confirmacao_necessaria_returns_409(self):
        # Enviar animal com espécie inédita sem confirmar nova espécie retorna 409 Conflict estruturado
        payload = {
            "animal_id": "ANI_ERR_01",
            "nome_comum": "Animal Inédito Desconhecido",
            "nome_cientifico": "Alienigena ficticius",
            "classe": "Mamífero",
            "sexo": "Macho",
            "orgao": "UFPI",
            "local_origem": "Teresina/PI",
            "status": "Vida livre",
            "status_vital": "Vivo",
            "faixa_etaria": "Adulto",
            "peso": 2.5,
        }
        res = self.client.post("/animal/?confirmar_nova_especie=false", json=payload)
        self.assertEqual(res.status_code, 409)
        self.assertIn("detail", res.json())
        detail = res.json()["detail"]
        self.assertEqual(detail["codigo"], "ESPECIE_NAO_ENCONTRADA")
        self.assertEqual(detail["confirmacao"], "confirmar_nova_especie")

    def test_especie_controller_not_found_returns_404(self):
        res = self.client.get("/especie/999999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_especie_controller_file_not_found_returns_404(self):
        res = self.client.post("/especie/importar-catalogo?caminho_arquivo=/arquivo_inexistente_12345.csv")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_amostra_controller_not_found_returns_404(self):
        res = self.client.get("/amostra/AMO_INEXISTENTE_999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_exame_controller_not_found_returns_404(self):
        res = self.client.get("/exame/EXA_INEXISTENTE_999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_reagente_controller_not_found_returns_404(self):
        res = self.client.get("/reagente/REA_INEXISTENTE_999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_estoque_reagente_controller_not_found_returns_404(self):
        res = self.client.get("/estoque_reagente/EST_INEXISTENTE_999999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("detail", res.json())

    def test_permission_error_returns_403(self):
        from unittest.mock import patch
        with patch("src.controllers.animal_controller.animal_service.deletar_animal", side_effect=PermissionError("Ação não permitida para o usuário atual.")):
            res = self.client.delete("/animal/ANI_QUALQUER")
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json(), {"detail": "Ação não permitida para o usuário atual."})

    def test_no_content_error_returns_204(self):
        from unittest.mock import patch
        from src.controllers.response_controller import NoContentError
        with patch("src.controllers.animal_controller.animal_service.deletar_animal", side_effect=NoContentError()):
            res = self.client.delete("/animal/ANI_QUALQUER")
            self.assertEqual(res.status_code, 204)
            self.assertEqual(res.content, b"")

    def test_animal_controller_crud_flow(self):
        # 1. Criar espécie e animal
        payload_animal = {
            "animal_id": "ANI_CENTRAL_01",
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": "Mamífero",
            "sexo": "Macho",
            "orgao": "UFPI",
            "local_origem": "Teresina/PI",
            "status": "Vida livre",
            "status_vital": "Vivo",
            "faixa_etaria": "Adulto",
            "peso": 30.0,
        }
        res_post = self.client.post("/animal/?confirmar_nova_especie=true", json=payload_animal)
        self.assertEqual(res_post.status_code, 201)

        # 2. Obter animal
        res_get = self.client.get("/animal/ANI_CENTRAL_01")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["animal_id"], "ANI_CENTRAL_01")

        # 3. Obter detalhes
        res_det = self.client.get("/animal/ANI_CENTRAL_01/detalhes")
        self.assertEqual(res_det.status_code, 200)

        # 4. Atualizar animal
        res_put = self.client.put(
            "/animal/ANI_CENTRAL_01",
            json={"animal_id": "ANI_CENTRAL_01", "peso": 32.5, "sexo": "Macho"},
        )
        self.assertEqual(res_put.status_code, 200)

        # 5. Listar animais
        res_list = self.client.get("/animal/?termo_busca=Desmodus")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # 6. Deletar animal
        res_del = self.client.delete("/animal/ANI_CENTRAL_01")
        self.assertEqual(res_del.status_code, 204)
        self.assertEqual(res_del.content, b"")

    def test_especie_controller_crud_flow(self):
        # 1. Cadastrar espécie
        payload_especie = {
            "nome_comum": "Gavião-real",
            "nome_cientifico": "Harpia harpyja",
            "classe": "Ave",
        }
        res_post = self.client.post("/especie/cadastro", json=payload_especie)
        self.assertEqual(res_post.status_code, 201)
        esp_id = res_post.json().get("id") or res_post.json().get("_id")

        # 2. Obter detalhes da espécie
        res_det = self.client.get(f"/especie/{esp_id}")
        self.assertEqual(res_det.status_code, 200)
        nome_det = res_det.json().get("nome_comum") or res_det.json().get("nome")
        self.assertEqual(nome_det, "Gavião-real")

        # 3. Listar espécies com filtro
        res_list = self.client.get("/especie/?classe=Ave")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # 4. Atualizar espécie
        res_put = self.client.put(
            f"/especie/{esp_id}",
            json={
                "nome_comum": "Harpia",
                "nome_cientifico": "Harpia harpyja",
                "classe": "Ave",
            },
        )
        self.assertEqual(res_put.status_code, 200)
        nome_put = res_put.json().get("nome_comum") or res_put.json().get("nome")
        self.assertEqual(nome_put, "Harpia")

        # 5. Deletar espécie
        res_del = self.client.delete(f"/especie/{esp_id}")
        self.assertEqual(res_del.status_code, 204)
        self.assertEqual(res_del.content, b"")

    def test_amostra_controller_crud_flow(self):
        # Limpa registros remanescentes de testes anteriores
        self.client.delete("/amostra/AMO_CENTRAL_01")
        self.client.delete("/animal/ANI_AMO_01")

        # Garante animal existente
        self.client.post(
            "/animal/?confirmar_nova_especie=true",
            json={
                "animal_id": "ANI_AMO_01",
                "nome_comum": "Bugio-preto",
                "nome_cientifico": "Alouatta caraya",
                "classe": "Mamífero",
                "sexo": "Fêmea",
                "orgao": "UFPI",
                "local_origem": "Teresina/PI",
                "status": "Vida livre",
                "status_vital": "Vivo",
                "faixa_etaria": "Adulto",
                "peso": 4.2,
            },
        )

        payload_amostra = {
            "amostra_id": "AMO_CENTRAL_01",
            "animal_id": "ANI_AMO_01",
            "data_coleta": "2026-05-10",
            "material_biologico": "Soro",
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "status_amostra": "Disponível",
            "laudo_liberado": False,
            "local_coleta": "Teresina - Zoobotânico",
            "nome_coletor": "Pesquisador LABVEPI",
            "condicao_armazenamento": "Congelada",
            "fase_amostra": "Extração",
            "destino_amostra": "LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI",
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        }

        # 1. Criar amostra
        res_post = self.client.post("/amostra/", json=payload_amostra)
        self.assertEqual(res_post.status_code, 201)

        # 2. Obter amostra
        res_get = self.client.get("/amostra/AMO_CENTRAL_01")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["amostra_id"], "AMO_CENTRAL_01")

        # 3. Obter detalhes da amostra
        res_det = self.client.get("/amostra/AMO_CENTRAL_01/detalhes")
        self.assertEqual(res_det.status_code, 200)

        # 4. Listar amostras por animal
        res_ani = self.client.get("/amostra/animal/ANI_AMO_01")
        self.assertEqual(res_ani.status_code, 200)
        self.assertGreaterEqual(len(res_ani.json()), 1)

        # 5. Atualizar amostra
        res_patch = self.client.patch(
            "/amostra/AMO_CENTRAL_01",
            json={"amostra_id": "AMO_CENTRAL_01", "caixa": "Caixa 02 - Freezer -80"},
        )
        self.assertEqual(res_patch.status_code, 200)

        # 6. Deletar amostra
        res_del = self.client.delete("/amostra/AMO_CENTRAL_01")
        self.assertEqual(res_del.status_code, 204)

    def test_exame_controller_crud_flow(self):
        # 1. Criar amostra para associar ao exame
        self.client.post(
            "/animal/?confirmar_nova_especie=true",
            json={
                "animal_id": "ANI_EXA_01",
                "nome_comum": "Bugio-preto",
                "nome_cientifico": "Alouatta caraya",
                "classe": "Mamífero",
                "sexo": "Macho",
                "orgao": "UFPI",
                "local_origem": "Teresina/PI",
                "status": "Vida livre",
                "status_vital": "Vivo",
                "faixa_etaria": "Adulto",
                "peso": 4.5,
            },
        )
        self.client.post(
            "/amostra/",
            json={
                "amostra_id": "AMO_EXA_01",
                "animal_id": "ANI_EXA_01",
                "data_coleta": "2026-05-10",
                "material_biologico": "Soro",
                "kit_utilizado": "QIAamp Viral RNA Mini Kit",
                "status_amostra": "Disponível",
                "laudo_liberado": False,
                "local_coleta": "Teresina",
                "nome_coletor": "Pesquisador",
                "condicao_armazenamento": "Congelada",
                "fase_amostra": "Extração",
                "destino_amostra": "LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI",
                "caixa": "Caixa 01",
                "dna_disponivel": True,
                "rna_disponivel": False,
                "sequenciamento": False,
            },
        )

        payload_exame = {
            "id": 999999,
            "_id": "EX_FAKE_PK",
            "amostra_id": "AMO_EXA_01",
            "tipo_exame": "Raiva",
            "resultado": "Negativo",
            "teste_laboratorial": "PCR",
            "data_realizacao": "2026-05-12",
            "responsavel_exame": "Dr. Silva",
            "kit_utilizado": "Kit PCR Raiva",
            "protocolo": "PRT-001",
        }

        # Criar exame
        res_post = self.client.post("/exame/", json=payload_exame)
        self.assertEqual(res_post.status_code, 201)
        exame_criado = res_post.json()
        pk_criado = exame_criado.get("id") or exame_criado.get("_id")
        self.assertNotEqual(pk_criado, 999999)
        self.assertNotEqual(exame_criado.get("exame_id"), "EX_FAKE_PK")
        exame_id = exame_criado.get("exame_id") or pk_criado

        # Obter exame
        res_get = self.client.get(f"/exame/{exame_id}")
        self.assertEqual(res_get.status_code, 200)

        # Obter detalhes
        res_det = self.client.get(f"/exame/{exame_id}/detalhes")
        self.assertEqual(res_det.status_code, 200)

        # Contagem
        res_count = self.client.get("/exame/contagem")
        self.assertEqual(res_count.status_code, 200)
        self.assertIn("total", res_count.json())

        # Listar por amostra
        res_list = self.client.get("/exame/amostra/AMO_EXA_01")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # Atualizar exame
        res_put = self.client.put(
            f"/exame/{exame_id}",
            json={
                "amostra_id": "AMO_EXA_01",
                "tipo_exame": "Raiva",
                "resultado": "Positivo",
                "teste_laboratorial": "PCR",
            },
        )
        self.assertEqual(res_put.status_code, 200)

        # Deletar exame
        res_del = self.client.delete(f"/exame/{exame_id}")
        self.assertEqual(res_del.status_code, 204)


if __name__ == "__main__":
    unittest.main()