from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import Reagente, ReagenteUpdate, ReagenteCreate

class EstoqueReagenteUpdate(BaseModel):
    """
    Schema de atualização / DTO de entrada para consolidação de estoque de reagente.
    - O estoque é identificado pelo identificador na rota da requisição (PUT/PATCH /estoque_reagente/{identificador}).
    - A chave primária ('id'/'_id', gerada pelo banco) é imutável e não é aceita no corpo:
      campos extras são ignorados.
    - Suporta atualização parcial ou completa.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    # Opcionais (atualização parcial ou completa: permite alterar um ou mais campos mantendo os demais inalterados)
    reagente_nome: Optional[str] = Field(default=None, alias="nome", description="Nome do reagente")
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código de referência do reagente")
    lotes: Optional[List[Union[Reagente, ReagenteUpdate, ReagenteCreate]]] = Field(
        default=None, 
        description="Lista de lotes associados ao reagente (se não informada, mantém os lotes atuais)"
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