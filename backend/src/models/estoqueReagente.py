from src.models.reagente import Reagente
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from typing import Optional, List

class EstoqueReagente(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reagente_nome: str = Field(..., alias="nome")
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo")
    lotes: List[Reagente] = Field(default_factory=list)

    @field_validator("lotes")
    @classmethod
    def validar_lotes_unicos(cls, lotes: List[Reagente]) -> List[Reagente]:
        numeros_lotes = [lote.numero_lote for lote in lotes]
        if len(numeros_lotes) != len(set(numeros_lotes)):
            raise ValueError("Não pode haver números de lote repetidos para o mesmo reagente.")
        return lotes

    @computed_field
    @property
    def quantidade_total_unidades(self) -> int:
        return sum(lote.quantidade_unidade for lote in self.lotes)

    @computed_field
    @property
    def quantidade_total_volume(self) -> float:
        return sum((lote.quantidade_volume or 0.0) for lote in self.lotes)