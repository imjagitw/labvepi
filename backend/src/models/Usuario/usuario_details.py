from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from src.models.Usuario.enums.StatusUsuario import StatusUsuario
from src.models.Usuario.enums.Perfil import Perfil

class UsuarioDetails(BaseModel):
    """
    Schema de resposta detalhada de um usuário (projeção pública/segura):
    - Todas as informações cadastrais e administrativas do usuário.
    - Saneamento explícito de campos não informados ('Não informado', 'Nunca').
    - Exclusão estrita de campos sensíveis de credenciais (password / hash de senha).
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação
    id: Optional[Union[int, str]] = Field(
        default=None, 
        alias="_id", 
        description="Identificador sequencial ou ObjectId no banco"
    )
    username: str = Field(
        ..., 
        alias="usuario", 
        description="Nome de usuário / identificador de login no sistema"
    )

    # Dados cadastrais e institucionais
    name: Optional[Union[str, None]] = Field(
        default="Não informado", 
        alias="nome", 
        description="Nome completo do usuário ou 'Não informado'"
    )
    email: EmailStr = Field(
        ..., 
        description="E-mail institucional ou de contato cadastrado"
    )
    perfil: Union[Perfil, str] = Field(
        ..., 
        description="Perfil de acesso e permissões atribuídas no sistema"
    )
    matricula: Optional[Union[str, None]] = Field(
        default="Não informado", 
        description="Matrícula institucional padronizada ou 'Não informado'"
    )

    # Auditoria e acesso
    created_at: Optional[datetime] = Field(
        default=None, 
        description="Data e hora em que a conta foi criada"
    )
    last_login: Optional[Union[datetime, str]] = Field(
        default="Nunca", 
        description="Data e hora do último acesso registrado ou 'Nunca'"
    )
    status: Union[StatusUsuario, str] = Field(
        default=StatusUsuario.PENDENTE,
        description="Status do usuário (ativo, inativo, pendente, bloqueado)"
    )

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Exclusão Estrita de Credenciais Sensíveis:
    #      - Garantir que a senha (em texto puro ou hash) NUNCA seja retornada
    #        ou projetada no schema de detalhes.
    #   2. Saneamento de Campos Opcionais / Ausentes:
    #      - Preencher 'name' e 'matricula' com 'Não informado' caso nulos ou vazios.
    #      - Preencher 'last_login' com 'Nunca' caso o usuário ainda não tenha acessado.
    #   3. Formatação Amigável de Perfil:
    #      - Prover descrição textual amigável do perfil na camada de apresentação (UI).
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/usuario_service.py' (obter_usuario_detalhes).
    #   - Camada de Controladores: 'backend/src/controllers/usuario_controller.py'.
    # =========================================================================
