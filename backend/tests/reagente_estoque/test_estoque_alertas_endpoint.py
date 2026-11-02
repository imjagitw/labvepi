import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from src.main import app
from src.services.estoque_reagente_service import estoque_reagente_service
from src.models.EstoqueReagente import EstoqueReagente
from src.models.Reagente import Reagente, UnidadeMedida

class TestEstoqueAlertasEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_alertas_endpoint_multiplos_prefixos(self):
        # Garante que /estoque/alertas e /reagente/alertas respondem com 200
        for rota in ["/estoque/alertas", "/reagente/alertas"]:
            resp = self.client.get(rota)
            self.assertEqual(resp.status_code, 200, f"Falha na rota {rota}")
            data = resp.json()
            self.assertIn("parametros", data)
            self.assertIn("totais", data)
            self.assertIn("reagentes_com_alerta", data)

    def test_service_obter_alertas_agregados(self):
        hoje = date.today()
        # Mock de lotes com validades variadas para um reagente
        lotes_teste = [
            Reagente(
                codigo="PBS_01",
                nome="PBS Buffer 10x",
                numero_lote="LOTE_VENCIDO",
                marca="Sigma",
                data_validade=hoje - timedelta(days=10),
                quantidade_unidade=1,
                local_armazenamento="Prateleira 1",
                unidade_medida=UnidadeMedida.ML,
            ),
            Reagente(
                codigo="PBS_01",
                nome="PBS Buffer 10x",
                numero_lote="LOTE_VENCENDO",
                marca="Sigma",
                data_validade=hoje + timedelta(days=15),
                quantidade_unidade=1,
                local_armazenamento="Prateleira 1",
                unidade_medida=UnidadeMedida.ML,
            ),
            Reagente(
                codigo="PBS_01",
                nome="PBS Buffer 10x",
                numero_lote="LOTE_REGULAR",
                marca="Sigma",
                data_validade=hoje + timedelta(days=180),
                quantidade_unidade=3,
                local_armazenamento="Prateleira 1",
                unidade_medida=UnidadeMedida.ML,
            ),
        ]

        estoque_teste = EstoqueReagente(
            nome="PBS Buffer 10x",
            codigo="PBS_01",
            lotes=lotes_teste,
            quantidade_total_unidades=5,
            quantidade_total_volume=5000.0,
            resumo_estoque="5 un | 5000 ml",
        )

        # Salva no repositório de estoque
        estoque_reagente_service.estoque_repo.save(estoque_teste)

        resposta = estoque_reagente_service.obter_alertas_estoque(
            limite_baixo_estoque=2,
            dias_vencimento=30,
            data_referencia=hoje,
        )

        # Deve encontrar o reagente nos alertas devido aos lotes vencido e a vencer
        reags = [r for r in resposta.reagentes_com_alerta if r.reagente_nome == "PBS Buffer 10x"]
        self.assertEqual(len(reags), 1)
        r = reags[0]
        self.assertEqual(r.quantidade_total_unidades, 5)
        self.assertFalse(r.baixo_estoque_global) # 5 > 2
        self.assertTrue(r.tem_lotes_vencidos)
        self.assertTrue(r.tem_lotes_vencendo)
        self.assertTrue(r.tem_alerta)
        self.assertEqual(len(r.lotes_vencidos), 1)
        self.assertEqual(r.lotes_vencidos[0].numero_lote, "LOTE_VENCIDO")
        self.assertEqual(len(r.lotes_proximos_vencimento), 1)
        self.assertEqual(r.lotes_proximos_vencimento[0].numero_lote, "LOTE_VENCENDO")
        self.assertEqual(len(r.lotes_regulares), 1)
        self.assertEqual(r.lotes_regulares[0].numero_lote, "LOTE_REGULAR")

if __name__ == "__main__":
    unittest.main()
