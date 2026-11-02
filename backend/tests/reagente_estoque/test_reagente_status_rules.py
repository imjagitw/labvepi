import unittest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from src.main import app
from src.models.Reagente import (
    Reagente,
    ReagenteCreate,
    ReagenteUpdate,
    ReagenteDetails,
    StatusReagente,
)
from src.repositories.reagente_repository import ReagenteRepository
from src.services.reagente_service import ReagenteService
from src.utils.normalizacao import normalizar_status_reagente


class TestReagenteStatusRules(unittest.TestCase):
    def setUp(self):
        self.repo = ReagenteRepository(reagentes=[])
        self.service = ReagenteService(reagente_repo=self.repo)
        self.hoje = date.today()
        self.futuro = self.hoje + timedelta(days=60)
        self.passado = self.hoje - timedelta(days=10)

    def test_status_reagente_enum_members(self):
        """Valida que StatusReagente possui estritamente Disponível, Vencido, Reservado e Esgotado."""
        valores = [s.value for s in StatusReagente]
        self.assertIn("Disponível", valores)
        self.assertIn("Vencido", valores)
        self.assertIn("Reservado", valores)
        self.assertIn("Esgotado", valores)
        self.assertEqual(len(valores), 4)

        # Não deve conter baixo estoque nem usado no enum
        self.assertNotIn("Baixo Estoque", valores)
        self.assertNotIn("baixo estoque", valores)
        self.assertNotIn("Usado", valores)
        self.assertNotIn("usado", valores)

    def test_normalizacao_status_reagente(self):
        """Valida normalização textual e mapeamento de usado para esgotado."""
        self.assertEqual(normalizar_status_reagente("disponivel"), StatusReagente.DISPONIVEL)
        self.assertEqual(normalizar_status_reagente("Disponível"), StatusReagente.DISPONIVEL)
        self.assertEqual(normalizar_status_reagente("vencido"), StatusReagente.VENCIDO)
        self.assertEqual(normalizar_status_reagente("reservado"), StatusReagente.RESERVADO)
        self.assertEqual(normalizar_status_reagente("usado"), StatusReagente.ESGOTADO)
        self.assertEqual(normalizar_status_reagente("esgotado"), StatusReagente.ESGOTADO)

    def test_criar_reagente_vencido_automatico(self):
        """Lote com data no passado deve receber status Vencido automaticamente."""
        r = self.service.criar_reagente({
            "codigo": "REA_01",
            "nome": "Primer F",
            "numero_lote": "LOTE_01",
            "marca": "IDT",
            "data_validade": self.passado,
            "local_armazenamento": "Freezer -20",
        })
        self.assertEqual(r.status_reagente, StatusReagente.VENCIDO)
        self.assertTrue(r.esta_vencido)

    def test_bloqueio_usuario_colocar_vencido_quando_nao_vencido_no_create(self):
        """Usuário não pode colocar como vencido um reagente cuja validade não expirou."""
        with self.assertRaises(ValueError) as ctx:
            self.service.criar_reagente({
                "codigo": "REA_02",
                "nome": "Primer R",
                "numero_lote": "LOTE_02",
                "marca": "IDT",
                "data_validade": self.futuro,
                "local_armazenamento": "Freezer -20",
                "status": "Vencido",
            })
        self.assertIn("não expirou", str(ctx.exception))

    def test_criar_reagente_com_status_esgotado_ou_reservado(self):
        """Criação válida de lote com status Reservado ou Esgotado."""
        r_res = self.service.criar_reagente({
            "codigo": "REA_03",
            "nome": "Taq Polimerase",
            "numero_lote": "LOTE_RES",
            "marca": "Thermo",
            "data_validade": self.futuro,
            "local_armazenamento": "Freezer -20",
            "status": "Reservado",
        })
        self.assertEqual(r_res.status_reagente, StatusReagente.RESERVADO)

        r_usado = self.service.criar_reagente({
            "codigo": "REA_04",
            "nome": "Buffer 10x",
            "numero_lote": "LOTE_USADO",
            "marca": "Thermo",
            "data_validade": self.futuro,
            "local_armazenamento": "Freezer -20",
            "status": "Esgotado",
        })
        self.assertEqual(r_usado.status_reagente, StatusReagente.ESGOTADO)

    def test_reagente_esgotado_nao_vira_vencido_automaticamente(self):
        """Se o status estiver como Esgotado, ele NÃO vira Vencido automaticamente ao expirar."""
        r = self.service.criar_reagente({
            "codigo": "REA_05",
            "nome": "Agarose",
            "numero_lote": "LOTE_AG",
            "marca": "Sigma",
            "data_validade": self.futuro,
            "local_armazenamento": "Armário",
            "status": "Esgotado",
        })
        self.assertEqual(r.status_reagente, StatusReagente.ESGOTADO)

        # Simula expiração: altera a data de validade para o passado
        r_atualizado = self.service.atualizar_reagente(
            r.id,
            {"data_validade": self.passado}
        )
        self.assertTrue(r_atualizado.esta_vencido)
        # Permanece Esgotado
        self.assertEqual(r_atualizado.status_reagente, StatusReagente.ESGOTADO)

        # Ao consultar detalhes também permanece Esgotado
        detalhes = self.service.obter_reagente_detalhes(r.id)
        self.assertEqual(detalhes.status_reagente, StatusReagente.ESGOTADO)

    def test_transicao_proibida_esgotado_para_vencido(self):
        """Se estiver como Esgotado, não pode ser alterado para Vencido."""
        r = self.service.criar_reagente({
            "codigo": "REA_06",
            "nome": "dNTPs",
            "numero_lote": "LOTE_DNTP",
            "marca": "Thermo",
            "data_validade": self.passado,
            "local_armazenamento": "Freezer",
            "status": "Esgotado",
        })
        self.assertEqual(r.status_reagente, StatusReagente.ESGOTADO)

        with self.assertRaises(ValueError) as ctx:
            self.service.atualizar_reagente(r.id, {"status": "Vencido"})
        self.assertIn("não pode ser alterado para Vencido", str(ctx.exception))

    def test_transicao_proibida_vencido_para_esgotado(self):
        """Se estiver como Vencido, não vira Esgotado."""
        r = self.service.criar_reagente({
            "codigo": "REA_07",
            "nome": "Enzima Restrição",
            "numero_lote": "LOTE_ENZ",
            "marca": "NEB",
            "data_validade": self.passado,
            "local_armazenamento": "Freezer -20",
        })
        self.assertEqual(r.status_reagente, StatusReagente.VENCIDO)

        with self.assertRaises(ValueError) as ctx:
            self.service.atualizar_reagente(r.id, {"status": "Esgotado"})
        self.assertIn("não pode ser alterado para Esgotado", str(ctx.exception))

    def test_bloqueio_atualizar_para_vencido_quando_nao_vencido(self):
        """Não permite alterar para Vencido lote que tem validade futura."""
        r = self.service.criar_reagente({
            "codigo": "REA_08",
            "nome": "Álcool 70%",
            "numero_lote": "LOTE_ALC",
            "marca": "Labs",
            "data_validade": self.futuro,
            "local_armazenamento": "Prateleira",
        })
        self.assertEqual(r.status_reagente, StatusReagente.DISPONIVEL)

        with self.assertRaises(ValueError) as ctx:
            self.service.atualizar_reagente(r.id, {"status": "Vencido"})
        self.assertIn("não expirou", str(ctx.exception))

    def test_filtrar_por_status_no_servico(self):
        """Listagem no serviço com filtro por status."""
        self.service.criar_reagente({
            "codigo": "R_A",
            "nome": "Reagente A",
            "numero_lote": "L1",
            "marca": "M",
            "data_validade": self.futuro,
            "local_armazenamento": "L",
            "status": "Disponível",
        })
        self.service.criar_reagente({
            "codigo": "R_B",
            "nome": "Reagente B",
            "numero_lote": "L2",
            "marca": "M",
            "data_validade": self.passado,
            "local_armazenamento": "L",
        })
        self.service.criar_reagente({
            "codigo": "R_C",
            "nome": "Reagente C",
            "numero_lote": "L3",
            "marca": "M",
            "data_validade": self.futuro,
            "local_armazenamento": "L",
            "status": "Esgotado",
        })

        disp = self.service.listar_reagentes(status=StatusReagente.DISPONIVEL)
        self.assertEqual(len(disp), 1)
        self.assertEqual(disp[0].reagente_nome, "Reagente A")

        venc = self.service.listar_reagentes(status=StatusReagente.VENCIDO)
        self.assertEqual(len(venc), 1)
        self.assertEqual(venc[0].reagente_nome, "Reagente B")

        esgot = self.service.listar_reagentes(status=StatusReagente.ESGOTADO)
        self.assertEqual(len(esgot), 1)
        self.assertEqual(esgot[0].reagente_nome, "Reagente C")


class TestCORSConfiguration(unittest.TestCase):
    def test_cors_headers_and_options(self):
        client = TestClient(app)
        res = client.options(
            "/reagente/",
            headers={
                "Origin": "http://localhost:8501",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertIn(res.status_code, [200, 204])
        self.assertEqual(res.headers.get("access-control-allow-origin"), "http://localhost:8501")


if __name__ == "__main__":
    unittest.main()
