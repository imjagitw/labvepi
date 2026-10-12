from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class Classe(str, Enum):
    AVES = 'Ave'
    MAMIFERO = 'Mamífero'
    REPTIL = 'Réptil'
    ANFIBIO = 'Anfíbio'
    PEIXE = 'Peixe'

class Especie(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    nome_comum: str
    nome_cientifico: str
    classe: Classe