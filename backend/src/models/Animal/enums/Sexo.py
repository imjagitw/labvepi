from enum import Enum

class Sexo(str, Enum): 
    MACHO = 'Macho'
    FEMEA = 'Fêmea'
    INDETERMINADO = 'Indeterminado'
    NAO_INFORMADO = 'Não informado'