from enum import Enum

class DestinoAmostra(str, Enum): 
    BIOBANCO_UFPI = 'Biobanco UFPI'
    BIOBANCO_UFPA = 'Biobanco UFPA'
    FIOFRUZ_AM = 'Fiofruz AM'
    LASAN_UFPI = 'LASAN UFPI'
    LAPATO_UFPI = 'LAPATO UFPI'
    LAPATO_UFPA = 'LAPATO UFPA'
    LAB_VIGILANCIA_EPIZOOTIAS_UFPI = 'LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI'
    OUTRO = 'Outro'