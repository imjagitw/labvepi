from typing import Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie.enums.Classe import Classe

class EspecieCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nome_comum: str = Field(..., alias="nome")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Union[Classe, str]
    confirmar_nova_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Nomenclatura Científica:
    #      - Validar ortografia binominal e unicidade no banco.
    #   2. Normalização de Classe Taxonômica:
    #      - Converter strings textuais de classe para o Enum Classe.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/especie_service.py' (criar_especie).
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'.
    # =========================================================================