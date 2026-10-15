from enum import Enum

class StatusVital(str, Enum): 
    VIVO = 'Vivo'
    MORTO = 'Morto'
    EUTANASIADO = 'Eutanasiado'
    NAO_INFORMADO = 'Não informado'