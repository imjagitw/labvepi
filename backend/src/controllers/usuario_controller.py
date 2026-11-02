from typing import Optional, List
from fastapi import Query, status
from pydantic import BaseModel, Field
from src.controllers.response_controller import (
    criar_router,
    RESPOSTAS_CRIAR,
    RESPOSTAS_LISTAR,
    RESPOSTAS_OBTER,
    RESPOSTAS_ATUALIZAR,
    RESPOSTAS_DELETAR,
)
from src.services.usuario_service import (
    usuario_service,
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioDetails,
    UsuarioTrocaSenha,
    UsuarioPerfilUpdate,
    UsuarioStatusUpdate,
    Perfil,
    StatusUsuario,
)

router = criar_router(prefix="/usuario", tags=["Usuário"])

class LoginRequest(BaseModel):
    """Schema para autenticação de usuário via corpo da requisição."""
    login: str = Field(..., description="Nome de usuário (username) ou e-mail cadastrado")
    senha: str = Field(..., description="Senha de acesso em texto puro")

@router.post(
    "/",
    response_model=UsuarioDetails,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Cadastrar um novo usuário",
    description=(
        "Cria um novo usuário no sistema, aplicando validações de unicidade, normalização de perfil e hashing de senha. "
        "A chave primária (_id) é gerada automaticamente pelo banco e não deve ser informada."
    ),
)
def criar_usuario(
    usuario_input: UsuarioCreate,
):
    usuario = usuario_service.criar_usuario(dados_usuario=usuario_input)
    return usuario_service.preencher_nao_informados(usuario)

@router.post(
    "/solicitar-cadastro",
    response_model=UsuarioDetails,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Solicitar novo cadastro de usuário",
    description=(
        "Registra uma solicitação pública de cadastro. "
        "A conta é criada automaticamente com status 'Pendente', aguardando aprovação por um docente ou administrador."
    ),
)
def solicitar_cadastro(
    usuario_input: UsuarioCreate,
):
    usuario = usuario_service.solicitar_cadastro(dados_usuario=usuario_input)
    return usuario_service.preencher_nao_informados(usuario)

@router.get(
    "/",
    response_model=List[UsuarioDetails],
    responses=RESPOSTAS_LISTAR,
    summary="Listar usuários com filtros",
    description="Retorna a lista de usuários cadastrados com suporte a filtro por perfil, status da conta, busca textual e paginação.",
)
def listar_usuarios(
    perfil: Optional[Perfil] = Query(None, description="Filtrar por perfil de usuário"),
    status: Optional[StatusUsuario] = Query(None, description="Filtrar por status da conta (Ativo, Inativo, Pendente, Bloqueado)"),
    termo_busca: Optional[str] = Query(None, description="Busca textual por ID, login, nome, e-mail ou matrícula"),
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    usuarios = usuario_service.listar_usuarios(
        perfil=perfil,
        status=status,
        termo_busca=termo_busca,
        skip=skip,
        limit=limit,
    )
    return [usuario_service.preencher_nao_informados(u) for u in usuarios]

@router.get(
    "/pendentes",
    response_model=List[UsuarioDetails],
    responses=RESPOSTAS_LISTAR,
    summary="Listar solicitações de cadastro pendentes",
    description="Retorna todas as contas de usuários com status 'Pendente' que aguardam aprovação.",
)
def listar_pendentes(
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    usuarios = usuario_service.listar_solicitacoes_pendentes(skip=skip, limit=limit)
    return [usuario_service.preencher_nao_informados(u) for u in usuarios]

@router.post(
    "/login",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_OBTER,
    summary="Autenticar usuário",
    description="Valida as credenciais de acesso (login e senha) e o status da conta (exige conta 'Ativo'), registrando a data/hora do último acesso.",
)
def autenticar_usuario(
    dados_login: Optional[LoginRequest] = None,
    login: Optional[str] = Query(None, description="Nome de usuário ou e-mail (caso enviado via query)"),
    senha: Optional[str] = Query(None, description="Senha de acesso em texto puro (caso enviada via query)"),
):
    login_val = (dados_login.login if dados_login else None) or login
    senha_val = (dados_login.senha if dados_login else None) or senha
    if not login_val or not senha_val:
        raise ValueError("Login e senha são obrigatórios para autenticação.")

    usuario = usuario_service.autenticar_usuario(login=login_val, senha_texto_puro=senha_val)
    if not usuario:
        raise PermissionError("Credenciais inválidas: login ou senha incorretos.")

    return usuario_service.preencher_nao_informados(usuario)

@router.get(
    "/{identificador}",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_OBTER,
    summary="Buscar usuário por ID ou username",
    description="Recupera um usuário cadastrado pelo seu ID numérico ou login (username).",
)
def obter_usuario(identificador: str):
    return usuario_service.obter_usuario_detalhes(identificador)

@router.get(
    "/{identificador}/detalhes",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_OBTER,
    summary="Buscar detalhes completos do usuário por ID ou username",
    description="Recupera a visão detalhada do usuário com saneamento explícito de campos não preenchidos ('Não informado', 'Nunca').",
)
def obter_usuario_detalhes(identificador: str):
    return usuario_service.obter_usuario_detalhes(identificador)

@router.put(
    "/{identificador}",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar usuário",
    description=(
        "Atualiza dados cadastrais de um usuário existente, permitindo alterar apenas um campo ou mais e deixando o restante inalterado. "
        "Valida unicidade e re-criptografa senha se fornecida. "
        "O usuário é identificado na rota; a chave primária (_id) é imutável."
    ),
)
def atualizar_usuario(
    identificador: str,
    usuario_update: UsuarioUpdate,
):
    usuario = usuario_service.atualizar_usuario(
        identificador=identificador,
        dados_atualizacao=usuario_update,
    )
    return usuario_service.preencher_nao_informados(usuario)

@router.patch(
    "/{identificador}",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualização parcial de usuário",
    description=(
        "Aplica alterações parciais nos dados cadastrais de um usuário existente, alterando apenas os campos fornecidos e mantendo os demais inalterados. "
        "O usuário é identificado na rota; a chave primária (_id) é imutável."
    ),
)
def atualizar_usuario_parcial(
    identificador: str,
    usuario_update: UsuarioUpdate,
):
    usuario = usuario_service.atualizar_usuario(
        identificador=identificador,
        dados_atualizacao=usuario_update,
    )
    return usuario_service.preencher_nao_informados(usuario)

@router.patch(
    "/{identificador}/aprovar",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Aprovar e ativar conta de usuário",
    description="Aprova a solicitação de cadastro do usuário e define seu status como 'Ativo', liberando o acesso ao sistema.",
)
def aprovar_usuario(identificador: str):
    usuario = usuario_service.aprovar_usuario(identificador=identificador)
    return usuario_service.preencher_nao_informados(usuario)

@router.patch(
    "/{identificador}/inativar",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Inativar conta de usuário",
    description="Inativa o acesso de um usuário ao sistema, definindo seu status como 'Inativo'.",
)
def inativar_usuario(identificador: str):
    usuario = usuario_service.inativar_usuario(identificador=identificador)
    return usuario_service.preencher_nao_informados(usuario)

@router.patch(
    "/{identificador}/status",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Alterar status da conta do usuário",
    description="Altera formalmente o status da conta do usuário para qualquer valor permitido (Ativo, Inativo, Pendente, Bloqueado).",
)
def alterar_status_usuario(
    identificador: str,
    dados_status: UsuarioStatusUpdate,
):
    usuario = usuario_service.alterar_status_usuario(
        identificador=identificador,
        novo_status=dados_status.status,
    )
    return usuario_service.preencher_nao_informados(usuario)

@router.patch(
    "/{identificador}/perfil",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar perfil de acesso institucional do usuário",
    description="Altera especificamente o perfil institucional (papel/função) atribuído ao usuário no sistema.",
)
def atualizar_perfil(
    identificador: str,
    dados_perfil: UsuarioPerfilUpdate,
):
    usuario = usuario_service.atualizar_perfil(
        identificador=identificador,
        novo_perfil=dados_perfil.perfil,
    )
    return usuario_service.preencher_nao_informados(usuario)

@router.post(
    "/{identificador}/trocar-senha",
    response_model=UsuarioDetails,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Trocar senha de acesso do usuário",
    description="Efetua a alteração segura da senha mediante validação obrigatória da senha atual e criptografia da nova credencial.",
)
def trocar_senha(
    identificador: str,
    dados_troca: UsuarioTrocaSenha,
):
    usuario = usuario_service.trocar_senha(
        identificador=identificador,
        senha_atual=dados_troca.senha_atual,
        nova_senha=dados_troca.nova_senha,
        confirmar_nova_senha=dados_troca.confirmar_nova_senha,
    )
    return usuario_service.preencher_nao_informados(usuario)

@router.delete(
    "/{identificador}",
    responses=RESPOSTAS_DELETAR,
    summary="Remover usuário",
    description="Remove um usuário cadastrado pelo seu ID numérico ou username.",
)
def deletar_usuario(identificador: str):
    usuario_service.deletar_usuario(identificador)
    return None