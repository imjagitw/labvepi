from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union
from src.models.Especie.enums.Classe import Classe
from src.models.Animal import Funcao, Orgao, RegimeVida, Sexo, StatusVital, FaixaEtaria

class AnimalUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    animal_id: str = Field(..., alias="_id")
    classe: Optional[Classe] = None
    nome_comum: Optional[str] = None
    nome_cientifico: Optional[str] = None
    sexo: Optional[Sexo] = Sexo.NAO_INFORMADO
    peso: Optional[Union[float, str]] = None
    faixa_etaria: Optional[FaixaEtaria] = FaixaEtaria.NAO_INFORMADO
    orgao_origem: Optional[Orgao] = Field(default=Orgao.NAO_INFORMADO, alias="orgao")
    local_origem: Optional[str] = "Não Informado"
    regime_vida: Optional[RegimeVida] = Field(default=RegimeVida.NAO_INFORMADO, alias="status")
    status_vital: Optional[StatusVital] = StatusVital.NAO_INFORMADO
    animal_id_projeto: Optional[str] = None
    microchip: Optional[str] = None
    funcao: Optional[Funcao] = Funcao.NAO_APLICAVEL
    idade: Optional[str] = None
    suspeita_clinica: Optional[str] = None
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_atualizacao_animal: bool = False
    confirmar_nova_especie: bool = False