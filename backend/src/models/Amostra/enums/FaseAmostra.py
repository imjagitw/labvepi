from enum import Enum

class FaseAmostra(str, Enum): 
    EXTRACAO = 'Extração'
    PCR = 'PCR'
    ELETRO = 'ELETRO'