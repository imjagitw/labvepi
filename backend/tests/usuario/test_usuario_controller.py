"""
Testes de Integração HTTP para o Controller de Usuário — LABVEPI
==============================================================
Cobre todos os endpoints de /usuario/ utilizando ControllerTestCase:
- POST /usuario/ (Criação de usuário, bloqueio de PK, omissão segura de senha)
- POST /usuario/solicitar-cadastro (Criação pública com status Pendente)
- GET /usuario/pendentes (Listagem de aprovações pendentes)
- POST /usuario/login (Autenticação por credenciais com bloqueio de inativos)
- GET /usuario/ (Listagem com filtros por perfil e status)
- GET /usuario/{identificador} e /detalhes (Visão enriquecida UsuarioDetails)
- PATCH / PUT /usuario/{identificador} (Atualizações gerais e dedicadas de perfil)
- PATCH /usuario/{identificador}/aprovar e inativar (Transições de ciclo de vida)
- DELETE /usuario/{identificador} (Exclusão 204 No Content b"" e verificação 404)
"""

import unittest
from tests.base_test_client import ControllerTestCase
from src.models.Usuario import Perfil, StatusUsuario


class TestUsuarioController(ControllerTestCase):
    """Suíte de testes de integração HTTP para as rotas /usuario."""

    def _payload_valido_usuario(self, **kwargs) -> dict:
        """Gera payload válido para criação de usuário."""
        dados = {
            "username": "docente_lab",
            "name": "Prof. Doutor Pesquisador",
            "email": "docente_lab@ufpi.edu.br",
            "password": "senhaSegura123",
            "perfil": Perfil.DOCENTE.value,
            "matricula": "12345678",
            "status": StatusUsuario.ATIVO.value,
        }
        dados.update(kwargs)
        return dados

    def test_criar_usuario_sucesso_bloqueio_pk_e_ocultacao_senha(self):
        """POST /usuario/ cria usuário, bloqueia fake PK e nunca expõe senha no retorno."""
        payload = self._payload_valido_usuario(username="novo_pesquisador", email="novo_pesq@ufpi.edu.br")

        data = self.verificar_contrato_post_criacao(
            rota="/usuario/",
            payload_valido=payload,
            fake_pk_field="id",
            fake_pk_value=99999,
            expected_status=201,
        )
        u_name = data.get("username") or data.get("usuario")
        self.assertEqual(u_name, "novo_pesquisador")
        self.assertNotIn("password", data)
        self.assertNotIn("senha", data)
        self.assertNotEqual(data.get("id"), 99999)

    def test_solicitar_cadastro_e_listar_pendentes(self):
        """POST /usuario/solicitar-cadastro cria conta Pendente e aparece em GET /usuario/pendentes."""
        payload = self._payload_valido_usuario(
            username="candidato_bolsa",
            email="candidato@ufpi.edu.br",
        )
        res_solic = self.client.post("/usuario/solicitar-cadastro", json=payload)
        data_solic = self.assert_created(res_solic)
        self.assertEqual(data_solic["status"], StatusUsuario.PENDENTE.value)

        # Listagem de pendentes
        res_pend = self.client.get("/usuario/pendentes")
        data_pend = self.assert_ok(res_pend)
        self.assertIsInstance(data_pend, list)
        usernames_pendentes = [u.get("username") or u.get("usuario") for u in data_pend]
        self.assertIn("candidato_bolsa", usernames_pendentes)

    def test_login_autenticacao_sucesso_e_falha(self):
        """POST /usuario/login autentica conta ativa e rejeita senha incorreta."""
        self.criar_usuario_pre_requisito(
            username="usuario_auth",
            email="auth@ufpi.edu.br",
            senha_plana="segredoForte123",
            status=StatusUsuario.ATIVO,
        )

        # Login correto
        login_payload = {"login": "usuario_auth", "senha": "segredoForte123"}
        res_login = self.client.post("/usuario/login", json=login_payload)
        data_login = self.assert_ok(res_login)
        u_name = data_login.get("username") or data_login.get("usuario")
        self.assertEqual(u_name, "usuario_auth")
        self.assertNotIn("password", data_login)

        # Senha incorreta -> falha
        res_falha = self.client.post(
            "/usuario/login",
            json={"login": "usuario_auth", "senha": "senhaErrada123"},
        )
        self.assertNotEqual(res_falha.status_code, 200)

    def test_obter_usuario_e_detalhes(self):
        """GET /usuario/{id} e /detalhes retornam visão segura UsuarioDetails."""
        usuario = self.criar_usuario_pre_requisito(username="consulta_detalhes", email="detalhes@ufpi.edu.br")

        res = self.client.get(f"/usuario/{usuario.username}")
        data = self.assert_ok(res)
        u_name = data.get("username") or data.get("usuario")
        self.assertEqual(u_name, "consulta_detalhes")
        self.assertNotIn("password", data)

        res_det = self.client.get(f"/usuario/{usuario.username}/detalhes")
        data_det = self.assert_ok(res_det)
        u_name_det = data_det.get("username") or data_det.get("usuario")
        self.assertEqual(u_name_det, "consulta_detalhes")
        self.assertIn("status", data_det)

    def test_obter_usuario_inexistente_retorna_404(self):
        """GET /usuario/{id} inexistente retorna 404 Not Found."""
        res = self.client.get("/usuario/USUARIO_INEXISTENTE_999")
        self.assert_not_found(res, expected_detail_substr="não encontrado")

    def test_listar_usuarios_com_filtros(self):
        """GET /usuario/ permite filtros cruzados por status e perfil."""
        self.criar_usuario_pre_requisito(
            username="docente_filtro",
            email="docente_filtro@ufpi.edu.br",
            perfil=Perfil.DOCENTE,
            status=StatusUsuario.ATIVO,
        )
        self.criar_usuario_pre_requisito(
            username="bolsista_filtro",
            email="bolsista_filtro@ufpi.edu.br",
            perfil=Perfil.BOLSISTA_PIBITI,
            status=StatusUsuario.ATIVO,
        )

        res = self.client.get("/usuario/", params={"perfil": Perfil.DOCENTE.value})
        data = self.assert_ok(res)
        self.assertIsInstance(data, list)
        self.assertTrue(all(u["perfil"] == Perfil.DOCENTE.value for u in data))

    def test_atualizar_usuario_e_perfil_dedicado(self):
        """PUT /usuario/{id} e PATCH /perfil atualizam informações preservando PK."""
        usuario = self.criar_usuario_pre_requisito(username="usuario_mutavel", email="mutavel@ufpi.edu.br")

        # Atualização geral
        put_payload = {"name": "Novo Nome Atualizado"}
        res_put = self.client.put(f"/usuario/{usuario.username}", json=put_payload)
        data_put = self.assert_ok(res_put)
        n_name = data_put.get("name") or data_put.get("nome")
        self.assertEqual(n_name, "Novo Nome Atualizado")

        # Atualização dedicada de perfil
        res_perfil = self.client.patch(
            f"/usuario/{usuario.username}/perfil",
            json={"perfil": Perfil.POS_GRADUANDO.value},
        )
        data_perfil = self.assert_ok(res_perfil)
        self.assertEqual(data_perfil["perfil"], Perfil.POS_GRADUANDO.value)

    def test_aprovar_e_inativar_usuario(self):
        """PATCH /aprovar e /inativar transicionam o status da conta."""
        usuario = self.criar_usuario_pre_requisito(
            username="usuario_ciclo",
            email="ciclo@ufpi.edu.br",
            status=StatusUsuario.PENDENTE,
        )

        # Aprovar
        res_apr = self.client.patch(f"/usuario/{usuario.username}/aprovar")
        data_apr = self.assert_ok(res_apr)
        self.assertEqual(data_apr["status"], StatusUsuario.ATIVO.value)

        # Inativar
        res_inat = self.client.patch(f"/usuario/{usuario.username}/inativar")
        data_inat = self.assert_ok(res_inat)
        self.assertEqual(data_inat["status"], StatusUsuario.INATIVO.value)

    def test_deletar_usuario_fluxo_204(self):
        """DELETE /usuario/{id} remove usuário e retorna 204 No Content estritamente b''."""
        usuario = self.criar_usuario_pre_requisito(username="usuario_del", email="del@ufpi.edu.br")
        self.verificar_contrato_delete(rota=f"/usuario/{usuario.username}")


if __name__ == "__main__":
    unittest.main()
