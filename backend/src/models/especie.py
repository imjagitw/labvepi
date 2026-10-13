from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field

class Classe(str, Enum):
    AVES = "Ave"
    MAMIFERO = "Mamífero"
    REPTIL = "Réptil"
    ANFIBIO = "Anfíbio"
    PEIXE = "Peixe"

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
    #   1. Validação e Formatação Taxonômica de 'nome_cientifico':
    #      - Validar preenchimento obrigatório real (rejeitar vazios, '-', 'NI', 'N/A').
    #      - Aplicar formatação taxonômica padrão (Gênero com inicial maiúscula e
    #        epíteto específico ou 'sp.'/'spp.' em minúsculo).
    #   2. Normalização de 'classe':
    #      - Mapear variações textuais, acentuações e plurais ('aves', 'mamifero',
    #        'repteis', 'anfíbios', etc.) para os membros canônicos do Enum 'Classe'.
    #
    # ONDE FAZER:
    #   - Camada de Repositórios / Serviços: 'backend/src/repositories/especie_repository.py'
    #     e 'backend/src/services/animal_service.py' (no método 'resolver_especie').
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'
    #     ao receber dados de entrada para cadastro ou alteração de espécies.
    # =========================================================================