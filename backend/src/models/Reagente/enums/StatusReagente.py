from enum import Enum

class StatusReagente(str, Enum):
    DISPONIVEL = "Disponível"
    VENCIDO = "Vencido"
    RESERVADO = "Reservado"
    ESGOTADO = "Esgotado"