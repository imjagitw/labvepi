import unittest
import sys
from pathlib import Path
from datetime import date
from pydantic import ValidationError

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
            "sexo": "Macho",
            "peso": 4.5,
            "faixa_etaria": "Adulto",
            "orgao": "UFPI",
            "local_origem": "Teresina",
            "status": "Vida livre",
            "status_vital": "Vivo",
        })

        self.service = AmostraService(
            amostra_repo=self.amostra_repo,
            animal_service=self.animal_service,
        )

    def _dados_completos(self, **sobrescrever):
        dados = {
            "amostra_id": "AMS001",
            "animal_id": "AN001",
            "data_coleta": date.today(),
            "material_biologico": MaterialBiologico.SORO,
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "status_amostra": StatusAmostra.DISPONIVEL,
            "laudo_liberado": False,
            "local_coleta": "Teresina - Parque Zoobotânico",
            "nome_coletor": "Pesquisador LABVEPI",
            "condicao_armazenamento": CondicaoArmazenamento.CONGELADA,
            "fase_amostra": FaseAmostra.EXTRACAO,
            "destino_amostra": DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI,
            "caixa": "Caixa 01 - Freezer -80",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        }
        dados.update(sobrescrever)
        return {k: v for k, v in dados.items() if v is not ...}

    def test_criar_amostra_sucesso(self):
        """Testa criação bem sucedida de amostra com validação estrita de campos."""
        dados = self._dados_completos()
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
            self.service.criar_amostra(self._dados_completos(amostra_id=""))

        self.service.criar_amostra(self._dados_completos(amostra_id="AMS_DUP"))
        with self.assertRaises(ValueError):
            self.service.criar_amostra(self._dados_completos(amostra_id="AMS_DUP"))

    def test_validacao_animal_e_confirmacao_novo_animal(self):
        """Testa validação do vínculo com o animal de origem e a flag confirmar_novo_animal."""
        # Animal inexistente sem flag de confirmação deve falhar
        with self.assertRaises(ValueError):
            self.service.criar_amostra(
                self._dados_completos(amostra_id="AMS_ANM_NOVO", animal_id="AN_INEXISTENTE"),
                confirmar_novo_animal=False,
            )

        # Animal inexistente com flag de confirmação deve ser aceito
        amostra = self.service.criar_amostra(
            self._dados_completos(amostra_id="AMS_ANM_NOVO", animal_id="AN_INEXISTENTE"),
            confirmar_novo_animal=True,
        )
        self.assertEqual(amostra.animal_id, "AN_INEXISTENTE")

    def test_rejeitar_campo_obrigatorio_ausente_ou_nao_informado(self):
        """Testa que novos cadastros exigem todos os campos obrigatórios preenchidos."""
        casos = {
            "local_coleta": [..., "", "   ", "Não informado", None],
            "nome_coletor": [..., "", "   ", "Não informado", None],
            "kit_utilizado": [..., "", "   ", "Não informado", None],
            "caixa": [..., "", "   ", "Não informado", None],
            "condicao_armazenamento": [..., "", "Não informado", None],
            "fase_amostra": [..., "", "Não informado", None],
            "destino_amostra": [..., "", "Não informado", None],
            "status_amostra": [..., "", "Não informado", None],
            "material_biologico": [..., "", "Não informado", None],
            "data_coleta": [..., "", "Não informado", None, "data_invalida"],
            "dna_disponivel": [..., None, "Não informado", "indefinido"],
            "rna_disponivel": [..., None, "Não informado"],
            "sequenciamento": [..., None, "Não informado"],
            "laudo_liberado": [..., None, "Não informado"],
        }
        for campo, valores in casos.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaises(ValueError):
                        self.service.criar_amostra(self._dados_completos(**{campo: valor}))
        self.assertEqual(self.amostra_repo.count(), 0)

    def test_amostra_create_schema_estrito(self):
        """Garante que AmostraCreate rejeita payloads sem os campos obrigatórios."""
        with self.assertRaises(ValidationError):
            AmostraCreate(amostra_id="AMS_DTO", animal="AN001")

        dto = AmostraCreate(**self._dados_completos(amostra_id="AMS_DTO_OK"))
        amostra = self.service.criar_amostra(dto)
        self.assertEqual(amostra.amostra_id, "AMS_DTO_OK")

    def test_update_parcial_rejeita_obrigatorio_vazio(self):
        """Update parcial: campos enviados são validados estritamente."""
        self.service.criar_amostra(
            self._dados_completos(amostra_id="LEG_AMS_02")
        )

        # Atualização parcial válida
        atualizada = self.service.atualizar_amostra("LEG_AMS_02", {"kit_utilizado": "Novo Kit PCR"})
        self.assertEqual(atualizada.kit_utilizado, "Novo Kit PCR")

        # Rejeição de atualização de campo obrigatório para vazio ou não informado
        with self.assertRaises(ValueError):
            self.service.atualizar_amostra("LEG_AMS_02", {"kit_utilizado": ""})
        with self.assertRaises(ValueError):
            self.service.atualizar_amostra("LEG_AMS_02", {"local_coleta": "Não informado"})
        with self.assertRaises(ValueError):
            self.service.atualizar_amostra(
                "LEG_AMS_02", AmostraUpdate(local_coleta="Não informado")
            )

    def test_obter_amostra_detalhes(self):
        """Testa geração de AmostraDetails com preenchimento de campos não informados e vínculo com Animal."""
        self.service.criar_amostra(
            self._dados_completos(
                amostra_id="AMS_DETALHES",
                animal_id="AN001",
                material_biologico=MaterialBiologico.SWAB_CLOACAL,
            )
        )

        detalhes = self.service.obter_amostra_detalhes("AMS_DETALHES")
        self.assertIsInstance(detalhes, AmostraDetails)
        self.assertEqual(detalhes.amostra_id, "AMS_DETALHES")
        self.assertEqual(detalhes.material_biologico, MaterialBiologico.SWAB_CLOACAL)
        self.assertIsNotNone(detalhes.animal)
        self.assertEqual(detalhes.animal.animal_id, "AN001")
        self.assertEqual(detalhes.quantidade_exames, 0)
        self.assertEqual(detalhes.exames, [])

        # Testa preenchimento automático para dicionários com campos omitidos
        dados_parciais = {
            "amostra_id": "AMS_PART",
            "animal_id": "AN001",
            "material_biologico": "swab cloacal",
        }
        detalhes_parc = AmostraService.preencher_nao_informados_e_relacionamentos(dados_parciais)
        self.assertEqual(detalhes_parc.local_coleta_amostra, "Não informado")
        self.assertEqual(detalhes_parc.nome_coletor, "Não informado")
        self.assertEqual(detalhes_parc.condicao_armazenamento, "Não informado")
        self.assertEqual(detalhes_parc.caixa_armazenamento, "Não informado")


class TestAmostraController(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_fluxo_api_amostras(self):
        """Testa requisições HTTP RESTful no endpoint /amostra/."""
        # 1. Cadastro de amostra estrita via API
        payload = {
            "amostra_id": "API_AMS01",
            "animal": "AN001",
            "data_coleta": "2026-10-17",
            "material_biologico": "Soro",
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "status_amostra": "Disponível",
            "laudo_liberado": False,
            "local_coleta": "Teresina",
            "nome_coletor": "Dr. Coletor",
            "condicao_armazenamento": "Congelada",
            "fase_amostra": "Extração",
            "destino_amostra": "Biobanco UFPI",
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
            "confirmar_novo_animal": True,
        }
        res_post = self.client.post("/amostra/", json=payload)
        self.assertEqual(res_post.status_code, 201)

        data = res_post.json()
        self.assertEqual(data["amostra_id"], "API_AMS01")

        # 2. Obter por ID
        res_get = self.client.get("/amostra/API_AMS01")
        self.assertEqual(res_get.status_code, 200)

        # 3. Obter detalhes
        res_det = self.client.get("/amostra/API_AMS01/detalhes")
        self.assertEqual(res_det.status_code, 200)
        self.assertEqual(res_det.json()["amostra_id"], "API_AMS01")
        self.assertEqual(res_det.json()["_id"], 1)

        # 4. Listar
        res_list = self.client.get("/amostra/")
        self.assertEqual(res_list.status_code, 200)
        self.assertIsInstance(res_list.json(), list)

        # 5. Contagem
        res_count = self.client.get("/amostra/contagem")
        self.assertEqual(res_count.status_code, 200)
        self.assertIn("total", res_count.json())

        # 6. Atualização
        res_patch = self.client.patch("/amostra/API_AMS01", json={"observacoes": "Atualizado via API"})
        self.assertEqual(res_patch.status_code, 200)

        # 7. Exclusão
        res_del = self.client.delete("/amostra/API_AMS01")
        self.assertEqual(res_del.status_code, 204)


if __name__ == "__main__":
    unittest.main()
