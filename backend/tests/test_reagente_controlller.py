import unittest
from fastapi.testclient import TestClient
from src.main import app

class TestReagenteEEstoqueControllers(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Limpa lote e estoque de teste remanescentes
        res_lote = self.client.get("/reagente/lote/LOTE_TAQ_2026")
        if res_lote.status_code == 200 and isinstance(res_lote.json(), list):
            for item in res_lote.json():
                item_id = item.get("id") or item.get("_id")
                if item_id:
                    self.client.delete(f"/reagente/{item_id}")

    def test_fluxo_completo_reagente_e_estoque(self):
        # 1. Contagem inicial
        res_count_r = self.client.get("/reagente/contagem")
        self.assertEqual(res_count_r.status_code, 200)
        self.assertIn("total", res_count_r.json())

        res_count_e = self.client.get("/estoque_reagente/contagem")
        self.assertEqual(res_count_e.status_code, 200)
        self.assertIn("total", res_count_e.json())

        # 2. Criar lote de reagente via POST /reagente/ (tentando enviar id/_id que deve ser ignorado)
        payload_lote = {
            "id": 999999,
            "_id": "FAKE_PK",
            "reagente_codigo": "REAG_TEST_01",
            "reagente_nome": "Taq DNA Polimerase",
            "numero_lote": "LOTE_TAQ_2026",
            "marca": "ThermoFisher",
            "data_validade": "2027-12-31",
            "reagente_local_armazenamento": "Freezer -20 C",
            "quantidade_unidade": 2,
            "quantidade_volume": 500,
            "unidade_medida": "µl",
            "reagente_etapa": "PCR",
        }
        res_post = self.client.post("/reagente/", json=payload_lote)
        self.assertEqual(res_post.status_code, 201)
        data_criada = res_post.json()
        reagente_id = data_criada["reagente_id"]
        id_num = data_criada.get("id") or data_criada.get("_id")
        self.assertNotEqual(id_num, 999999)
        self.assertNotEqual(reagente_id, "FAKE_PK")

        # 3. Consultar Reagente por identificador e detalhes
        res_get = self.client.get(f"/reagente/{reagente_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["numero_lote"], "LOTE_TAQ_2026")

        res_det = self.client.get(f"/reagente/{reagente_id}/detalhes")
        self.assertEqual(res_det.status_code, 200)
        self.assertIn("esta_vencido", res_det.json())
        self.assertFalse(res_det.json()["esta_vencido"])

        # 4. Listar por lote
        res_lote = self.client.get("/reagente/lote/LOTE_TAQ_2026")
        self.assertEqual(res_lote.status_code, 200)
        self.assertGreaterEqual(len(res_lote.json()), 1)

        # 5. Listar com filtros
        res_list = self.client.get("/reagente/?nome=Taq DNA Polimerase")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # 6. Atualizar Reagente via PUT /reagente/{id}
        payload_update = dict(payload_lote)
        payload_update["quantidade_unidade"] = 3
        res_put = self.client.put(
            f"/reagente/{id_num}",
            json=payload_update,
        )
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.json()["quantidade_unidade"], 3)

        # 7. Consultar EstoqueReagente criado/sincronizado automaticamente
        res_est = self.client.get("/estoque_reagente/Taq DNA Polimerase")
        self.assertEqual(res_est.status_code, 200)
        est_data = res_est.json()
        nome_est = est_data.get("nome") or est_data.get("reagente_nome")
        id_est = est_data.get("id") or est_data.get("_id")
        self.assertEqual(nome_est, "Taq DNA Polimerase")
        self.assertEqual(est_data["quantidade_total_unidades"], 3)
        self.assertEqual(est_data["totais_convertidos_base"]["ml"], 1.5)

        # 8. Detalhes do estoque
        res_est_det = self.client.get(f"/estoque_reagente/{id_est}/detalhes")
        self.assertEqual(res_est_det.status_code, 200)
        self.assertGreaterEqual(len(res_est_det.json()["lotes"]), 1)

        # 9. Listar estoques e recalcular
        res_est_list = self.client.get("/estoque_reagente/?termo_busca=Taq")
        self.assertEqual(res_est_list.status_code, 200)
        self.assertGreaterEqual(len(res_est_list.json()), 1)

        res_recalc = self.client.post("/estoque_reagente/recalcular")
        self.assertEqual(res_recalc.status_code, 200)
        self.assertIn("reagentes_atualizados", res_recalc.json())

        # 10. Deletar Reagente
        res_del_r = self.client.delete(f"/reagente/{id_num}")
        self.assertEqual(res_del_r.status_code, 204)

        # 11. Deletar Estoque
        res_del_e = self.client.delete(f"/estoque_reagente/{id_est}")
        self.assertEqual(res_del_e.status_code, 204)


if __name__ == "__main__":
    unittest.main()
