from enum import Enum

class StatusUsuario(str, Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    PENDENTE = "Pendente"
    BLOQUEADO = "Bloqueado"