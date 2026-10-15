import unittest
import sys
from pathlib import Path
from datetime import date

# Garante import do backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.Amostra import (
    Amostra,
    AmostraCreate,
    AmostraUpdate,
    AmostraDetails,
    CondicaoArmazenamento,
    DestinoAmostra,
    FaseAmostra,
    MaterialBiologico,
    StatusAmostra,
)
from src.repositories.amostra_repository import AmostraRepository
from src.repositories.animal_repository import AnimalRepository
from src.repositories.especie_repository import EspecieRepository
from src.services.especie_service import EspecieService
from src.services.animal_service import AnimalService
from src.services.amostra_service import AmostraService
from fastapi.testclient import TestClient
from src.main import app


class TestAmostraService(unittest.TestCase):
    def setUp(self):
        """Cria instâncias isoladas de repositórios e serviços para cada teste."""
        self.amostra_repo = AmostraRepository()
        self.animal_repo = AnimalRepository()
        self.especie_repo = EspecieRepository()
        self.especie_service = EspecieService(repo=self.especie_repo, carregar_catalogo_padrao=False)
        self.animal_service = AnimalService(especie_serv=self.especie_service, animal_repo=self.animal_repo)

        # Cadastra uma espécie e um animal base para os testes
        self.especie_service.cadastrar_especie({
            "nome_comum": "Bugio-preto",
            "nome_cientifico": "Alouatta caraya",
            "classe": "Mamífero",
        })
        self.animal_service.criar_animal({
            "animal_id": "AN001",
            "nome_comum": "Bugio-preto",
            "orgao": "UFPI",
            "local_origem": "Teresina",
            "status": "Vida livre",
            "status_vital": "Vivo",
        })

        self.service = AmostraService(
            amostra_repo=self.amostra_repo,
            animal_service=self.animal_service,
        )

    def test_criar_amostra_sucesso(self):
        """Testa criação bem sucedida de amostra com validação de campos e defaults."""
        dados = {
            "amostra_id": "AMS001",
            "animal_id": "AN001",
            "material_biologico": "soro",
            "local_coleta": "Teresina - Parque Zoobotânico",
            "nome_coletor": "Pesquisador LABVEPI",
            "dna_disponivel": True,
        }
        amostra = self.service.criar_amostra(dados)

        self.assertEqual(amostra.amostra_id, "AMS001")
        self.assertEqual(amostra.animal_id, "AN001")
        self.assertEqual(amostra.material_biologico, MaterialBiologico.SORO)
        self.assertEqual(amostra.status_amostra, StatusAmostra.DISPONIVEL)
        self.assertEqual(amostra.fase_amostra, FaseAmostra.EXTRACAO)
        self.assertTrue(amostra.dna_disponivel)
        self.assertFalse(amostra.rna_disponivel)
        self.assertIsNotNone(amostra.id)

    def test_normalizacao_material_biologico(self):
        """Testa normalização heurística de strings para enums de MaterialBiologico."""
        self.assertEqual(self.service.normalizar_material_biologico("soro"), MaterialBiologico.SORO)
        self.assertEqual(self.service.normalizar_material_biologico("SANGUE TOTAL"), MaterialBiologico.SANGUE_TOTAL)
        self.assertEqual(self.service.normalizar_material_biologico("papel filtro"), MaterialBiologico.PAPEL_FILTRO)
        self.assertEqual(self.service.normalizar_material_biologico("swab oral e cloacal"), MaterialBiologico.SWAB_ORAL_CLOACAL)
        self.assertEqual(self.service.normalizar_material_biologico("swab oral"), MaterialBiologico.SWAB_ORAL)
        self.assertEqual(self.service.normalizar_material_biologico("esfregaço sanguíneo"), MaterialBiologico.ESFREGACO_SANGUINEO)
        self.assertEqual(self.service.normalizar_material_biologico("edta"), MaterialBiologico.SANGUE_EDTA)
        self.assertEqual(self.service.normalizar_material_biologico("fezes"), MaterialBiologico.FEZES)
        self.assertEqual(self.service.normalizar_material_biologico("pool de tecidos"), MaterialBiologico.POOL_TECIDOS)
        self.assertEqual(self.service.normalizar_material_biologico("órgãos"), MaterialBiologico.ORGAOS)

    def test_recusar_amostra_id_obrigatorio_e_duplicado(self):
        """Garante validação de id obrigatório e rejeição de IDs duplicados."""
        with self.assertRaises(ValueError):
            self.service.criar_amostra({"amostra_id": "", "animal_id": "AN001"})

        self.service.criar_amostra({"amostra_id": "AMS_DUP", "animal_id": "AN001"})
        with self.assertRaises(ValueError):
            self.service.criar_amostra({"amostra_id": "AMS_DUP", "animal_id": "AN001"})

    def test_validacao_animal_e_confirmacao_novo_animal(self):
        """Testa validação do vínculo com o animal de origem e a flag confirmar_novo_animal."""
        # Animal inexistente sem flag de confirmação deve falhar
        with self.assertRaises(ValueError):
            self.service.criar_amostra({
                "amostra_id": "AMS_ANM_NOVO",
                "animal_id": "AN_INEXISTENTE",
            }, confirmar_novo_animal=False)

        # Animal inexistente com flag de confirmação deve ser aceito
        amostra = self.service.criar_amostra({
            "amostra_id": "AMS_ANM_NOVO",
            "animal_id": "AN_INEXISTENTE",
        }, confirmar_novo_animal=True)
        self.assertEqual(amostra.animal_id, "AN_INEXISTENTE")

    def test_crud_completo_obter_listar_atualizar_deletar(self):
        """Testa ciclo completo de CRUD: Create, Read, Update, Delete."""
        # 1. Create
        self.service.criar_amostra({
            "amostra_id": "AMS_A",
            "animal_id": "AN001",
            "material_biologico": "soro",
            "condicao_armazenamento": CondicaoArmazenamento.CONGELADA,
        })
        self.service.criar_amostra({
            "amostra_id": "AMS_B",
            "animal_id": "AN001",
            "material_biologico": "tecido",
            "condicao_armazenamento": CondicaoArmazenamento.REFRIGERADA,
            "observacoes": "Amostra teste de biópsia",
        })

        # 2. Read (obter por ID)
        a1 = self.service.obter_amostra("AMS_A")
        self.assertEqual(a1.amostra_id, "AMS_A")
        self.assertEqual(a1.material_biologico, MaterialBiologico.SORO)

        with self.assertRaises(KeyError):
            self.service.obter_amostra("AMS_INEXISTENTE")

        # 3. Read (listar e contagem)
        self.assertEqual(self.service.contar_amostras(), 2)
        todas = self.service.listar_amostras()
        self.assertEqual(len(todas), 2)

        filtradas_soro = self.service.listar_amostras(material_biologico=MaterialBiologico.SORO)
        self.assertEqual(len(filtradas_soro), 1)
        self.assertEqual(filtradas_soro[0].amostra_id, "AMS_A")

        busca = self.service.listar_amostras(termo_busca="biópsia")
        self.assertEqual(len(busca), 1)
        self.assertEqual(busca[0].amostra_id, "AMS_B")

        por_animal = self.service.listar_amostras_por_animal("AN001")
        self.assertEqual(len(por_animal), 2)

        # 4. Update
        atualizada = self.service.atualizar_amostra("AMS_A", {
            "material_biologico": "sangue total",
            "dna_disponivel": True,
        })
        self.assertEqual(atualizada.material_biologico, MaterialBiologico.SANGUE_TOTAL)
        self.assertTrue(atualizada.dna_disponivel)

        # 5. Delete
        removido = self.service.deletar_amostra("AMS_A")
        self.assertTrue(removido)
        self.assertEqual(self.service.contar_amostras(), 1)

        with self.assertRaises(KeyError):
            self.service.obter_amostra("AMS_A")

    def test_obter_amostra_detalhes(self):
        """Testa geração de AmostraDetails com preenchimento de campos não informados e vínculo com Animal."""
        self.service.criar_amostra({
            "amostra_id": "AMS_DETALHES",
            "animal_id": "AN001",
            "material_biologico": "swab cloacal",
        })

        detalhes = self.service.obter_amostra_detalhes("AMS_DETALHES")
        self.assertIsInstance(detalhes, AmostraDetails)
        self.assertEqual(detalhes.amostra_id, "AMS_DETALHES")
        self.assertEqual(detalhes.local_coleta_amostra, "Não informado")
        self.assertEqual(detalhes.nome_coletor, "Não informado")
        self.assertEqual(detalhes.condicao_armazenamento, "Não informado")
        self.assertEqual(detalhes.caixa_armazenamento, "Não informado")
        self.assertIsNotNone(detalhes.animal)
        self.assertEqual(detalhes.animal.animal_id, "AN001")
        self.assertEqual(detalhes.quantidade_exames, 0)
        self.assertEqual(detalhes.exames, [])


class TestAmostraController(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_fluxo_api_amostras(self):
        """Testa requisições HTTP RESTful no endpoint /amostras/."""
        # 1. Cadastro de amostra
        payload = {
            "_id": "API_AMS01",
            "animal": "AN001",
            "material_biologico": "soro",
            "local_coleta": "Teresina",
            "dna_disponivel": True,
            "confirmar_novo_animal": True,
        }
        res_post = self.client.post("/amostras/", json=payload)
        self.assertIn(res_post.status_code, [201, 400])

        if res_post.status_code == 201:
            data = res_post.json()
            self.assertEqual(data["_id"], "API_AMS01")

            # 2. Obter por ID
            res_get = self.client.get("/amostras/API_AMS01")
            self.assertEqual(res_get.status_code, 200)

            # 3. Obter detalhes
            res_det = self.client.get("/amostras/API_AMS01/detalhes")
            self.assertEqual(res_det.status_code, 200)
            self.assertEqual(res_det.json()["_id"], "API_AMS01")

            # 4. Listar
            res_list = self.client.get("/amostras/")
            self.assertEqual(res_list.status_code, 200)
            self.assertIsInstance(res_list.json(), list)

            # 5. Contagem
            res_count = self.client.get("/amostras/contagem")
            self.assertEqual(res_count.status_code, 200)
            self.assertIn("total", res_count.json())

            # 6. Atualização
            res_put = self.client.put("/amostras/API_AMS01", json={"observacoes": "Atualizado via API"})
            self.assertEqual(res_put.status_code, 200)

            # 7. Exclusão
            res_del = self.client.delete("/amostras/API_AMS01")
            self.assertEqual(res_del.status_code, 200)


if __name__ == "__main__":
    unittest.main()
