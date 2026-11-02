from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Exame import TipoExame, ResultadoExame, TesteLaboratorial

class ExameUpdate(BaseModel):
    """
    Schema de atualização de exame laboratorial existente (DTO de entrada):
    - O exame é identificado pelo identificador na rota da requisição (PUT/PATCH /exame/{identificador}).
    - A chave primária ('id'/'_id', gerada pelo banco) é imutável e não é aceita no corpo:
      campos extras são ignorados.
    - Suporta atualização parcial ou completa.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    amostra_id: Optional[str] = None
    exame_id: Optional[str] = None
    tipo_exame: Optional[TipoExame] = None
    resultado: Optional[ResultadoExame] = Field(default=None, alias="resultado_detalhado")
    teste_laboratorial: Optional[TesteLaboratorial] = None
    data_realizacao: Optional[Union[date, str]] = None
    material_biologico: Optional[str] = None # herdado da Amostra (material_biologico) se não informado
    laboratorio_realizador: Optional[str] = None
    responsavel_exame: Optional[str] = None
    kit_utilizado: Optional[str] = None
    protocolo_exame: Optional[str] = None
    exame_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_atualizacao_exame: bool = False