from typing import Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie import Classe

class EspecieUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nome_comum: str = Field(..., alias="nome")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Union[Classe, str]
    confirmar_atualizacao_especie: bool = False