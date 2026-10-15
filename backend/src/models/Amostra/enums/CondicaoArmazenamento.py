from enum import Enum

class CondicaoArmazenamento(str, Enum): 
    TEMPERATURA_AMBIENTE = 'Temperatura ambiente'
    REFRIGERADA = 'Refrigerada'
    CONGELADA = 'Congelada'
    SEM_IDENTIFICACAO = 'Sem identificação'
    COAGULADA = 'Coagulada'
    HEMOLISADA = 'Hemolisada'
    NITROGENIO_LIQUIDO = 'Nitrogênio líquido'
    GELO_SECO = 'Gelo seco'