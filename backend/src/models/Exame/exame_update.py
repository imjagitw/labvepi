from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.models.Exame import TipoExame, ResultadoExame, TesteLaboratorial

class ExameUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    amostra_id: str
    exame_id: Optional[str] = None
    tipo_exame: TipoExame
    resultado: ResultadoExame = Field(..., alias="resultado_detalhado")
    teste_laboratorial: TesteLaboratorial
    data_realizacao: Optional[str] = None
    material_biologico: Optional[str] = None # herdado da Amostra (material_biologico) se não informado
    laboratorio_realizador: Optional[str] = None
    responsavel_exame: Optional[str] = None
    kit_utilizado: Optional[str] = None
    protocolo_exame: Optional[str] = None
    exame_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_atualizacao_exame: bool = False