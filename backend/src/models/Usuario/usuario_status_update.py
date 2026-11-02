from pydantic import BaseModel, ConfigDict, Field
from src.models.Usuario.enums.StatusUsuario import StatusUsuario

class UsuarioStatusUpdate(BaseModel):
    """
    Schema de requisição para alteração semântica e dedicada do status de um usuário
    (ativação, aprovação, inativação ou bloqueio).
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    status: StatusUsuario = Field(
        ...,
        description="Novo status da conta do usuário (Ativo, Inativo, Pendente, Bloqueado)"
    )

# Alias para flexibilidade de nomenclatura
AtualizarStatusRequest = UsuarioStatusUpdate
