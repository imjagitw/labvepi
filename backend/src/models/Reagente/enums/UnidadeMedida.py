from enum import Enum

class UnidadeMedida(str, Enum):
    ML = 'ml'
    L = 'L'
    UL = 'µl'
    G = 'g'
    MG = 'mg'
    KG = 'kg'
    UNIDADE = 'un'