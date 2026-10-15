from enum import Enum

class RegimeVida(str, Enum):
    VIDA_LIVRE = 'Vida livre'
    CATIVEIRO = 'Cativeiro'
    DOMICILIADO = 'Domiciliado'
    NAO_INFORMADO = 'Não informado'