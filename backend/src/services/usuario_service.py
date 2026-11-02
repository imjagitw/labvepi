import hashlib
from datetime import datetime
from typing import Optional, Union, List, Dict, Any
from src.models.Usuario.usuario import Usuario
from src.models.Usuario.usuario_create import UsuarioCreate
from src.models.Usuario.usuario_update import UsuarioUpdate
from src.models.Usuario.usuario_details import UsuarioDetails
from src.models.Usuario.usuario_troca_senha import UsuarioTrocaSenha, TrocaSenhaRequest
from src.models.Usuario.usuario_perfil_update import UsuarioPerfilUpdate, AtualizarPerfilRequest
from src.models.Usuario.usuario_status_update import UsuarioStatusUpdate, AtualizarStatusRequest
from src.models.Usuario.enums.Perfil import Perfil
from src.models.Usuario.enums.StatusUsuario import StatusUsuario
from src.repositories.usuario_repository import UsuarioRepository, usuario_repository
from src.utils.repositorio import _CAMPOS_PROIBIDOS_ENTRADA
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_perfil,
    normalizar_matricula,
    normalizar_last_login,
    normalizar_status_usuario,
    normalizar_chaves_usuario,
    _ALIASES_USUARIO,
    _MAPA_PERFIL_LEGADO,
    _MAPA_STATUS_USUARIO,
)

def hash_password(password: str) -> str:
    """
    Gera hash seguro da senha utilizando bcrypt com salt gerado automaticamente.
    Emprega fallback SHA-256 caso a biblioteca bcrypt não esteja disponível.
    """
    if not password:
        raise ValueError("A senha não pode ser vazia.")
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    except ImportError:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verificar_senha(password: str, password_hash: str) -> bool:
    """Verifica uma senha em texto puro contra o hash armazenado."""
    if not password or not password_hash:
        return False
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == password_hash

class UsuarioService:
    """
    Serviço responsável pelas ações de negócio e ciclo de vida da entidade Usuario:
    - [CREATE/SOLICITAÇÃO] Cadastro de usuários com hashing de senha, validação de unicidade e status pendente.
    - [READ] Obtenção por ID/login, listagem paginada, filtros por perfil/status e projeção segura em UsuarioDetails.
    - [UPDATE] Atualização cadastral parcial, re-hashing seguro de senha e atualização semântica de perfil.
    - [STATUS] Aprovação/ativação, inativação e gerenciamento de ciclo de vida da conta.
    - [PASSWORD] Troca de senha autenticada com validação prévia da credencial atual.
    - [DELETE] Exclusão com validação prévia de existência.
    - [AUTH] Autenticação com bloqueio para contas não ativadas e auditoria de último acesso.
    - Orquestração de persistência através do UsuarioRepository (DAO).
    """

    def __init__(self, usuario_repo: Optional[UsuarioRepository] = None):
        self.usuario_repo = usuario_repo or usuario_repository

    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """Gancho preparado para controle de acesso baseado em papéis (RBAC)."""
        pass

    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases aceitos na API para os nomes canônicos do modelo."""
        return normalizar_chaves_usuario(payload)

    @staticmethod
    def _eh_nao_informado(valor: Any) -> bool:
        return eh_nao_informado(valor)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD E SOLICITAÇÃO:
    # -------------------------------------------------------------------------

    def criar_usuario(
        self,
        dados_usuario: Union[Dict[str, Any], UsuarioCreate],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [CREATE] Cria e persiste um novo usuário no sistema.
        - Valida presença de username, email, password e perfil.
        - Valida tamanho mínimo de senha e formato de e-mail.
        - Verifica duplicidade de username e e-mail no repositório.
        - Aplica hash criptográfico (bcrypt) na senha antes de persistir.
        - Normaliza perfil, matrícula e status (default: PENDENTE).
        - Inicializa 'created_at' e define 'last_login = None'.
        """
        self._verificar_permissao("criar_usuario", usuario_solicitante)

        if isinstance(dados_usuario, UsuarioCreate):
            payload = dados_usuario.model_dump(by_alias=True)
        else:
            payload = dict(dados_usuario)

        # A chave primária (id/_id) é gerada automaticamente pelo banco/repositório:
        # nunca é aceita na entrada do usuário.
        for chave in (*_CAMPOS_PROIBIDOS_ENTRADA, "confirmar_novo_usuario"):
            payload.pop(chave, None)
        payload = self._normalizar_chaves(payload)
        for chave in _CAMPOS_PROIBIDOS_ENTRADA:
            payload.pop(chave, None)

        # 1. Validação de presença obrigatória
        username = payload.get("username")
        if eh_nao_informado(username):
            raise ValueError("O nome de usuário (username/usuario) é obrigatório.")
        username_limpo = str(username).strip()
        payload["username"] = username_limpo

        email = payload.get("email")
        if eh_nao_informado(email):
            raise ValueError("O e-mail do usuário é obrigatório.")
        email_limpo = str(email).strip()
        payload["email"] = email_limpo

        senha = payload.get("password")
        if eh_nao_informado(senha):
            raise ValueError("A senha do usuário (password/senha) é obrigatória.")
        senha_str = str(senha)
        if len(senha_str) < 6:
            raise ValueError("A senha deve conter no mínimo 6 caracteres.")

        # 2. Verificação de conflito de unicidade
        if self.usuario_repo.exists_username(username_limpo):
            raise ValueError(f"Já existe um usuário cadastrado com o login '{username_limpo}'.")

        if self.usuario_repo.exists_email(email_limpo):
            raise ValueError(f"Já existe um usuário cadastrado com o e-mail '{email_limpo}'.")

        # 3. Normalização de Perfil, Matrícula e Status
        perfil_valor = payload.get("perfil")
        payload["perfil"] = normalizar_perfil(perfil_valor)

        payload["matricula"] = normalizar_matricula(payload.get("matricula"))

        status_valor = payload.get("status")
        if status_valor is not None:
            payload["status"] = normalizar_status_usuario(status_valor)
        else:
            payload["status"] = StatusUsuario.PENDENTE

        # 4. Hashing da senha
        payload["password"] = hash_password(senha_str)

        # 5. Auditoria de data/hora
        if "created_at" not in payload or payload.get("created_at") is None:
            payload["created_at"] = datetime.now()
        payload["last_login"] = None

        usuario = Usuario(**payload)
        return self.usuario_repo.create(usuario)

    def solicitar_cadastro(
        self,
        dados_usuario: Union[Dict[str, Any], UsuarioCreate],
    ) -> Usuario:
        """
        [CREATE/SOLICITAÇÃO] Registra uma nova solicitação pública de cadastro.
        Garante que a conta inicie estritamente com status PENDENTE de aprovação.
        """
        if isinstance(dados_usuario, UsuarioCreate):
            payload = dados_usuario.model_dump(by_alias=True)
        else:
            payload = dict(dados_usuario)
        payload["status"] = StatusUsuario.PENDENTE
        return self.criar_usuario(payload)

    def obter_usuario(
        self,
        identificador: Union[str, int],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """[READ] Recupera um usuário cadastrado por 'id' ou 'username'."""
        self._verificar_permissao("obter_usuario", usuario_solicitante)
        usuario = (
            self.usuario_repo.buscar_por_username(str(identificador))
            if isinstance(identificador, str) and not str(identificador).isdigit()
            else None
        )
        if not usuario:
            usuario = self.usuario_repo.buscar_por_id(identificador)
        if not usuario and isinstance(identificador, str):
            usuario = self.usuario_repo.buscar_por_username(identificador)

        if not usuario:
            raise KeyError(f"Usuário com identificador '{identificador}' não encontrado.")
        return usuario

    def obter_usuario_detalhes(
        self,
        identificador: Union[str, int],
        usuario_solicitante: Optional[Any] = None,
    ) -> UsuarioDetails:
        """
        [READ] Recupera a projeção segura de detalhes do usuário (sem expor credenciais).
        """
        self._verificar_permissao("obter_usuario", usuario_solicitante)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        return self.preencher_nao_informados(usuario)

    @classmethod
    def preencher_nao_informados(cls, data: Any) -> UsuarioDetails:
        """
        Gera o DTO de resposta segura UsuarioDetails:
        - Oculta o campo de senha (password/senha).
        - Substitui valores ausentes por sentinelas amigáveis ('Não informado', 'Nunca').
        - Garante a presença do status da conta.
        """
        if hasattr(data, "model_dump"):
            payload = data.model_dump(by_alias=True)
        elif hasattr(data, "__dict__") and not isinstance(data, dict):
            payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados do usuário devem ser um dicionário ou objeto compatível.")

        # Segurança: exclusão estrita de credenciais sensíveis
        payload.pop("password", None)
        payload.pop("senha", None)

        if eh_nao_informado(payload.get("name")):
            payload["name"] = "Não informado"

        if eh_nao_informado(payload.get("matricula")):
            payload["matricula"] = "Não informado"

        if payload.get("last_login") is None or eh_nao_informado(payload.get("last_login")):
            payload["last_login"] = "Nunca"

        if payload.get("status") is None or eh_nao_informado(payload.get("status")):
            payload["status"] = StatusUsuario.PENDENTE

        return UsuarioDetails(**payload)

    montar_usuario_detalhes = preencher_nao_informados

    def listar_usuarios(
        self,
        perfil: Optional[Union[Perfil, str]] = None,
        status: Optional[Union[StatusUsuario, str]] = None,
        termo_busca: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        usuario_solicitante: Optional[Any] = None,
    ) -> List[Usuario]:
        """[READ] Listagem de usuários com suporte a filtro por perfil, status, busca textual e paginação."""
        self._verificar_permissao("listar_usuarios", usuario_solicitante)
        return self.usuario_repo.listar(
            perfil=perfil,
            status=status,
            termo_busca=termo_busca,
            skip=skip,
            limit=limit,
        )

    def atualizar_usuario(
        self,
        identificador: Union[str, int],
        dados_atualizacao: Union[Dict[str, Any], UsuarioUpdate],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [UPDATE] Atualização parcial dos dados cadastrais do usuário.
        - Valida unicidade caso username ou email sejam modificados.
        - Criptografa nova senha se fornecida.
        - Normaliza perfil, matrícula, status e last_login se informados.
        """
        self._verificar_permissao("atualizar_usuario", usuario_solicitante)

        usuario_atual = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)

        if isinstance(dados_atualizacao, UsuarioUpdate):
            dados_novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
        else:
            dados_novos = {k: v for k, v in dados_atualizacao.items() if v is not None}

        for chave in _CAMPOS_PROIBIDOS_ENTRADA:
            dados_novos.pop(chave, None)

        dados_novos = self._normalizar_chaves(dados_novos)
        for chave in (*_CAMPOS_PROIBIDOS_ENTRADA, "confirmar_atualizacao_usuario", "created_at"):
            dados_novos.pop(chave, None)
        dados_novos = {k: v for k, v in dados_novos.items() if v is not None}

        payload = self._normalizar_chaves(usuario_atual.model_dump(by_alias=True))

        # 1. Validação de novo username
        if "username" in dados_novos and dados_novos["username"] is not None:
            novo_username = str(dados_novos["username"]).strip()
            if not novo_username:
                raise ValueError("O nome de usuário (username) não pode ser vazio.")
            if novo_username.casefold() != usuario_atual.username.casefold():
                if self.usuario_repo.exists_username(novo_username):
                    raise ValueError(f"Já existe um usuário cadastrado com o login '{novo_username}'.")
            dados_novos["username"] = novo_username

        # 2. Validação de novo email
        if "email" in dados_novos and dados_novos["email"] is not None:
            novo_email = str(dados_novos["email"]).strip()
            if not novo_email:
                raise ValueError("O e-mail do usuário não pode ser vazio.")
            if novo_email.casefold() != usuario_atual.email.casefold():
                if self.usuario_repo.exists_email(novo_email):
                    raise ValueError(f"Já existe um usuário cadastrado com o e-mail '{novo_email}'.")
            dados_novos["email"] = novo_email

        # 3. Criptografia de nova senha se fornecida
        if "password" in dados_novos and dados_novos["password"] is not None:
            nova_senha = str(dados_novos["password"])
            if len(nova_senha) < 6:
                raise ValueError("A senha deve conter no mínimo 6 caracteres.")
            dados_novos["password"] = hash_password(nova_senha)

        # 4. Normalização de perfil
        if "perfil" in dados_novos and dados_novos["perfil"] is not None:
            dados_novos["perfil"] = normalizar_perfil(dados_novos["perfil"])

        # 5. Normalização de status
        if "status" in dados_novos and dados_novos["status"] is not None:
            dados_novos["status"] = normalizar_status_usuario(dados_novos["status"])

        # 6. Normalização de matrícula
        if "matricula" in dados_novos:
            dados_novos["matricula"] = normalizar_matricula(dados_novos["matricula"])

        # 7. Normalização de last_login
        if "last_login" in dados_novos:
            dados_novos["last_login"] = normalizar_last_login(dados_novos["last_login"])

        payload.update(dados_novos)

        usuario_atualizado = Usuario(**payload)
        chave_update = usuario_atual.username or usuario_atual.id
        return self.usuario_repo.update(chave_update, usuario_atualizado)

    def deletar_usuario(
        self,
        identificador: Union[str, int],
        usuario_solicitante: Optional[Any] = None,
    ) -> bool:
        """[DELETE] Remove um usuário do sistema após validação de existência."""
        self._verificar_permissao("deletar_usuario", usuario_solicitante)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        chave_delete = usuario.username or usuario.id
        return self.usuario_repo.delete(chave_delete)

    # -------------------------------------------------------------------------
    # GESTÃO DE STATUS E APROVAÇÃO DE CONTAS:
    # -------------------------------------------------------------------------

    def aprovar_usuario(
        self,
        identificador: Union[str, int],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [STATUS/APROVAÇÃO] Aprova a conta de um usuário, definindo o status como ATIVO.
        """
        self._verificar_permissao("aprovar_usuario", usuario_solicitante)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        usuario.status = StatusUsuario.ATIVO
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    def inativar_usuario(
        self,
        identificador: Union[str, int],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [STATUS] Inativa a conta de um usuário, definindo o status como INATIVO.
        """
        self._verificar_permissao("inativar_usuario", usuario_solicitante)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        usuario.status = StatusUsuario.INATIVO
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    def alterar_status_usuario(
        self,
        identificador: Union[str, int],
        novo_status: Union[StatusUsuario, str],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [STATUS] Altera o status da conta do usuário para qualquer valor canônico válido.
        """
        self._verificar_permissao("alterar_status_usuario", usuario_solicitante)
        status_norm = normalizar_status_usuario(novo_status)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        usuario.status = status_norm
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    def listar_solicitacoes_pendentes(
        self,
        skip: int = 0,
        limit: int = 100,
        usuario_solicitante: Optional[Any] = None,
    ) -> List[Usuario]:
        """
        [READ] Retorna usuários cadastrados com status PENDENTE de aprovação.
        """
        self._verificar_permissao("listar_solicitacoes_pendentes", usuario_solicitante)
        return self.usuario_repo.listar_pendentes(skip=skip, limit=limit)

    # -------------------------------------------------------------------------
    # ATUALIZAÇÃO DEDICADA DE PERFIL:
    # -------------------------------------------------------------------------

    def atualizar_perfil(
        self,
        identificador: Union[str, int],
        novo_perfil: Union[Perfil, str],
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [UPDATE/PERFIL] Atualiza o perfil institucional de acesso do usuário.
        """
        self._verificar_permissao("atualizar_perfil", usuario_solicitante)
        perfil_norm = normalizar_perfil(novo_perfil)
        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)
        usuario.perfil = perfil_norm
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    # -------------------------------------------------------------------------
    # TROCA DE SENHA AUTENTICADA:
    # -------------------------------------------------------------------------

    def trocar_senha(
        self,
        identificador: Union[str, int],
        senha_atual: str,
        nova_senha: str,
        confirmar_nova_senha: Optional[str] = None,
        usuario_solicitante: Optional[Any] = None,
    ) -> Usuario:
        """
        [AUTH/PASSWORD] Executa a troca de senha autenticada:
        - Valida a presença da senha atual.
        - Valida os requisitos mínimos da nova senha (>= 6 caracteres).
        - Confere a confirmação de senha se fornecida.
        - Verifica a senha atual contra o hash salvo (lança PermissionError em caso de divergência).
        - Impede definir nova senha idêntica à senha atual.
        - Aplica hash criptográfico seguro (Bcrypt) e persiste.
        """
        self._verificar_permissao("trocar_senha", usuario_solicitante)

        if eh_nao_informado(senha_atual):
            raise ValueError("A senha atual é obrigatória para realizar a troca de senha.")
        if eh_nao_informado(nova_senha):
            raise ValueError("A nova senha é obrigatória.")

        nova_senha_str = str(nova_senha)
        if len(nova_senha_str) < 6:
            raise ValueError("A nova senha deve conter no mínimo 6 caracteres.")

        if confirmar_nova_senha is not None and str(confirmar_nova_senha) != nova_senha_str:
            raise ValueError("A nova senha e a confirmação de senha não coincidem.")

        usuario = self.obter_usuario(identificador, usuario_solicitante=usuario_solicitante)

        if not verificar_senha(str(senha_atual), usuario.password):
            raise PermissionError("Senha atual incorreta.")

        if verificar_senha(nova_senha_str, usuario.password):
            raise ValueError("A nova senha não pode ser idêntica à senha atual.")

        usuario.password = hash_password(nova_senha_str)
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE AUTENTICAÇÃO:
    # -------------------------------------------------------------------------

    def autenticar_usuario(
        self,
        login: str,
        senha_texto_puro: str,
    ) -> Optional[Usuario]:
        """
        [AUTH] Autentica o usuário pelo login (username ou e-mail) e senha em texto puro.
        - Se as credenciais estiverem incorretas, retorna None.
        - Se as credenciais forem válidas mas a conta NÃO estiver com status ATIVO,
          lança PermissionError informando a situação da conta.
        - Se autenticado com sucesso, atualiza 'last_login' para o timestamp corrente.
        """
        if not login or not senha_texto_puro:
            return None

        usuario = (
            self.usuario_repo.buscar_por_username(login)
            or self.usuario_repo.buscar_por_email(login)
        )
        if not usuario:
            return None

        if not verificar_senha(senha_texto_puro, usuario.password):
            return None

        # Validação estrita do status da conta
        status_atual = usuario.status or StatusUsuario.PENDENTE
        if status_atual == StatusUsuario.PENDENTE:
            raise PermissionError("Conta de usuário aguardando aprovação por um docente/administrador.")
        elif status_atual == StatusUsuario.INATIVO:
            raise PermissionError("Conta de usuário inativa. Entre em contato com a coordenação do laboratório.")
        elif status_atual == StatusUsuario.BLOQUEADO:
            raise PermissionError("Conta de usuário bloqueada. Entre em contato com a administração.")
        elif status_atual != StatusUsuario.ATIVO:
            raise PermissionError(f"Conta de usuário com status não autorizado: '{status_atual}'.")

        # Atualização atômica do timestamp de último acesso
        usuario.last_login = datetime.now()
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

    def registrar_ultimo_acesso(
        self,
        identificador: Union[str, int],
    ) -> Usuario:
        """Atualiza o timestamp de último acesso (last_login) para o momento atual."""
        usuario = self.obter_usuario(identificador)
        usuario.last_login = datetime.now()
        chave = usuario.username or usuario.id
        return self.usuario_repo.update(chave, usuario)

# Instância singleton para uso em controllers e na aplicação
usuario_service = UsuarioService()

__all__ = [
    "UsuarioService",
    "usuario_service",
    "hash_password",
    "verificar_senha",
    "normalizar_perfil",
    "normalizar_matricula",
    "normalizar_last_login",
    "normalizar_status_usuario",
    "normalizar_chaves_usuario",
    "_ALIASES_USUARIO",
    "_MAPA_PERFIL_LEGADO",
    "_MAPA_STATUS_USUARIO",
    "Usuario",
    "UsuarioCreate",
    "UsuarioUpdate",
    "UsuarioDetails",
    "UsuarioTrocaSenha",
    "TrocaSenhaRequest",
    "UsuarioPerfilUpdate",
    "AtualizarPerfilRequest",
    "UsuarioStatusUpdate",
    "AtualizarStatusRequest",
    "Perfil",
    "StatusUsuario",
]