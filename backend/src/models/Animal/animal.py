from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union
from src.models.Animal import Funcao, Orgao, RegimeVida, Sexo, StatusVital, FaixaEtaria, UnidadePeso, UnidadeIdade
from src.models.Especie.enums.Classe import Classe

class Animal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # obrigatorios
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    animal_id: str = Field(..., description="ID único do laboratório (ex: AN001)")
    classe: Classe # definido com base na espécie
    nome_comum: str # nome comum da espécie
    nome_cientifico: str # nome científico da espécie
    sexo: Sexo = Sexo.NAO_INFORMADO
    
    # Peso: aceita float (padronizado em kg) ou a string literal 'Não aferido'
    peso: Union[float, str] = Field(
        default="Não aferido", 
        description="Peso canônico em kg (se aferido) ou 'Não aferido'"
    )
    peso_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico aferido do peso"
    )
    peso_unidade: Optional[UnidadePeso] = Field(
        default=None, 
        description="Unidade do peso aferido ('kg', 'g' ou 'mg')"
    )
    
    faixa_etaria: FaixaEtaria = FaixaEtaria.NAO_INFORMADO
    orgao_origem: Orgao = Field(..., alias="orgao", description="Orgao de origem do animal")
    local_origem: str = Field(default="Não informado", description="Município ou localidade de procedência (composto)")
    municipio: Optional[str] = Field(default=None, description="Município de procedência")
    uf: Optional[str] = Field(default=None, max_length=2, description="Sigla da Unidade Federativa (2 letras)")
    localidade_detalhe: Optional[str] = Field(default=None, description="Bairro, parque, fazenda ou ponto de resgate")
    regime_vida: RegimeVida = Field(..., alias="status") # Condição ambiental / procedência ecológica (antigo 'status' da planilha e banco)
    status_vital: StatusVital  # Condição vital no momento da coleta ou desfecho clínico
    
    # opcionais
    animal_id_projeto: Optional[str] = None # id do projeto a que o animal pertence
    microchip: Optional[str] = None # microchip se houver
    funcao: Optional[Funcao] = None # aplicável a animais domésticos/equídeos/pets
    idade: Optional[str] = None # representação textual (ex: '6 meses', '2 anos')
    idade_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico da idade"
    )
    idade_unidade: Optional[UnidadeIdade] = Field(
        default=None, 
        description="Unidade temporal da idade ('anos', 'meses', 'semanas', 'dias')"
    )
    suspeita_clinica: Optional[str] = None       
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Decomposição e Normalização de Localidade:
    #      - Se 'local_origem' for informado (ex: 'Teresina/PI', 'Fazenda X, Teresina/PI'),
    #        decompor automaticamente em municipio ('Teresina'), uf ('PI') e
    #        localidade_detalhe ('Fazenda X').
    #      - Se 'municipio' e 'uf' forem fornecidos isoladamente, compor o campo
    #        'local_origem' automaticamente como '{municipio}/{uf}'.
    #   2. Biometria (Peso e Idade):
    #      - Conversão de peso com unidades ('kg', 'g', 'mg') para o peso canônico em kg.
    #      - Conversão de idade com unidades ('anos', 'meses', 'semanas', 'dias') e
    #        dedução automática de faixa etária caso ausente.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/animal_service.py' (métodos
    #     criar_animal, atualizar_animal e preencher_nao_informados_e_relacionamentos).
    #   - Camada de Domínio: 'backend/src/domain/normalizacao.py' (funções
    #     decompor_localidade, decompor_peso, decompor_idade).
    # =========================================================================