from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field
from datetime import date
from typing import Optional, List

class Reagente(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # obrigatorios
    id: Optional[int] = None # gerado automaticamente autoincrementado
    reagente_codigo: str = Field(..., alias="codigo") # alarmar se não informado
    reagente_nome: str = Field(..., alias="nome") # alarmar se não informado
    numero_lote: str # alarmar se não informado
    marca: str # alarmar se não informado
    data_validade: date # alarmar se não informado
    quantidade_unidade: int # alarmar se não informado
    reagente_local_armazenamento: str = Field(..., alias="local_armazenamento")
    
    # opcionais
    reagente_id: Optional[str] = Field(default=None, alias="_id") # se o laboratorio tiver um id padrao pode ser informado
    quantidade_volume: Optional[float] = None
    unidade_medida: str = Field(default="ml", alias="unidade")
    reagente_etapa: Optional[str] = Field(default=None, alias="etapa")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    @field_validator("data_validade")
    @classmethod
    def validar_data_validade(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("A data de validade não pode ser inferior à data atual.")
        return v