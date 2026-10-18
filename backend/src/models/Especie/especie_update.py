from typing import Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie import Classe

class EspecieUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nome_comum: str = Field(..., alias="nome")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Union[Classe, str]
    confirmar_atualizacao_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Alteração de Nomenclatura Científica:
    #      - Se o binômio for alterado, verificar se impacta registros de animais vinculados.
    #   2. Normalização de Classe Taxonômica:
    #      - Converter string de classe para Enum Classe.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/especie_service.py' (atualizar_especie).
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'.
    # =========================================================================