from enum import Enum

class TesteLaboratorial(str, Enum):
    PCR = 'PCR'
    SOROLOGICO = 'Sorológico'
    COPROPARASITOLOGICO = 'Coproparasitológico'
    HEMOPARASITO_EM_LAMINA = 'Hemoparasito em lâmina'
    OUTRO = 'Outro'