from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from src.models.Usuario.enums.Perfil import Perfil
from src.models.Usuario.enums.StatusUsuario import StatusUsuario

class UsuarioCreate(BaseModel):
    """
    Schema de entrada para NOVOS cadastros de usuários (estrito):
    - Campos obrigatórios não possuem valor padrão e devem ser enviados explicitamente.
    - Senha deve ser enviada em texto puro para ser hasheada na camada de serviço.
    - Validações de unicidade (login e e-mail) e normalização de perfil são tratadas pelo service.
    - A chave primária ('id'/'_id') NÃO é aceita: é gerada automaticamente pelo banco.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    username: str = Field(
        ..., 
        alias="usuario", 
        min_length=1, 
        description="Nome de usuário / login único de acesso ao sistema"
    )
    name: Optional[str] = Field(
        default=None, 
        alias="nome", 
        description="Nome completo do usuário"
    )
    email: EmailStr = Field(
        ..., 
        description="E-mail institucional ou de contato do usuário"
    )
    password: str = Field(
        ..., 
        alias="senha", 
        min_length=6, 
        description="Senha de acesso em texto puro (a ser hasheada pelo service)"
    )
    perfil: Perfil = Field(
        ..., 
        description="Perfil de acesso e permissões institucionais do usuário"
    )
    matricula: Optional[str] = Field(
        default=None, 
        description="Matrícula institucional padronizada como texto"
    )
    status: StatusUsuario = StatusUsuario.PENDENTE
    confirmar_novo_usuario: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Hashing e Segurança de Senha:
    #      - Criptografar a senha recebida em texto puro utilizando algoritmo
    #        seguro (ex: Bcrypt, Argon2) antes de persistir no banco de dados.
    #      - Nunca armazenar a senha em texto puro.
    #   2. Validação de Unicidade:
    #      - Verificar duplicidade de 'username' (usuário) e 'email' antes de salvar.
    #   3. Normalização e Mapeamento de 'perfil':
    #      - Sanitizar strings recebidas (remoção de espaços, acentos e conversão para minúsculas).
    #      - Mapear termos legados para o Enum 'Perfil':
    #        * 'professor', 'prof', 'doscente', 'pos_docente' -> Perfil.DOCENTE
    #        * 'mestrando', 'doutorando', 'pos_graduacao', 'mestrado', 'doutorado' -> Perfil.POS_GRADUANDO
    #        * 'bolsista_pibiti', 'bolsista_pibit', 'pibit', 'pibiti' -> Perfil.BOLSISTA_PIBITI
    #        * 'bolsista_pibic', 'pibic' -> Perfil.BOLSISTA_PIBIC
    #        * 'bolsista_externo', 'externo' -> Perfil.BOLSISTA_EXTERNO
    #   4. Padronização de 'matricula':
    #      - Converter inteiros ou strings recebidas para string limpa (evitando perda de zeros à esquerda).
    #      - Tratar sentinelas ("-", "NI", "None", "") como None.
    #   5. Inicialização de Auditoria:
    #      - Atribuir 'created_at' no momento do cadastro e inicializar 'last_login' como None.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/usuario_service.py' (criar_usuario / registrar_usuario).
    #   - Camada de Controladores: 'backend/src/controllers/usuario_controller.py'.
    # =========================================================================