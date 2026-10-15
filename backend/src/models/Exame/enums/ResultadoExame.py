from enum import Enum

class ResultadoExame(str, Enum):
    POSITIVO = 'Positivo'
    NEGATIVO = 'Negativo'
    INCONCLUSIVO = 'Inconclusivo'
    AGUARDANDO = 'Aguardando Resultado'
    NAO_REALIZADO = 'Não Realizado'