from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import ReagenteDetails

class ReagenteAlertaItem(BaseModel):
    """
    Visão agregada de alerta para um reagente específico.
    Centraliza a situação global de estoque do produto e discrimina seus lotes físicos
    por categoria de validade (vencidos, prestes a vencer e regulares).
    """
    model_config = ConfigDict(populate_by_name=True)

    reagente_nome: str = Field(..., alias="nome", description="Nome canônico do reagente químico/biológico")
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código identificador do reagente no laboratório")
    
    # Métricas consolidadas de estoque
    quantidade_total_unidades: int = Field(default=0, description="Soma total de frascos/unidades de todos os lotes físicos vinculados")
    quantidade_total_volume: Optional[float] = Field(default=None, description="Volume ou massa total unificado na unidade canônica")
    resumo_estoque: Optional[str] = Field(default=None, description="Resumo textual legível do estoque (ex: '2 un | 1000 ml')")

    # Indicadores consolidados de alerta
    baixo_estoque_global: bool = Field(default=False, description="Indica se o estoque consolidado está em nível crítico (<= limite)")
    tem_lotes_vencidos: bool = Field(default=False, description="Indica se o reagente possui pelo menos um lote físico vencido")
    tem_lotes_vencendo: bool = Field(default=False, description="Indica se o reagente possui pelo menos um lote físico a vencer na janela definida")
    tem_alerta: bool = Field(default=False, description="Flag geral indicando se o reagente requer qualquer ação ou atenção")

    # Discriminação detalhada dos lotes por categoria
    lotes_vencidos: List[ReagenteDetails] = Field(
        default_factory=list,
        description="Lotes físicos do reagente com prazo de validade expirado (ordenados do mais antigo para o mais recente)"
    )
    lotes_proximos_vencimento: List[ReagenteDetails] = Field(
        default_factory=list,
        description="Lotes físicos do reagente prestes a vencer na janela de dias (ordenados por prioridade PEPS/FIFO)"
    )
    lotes_regulares: List[ReagenteDetails] = Field(
        default_factory=list,
        description="Lotes físicos do reagente com prazo de validade seguro e em conformidade"
    )