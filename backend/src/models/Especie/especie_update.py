from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie.enums.Classe import Classe

class EspecieUpdate(BaseModel):
    """
    Schema de atualização de espécie existente (DTO de entrada):
    - A espécie é identificada pelo ID na rota da requisição (PUT /especie/{id}).
    - A chave primária ('id'/'_id', gerada pelo banco) é imutável e não é aceita no corpo da requisição:
      campos extras são ignorados.
    - Suporta atualização parcial (campos opcionais).
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    nome_comum: Optional[str] = Field(default=None, alias="nome", description="Nome popular/comum da espécie")
    nome_cientifico: Optional[str] = Field(default=None, description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Optional[Union[Classe, str]] = Field(default=None, description="Classe taxonômica")
    confirmar_atualizacao_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Alteração de Nomenclatura Científica:
    #      - Se o binômio for alterado, verificar consistência e unicidade no banco.
    #   2. Normalização de Classe Taxonômica:
    #      - Converter string de classe para Enum Classe.
    #   3. Proteção da Chave Primária:
    #      - Garantir que o ID da rota seja mantido e não sobrescrito pelo corpo.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/especie_service.py' (atualizar_especie).
    #   - Camada de Controladores: 'backend/src/controllers/especie_controller.py'.
    # =========================================================================