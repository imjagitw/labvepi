import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.main import app
from src.repositories.amostra_repository import amostra_repository
from src.repositories.animal_repository import animal_repository
from src.repositories.especie_repository import especie_repository
from src.repositories.exame_repository import exame_repository
from src.repositories.reagente_repository import reagente_repository
from src.repositories.estoque_reagente_repository import estoque_reagente_repository
from src.repositories.usuario_repository import usuario_repository


class TestPartialUpdates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        amostra_repository.clear()
        animal_repository.clear()
        especie_repository.clear()
        exame_repository.clear()
        reagente_repository.clear()
        estoque_reagente_repository.clear()
        usuario_repository.clear()

    def test_animal_partial_update_single_field(self):
        # 1. Cria animal completo
        payload_create = {
            "animal_id": "ANI_PART_01",
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": "Mamífero",
            "sexo": "Macho",
            "peso": 35.0,
            "faixa_etaria": "Adulto",
            "orgao": "UFPI",
            "local_origem": "Teresina/PI",
            "status": "Vida livre",
            "status_vital": "Vivo",
            "microchip": "CHIP-111",
            "observacoes": "Capturado em campo",
        }
        res_create = self.client.post("/animal/?confirmar_nova_especie=true", json=payload_create)
        self.assertEqual(res_create.status_code, 201)

        # 2. Atualiza via PATCH alterando APENAS o microchip
        res_patch = self.client.patch("/animal/ANI_PART_01", json={"microchip": "CHIP-999"})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data["microchip"], "CHIP-999")
        # Todos os outros campos devem permanecer inalterados
        self.assertEqual(data["sexo"], "Macho")
        self.assertEqual(data["nome_comum"], "Morcego-vampiro")
        self.assertEqual(data["nome_cientifico"], "Desmodus rotundus")
        self.assertEqual(data["status_vital"], "Vivo")
        obs_val = data.get("observacoes") or data.get("animal_observacoes")
        self.assertEqual(obs_val, "Capturado em campo")

        # 3. Atualiza via PUT alterando APENAS observacoes
        res_put = self.client.put("/animal/ANI_PART_01", json={"observacoes": "Nova observacao atualizada"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        self.assertEqual(data_put["microchip"], "CHIP-999")
        obs_put = data_put.get("observacoes") or data_put.get("animal_observacoes")
        self.assertEqual(obs_put, "Nova observacao atualizada")
        self.assertEqual(data_put["sexo"], "Macho")

    def test_amostra_partial_update_single_field(self):
        # 1. Animal base
        self.client.post("/animal/?confirmar_nova_especie=true", json={
            "animal_id": "ANI_AMO_01",
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": "Mamífero",
            "sexo": "Macho",
            "peso": 30.0,
            "faixa_etaria": "Adulto",
            "orgao": "UFPI",
            "local_origem": "Teresina/PI",
            "status": "Vida livre",
            "status_vital": "Vivo",
        })

        # 2. Amostra
        res_create = self.client.post("/amostra/", json={
            "amostra_id": "AMO_PART_01",
            "animal_id": "ANI_AMO_01",
            "data_coleta": "2026-03-10",
            "data_recebimento": "2026-03-12",
            "material_biologico": "Soro",
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "status_amostra": "Disponível",
            "laudo_liberado": False,
            "local_coleta": "Zoobotânico",
            "nome_coletor": "Dr. Silva",
            "condicao_armazenamento": "Congelada",
            "fase_amostra": "Extração",
            "destino_amostra": "LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI",
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        })
        self.assertEqual(res_create.status_code, 201)

        # 3. Atualiza via PATCH alterando APENAS laudo_liberado
        res_patch = self.client.patch("/amostra/AMO_PART_01", json={"laudo_liberado": True})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertTrue(data["laudo_liberado"])
        mat_val = data.get("material_biologico") or data.get("metodo_coleta")
        self.assertEqual(mat_val, "Soro")
        self.assertEqual(data["nome_coletor"], "Dr. Silva")
        self.assertEqual(data["animal_id"], "ANI_AMO_01")

        # 4. Atualiza via PUT alterando APENAS nome_coletor
        res_put = self.client.put("/amostra/AMO_PART_01", json={"nome_coletor": "Dra. Santos"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        self.assertTrue(data_put["laudo_liberado"])
        self.assertEqual(data_put["nome_coletor"], "Dra. Santos")
        mat_put = data_put.get("material_biologico") or data_put.get("metodo_coleta")
        self.assertEqual(mat_put, "Soro")

    def test_especie_partial_update_single_field(self):
        res_create = self.client.post("/especie/cadastro", json={
            "nome_comum": "Morcego Falso",
            "nome_cientifico": "Artibeus lituratus",
            "classe": "Ave",
        })
        self.assertEqual(res_create.status_code, 201)
        esp_id = res_create.json().get("id") or res_create.json().get("_id")

        # Atualiza apenas o nome_comum via PATCH
        res_patch = self.client.patch(f"/especie/{esp_id}", json={"nome_comum": "Morcego das Frutas"})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data.get("nome_comum") or data.get("nome"), "Morcego das Frutas")
        self.assertEqual(data["nome_cientifico"], "Artibeus lituratus")

        # Atualiza apenas o nome_comum via PUT
        res_put = self.client.put(f"/especie/{esp_id}", json={"nome_comum": "Morcego Frugívoro Grande"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        self.assertEqual(data_put.get("nome_comum") or data_put.get("nome"), "Morcego Frugívoro Grande")
        self.assertEqual(data_put["nome_cientifico"], "Artibeus lituratus")

    def test_exame_partial_update_single_field(self):
        # 1. Animal e amostra base
        self.client.post("/animal/?confirmar_nova_especie=true", json={
            "animal_id": "ANI_EX_01",
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": "Mamífero",
            "sexo": "Macho",
            "peso": 30.0,
            "faixa_etaria": "Adulto",
            "orgao": "UFPI",
            "local_origem": "Teresina/PI",
            "status": "Vida livre",
            "status_vital": "Vivo",
        })
        self.client.post("/amostra/", json={
            "amostra_id": "AMO_EX_01",
            "animal_id": "ANI_EX_01",
            "data_coleta": "2026-03-10",
            "data_recebimento": "2026-03-12",
            "material_biologico": "Soro",
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "status_amostra": "Disponível",
            "laudo_liberado": False,
            "local_coleta": "Zoobotânico",
            "nome_coletor": "Dr. Silva",
            "condicao_armazenamento": "Congelada",
            "fase_amostra": "Extração",
            "destino_amostra": "LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI",
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        })

        # 2. Exame
        res_create = self.client.post("/exame/", json={
            "amostra_id": "AMO_EX_01",
            "tipo_exame": "Raiva",
            "resultado": "Negativo",
            "teste_laboratorial": "PCR",
            "data_realizacao": "2026-03-15",
            "responsavel_exame": "Dra. Ana",
            "observacoes": "Sem amplificação",
        })
        self.assertEqual(res_create.status_code, 201)
        exame_id = res_create.json().get("id") or res_create.json().get("_id")

        # 3. Atualiza via PATCH alterando APENAS resultado
        res_patch = self.client.patch(f"/exame/{exame_id}", json={"resultado": "Positivo"})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        res_val = data.get("resultado") or data.get("resultado_detalhado")
        self.assertEqual(res_val, "Positivo")
        self.assertEqual(data["tipo_exame"], "Raiva")
        self.assertEqual(data["teste_laboratorial"], "PCR")
        self.assertEqual(data["responsavel_exame"], "Dra. Ana")
        obs_val = data.get("observacoes") or data.get("exame_observacoes")
        self.assertEqual(obs_val, "Sem amplificação")

        # 4. Atualiza via PUT alterando APENAS responsavel_exame
        res_put = self.client.put(f"/exame/{exame_id}", json={"responsavel_exame": "Dr. Carlos"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        res_put_val = data_put.get("resultado") or data_put.get("resultado_detalhado")
        self.assertEqual(res_put_val, "Positivo")
        self.assertEqual(data_put["responsavel_exame"], "Dr. Carlos")

    def test_reagente_partial_update_single_field(self):
        res_create = self.client.post("/reagente/", json={
            "reagente_nome": "Água Nuclease-Free",
            "reagente_codigo": "H2O-NF",
            "numero_lote": "LOT-001",
            "marca": "Thermo",
            "data_validade": "2027-12-31",
            "quantidade_unidade": 10,
            "quantidade_volume": 50.0,
            "unidade": "ml",
            "local_armazenamento": "Freezer -20",
        })
        self.assertEqual(res_create.status_code, 201)
        data_c = res_create.json()
        r_id = data_c.get("id") or data_c.get("_id")

        # Atualiza apenas quantidade_unidade via PATCH
        res_patch = self.client.patch(f"/reagente/{r_id}", json={"quantidade_unidade": 8})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data["quantidade_unidade"], 8)
        nome_val = data.get("nome") or data.get("reagente_nome")
        self.assertEqual(nome_val, "Água Nuclease-Free")
        self.assertEqual(data["marca"], "Thermo")
        loc_val = data.get("local_armazenamento") or data.get("reagente_local_armazenamento")
        self.assertEqual(loc_val, "Freezer -20")

        # Atualiza apenas local_armazenamento via PUT
        res_put = self.client.put(f"/reagente/{r_id}", json={"local_armazenamento": "Geladeira 4C"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        self.assertEqual(data_put["quantidade_unidade"], 8)
        loc_put = data_put.get("local_armazenamento") or data_put.get("reagente_local_armazenamento")
        self.assertEqual(loc_put, "Geladeira 4C")

    def test_estoque_reagente_partial_update_single_field(self):
        res_create = self.client.post("/estoque_reagente/", json={
            "reagente_nome": "Primer Raiva Forward",
            "reagente_codigo": "PRI-01",
        })
        self.assertEqual(res_create.status_code, 201)
        data_c = res_create.json()
        est_id = data_c.get("id") or data_c.get("_id")

        # Atualiza apenas reagente_codigo via PATCH
        res_patch = self.client.patch(f"/estoque_reagente/{est_id}", json={"reagente_codigo": "PRI-01-REV"})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        cod_val = data.get("codigo") or data.get("reagente_codigo")
        self.assertEqual(cod_val, "PRI-01-REV")
        nome_val = data.get("nome") or data.get("reagente_nome")
        self.assertEqual(nome_val, "Primer Raiva Forward")

        # Atualiza apenas reagente_codigo via PUT
        res_put = self.client.put(f"/estoque_reagente/{est_id}", json={"reagente_codigo": "PRI-01-FINAL"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        cod_put = data_put.get("codigo") or data_put.get("reagente_codigo")
        self.assertEqual(cod_put, "PRI-01-FINAL")
        nome_put = data_put.get("nome") or data_put.get("reagente_nome")
        self.assertEqual(nome_put, "Primer Raiva Forward")

    def test_usuario_partial_update_single_field(self):
        res_create = self.client.post("/usuario/", json={
            "usuario": "pesquisador1",
            "nome": "Pesquisador Silva",
            "email": "pesq@labvepi.ufv.br",
            "senha": "senhaSegura123",
            "perfil": "docente",
            "matricula": "12345",
        })
        self.assertEqual(res_create.status_code, 201)

        # Atualiza apenas matricula via PATCH
        res_patch = self.client.patch("/usuario/pesquisador1", json={"matricula": "99999"})
        self.assertEqual(res_patch.status_code, 200)
        data = res_patch.json()
        self.assertEqual(data["matricula"], "99999")
        nome_val = data.get("nome") or data.get("name")
        self.assertEqual(nome_val, "Pesquisador Silva")
        self.assertEqual(data["email"], "pesq@labvepi.ufv.br")
        self.assertEqual(data["perfil"], "docente")

        # Atualiza apenas nome via PUT
        res_put = self.client.put("/usuario/pesquisador1", json={"nome": "Pesquisador Silva Junior"})
        self.assertEqual(res_put.status_code, 200)
        data_put = res_put.json()
        nome_put = data_put.get("nome") or data_put.get("name")
        self.assertEqual(nome_put, "Pesquisador Silva Junior")
        self.assertEqual(data_put["matricula"], "99999")
        self.assertEqual(data_put["email"], "pesq@labvepi.ufv.br")


if __name__ == "__main__":
    unittest.main()
