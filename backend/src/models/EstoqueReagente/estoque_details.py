from typing import Optional, List, Dict, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import Reagente, ReagenteDetails

class EstoqueReagenteDetails(BaseModel):
    """
    Schema de resposta detalhada / DTO de saída do estoque consolidado de reagente.
    Contém a visão agregada com todos os lotes físicos detalhados e as métricas consolidadas
    calculadas pela camada de serviço (volumes unificados, totais por unidade e resumo).
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código de referência do reagente")
    
    # Relação com lotes físicos (detalhados com status de validade enriquecido)
    quantidade_lotes: Optional[int] = Field(default=None, description="Quantidade total de lotes associados ao reagente")
    lotes: List[Union[ReagenteDetails, Reagente]] = Field(default_factory=list, description="Lista detalhada dos lotes associados ao reagente")

    # Atributos consolidados (calculados e preenchidos pela camada de serviço):
    quantidade_total_unidades: int = Field(default=0, description="Soma total de frascos/unidades físicas de todos os lotes")
    quantidade_total_volume: Optional[float] = Field(default=None, description="Volume/massa total unificado na unidade base")
    totais_por_unidade: Dict[str, float] = Field(default_factory=dict, description="Totais segregados exatamente por unidade declarada")
    totais_convertidos_base: Dict[str, float] = Field(default_factory=dict, description="Totais consolidados em unidades base (ml para volume, g para massa)")
    resumo_estoque: Optional[str] = Field(default=None, description="Resumo textual legível do estoque (ex: '1500 ml')")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Agregação e Enriquecimento de Visão Detalhada:
    #      - Consultar lotes vinculados via ReagenteRepository / ReagenteService e enriquecer
    #        cada lote com atributos de status de validade (esta_vencido, dias_para_vencer).
    #      - Computar quantidade_lotes como o total de lotes físicos associados.
    #      - Calcular métricas consolidadas (quantidade_total_unidades, quantidade_total_volume,
    #        totais_por_unidade, totais_convertidos_base e resumo_estoque).
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/estoque_service.py' (obter_estoque_detalhes).
    #   - Camada de Controladores: 'backend/src/controllers/estoque_controller.py'.
    # =========================================================================