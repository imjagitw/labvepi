from __future__ import annotations
from typing import Optional, Union, List, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie.enums.Classe import Classe

if TYPE_CHECKING:
    from src.models.Animal.animal import Animal

class EspecieDetails(BaseModel):
    """
    Schema de resposta detalhada de uma espécie:
    - Dados taxonômicos (id, nome comum, nome científico, classe).
    - Quantidade total de animais cadastrados pertencentes à espécie.
    - Listagem completa dos animais cadastrados dessa espécie.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[Union[int, str]] = Field(default=None, alias="_id")
    nome_comum: str = Field(..., alias="nome")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Classe
    quantidade_animais: int = Field(..., description="Quantidade total de animais cadastrados desta espécie")
    animais: List[Animal] = Field(default_factory=list, description="Lista dos animais pertencentes a esta espécie")
