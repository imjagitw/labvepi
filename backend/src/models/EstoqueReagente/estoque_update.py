from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import Reagente, ReagenteUpdate, ReagenteCreate

class EstoqueReagenteUpdate(BaseModel):
    """
    Schema de atualização / DTO de entrada para consolidação de estoque de reagente.
    Contém apenas atributos e tipagens declarativas para atualização de estoque e lotes vinculados,
    sem propriedades computadas em tempo de execução.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Obrigatórios
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")

    # Opcionais
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código de referência do reagente")
    lotes: List[Union[Reagente, ReagenteUpdate, ReagenteCreate]] = Field(
        default_factory=list, 
        description="Lista de lotes associados ao reagente"
    )

    # Flags de controle
    confirmar_atualizacao_estoque: bool = False
    confirmar_atualizacao_reagente: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Sincronização de Metadados e Lotes:
    #      - Se reagente_nome ou codigo forem alterados, atualizar referências nos lotes vinculados.
    #   2. Recálculo Consolidado:
    #      - Re-executar cálculo dos volumes consolidados e totais por unidade após qualquer
    #        inclusão, alteração ou exclusão de lotes vinculados.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/estoque_service.py' (atualizar_estoque).
    #   - Camada de Controladores: 'backend/src/controllers/estoque_controller.py'.
    # =========================================================================