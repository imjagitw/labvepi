from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import Reagente

class EstoqueReagente(BaseModel):
    """
    Entidade / Modelo Agregado que representa a visão consolidada de estoque de um reagente.
    Contém estritamente atributos de dados estruturados, sem lógica operacional, regras de conversão
    dimensional ou propriedades computadas em tempo de execução.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código de referência do reagente")
    lotes: List[Reagente] = Field(default_factory=list, description="Lista de lotes associados ao reagente")

    # Atributos puros de dados consolidados (calculados e preenchidos pela camada de serviço):
    quantidade_total_unidades: int = Field(default=0, description="Soma total de frascos/unidades físicas de todos os lotes")
    quantidade_total_volume: Optional[float] = Field(default=None, description="Volume/massa total unificado na unidade base")
    totais_por_unidade: Dict[str, float] = Field(default_factory=dict, description="Totais segregados exatamente por unidade declarada")
    totais_convertidos_base: Dict[str, float] = Field(default_factory=dict, description="Totais consolidados em unidades base (ml para volume, g para massa)")
    resumo_estoque: Optional[str] = Field(default=None, description="Resumo textual legível do estoque (ex: '1500 ml')")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Agregação e Consolidação de Estoque:
    #      - Agrupar lotes físicos por reagente e somar 'quantidade_total_unidades'.
    #      - Converter dimensionalmente volumes e massas para a unidade canônica
    #        (litros -> ml, kg -> g) e totalizar em 'quantidade_total_volume'.
    #      - Manter totais discriminados por unidade original em 'totais_por_unidade'.
    #      - Gerar 'resumo_estoque' textual para exibição na interface.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/estoque_service.py' (consolidar_estoque,
    #     atualizar_metricas_estoque).
    #   - Camada de Controladores: 'backend/src/controllers/estoque_controller.py'.
    # =========================================================================