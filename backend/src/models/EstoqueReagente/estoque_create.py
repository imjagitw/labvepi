from typing import Optional, List, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Reagente import Reagente, ReagenteCreate

class EstoqueReagenteCreate(BaseModel):
    """
    Schema de criação / DTO de entrada para consolidação de estoque de reagente.
    Contém apenas atributos e tipagens declarativas para cadastro inicial de estoque e vinculação de lotes,
    sem cálculos consolidados ou regras de conversão dimensional em tempo de execução.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Obrigatórios
    id: Optional[int] = None # Gerado automaticamente autoincrementado
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")

    # Opcionais
    reagente_codigo: Optional[str] = Field(default=None, alias="codigo", description="Código de referência do reagente")
    lotes: List[Union[Reagente, ReagenteCreate]] = Field(default_factory=list, description="Lista de lotes associados ao reagente")

    # Flags de controle
    confirmar_novo_estoque: bool = False
    confirmar_novo_reagente: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Unicidade e Cadastro de Estoque:
    #      - Verificar se já existe registro de estoque cadastrado com o mesmo nome/código.
    #   2. Inicialização Consolidada:
    #      - Se lotes forem enviados na criação, delegar cadastro dos lotes ao ReagenteService
    #        e calcular as métricas agregadas iniciais.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/estoque_service.py' (criar_estoque).
    #   - Camada de Controladores: 'backend/src/controllers/estoque_controller.py'.
    # =========================================================================
