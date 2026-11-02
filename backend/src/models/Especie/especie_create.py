from typing import Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie.enums.Classe import Classe

class EspecieCreate(BaseModel):
    """
    Schema de entrada para NOVOS cadastros de espécie (estrito):
    - O nome comum, nome científico e classe são obrigatórios.
    - A chave primária ('id'/'_id') NÃO é aceita: é gerada automaticamente pelo banco.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    nome_comum: str = Field(..., alias="nome", min_length=1, description="Nome popular/comum da espécie")
    nome_cientifico: str = Field(..., min_length=1, description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Union[Classe, str] = Field(..., description="Classe taxonômica (ex: Mamífero, Aves, Répteis)")
    confirmar_nova_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Nomenclatura Científica:
    #      - Validar ortografia binominal e unicidade no banco.
    #   2. Normalização de Classe Taxonômica:
    #      - Converter strings textuais de classe para o Enum Classe.
    #   3. Geração Automática de Identificador:
    #      - Chave primária gerada exclusivamente pelo banco/repositório.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/especie_service.py' (cadastrar_especie).
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'.
    #   - Camada de Repositório: 'backend/src/repositories/especie_repository.py'.
    # =========================================================================