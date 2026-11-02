from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from src.models.Usuario.enums.Perfil import Perfil
from src.models.Usuario.enums.StatusUsuario import StatusUsuario

class UsuarioUpdate(BaseModel):
    """
    Schema de atualização parcial de dados cadastrais de usuários:
    - Apenas os campos enviados são alterados (PATCH/PUT parcial).
    - O usuário é identificado pelo identificador na rota; a chave primária
      ('id'/'_id', gerada pelo banco) é imutável e não é aceita no corpo.
    - Atualização de senha opcional: caso enviada, deve ser hasheada na camada de serviço.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    username: Optional[str] = Field(
        default=None, 
        alias="usuario", 
        description="Nome de usuário / login de acesso"
    )

    # Atualização parcial: apenas os campos enviados são alterados
    name: Optional[str] = Field(
        default=None, 
        alias="nome", 
        description="Nome completo atualizado do usuário"
    )
    email: Optional[EmailStr] = Field(
        default=None, 
        description="Novo e-mail do usuário"
    )
    password: Optional[str] = Field(
        default=None, 
        alias="senha", 
        min_length=6, 
        description="Nova senha em texto puro (a ser hasheada pelo service se fornecida)"
    )
    perfil: Optional[Perfil] = Field(
        default=None, 
        description="Novo perfil de acesso do usuário"
    )
    matricula: Optional[str] = Field(
        default=None, 
        description="Nova matrícula institucional padronizada como texto"
    )
    last_login: Optional[datetime] = Field(
        default=None, 
        description="Data e hora do último acesso (se atualizado manualmente ou por rotina)"
    )
    status: Optional[StatusUsuario] = Field(
        default=None,
        description="Novo status do usuário"
    )
    confirmar_atualizacao_usuario: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Atualização Parcial e Validação de Unicidade:
    #      - Atualizar apenas os campos explicitamente informados no payload.
    #      - Se 'email' ou 'username' forem alterados, verificar unicidade no repositório.
    #   2. Criptografia de Nova Senha:
    #      - Se 'password' (senha) for informada, aplicar hash criptográfico (ex: Bcrypt)
    #        antes de persistir a alteração.
    #   3. Normalização de 'perfil' e 'matricula':
    #      - Re-sanitizar e mapear string de perfil para Enum Perfil, se informada.
    #      - Tratar sentinelas de matrícula ("-", "NI", "None", "") convertendo para None.
    #   4. Normalização de 'last_login':
    #      - Converter sentinelas ("Nunca", vazios) para None e aceitar ISO datetime.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/usuario_service.py' (atualizar_usuario).
    #   - Camada de Controladores: 'backend/src/controllers/usuario_controller.py'.
    # =========================================================================
