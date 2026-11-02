from typing import List
from pydantic import BaseModel, ConfigDict, Field
from .alerta_item import ReagenteAlertaItem
from .parametros_alertas import ParametrosAlertaEstoque
from .estoque_alertas_totais import TotaisAlertasEstoque

class EstoqueAlertasResponse(BaseModel):
    """Schema de resposta unificado do endpoint de alertas de estoque (/estoque/alertas)."""
    model_config = ConfigDict(populate_by_name=True)

    parametros: ParametrosAlertaEstoque = Field(..., description="Parâmetros utilizados na avaliação dos alertas")
    totais: TotaisAlertasEstoque = Field(..., description="Sumário quantitativo consolidado de todos os alertas")
    reagentes_com_alerta: List[ReagenteAlertaItem] = Field(
        default_factory=list,
        description="Listagem dos reagentes que possuem ao menos uma pendência ou alerta de estoque"
    )