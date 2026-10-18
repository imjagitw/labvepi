from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from src.models.Reagente import EtapaReagente, UnidadeMedida

class ReagenteDetails(BaseModel):
    """
    Entidade representativa de um lote físico de reagente no laboratório.
    Contém apenas atributos e tipagens declarativas, sem ações temporais,
    resolução dinâmica de sinônimos ou validadores heurísticos.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    reagente_codigo: str = Field(..., alias="codigo", description="Código do reagente")
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")
    numero_lote: str = Field(..., description="Número identificador do lote")
    marca: str = Field(..., description="Marca ou fabricante do reagente")
    data_validade: date = Field(..., description="Data de validade do lote")
    quantidade_unidade: int = Field(default=1, alias="quantidade_unidade", description="Quantidade de frascos/unidades")
    reagente_local_armazenamento: str = Field(..., alias="local_armazenamento", description="Local físico de armazenamento")
    reagente_id: Optional[str] = Field(default=None, description="Identificador único padrão do laboratório")
    quantidade_volume: Optional[float] = Field(default=None, description="Volume ou massa contida em cada unidade")
    unidade_medida: UnidadeMedida = Field(default="ml", alias="unidade", description="Unidade de medida (ex: ml, L, g)")
    reagente_etapa: Optional[EtapaReagente] = Field(default=None, alias="etapa", description="Etapa laboratorial em que é empregado")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes", description="Observações complementares")

    esta_vencido: Optional[bool] = Field(default=None, description="Indicação se o lote está vencido (calculado pelo serviço)")
    dias_para_vencer: Optional[int] = Field(default=None, description="Dias restantes até o vencimento (calculado pelo serviço)")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Enriquecimento de Dados de Validade:
    #      - Calcular e preencher 'esta_vencido' e 'dias_para_vencer'.
    #   2. Formatação para Apresentação:
    #      - Formatar strings de datas legíveis e alertas de vencimento próximo.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/reagente_service.py' (obter_reagente_detalhes).
    #   - Camada de Controladores: 'backend/src/controllers/reagente_controller.py'.
    # =========================================================================