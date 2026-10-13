from enum import Enum
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class Perfil(str, Enum):
    DOCENTE = "docente"
    POS_GRADUANDO = "pos_graduando"
    BOLSISTA_PIBITI = "bolsista_pibiti"
    BOLSISTA_PIBIC = "bolsista_pibic"
    BOLSISTA_EXTERNO = "bolsista_externo"

class Usuario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[Union[int, str]] = Field(default=None, alias="_id")
    username: str = Field(..., alias="usuario")
    name: Optional[str] = Field(default=None, alias="nome")
    email: EmailStr
    password: str = Field(..., alias="senha") # adicionar segurança
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[Union[datetime, str]] = Field(default=None) # nasce como 'Nunca' / None
    perfil: Perfil
    matricula: Optional[Union[int, str]] = None

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Normalização e Mapeamento de 'perfil':
    #      - Sanitizar strings recebidas (remoção de espaços, acentos e conversão para minúsculas).
    #      - Mapear termos legados do banco ou planilhas para o Enum 'Perfil':
    #        * 'professor', 'prof', 'doscente', 'pos_docente' -> Perfil.DOCENTE
    #        * 'mestrando', 'doutorando', 'pos_graduacao', 'mestrado', 'doutorado' -> Perfil.POS_GRADUANDO
    #        * 'bolsista_pibiti', 'bolsista_pibit', 'pibit', 'pibiti' -> Perfil.BOLSISTA_PIBITI
    #        * 'bolsista_pibic', 'pibic' -> Perfil.BOLSISTA_PIBIC
    #        * 'bolsista_externo', 'externo' -> Perfil.BOLSISTA_EXTERNO
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/usuario_service.py' (ou
    #     serviço de autenticação/gestão de perfis de usuário).
    #   - Camada de Controladores: 'backend/src/controllers/usuario_controller.py'
    #     e formulário de login/cadastro de usuários ('streamlit/widgets.py').
    # =========================================================================