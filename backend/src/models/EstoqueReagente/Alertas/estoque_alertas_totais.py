from pydantic import BaseModel, ConfigDict, Field

class TotaisAlertasEstoque(BaseModel):
    """Métricas agregadas e contadores de alertas em todo o estoque do laboratório."""
    model_config = ConfigDict(populate_by_name=True)

    total_reagentes_monitorados: int = Field(default=0, description="Total de reagentes distintos cadastrados no inventário")
    total_reagentes_com_alerta: int = Field(default=0, description="Total de reagentes que possuem pelo menos uma condição de alerta ativa")
    total_reagentes_baixo_estoque: int = Field(default=0, description="Total de reagentes com estoque global crítico (<= limite)")
    total_reagentes_com_lotes_vencidos: int = Field(default=0, description="Total de reagentes que possuem um ou mais lotes com prazo de validade expirado")
    total_reagentes_com_lotes_vencendo: int = Field(default=0, description="Total de reagentes que possuem um ou mais lotes próximos do vencimento")
    total_lotes_vencidos: int = Field(default=0, description="Contagem total de lotes físicos expirados em todo o laboratório")
    total_lotes_vencendo: int = Field(default=0, description="Contagem total de lotes físicos prestes a vencer em todo o laboratório")
