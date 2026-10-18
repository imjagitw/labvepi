from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union
from src.models.Especie.enums.Classe import Classe
from src.models.Animal import Funcao, Orgao, RegimeVida, Sexo, StatusVital, FaixaEtaria, UnidadePeso, UnidadeIdade

class AnimalUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    animal_id: str = Field(..., description="ID único do laboratório (ex: AN001)")
    classe: Optional[Classe] = None
    nome_comum: Optional[str] = None
    nome_cientifico: Optional[str] = None
    # Atualização parcial: apenas os campos enviados são alterados.
    # Campos obrigatórios enviados não podem ser vazios / 'Não informado' (validado no service).
    sexo: Optional[Sexo] = None
    peso: Optional[Union[float, str]] = None
    peso_valor: Optional[float] = None
    peso_unidade: Optional[UnidadePeso] = None
    faixa_etaria: Optional[FaixaEtaria] = None
    orgao_origem: Optional[Orgao] = Field(default=None, alias="orgao")
    local_origem: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = Field(default=None, max_length=2)
    localidade_detalhe: Optional[str] = None
    regime_vida: Optional[RegimeVida] = Field(default=None, alias="status")
    status_vital: Optional[StatusVital] = None
    animal_id_projeto: Optional[str] = None
    microchip: Optional[str] = None
    funcao: Optional[Funcao] = None
    idade: Optional[str] = None
    idade_valor: Optional[float] = None
    idade_unidade: Optional[UnidadeIdade] = None
    suspeita_clinica: Optional[str] = None
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_atualizacao_animal: bool = False
    confirmar_nova_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Decomposição e Atualização de Localidade:
    #      - Se 'local_origem' for alterado, re-decompor municipio, uf e detalhe.
    #      - Se 'municipio' ou 'uf' forem alterados, atualizar 'local_origem' composto.
    #   2. Biometria (Peso e Idade):
    #      - Atualizar peso canônico em kg se peso_valor/peso_unidade forem alterados.
    #      - Recalcular faixa etária se idade_valor/idade_unidade forem alterados.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/animal_service.py' (atualizar_animal).
    #   - Camada de Controladores: 'backend/src/controllers/animal_controller.py'.
    # =========================================================================