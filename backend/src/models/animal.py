from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.models.especie import Classe

class Sexo(str, Enum): 
    MACHO = 'Macho'
    FEMEA = 'Fêmea'
    INDETERMINADO = 'Indeterminado'

class FaixaEtaria(str, Enum): 
    FILHOTE = 'Filhote'
    JUVENIL = 'Juvenil'
    SUB_ADULTO = 'Sub Adulto'
    ADULTO = 'Adulto'
    SENIL = 'Senil'

class Orgao(str, Enum): 
    UFPI = 'UFPI'
    NEPPAS = 'NEPPAS'
    IBAMA_CETAS_PI = 'IBAMA - CETAS - PI'
    IBAMA_CETAS_CE = 'IBAMA - CETAS - CE'
    IBAMA_CETAS_RN = 'IBAMA - CETAS - RN'
    SEMARH_CETAS_PI = 'SEMARH - CETAS - PI'
    UFPA = 'UFPA'
    UFRR = 'UFRR'
    UFAC = 'UFAC'
    UFOB = 'UFOB'
    DSEI_LESTE_AM = 'DSEI LESTE - AM'
    ZOOLOGICO_PI = 'ZOOLOGICO -PI'
    PARTICULAR = 'PARTICULAR'
    OUTRO = 'OUTRO'

class Funcao(str, Enum): 
    PET = 'Pet'
    TRABALHO = 'Trabalho'
    LAZER = 'Lazer'
    OUTRO = 'Outro'

class Status(str, Enum): 
    VIVO = 'Vivo'
    MORTO = 'Morto'

class Animal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # obrigatorios
    id: Optional[int] = None  # Autoincrementado no banco
    animal_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: AN001)")
    classe: Classe # definido com base na espécie
    nome_comum: str # nome comum da espécie
    nome_cientifico: str # nome científico da espécie
    sexo: Sexo # alarmar se não informado
    peso: float # opcao de nao aferido
    faixa_etaria: FaixaEtaria # calculado automaticamente se tiver idade # alarmar se não informado  
    orgao_origem: Orgao = Field(..., alias="orgao", description="Orgao de origem do animal") # alarmar se não informado
    local_origem: str # alarmar se não informado  
    funcao: Funcao # alarmar se não informado
    status: Status # alarmar se não informado  
    
    # opcionais
    animal_id_projeto: Optional[str] = None # id do projeto a que o animal pertence
    id_hvu: Optional[str] = None # id vindo do hvu # pode ser igual a microchip
    microchip: Optional[str] = None # microchip se houver # pode ser igual id_hvu
    idade: Optional[str] = None # definir formato anos/meses
    suspeita_clinica: Optional[str] = None       
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")