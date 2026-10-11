from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from pydantic import Field

class Reagente(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    #obrigatorios
    id: Optional[int] = None # gerado automaticamente autoincrementado
    reagente_codigo: str = Field(..., alias="codigo") # alarmar se não informado
    reagente_nome: str = Field(..., alias="nome") # alarmar se não informado #agrupar por nome, pode escolher como se fosse enum e caso não tenha na lista criar novo
    numero_lote: str # alarmar se não informado # pode ter mais de um numero de lote para o mesmo nome, mas nao pode se repetir o numero do lote para o mesmo nome.
    marca: str # alarmar se não informado # pode ter mais de uma marca para o mesmo nome e uma marca pode ter mais de um reagente
    data_validade: date # alarmar se não informado #nao pode ser inferior a data atual
    quantidade_unidade: int # alarmar se não informado
    reagente_local_armazenamento: str = Field(..., alias="local_armazenamento") #alarmar se não informado
       
    #opcionais
    reagente_id: Optional[str] = Field(default=None, alias="_id") # se o laboratorio tiver um id padrao pode ser informado
    quantidade_volume: Optional[float] = None # pode ter mais de uma quantidade para o mesmo nome
    reagente_etapa: Optional[str] = Field(default=None, alias="etapa")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes")