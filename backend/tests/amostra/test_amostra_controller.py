"""
Testes de Integração HTTP para o Controller de Amostra — LABVEPI
===============================================================
Cobre todos os endpoints de /amostra/ utilizando ControllerTestCase:
- POST /amostra/ (Criação, bloqueio de PK, confirmação de novo animal, conflito de duplicidade)
- GET /amostra/ (Listagem, filtros analíticos e paginação)
- GET /amostra/contagem (Totalização do acervo)
- GET /amostra/animal/{animal_id} (Amostras de um animal específico)
- GET /amostra/{amostra_id} (Recuperação direta)
- GET /amostra/{amostra_id}/detalhes (Visão enriquecida AmostraDetails)
- PATCH / PUT /amostra/{amostra_id} (Atualização parcial e total)
- DELETE /amostra/{amostra_id} (Exclusão 204 No Content b"" e verificação 404)
"""

import unittest
from datetime import date
from tests.base_test_client import ControllerTestCase
from src.models.Amostra import (
    MaterialBiologico,
    StatusAmostra,
    CondicaoArmazenamento,
    FaseAmostra,
    DestinoAmostra,
)


class TestAmostraController(ControllerTestCase):
    """Suíte de testes de integração HTTP para as rotas /amostra."""

    def _payload_valido_amostra(self, **kwargs) -> dict:
        """Retorna payload completo em conformidade com o schema estrito AmostraCreate."""
        dados = {
            "amostra_id": "AMO_CTRL_001",
            "animal_id": "ANI_TEST_001",
            "data_coleta": str(date.today()),
            "data_recebimento": str(date.today()),
            "material_biologico": MaterialBiologico.SORO.value,
            "status_amostra": StatusAmostra.DISPONIVEL.value,
            "laudo_liberado": False,
            "local_coleta": "Teresina - Zoobotânico",
            "nome_coletor": "Pesquisador LABVEPI",
            "condicao_armazenamento": CondicaoArmazenamento.CONGELADA.value,
            "fase_amostra": FaseAmostra.EXTRACAO.value,
            "destino_amostra": DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI.value,
            "kit_utilizado": "QIAamp Viral RNA Mini Kit",
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        }
        dados.update(kwargs)
        return dados

    def test_criar_amostra_com_sucesso_e_bloqueio_pk(self):
        """POST /amostra/ com animal existente deve retornar 201 Created e ignorar fake PK."""
        animal = self.criar_animal_pre_requisito(animal_id="ANI_AMO_001")
        payload = self._payload_valido_amostra(
            amostra_id="AMO_CTRL_001",
            animal_id=animal.animal_id,
        )

        data = self.verificar_contrato_post_criacao(
            rota="/amostra/",
            payload_valido=payload,
            fake_pk_field="id",
            fake_pk_value=88888,
            expected_status=201,
        )
        self.assertEqual(data["amostra_id"], "AMO_CTRL_001")
        self.assertEqual(data["animal_id"], "ANI_AMO_001")

    def test_criar_amostra_animal_inexistente_exige_confirmacao(self):
        """POST /amostra/ com animal inexistente sem confirmar_novo_animal deve retornar 409 Conflict."""
        payload = self._payload_valido_amostra(
            amostra_id="AMO_SEM_ANIMAL",
            animal_id="ANIMAL_INEXISTENTE_999",
        )
        # Sem query param de confirmação -> 409
        res = self.client.post("/amostra/", json=payload)
        self.assert_conflict(res, expected_code="ANIMAL_NAO_ENCONTRADO")

        # Com confirmar_novo_animal=true -> 201 Created
        res_confirmado = self.client.post(
            "/amostra/",
            json=payload,
            params={"confirmar_novo_animal": True},
        )
        self.assert_status(res_confirmado, 201)
        self.assertEqual(res_confirmado.json()["amostra_id"], "AMO_SEM_ANIMAL")

    def test_criar_amostra_duplicada_rejeitada(self):
        """POST /amostra/ com amostra_id duplicado deve retornar 400 Bad Request."""
        self.criar_amostra_pre_requisito(amostra_id="AMO_DUPLICADA")

        payload = self._payload_valido_amostra(amostra_id="AMO_DUPLICADA")
        res = self.client.post("/amostra/", json=payload)
        self.assert_status(res, 400)
        self.assertIn("já existe uma amostra", res.json()["detail"].lower())

    def test_obter_amostra_e_detalhes(self):
        """GET /amostra/{id} e /amostra/{id}/detalhes devem retornar 200 OK com schemas corretos."""
        amostra = self.criar_amostra_pre_requisito(amostra_id="AMO_CONSULTA_01")

        # 1. Obter normal
        res_get = self.client.get(f"/amostra/{amostra.amostra_id}")
        data_get = self.assert_ok(res_get)
        self.assertEqual(data_get["amostra_id"], "AMO_CONSULTA_01")

        # 2. Obter detalhes
        res_det = self.client.get(f"/amostra/{amostra.amostra_id}/detalhes")
        data_det = self.assert_ok(res_det)
        self.assertEqual(data_det["amostra_id"], "AMO_CONSULTA_01")
        self.assertIn("exames", data_det)
        self.assertIn("animal", data_det)

    def test_obter_amostra_inexistente_retorna_404(self):
        """GET /amostra/{id} inexistente deve retornar 404 Not Found."""
        res = self.client.get("/amostra/AMO_INEXISTENTE_999")
        self.assert_not_found(res, expected_detail_substr="não encontrada")

    def test_listar_amostras_e_contagem(self):
        """GET /amostra/ e GET /amostra/contagem devem retornar listagem filtrada e totalizador."""
        self.criar_amostra_pre_requisito(
            amostra_id="AMO_FILTRO_01",
            material_biologico=MaterialBiologico.SORO,
            status_amostra=StatusAmostra.DISPONIVEL,
        )
        self.criar_amostra_pre_requisito(
            amostra_id="AMO_FILTRO_02",
            material_biologico=MaterialBiologico.TECIDO,
            status_amostra=StatusAmostra.RESERVADA,
        )

        # 1. Contagem
        res_count = self.client.get("/amostra/contagem")
        data_count = self.assert_ok(res_count)
        self.assertIn("total", data_count)
        self.assertGreaterEqual(data_count["total"], 2)

        # 2. Listagem com filtro de material biológico
        res_list = self.client.get(
            "/amostra/",
            params={"material_biologico": MaterialBiologico.SORO.value},
        )
        data_list = self.assert_ok(res_list)
        self.assertIsInstance(data_list, list)
        self.assertTrue(
            all(
                (item.get("material_biologico") or item.get("metodo_coleta")) == MaterialBiologico.SORO.value
                for item in data_list
            )
        )

    def test_listar_amostras_por_animal(self):
        """GET /amostra/animal/{animal_id} retorna todas as amostras vinculadas ao animal."""
        animal = self.criar_animal_pre_requisito(animal_id="ANI_PAI_001")
        self.criar_amostra_pre_requisito(amostra_id="AMO_FILHO_01", animal_id=animal.animal_id)
        self.criar_amostra_pre_requisito(amostra_id="AMO_FILHO_02", animal_id=animal.animal_id)

        res = self.client.get(f"/amostra/animal/{animal.animal_id}")
        data = self.assert_ok(res)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        ids = [item["amostra_id"] for item in data]
        self.assertIn("AMO_FILHO_01", ids)
        self.assertIn("AMO_FILHO_02", ids)

    def test_atualizar_amostra_put_e_patch(self):
        """PUT e PATCH /amostra/{id} devem atualizar campos preservando integridade."""
        amostra = self.criar_amostra_pre_requisito(amostra_id="AMO_UPDATE_01")

        # PATCH
        patch_payload = {"amostra_observacoes": "Observação atualizada via PATCH"}
        res_patch = self.client.patch(f"/amostra/{amostra.amostra_id}", json=patch_payload)
        data_patch = self.assert_ok(res_patch)
        obs_val = data_patch.get("amostra_observacoes") or data_patch.get("observacoes")
        self.assertEqual(obs_val, "Observação atualizada via PATCH")

        # PUT
        put_payload = {"amostra_observacoes": "Observação atualizada via PUT", "caixa_armazenamento": "Caixa Nova"}
        res_put = self.client.put(f"/amostra/{amostra.amostra_id}", json=put_payload)
        data_put = self.assert_ok(res_put)
        obs_put = data_put.get("amostra_observacoes") or data_put.get("observacoes")
        caixa_put = data_put.get("caixa_armazenamento") or data_put.get("caixa")
        self.assertEqual(obs_put, "Observação atualizada via PUT")
        self.assertEqual(caixa_put, "Caixa Nova")

    def test_deletar_amostra_fluxo_204(self):
        """DELETE /amostra/{id} retorna 204 No Content estritamente b'' e 404 subsequente."""
        amostra = self.criar_amostra_pre_requisito(amostra_id="AMO_DEL_001")
        self.verificar_contrato_delete(rota=f"/amostra/{amostra.amostra_id}")


if __name__ == "__main__":
    unittest.main()
