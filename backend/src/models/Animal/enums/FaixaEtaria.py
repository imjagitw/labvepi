from enum import Enum

class FaixaEtaria(str, Enum): 
    FILHOTE = 'Filhote'
    JUVENIL = 'Juvenil'
    JOVEM = 'Jovem'
    SUB_ADULTO = 'Sub Adulto'
    ADULTO = 'Adulto'
    SENIL = 'Senil'
    IDOSO = 'Idoso'
    POTRO = 'Potro'
    NINHEGO = 'Ninhego'
    NAO_INFORMADO = 'Não Informado'