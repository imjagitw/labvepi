from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional
from src.models.Exame import TipoExame, ResultadoExame, TesteLaboratorial

class Exame(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # obrigatorios
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    amostra_id: str # chave estrangeira para a tabela/documento de amostra
    tipo_exame: TipoExame # patógeno ou painel investigado
    resultado: ResultadoExame = Field(..., alias="resultado_detalhado") # resultado categorizado do ensaio
    data_realizacao: date # cadastrar apenas exames realizados, então alarmar se não informado data

    # contextuais (herdados de Amostra ou preenchidos no laudo) 
    # atualizar como obrigatorio quando acrescentar a entidade laudo
    material_biologico: Optional[str] = None # herdado da Amostra (metodo_coleta) se não informado
    teste_laboratorial: TesteLaboratorial
    laboratorio_realizador: Optional[str] = None # preenchido no laudo
    responsavel_exame: Optional[str] = None # preenchido no laudo
    kit_utilizado: Optional[str] = None # preenchido no laudo
    protocolo_exame: Optional[str] = None # preenchido no laudo