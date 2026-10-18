from enum import Enum

class EtapaReagente(str, Enum):
    EXTRAÇÃO = 'Extração'
    PCR = 'PCR'
    ELETRO = 'ELETRO'