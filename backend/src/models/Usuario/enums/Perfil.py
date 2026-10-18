from enum import Enum

class Perfil(str, Enum):
    DOCENTE = "docente"
    POS_GRADUANDO = "pos_graduando"
    BOLSISTA_PIBITI = "bolsista_pibiti"
    BOLSISTA_PIBIC = "bolsista_pibic"
    BOLSISTA_EXTERNO = "bolsista_externo"