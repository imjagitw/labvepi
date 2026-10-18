from enum import Enum
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from src.models.Usuario.enums.Perfil import Perfil

class Usuario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[Union[int, str]] = Field(default=None, alias="_id")
    username: str = Field(..., alias="usuario")
    name: Optional[str] = Field(default=None, alias="nome")
    email: EmailStr
    password: str = Field(..., alias="senha") # adicionar segurança
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(default=None, description="Data e hora do último acesso")
    perfil: Perfil
    matricula: Optional[str] = Field(default=None, description="Matrícula institucional padronizada como texto")

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
    #   2. Padronização de 'matricula':
    #      - Converter inteiros ou strings recebidas para string limpa (evitando perda de zeros à esquerda).
    #      - Tratar sentinelas ("-", "NI", "None", "") como None.
    #
    #   3. Normalização de 'last_login':
    #      - Converter string literal "Nunca", sentinelas ou vazios para None.
    #      - Fazer parsing de strings de data/hora ISO ou datetime válido.
    #      - A formatação amigável ("Nunca") deve ser provida apenas na camada de apresentação (UI).
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/usuario_service.py' (ou
    #     serviço de autenticação/gestão de perfis de usuário).
    #   - Camada de Controladores: 'backend/src/controllers/usuario_controller.py'
    #     e formulário de login/cadastro de usuários ('streamlit/widgets.py').
    # =========================================================================