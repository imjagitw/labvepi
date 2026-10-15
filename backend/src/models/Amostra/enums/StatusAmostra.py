from enum import Enum 

class StatusAmostra(str, Enum): 
    DISPONIVEL = 'Disponível'
    RESERVADA = 'Reservada'
    EM_USO = 'Em uso'
    PERDIDA = 'Perdida'
    ESGOTADA = 'Esgotada'