"""
Testes de Integração HTTP para o Controller de Exame — LABVEPI
=============================================================
Cobre todos os endpoints de /exame/ utilizando ControllerTestCase:
- POST /exame/ (Criação, integridade com amostra, confirmação de nova amostra, bloqueio de PK)
- GET /exame/ (Listagem, filtros analíticos e paginação)
- GET /exame/contagem (Totalização do acervo de exames)
- GET /exame/amostra/{amostra_id} (Exames vinculados a uma amostra)
- GET /exame/{identificador} (Recuperação direta)
- GET /exame/{identificador}/detalhes (Visão enriquecida ExameDetails)
- PATCH / PUT /exame/{identificador} (Atualização parcial e total preservando PK)
- DELETE /exame/{identificador} (Exclusão 204 No Content b"" e verificação 404)
"""

import unittest
from datetime import date
from tests.base_test_client import ControllerTestCase
from src.models.Exame import (
    TipoExame,
    ResultadoExame,
    TesteLaboratorial,
)


class TestExameController(ControllerTestCase):
    """Suíte de testes de integração HTTP para as rotas /exame."""

    def _payload_valido_exame(self, **kwargs) -> dict:
        """Retorna payload válido para criação de exame laboratorial."""
        dados = {
            "amostra_id": "AMO_TEST_001",
            "tipo_exame": TipoExame.RAIVA.value,
            "resultado": ResultadoExame.NEGATIVO.value,
            "data_realizacao": str(date.today()),
            "teste_laboratorial": TesteLaboratorial.PCR.value,
            "responsavel_exame": "Dr. Silva",
            "kit_utilizado": "Kit PCR Raiva",
            "protocolo_exame": "PRT-001",
            "confirmar_novo_exame": True,
        }
        dados.update(kwargs)
        return dados

    def test_criar_exame_sucesso_e_bloqueio_pk(self):
        """POST /exame/ cria novo exame e bloqueia chave primária arbitrária."""
        amostra = self.criar_amostra_pre_requisito(amostra_id="AMO_EXAME_001")
        payload = self._payload_valido_exame(amostra_id=amostra.amostra_id)

        data = self.verificar_contrato_post_criacao(
            rota="/exame/",
            payload_valido=payload,
            fake_pk_field="id",
            fake_pk_value=44444,
            expected_status=201,
        )
        self.assertEqual(data["amostra_id"], "AMO_EXAME_001")
        self.assertEqual(data["tipo_exame"], TipoExame.RAIVA.value)
        self.assertNotEqual(data.get("id"), 44444)

    def test_criar_exame_amostra_inexistente_exige_confirmacao(self):
        """POST /exame/ com amostra inexistente sem confirmação deve retornar 400 Bad Request."""
        payload = self._payload_valido_exame(
            amostra_id="AMOSTRA_INEXISTENTE_999",
            confirmar_novo_exame=True,
        )

        # Sem confirmar_nova_amostra -> 400 Bad Request
        res = self.client.post("/exame/", json=payload)
        self.assert_status(res, 400)
        self.assertIn("confirmar_nova_amostra", res.json()["detail"])

        # Com confirmar_nova_amostra=true -> 201 Created
        res_conf = self.client.post(
            "/exame/",
            json=payload,
            params={"confirmar_nova_amostra": True, "confirmar_novo_exame": True},
        )
        self.assert_status(res_conf, 201)

    def test_obter_exame_e_detalhes(self):
        """GET /exame/{id} e /exame/{id}/detalhes retornam 200 OK com schemas corretos."""
        exame = self.criar_exame_pre_requisito(amostra_id="AMO_DET_01")
        exame_pk = exame.id or exame.exame_id

        # 1. Obter normal
        res_get = self.client.get(f"/exame/{exame_pk}")
        data_get = self.assert_ok(res_get)
        self.assertEqual(data_get["tipo_exame"], TipoExame.RAIVA.value)

        # 2. Obter detalhes
        res_det = self.client.get(f"/exame/{exame_pk}/detalhes")
        data_det = self.assert_ok(res_det)
        self.assertIn("amostra_id", data_det)

    def test_obter_exame_inexistente_retorna_404(self):
        """GET /exame/{id} inexistente retorna 404 Not Found."""
        res = self.client.get("/exame/EXAME_INEXISTENTE_999")
        self.assert_not_found(res, expected_detail_substr="não encontrado")

    def test_listar_exames_e_contagem(self):
        """GET /exame/ e GET /exame/contagem retornam lista filtrada e contagem."""
        self.criar_exame_pre_requisito(
            amostra_id="AMO_LIST_01",
            tipo_exame=TipoExame.RAIVA,
            resultado=ResultadoExame.NEGATIVO,
        )
        self.criar_exame_pre_requisito(
            amostra_id="AMO_LIST_02",
            tipo_exame=TipoExame.FEBRE_AMARELA,
            resultado=ResultadoExame.POSITIVO,
        )

        # 1. Contagem
        res_count = self.client.get("/exame/contagem")
        data_count = self.assert_ok(res_count)
        self.assertIn("total", data_count)
        self.assertGreaterEqual(data_count["total"], 2)

        # 2. Filtro por patógeno
        res_list = self.client.get("/exame/", params={"tipo_exame": TipoExame.RAIVA.value})
        data_list = self.assert_ok(res_list)
        self.assertIsInstance(data_list, list)
        self.assertTrue(all(item["tipo_exame"] == TipoExame.RAIVA.value for item in data_list))

    def test_listar_exames_por_amostra(self):
        """GET /exame/amostra/{amostra_id} retorna os exames vinculados àquela amostra."""
        amostra = self.criar_amostra_pre_requisito(amostra_id="AMO_PAI_001")
        self.criar_exame_pre_requisito(amostra_id=amostra.amostra_id, tipo_exame=TipoExame.RAIVA)
        self.criar_exame_pre_requisito(amostra_id=amostra.amostra_id, tipo_exame=TipoExame.FEBRE_AMARELA)

        res = self.client.get(f"/exame/amostra/{amostra.amostra_id}")
        data = self.assert_ok(res)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_atualizar_exame_put_e_patch(self):
        """PUT e PATCH /exame/{id} atualizam atributos do exame preservando o identificador."""
        exame = self.criar_exame_pre_requisito(amostra_id="AMO_UPD_01")
        exame_pk = exame.id or exame.exame_id

        # PATCH
        patch_payload = {
            "responsavel_exame": "Dra. Fernandes",
            "confirmar_atualizacao_exame": True,
        }
        res_patch = self.client.patch(
            f"/exame/{exame_pk}",
            json=patch_payload,
            params={"confirmar_atualizacao_exame": True},
        )
        data_patch = self.assert_ok(res_patch)
        self.assertEqual(data_patch["responsavel_exame"], "Dra. Fernandes")

        # PUT
        put_payload = {
            "protocolo_exame": "PRT-999-REVISADO",
            "confirmar_atualizacao_exame": True,
        }
        res_put = self.client.put(
            f"/exame/{exame_pk}",
            json=put_payload,
            params={"confirmar_atualizacao_exame": True},
        )
        data_put = self.assert_ok(res_put)
        self.assertEqual(data_put["protocolo_exame"], "PRT-999-REVISADO")

    def test_deletar_exame_fluxo_204(self):
        """DELETE /exame/{id} remove exame e retorna 204 No Content estritamente b''."""
        exame = self.criar_exame_pre_requisito(amostra_id="AMO_DEL_EX")
        exame_pk = exame.id or exame.exame_id
        self.verificar_contrato_delete(rota=f"/exame/{exame_pk}")


if __name__ == "__main__":
    unittest.main()
