from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.models.Exame import TipoExame, ResultadoExame, TesteLaboratorial

class ExameDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[int] = Field(default=None, alias="_id")
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

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Sincronização entre 'resultado' e 'resultado_qualitativo':
    #      - Garantir que ambos os campos qualitativos estejam preenchidos na resposta.
    #   2. Exibição quantitativa:
    #      - Formatar valor numérico quantitativo acompanhado da respectiva unidade métrica.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/exame_service.py' (método obter_exame_detalhes).
    #   - Camada de Controladores: 'backend/src/controllers/exame_controller.py'.
    # =========================================================================