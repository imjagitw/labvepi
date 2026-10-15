from enum import Enum

class Funcao(str, Enum): 
    PET = 'Pet'
    TRABALHO = 'Trabalho'
    LAZER = 'Lazer'
    REPRODUCAO = 'Reprodução'
    CONSERVACAO = 'Conservação / Zoológico'
    OUTRO = 'Outro'
    NAO_APLICAVEL = 'Não aplicável'