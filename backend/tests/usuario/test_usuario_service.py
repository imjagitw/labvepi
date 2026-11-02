import unittest
import sys
from pathlib import Path

# Garante import do backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.models.Usuario.usuario import Usuario
from src.models.Usuario.usuario_create import UsuarioCreate
from src.models.Usuario.usuario_update import UsuarioUpdate
from src.models.Usuario.usuario_details import UsuarioDetails
from src.models.Usuario.enums.Perfil import Perfil
from src.models.Usuario.enums.StatusUsuario import StatusUsuario
from src.repositories.usuario_repository import UsuarioRepository
from src.services.usuario_service import UsuarioService, verificar_senha


class TestUsuarioService(unittest.TestCase):
    def setUp(self):
        """Instancia repositório isolado em memória e serviço para cada teste."""
        self.repo = UsuarioRepository(usuarios=[])
        self.service = UsuarioService(usuario_repo=self.repo)

    def test_criar_usuario_com_aliases_e_normalizacao(self):
        """Testa criação usando aliases (usuario, nome, senha) e normalização de perfil legado."""
        dados = {
            "usuario": "prof_carlos",
            "nome": "Carlos Silva",
            "email": "carlos@ufpi.edu.br",
            "senha": "senhaSegura123",
            "perfil": "professor",
            "matricula": " 0012345 ",
        }
        usuario = self.service.criar_usuario(dados)

        self.assertEqual(usuario.username, "prof_carlos")
        self.assertEqual(usuario.name, "Carlos Silva")
        self.assertEqual(usuario.email, "carlos@ufpi.edu.br")
        self.assertEqual(usuario.perfil, Perfil.DOCENTE)
        self.assertEqual(usuario.matricula, "0012345")
        self.assertEqual(usuario.status, StatusUsuario.PENDENTE)
        self.assertIsNotNone(usuario.created_at)
        self.assertIsNone(usuario.last_login)
        self.assertTrue(verificar_senha("senhaSegura123", usuario.password))

    def test_criar_usuario_validacoes_obrigatorias_e_tamanho_senha(self):
        """Valida que campos obrigatórios e tamanho mínimo de senha disparam exceções."""
        # Username vazio
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "",
                "email": "a@b.com",
                "senha": "123456",
                "perfil": "docente",
            })

        # Email vazio
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "teste",
                "email": "",
                "senha": "123456",
                "perfil": "docente",
            })

        # Senha curta (< 6)
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "teste",
                "email": "teste@email.com",
                "senha": "123",
                "perfil": "docente",
            })

        # Perfil inválido
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "teste",
                "email": "teste@email.com",
                "senha": "123456",
                "perfil": "administrador_desconhecido",
            })

    def test_criar_usuario_duplicidade_username_e_email(self):
        """Garante que logins e e-mails duplicados são bloqueados."""
        dados = {
            "usuario": "marcos",
            "email": "marcos@email.com",
            "senha": "senha123",
            "perfil": "bolsista_pibiti",
        }
        self.service.criar_usuario(dados)

        # Mesma username
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "marcos",
                "email": "outro@email.com",
                "senha": "senha123",
                "perfil": "bolsista_pibiti",
            })

        # Mesmo email
        with self.assertRaises(ValueError):
            self.service.criar_usuario({
                "usuario": "outro_marcos",
                "email": "marcos@email.com",
                "senha": "senha123",
                "perfil": "bolsista_pibiti",
            })

    def test_obter_usuario_e_detalhes_seguros(self):
        """Testa busca por id/username e projeção segura em UsuarioDetails."""
        usuario = self.service.criar_usuario({
            "usuario": "ana",
            "email": "ana@email.com",
            "senha": "senha123",
            "perfil": "pós-graduando",
            "matricula": "NI",
        })

        # Obter por username
        buscado = self.service.obter_usuario("ana")
        self.assertEqual(buscado.id, usuario.id)

        # Obter por ID
        buscado_id = self.service.obter_usuario(usuario.id)
        self.assertEqual(buscado_id.username, "ana")

        # Projeção segura
        detalhes = self.service.obter_usuario_detalhes("ana")
        self.assertIsInstance(detalhes, UsuarioDetails)
        self.assertFalse(hasattr(detalhes, "password"))
        self.assertEqual(detalhes.matricula, "Não informado")
        self.assertEqual(detalhes.last_login, "Nunca")
        self.assertEqual(detalhes.status, StatusUsuario.PENDENTE)

    def test_atualizar_usuario_com_normalizacao_e_rehash(self):
        """Testa atualização com re-hashing e sanitização de perfil/matrícula."""
        usuario = self.service.criar_usuario({
            "usuario": "lucas",
            "email": "lucas@email.com",
            "senha": "senha123",
            "perfil": "bolsista_pibic",
        })

        atualizado = self.service.atualizar_usuario(
            usuario.id,
            {
                "senha": "novaSenhaSuperSegura456",
                "perfil": "mestrando",
                "matricula": " 20261099 ",
            },
        )

        self.assertEqual(atualizado.perfil, Perfil.POS_GRADUANDO)
        self.assertEqual(atualizado.matricula, "20261099")
        self.assertTrue(verificar_senha("novaSenhaSuperSegura456", atualizado.password))
        self.assertFalse(verificar_senha("senha123", atualizado.password))

    def test_autenticar_usuario_fluxo_completo(self):
        """Testa autenticação por username ou email com conta ativa e gravação de last_login."""
        self.service.criar_usuario({
            "usuario": "mariana",
            "email": "mariana@email.com",
            "senha": "senhaMariana123",
            "perfil": "externo",
            "status": "Ativo",
        })

        # Falha com senha errada
        self.assertIsNone(self.service.autenticar_usuario("mariana", "senhaErrada"))

        # Sucesso por username
        autenticado_user = self.service.autenticar_usuario("mariana", "senhaMariana123")
        self.assertIsNotNone(autenticado_user)
        self.assertIsNotNone(autenticado_user.last_login)

        # Sucesso por email
        autenticado_email = self.service.autenticar_usuario("mariana@email.com", "senhaMariana123")
        self.assertIsNotNone(autenticado_email)

    def test_solicitar_cadastro_e_listar_pendentes(self):
        """Testa o fluxo de solicitação de cadastro com status PENDENTE e listagem."""
        solicitacao = self.service.solicitar_cadastro({
            "usuario": "candidato_bolsista",
            "email": "candidato@ufpi.edu.br",
            "senha": "senhaCandidato123",
            "perfil": "bolsista_pibiti",
            "matricula": "998877",
        })

        self.assertEqual(solicitacao.status, StatusUsuario.PENDENTE)

        # Listar solicitações pendentes
        pendentes = self.service.listar_solicitacoes_pendentes()
        self.assertTrue(any(u.username == "candidato_bolsista" for u in pendentes))

        # Tentativa de login enquanto pendente deve ser bloqueada
        with self.assertRaises(PermissionError) as ctx:
            self.service.autenticar_usuario("candidato_bolsista", "senhaCandidato123")
        self.assertIn("pendente de aprovação", str(ctx.exception))

    def test_aprovar_usuario_e_liberar_login(self):
        """Testa aprovação de conta pendente e liberação subsequente de login."""
        self.service.solicitar_cadastro({
            "usuario": "rodrigo",
            "email": "rodrigo@email.com",
            "senha": "senhaRodrigo123",
            "perfil": "bolsista_pibic",
        })

        # Aprovar usuário
        aprovado = self.service.aprovar_usuario("rodrigo")
        self.assertEqual(aprovado.status, StatusUsuario.ATIVO)

        # Agora o login é liberado com sucesso
        autenticado = self.service.autenticar_usuario("rodrigo", "senhaRodrigo123")
        self.assertIsNotNone(autenticado)
        self.assertEqual(autenticado.username, "rodrigo")

    def test_inativar_e_alterar_status_usuario(self):
        """Testa inativação e transições de status bloqueando login."""
        self.service.criar_usuario({
            "usuario": "juliana",
            "email": "juliana@email.com",
            "senha": "senhaJuliana123",
            "perfil": "docente",
            "status": "Ativo",
        })

        # Inativar conta
        inativado = self.service.inativar_usuario("juliana")
        self.assertEqual(inativado.status, StatusUsuario.INATIVO)

        # Login bloqueado para conta inativa
        with self.assertRaises(PermissionError) as ctx_inativo:
            self.service.autenticar_usuario("juliana", "senhaJuliana123")
        self.assertIn("inativa", str(ctx_inativo.exception))

        # Bloquear conta
        self.service.alterar_status_usuario("juliana", StatusUsuario.BLOQUEADO)
        with self.assertRaises(PermissionError) as ctx_bloqueado:
            self.service.autenticar_usuario("juliana", "senhaJuliana123")
        self.assertIn("bloqueada", str(ctx_bloqueado.exception))

    def test_atualizar_perfil_dedicado(self):
        """Testa alteração semântica e dedicada do perfil de acesso institucional."""
        usuario = self.service.criar_usuario({
            "usuario": "bolsista_fernando",
            "email": "fernando@email.com",
            "senha": "senha123",
            "perfil": "bolsista_pibiti",
        })
        self.assertEqual(usuario.perfil, Perfil.BOLSISTA_PIBITI)

        # Atualizar para pós-graduando usando termo legado
        atualizado = self.service.atualizar_perfil("bolsista_fernando", "mestrando")
        self.assertEqual(atualizado.perfil, Perfil.POS_GRADUANDO)

    def test_trocar_senha_fluxo_completo(self):
        """Testa troca autenticada de senha e suas validações estritas."""
        self.service.criar_usuario({
            "usuario": "paulo",
            "email": "paulo@email.com",
            "senha": "senhaAntiga123",
            "perfil": "docente",
            "status": "Ativo",
        })

        # 1. Falha com senha atual incorreta
        with self.assertRaises(PermissionError) as ctx_errada:
            self.service.trocar_senha(
                identificador="paulo",
                senha_atual="senhaErradaXYZ",
                nova_senha="novaSenhaForte456",
            )
        self.assertIn("Senha atual incorreta", str(ctx_errada.exception))

        # 2. Falha com nova senha curta
        with self.assertRaises(ValueError):
            self.service.trocar_senha(
                identificador="paulo",
                senha_atual="senhaAntiga123",
                nova_senha="123",
            )

        # 3. Falha com confirmação de senha divergente
        with self.assertRaises(ValueError):
            self.service.trocar_senha(
                identificador="paulo",
                senha_atual="senhaAntiga123",
                nova_senha="novaSenhaForte456",
                confirmar_nova_senha="outraSenhaDivergente",
            )

        # 4. Falha com nova senha idêntica à atual
        with self.assertRaises(ValueError):
            self.service.trocar_senha(
                identificador="paulo",
                senha_atual="senhaAntiga123",
                nova_senha="senhaAntiga123",
            )

        # 5. Sucesso na troca
        self.service.trocar_senha(
            identificador="paulo",
            senha_atual="senhaAntiga123",
            nova_senha="novaSenhaForte456",
            confirmar_nova_senha="novaSenhaForte456",
        )

        # Validar que a senha antiga não funciona mais
        self.assertIsNone(self.service.autenticar_usuario("paulo", "senhaAntiga123"))

        # Validar que a nova senha autentica com sucesso
        autenticado = self.service.autenticar_usuario("paulo", "novaSenhaForte456")
        self.assertIsNotNone(autenticado)

    def test_deletar_usuario(self):
        """Testa exclusão com verificação prévia de existência."""
        usuario = self.service.criar_usuario({
            "usuario": "usuario_temp",
            "email": "temp@email.com",
            "senha": "senha123",
            "perfil": "bolsista_pibiti",
        })

        sucesso = self.service.deletar_usuario("usuario_temp")
        self.assertTrue(sucesso)

        with self.assertRaises(KeyError):
            self.service.obter_usuario("usuario_temp")

    def test_id_gerado_automaticamente_e_ignora_id_fornecido(self):
        """Garante que id/_id fornecido pelo usuário é ignorado na criação e atualização."""
        u1 = self.service.criar_usuario({
            "id": 9999,
            "_id": "fake_id",
            "usuario": "user_auto_1",
            "email": "u1@email.com",
            "senha": "senha123",
            "perfil": "docente",
        })
        self.assertEqual(u1.id, 1)

        u2 = self.service.criar_usuario(UsuarioCreate(
            **{
                "id": 8888,
                "_id": 7777,
                "usuario": "user_auto_2",
                "email": "u2@email.com",
                "senha": "senha123",
                "perfil": Perfil.DOCENTE,
            }
        ))
        self.assertEqual(u2.id, 2)

        u1_atualizado = self.service.atualizar_usuario(
            u1.id,
            {"id": 5555, "_id": 4444, "nome": "Nome Atualizado"},
        )
        self.assertEqual(u1_atualizado.id, 1)
        self.assertEqual(u1_atualizado.name, "Nome Atualizado")


if __name__ == "__main__":
    unittest.main()
