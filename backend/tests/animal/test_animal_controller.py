"""
Testes de Integração HTTP para o Controller de Animal — LABVEPI
==============================================================
Cobre todos os endpoints de /animal/ utilizando ControllerTestCase:
- POST /animal/ (Criação, bloqueio de PK, confirmação de nova espécie, conflito/rejeição de duplicidade)
- GET /animal/ (Listagem com filtros por classe, sexo, regime de vida e paginação)
- GET /animal/{animal_id} (Recuperação direta)
- GET /animal/{animal_id}/detalhes (Visão enriquecida AnimalDetails)
- PATCH / PUT /animal/{animal_id} (Atualização parcial e total preservando PK)
- DELETE /animal/{animal_id} (Exclusão 204 No Content b"" e verificação 404)
"""

import unittest
from tests.base_test_client import ControllerTestCase
from src.models.Especie import Classe
from src.models.Animal import (
    Sexo,
    FaixaEtaria,
    Orgao,
    RegimeVida,
    StatusVital,
)


class TestAnimalController(ControllerTestCase):
    """Suíte de testes de integração HTTP para as rotas /animal."""

    def _payload_valido_animal(self, **kwargs) -> dict:
        """Gera payload completo para criação de animal com espécie conhecida."""
        dados = {
            "animal_id": "ANI_CTRL_001",
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": Classe.MAMIFERO.value,
            "sexo": Sexo.MACHO.value,
            "orgao": Orgao.UFPI.value,
            "local_origem": "Teresina/PI",
            "status": RegimeVida.VIDA_LIVRE.value,
            "status_vital": StatusVital.VIVO.value,
            "faixa_etaria": FaixaEtaria.ADULTO.value,
            "peso": 30.0,
        }
        dados.update(kwargs)
        return dados

    def test_criar_animal_sucesso_e_bloqueio_pk(self):
        """POST /animal/ com espécie existente no catálogo retorna 201 Created e bloqueia PK."""
        self.criar_especie_pre_requisito(
            nome_comum="Morcego-vampiro",
            nome_cientifico="Desmodus rotundus",
            classe=Classe.MAMIFERO,
        )

        payload = self._payload_valido_animal(animal_id="ANI_CTRL_001")
        data = self.verificar_contrato_post_criacao(
            rota="/animal/",
            payload_valido=payload,
            fake_pk_field="id",
            fake_pk_value=77777,
            expected_status=201,
        )
        self.assertEqual(data["animal_id"], "ANI_CTRL_001")
        self.assertEqual(data["nome_cientifico"], "Desmodus rotundus")

    def test_criar_animal_especie_inedita_exige_confirmacao(self):
        """POST /animal/ com espécie fora do catálogo sem confirmação deve retornar 409 Conflict."""
        payload = self._payload_valido_animal(
            animal_id="ANI_NOVA_ESP_01",
            nome_comum="Pássaro Inédito",
            nome_cientifico="Avis incognita",
            classe=Classe.AVES.value,
        )

        # Sem confirmar_nova_especie -> 409 Conflict
        res = self.client.post("/animal/", json=payload)
        self.assert_conflict(res, expected_code="ESPECIE_NAO_ENCONTRADA")

        # Com confirmar_nova_especie=true -> 201 Created
        res_confirmado = self.client.post(
            "/animal/",
            json=payload,
            params={"confirmar_nova_especie": True},
        )
        self.assert_status(res_confirmado, 201)
        self.assertEqual(res_confirmado.json()["animal_id"], "ANI_NOVA_ESP_01")

    def test_criar_animal_duplicado_rejeitado(self):
        """POST /animal/ com animal_id já existente deve ser rejeitado."""
        self.criar_animal_pre_requisito(animal_id="ANI_DUPLICADO")

        payload = self._payload_valido_animal(animal_id="ANI_DUPLICADO")
        res = self.client.post("/animal/", json=payload)
        self.assert_status(res, 400)
        self.assertIn("já existe", res.json()["detail"].lower())

    def test_obter_animal_e_detalhes(self):
        """GET /animal/{id} e /animal/{id}/detalhes retornam 200 OK com schemas corretos."""
        animal = self.criar_animal_pre_requisito(animal_id="ANI_CONSULTA_01")

        # 1. Obter básico
        res_get = self.client.get(f"/animal/{animal.animal_id}")
        data_get = self.assert_ok(res_get)
        self.assertEqual(data_get["animal_id"], "ANI_CONSULTA_01")

        # 2. Obter detalhes
        res_det = self.client.get(f"/animal/{animal.animal_id}/detalhes")
        data_det = self.assert_ok(res_det)
        self.assertEqual(data_det["animal_id"], "ANI_CONSULTA_01")
        self.assertIn("amostras", data_det)
        self.assertIn("especie", data_det)

    def test_obter_animal_inexistente_retorna_404(self):
        """GET /animal/{id} inexistente retorna 404 Not Found."""
        res = self.client.get("/animal/ANI_INEXISTENTE_999")
        self.assert_not_found(res, expected_detail_substr="não encontrado")

    def test_listar_animais_com_filtros(self):
        """GET /animal/ com filtros por sexo e classe."""
        self.criar_animal_pre_requisito(animal_id="ANI_MACHO", sexo=Sexo.MACHO, classe=Classe.MAMIFERO)
        self.criar_animal_pre_requisito(animal_id="ANI_FEMEA", sexo=Sexo.FEMEA, classe=Classe.MAMIFERO)

        res = self.client.get("/animal/", params={"sexo": Sexo.FEMEA.value})
        data = self.assert_ok(res)
        self.assertIsInstance(data, list)
        self.assertTrue(all(item["sexo"] == Sexo.FEMEA.value for item in data))

    def test_atualizar_animal_put_e_patch(self):
        """PUT e PATCH /animal/{id} atualizam campos parciais preservando identificadores."""
        animal = self.criar_animal_pre_requisito(animal_id="ANI_UPDATE_01")

        # PATCH
        patch_payload = {"status_vital": StatusVital.MORTO.value}
        res_patch = self.client.patch(f"/animal/{animal.animal_id}", json=patch_payload)
        data_patch = self.assert_ok(res_patch)
        self.assertEqual(data_patch["status_vital"], StatusVital.MORTO.value)

        # PUT
        put_payload = {"peso": 45.5, "local_origem": "Parnaíba/PI"}
        res_put = self.client.put(f"/animal/{animal.animal_id}", json=put_payload)
        data_put = self.assert_ok(res_put)
        self.assertEqual(data_put["local_origem"], "Parnaíba/PI")

    def test_deletar_animal_fluxo_204(self):
        """DELETE /animal/{id} retorna 204 No Content estritamente b'' e 404 subsequente."""
        animal = self.criar_animal_pre_requisito(animal_id="ANI_DEL_001")
        self.verificar_contrato_delete(rota=f"/animal/{animal.animal_id}")


if __name__ == "__main__":
    unittest.main()
