from pydantic import BaseModel, ConfigDict, Field
from src.models.Usuario.enums.Perfil import Perfil

class UsuarioPerfilUpdate(BaseModel):
    """
    Schema de requisição para alteração semântica e dedicada do perfil de acesso de um usuário.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    perfil: Perfil = Field(
        ...,
        description="Novo perfil de acesso institucional do usuário"
    )

# Alias para flexibilidade de nomenclatura
AtualizarPerfilRequest = UsuarioPerfilUpdate
