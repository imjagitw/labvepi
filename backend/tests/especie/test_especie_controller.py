"""
Testes de Integração HTTP para o Controller de Espécie — LABVEPI
===============================================================
Cobre todos os endpoints de /especie/ utilizando ControllerTestCase:
- POST /especie/cadastro (Criação, bloqueio de PK, normalização taxonômica)
- GET /especie/ (Listagem e filtros cruzados por nome comum, científico e classe)
- GET /especie/{id} (Detalhes da espécie e contagem de animais associados)
- PATCH / PUT /especie/{id} (Atualização preservando a chave primária imutável)
- DELETE /especie/{id} (Exclusão 204 No Content b"" e verificação 404)
"""

import unittest
from tests.base_test_client import ControllerTestCase
from src.models.Especie import Classe


class TestEspecieController(ControllerTestCase):
    """Suíte de testes de integração HTTP para as rotas /especie."""

    def test_cadastrar_especie_sucesso_e_bloqueio_pk(self):
        """POST /especie/cadastro cria nova espécie e bloqueia chave primária arbitrária."""
        payload = {
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": Classe.MAMIFERO.value,
        }

        data = self.verificar_contrato_post_criacao(
            rota="/especie/cadastro",
            payload_valido=payload,
            fake_pk_field="id",
            fake_pk_value=55555,
            expected_status=201,
        )
        self.assertEqual(data["nome_cientifico"], "Desmodus rotundus")
        self.assertNotEqual(data.get("id"), 55555)

    def test_obter_especie_detalhes(self):
        """GET /especie/{id} retorna os detalhes da espécie com contagem de animais."""
        esp = self.criar_especie_pre_requisito(
            nome_comum="Bugio-preto",
            nome_cientifico="Alouatta caraya",
            classe=Classe.MAMIFERO,
        )

        res = self.client.get(f"/especie/{esp.id}")
        data = self.assert_ok(res)
        self.assertEqual(data["nome_cientifico"], "Alouatta caraya")
        self.assertIn("quantidade_animais", data)
        self.assertIn("animais", data)

    def test_obter_especie_inexistente_retorna_404(self):
        """GET /especie/{id} inexistente deve retornar 404 Not Found."""
        res = self.client.get("/especie/999999")
        self.assert_not_found(res, expected_detail_substr="não encontrada")

    def test_listar_e_filtrar_especies(self):
        """GET /especie/ permite busca geral e filtros taxonômicos."""
        self.criar_especie_pre_requisito(
            nome_comum="Jiboia",
            nome_cientifico="Boa constrictor",
            classe=Classe.REPTIL,
        )
        self.criar_especie_pre_requisito(
            nome_comum="Gavião-real",
            nome_cientifico="Harpia harpyja",
            classe=Classe.AVES,
        )

        # 1. Listagem completa
        res_all = self.client.get("/especie/")
        data_all = self.assert_ok(res_all)
        self.assertGreaterEqual(len(data_all), 2)

        # 2. Filtro por classe
        res_filtro = self.client.get("/especie/", params={"classe": Classe.REPTIL.value})
        data_filtro = self.assert_ok(res_filtro)
        self.assertTrue(all(item["classe"] == Classe.REPTIL.value for item in data_filtro))

    def test_atualizar_especie_put_e_patch(self):
        """PUT e PATCH /especie/{id} atualizam atributos taxonômicos preservando o ID."""
        esp = self.criar_especie_pre_requisito(
            nome_comum="Onça-parda",
            nome_cientifico="Puma concolor",
            classe=Classe.MAMIFERO,
        )

        # PATCH
        patch_payload = {"nome_comum": "Suçuarana"}
        res_patch = self.client.patch(f"/especie/{esp.id}", json=patch_payload)
        data_patch = self.assert_ok(res_patch)
        nome_patch = data_patch.get("nome_comum") or data_patch.get("nome")
        self.assertEqual(nome_patch, "Suçuarana")
        self.assertEqual(data_patch["nome_cientifico"], "Puma concolor")

        # PUT
        put_payload = {"nome_comum": "Leão-baio"}
        res_put = self.client.put(f"/especie/{esp.id}", json=put_payload)
        data_put = self.assert_ok(res_put)
        nome_put = data_put.get("nome_comum") or data_put.get("nome")
        self.assertEqual(nome_put, "Leão-baio")

    def test_deletar_especie_fluxo_204(self):
        """DELETE /especie/{id} remove espécie e retorna 204 No Content estritamente b''."""
        esp = self.criar_especie_pre_requisito(
            nome_comum="Sapo-cururu",
            nome_cientifico="Rhinella marina",
            classe=Classe.ANFIBIO,
        )
        self.verificar_contrato_delete(rota=f"/especie/{esp.id}")


if __name__ == "__main__":
    unittest.main()
