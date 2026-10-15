from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field
from src.models.reagente import Reagente

class EstoqueReagente(BaseModel):
    """
    Entidade / Modelo Agregado que representa a visão consolidada de estoque de um reagente.
    Contém estritamente atributos de dados estruturados, sem lógica operacional, regras de conversão
    dimensional ou propriedades computadas em tempo de execução.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
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
    #   1. Tabela e Lógica de Conversão Dimensional:
    #      - Manter dicionário de fatores de conversão (FATORES_CONVERSAO) para
    #        unidades base: volume (ml, L, µl) e massa (g, mg, kg).
    #      - Prevenir soma cega de grandezas incompatíveis (ex: somar ml com g).
    #   2. Validação de Lotes Únicos:
    #      - Validar se não há números de lote duplicados para o mesmo reagente.
    #   3. Consolidação de Estoque (Ações e Cálculos):
    #      - Calcular soma total de frascos/unidades físicas ('quantidade_total_unidades').
    #      - Consolidar quantidades por unidade declarada ('totais_por_unidade').
    #      - Calcular quantidades convertidas para unidades base ('totais_convertidos_base').
    #      - Calcular volume/massa unificado principal ('quantidade_total_volume').
    #      - Gerar descrição legível consolidada ('resumo_estoque', ex: '1500 ml').
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/reagente_service.py' (especificamente
    #     no método 'agrupar_por_nome' ou métodos de cálculo consolidado de inventário).
    #   - Camada de Controladores: 'backend/src/controllers/reagente_controller.py'
    #     ao preparar respostas agregadas de inventário para a interface web.
    # =========================================================================