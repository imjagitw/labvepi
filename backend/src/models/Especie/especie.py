from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from .enums.Classe import Classe

class Especie(BaseModel):
    """
    Representação taxonômica padronizada de uma espécie animal no laboratório.
    O nome_cientifico é estritamente obrigatório conforme as diretrizes do LABVEPI,
    podendo conter binômio completo (ex: 'Artibeus lituratus') ou gênero + 'sp.'/'spp.' 
    (ex: 'Artibeus sp.', 'Molossus sp.').
    """
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[Union[int, str]] = Field(default=None, alias="_id")
    nome_comum: str = Field(..., alias="nome")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Classe

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação e Formatação de Nomenclatura Científica:
    #      - Garantir que 'nome_cientifico' siga padrão binominal (ex: 'Artibeus lituratus')
    #        ou identificação genérica de gênero (ex: 'Artibeus sp.', 'Molossus spp.').
    #      - Aplicar formatação itálica apenas na camada de apresentação (Streamlit/UI).
    #   2. Dedução e Unicidade Taxonômica:
    #      - Inferir 'classe' caso ausente se a espécie já constar no catálogo taxonômico.
    #      - Evitar duplicidade de registros para o mesmo binômio científico.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/especie_service.py' (criar_especie,
    #     atualizar_especie).
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'.
    # =========================================================================