from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from src.models.Reagente import EtapaReagente, UnidadeMedida

class ReagenteUpdate(BaseModel):
    """
    Schema de atualização de um lote físico de reagente no laboratório (DTO de entrada):
    - O reagente é identificado pelo identificador na rota da requisição (PUT/PATCH /reagente/{identificador}).
    - A chave primária ('id'/'_id', gerada pelo banco) é imutável e não é aceita no corpo:
      campos extras são ignorados.
    - Suporta atualização parcial ou completa.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    
    # Campos de atualização (opcionais para suportar PUT/PATCH parcial)
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código do reagente")
    reagente_nome: Optional[str] = Field(default=None, alias="nome", description="Nome do reagente")
    numero_lote: Optional[str] = Field(default=None, description="Número identificador do lote")
    marca: Optional[str] = Field(default=None, description="Marca ou fabricante do reagente")
    data_validade: Optional[date] = Field(default=None, description="Data de validade do lote")
    quantidade_unidade: Optional[int] = Field(default=None, alias="quantidade_unidade", description="Quantidade de frascos/unidades")
    reagente_local_armazenamento: Optional[str] = Field(default=None, alias="local_armazenamento", description="Local físico de armazenamento")
    
    # Opcionais
    reagente_id: Optional[str] = Field(default=None, description="Identificador único padrão do laboratório")
    quantidade_volume: Optional[float] = Field(default=None, description="Volume ou massa contida em cada unidade")
    unidade_medida: Optional[UnidadeMedida] = Field(default=None, alias="unidade", description="Unidade de medida (ex: ml, L, g)")
    reagente_etapa: Optional[EtapaReagente] = Field(default=None, alias="etapa", description="Etapa laboratorial em que é empregado")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes", description="Observações complementares")

    confirmar_atualizacao_reagente: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Alterações de Lote:
    #      - Validar alterações na data de validade, quantidade e armazenamento.
    #   2. Recálculo e Sincronização de Estoque:
    #      - Ao atualizar volumes ou quantidades de unidades de um lote, disparar
    #        o recálculo dos totais agregados na entidade EstoqueReagente.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/reagente_service.py' (atualizar_reagente).
    #   - Camada de Controladores: 'backend/src/controllers/reagente_controller.py'.
    # =========================================================================