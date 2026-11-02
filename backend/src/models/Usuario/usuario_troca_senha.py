from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class UsuarioTrocaSenha(BaseModel):
    """
    Schema de requisição para troca de senha de usuário:
    - Exige a senha atual para validação de segurança.
    - Exige nova senha com requisitos mínimos de comprimento (mínimo 6 caracteres).
    - Opcionalmente aceita confirmação da nova senha.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    senha_atual: str = Field(
        ...,
        alias="senha_antiga",
        description="Senha de acesso atual em texto puro para validação de segurança"
    )
    nova_senha: str = Field(
        ...,
        min_length=6,
        description="Nova senha de acesso em texto puro (mínimo de 6 caracteres)"
    )
    confirmar_nova_senha: Optional[str] = Field(
        default=None,
        description="Confirmação da nova senha em texto puro"
    )

# Alias para compatibilidade de nomenclatura
TrocaSenhaRequest = UsuarioTrocaSenha
