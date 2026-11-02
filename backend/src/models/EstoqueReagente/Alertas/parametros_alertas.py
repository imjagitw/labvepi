from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class ParametrosAlertaEstoque(BaseModel):
    """Parâmetros e critérios temporais utilizados para a identificação de alertas de estoque."""
    model_config = ConfigDict(populate_by_name=True)

    limite_baixo_estoque: int = Field(default=2, description="Quantidade máxima de unidades para disparo de alerta de baixo estoque")
    janela_dias_vencimento: int = Field(default=30, description="Janela em dias a partir da data de referência para alerta de vencimento próximo")
    data_referencia: date = Field(default_factory=date.today, description="Data base utilizada para o cálculo de validade e dias para vencer")