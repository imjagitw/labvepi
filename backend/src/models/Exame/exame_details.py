from datetime import date
from pydantic import BaseModel, ConfigDict
from typing import Optional
from src.models.Exame import TipoExame, ResultadoExame, TesteLaboratorial

class ExameDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[int] = None
    exame_id: Optional[str] = None
    amostra_id: str
    tipo_exame: TipoExame
    resultado: ResultadoExame
    data_realizacao: date
    material_biologico: Optional[str] = None
    teste_laboratorial: TesteLaboratorial
    laboratorio_realizador: Optional[str] = None
    responsavel_exame: Optional[str] = None
    kit_utilizado: Optional[str] = None
    protocolo_exame: Optional[str] = None
    exame_observacoes: Optional[str] = None