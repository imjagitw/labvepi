from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import Field

class TesteLaboratorial(str, Enum):
    PCR = 'PCR'
    SOROLOGICO = 'Sorológico'
    COPROPARASITOLOGICO = 'Coproparasitológico'
    HEMOPARASITO_EM_LAMINA = 'Hemoparasito em lâmina'
    OUTRO = 'Outro'

class TipoExame(str, Enum): 
    FEBRE_DO_NILO = 'Febre do Nilo'
    ORTHOFLAVIRIDAE = 'ORTHOFLAVIRIDAE'
    FEBRE_AMARELA = 'FEBRE AMARELA'
    MYCOPLASMA = 'MYCOPLASMA'
    HERPESVIRIDAE = 'HERPESVIRIDAE'
    TRIPANOSTOMATIDAE = 'TRIPANOSTOMATIDAE'
    RESISTENCIA_BACTERIANA = 'RESISTÊNCIA BACTERIANA'
    HEPATOZOON = 'HEPATOZOON'
    RAIVA = 'RAIVA'
    OUTRO = 'Outro'

class Exame(BaseModel):
    # obrigatorios
    id: Optional[int] = None # gerado automaticamente autoincrementado
    amostra_id: int # chave estrangeira para a tabela de amostra
    data_realizacao: date #alarmar se não informado
    laboratorio_realizador: str #alarmar se não informado
    teste_laboratorial: TesteLaboratorial #alarmar se não informado
    tipo_exame: TipoExame #alarmar se não informado
    responsavel_exame: str #alarmar se não informado
    kit_utilizado: str #alarmar se não informado
    protocolo_exame: str #alarmar se não informado

    # opcionais
    exame_id: Optional[str] = Field(default=None, alias="_id")
    exame_observacoes: Optional[str] = Field(default=None, alias="observacoes")