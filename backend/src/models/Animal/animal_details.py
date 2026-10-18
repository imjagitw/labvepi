from typing import Optional, Union, List
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie import Classe, Especie
from src.models.Animal import Sexo, FaixaEtaria, Orgao, RegimeVida, StatusVital, Funcao, UnidadeIdade, UnidadePeso
from src.models.Amostra import Amostra

class AnimalDetails(BaseModel):
    """
    Schema de resposta detalhada de um animal:
    - Todas as informações do animal cadastrado (com saneamento explícito de campos não informados).
    - Dados completos da espécie taxonômica à qual pertence.
    - Quantidade total e lista completa das amostras biológicas associadas.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação
    id: Optional[int] = Field(default=None, alias="_id", description="Identificador sequencial do banco")
    animal_id: str = Field(..., description="ID único do laboratório (ex: AN001)")

    # Dados taxonômicos e espécie
    nome_comum: str = Field(..., alias="nome", description="Nome comum da espécie")
    nome_cientifico: str = Field(..., description="Nome científico formal (binominal ou Gênero sp.)")
    classe: Classe = Field(..., description="Classe taxonômica do animal")
    especie: Optional[Especie] = Field(default=None, description="Objeto detalhado da espécie à qual pertence")

    # Biometria e características
    sexo: Union[Sexo, str] = Field(
        default=Sexo.NAO_INFORMADO, 
        description="Sexo do indivíduo ou 'Não informado'"
    )
    peso: Union[float, str] = Field(
        default="Não aferido", 
        description="Peso canônico em kg (se aferido) ou 'Não aferido'"
    )
    peso_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico aferido do peso"
    )
    peso_unidade: Optional[Union[UnidadePeso, str]] = Field(
        default=None, 
        description="Unidade do peso aferido ('kg', 'g' ou 'mg')"
    )
    faixa_etaria: Union[FaixaEtaria, str] = Field(
        default=FaixaEtaria.NAO_INFORMADO, 
        description="Faixa etária estimada ou 'Não informado'"
    )
    orgao_origem: Union[Orgao, str] = Field(
        default=Orgao.NAO_INFORMADO, 
        alias="orgao", 
        description="Órgão de procedência do animal"
    )
    local_origem: Union[str, None] = Field(
        default="Não informado", 
        description="Município ou localidade de procedência"
    )
    municipio: Optional[str] = Field(
        default="Não informado",
        description="Município de procedência"
    )
    uf: Optional[str] = Field(
        default="Não informado",
        description="Sigla da Unidade Federativa (2 letras)"
    )
    localidade_detalhe: Optional[str] = Field(
        default="Não informado",
        description="Bairro, parque, fazenda ou ponto de resgate"
    )
    regime_vida: Union[RegimeVida, str] = Field(
        default=RegimeVida.NAO_INFORMADO, 
        alias="status", 
        description="Condição ambiental / procedência ecológica"
    )
    status_vital: Union[StatusVital, str] = Field(
        default=StatusVital.NAO_INFORMADO, 
        description="Condição biológica / desfecho vital"
    )

    # Informações opcionais / complementares (explicitando ausência quando não informado)
    animal_id_projeto: Optional[str] = Field(
        default="Não informado", 
        description="ID do projeto ao qual pertence"
    )
    microchip: Optional[str] = Field(
        default="Não informado", 
        description="Microchip de identificação"
    )
    funcao: Optional[Union[Funcao, str]] = Field(
        default="Não informado", 
        description="Função ou destinação do animal"
    )
    idade: Optional[str] = Field(
        default="Não informado", 
        description="Idade informada ou estimada"
    )
    idade_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico da idade"
    )
    idade_unidade: Optional[Union[UnidadeIdade, str]] = Field(
        default=None, 
        description="Unidade temporal da idade ('anos', 'meses', 'semanas', 'dias')"
    )
    suspeita_clinica: Optional[str] = Field(
        default="Não informado", 
        description="Suspeita clínica observada"
    )
    animal_observacoes: Optional[str] = Field(
        default="Não informado", 
        alias="observacoes", 
        description="Observações e notas adicionais"
    )

    # Amostras associadas
    quantidade_amostras: int = Field(
        default=0, 
        description="Quantidade total de amostras cadastradas deste animal"
    )
    amostras: List[Amostra] = Field(
        default_factory=list, 
        description="Lista completa das amostras biológicas pertencentes a este animal"
    )

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Saneamento e Formatação de Localidade:
    #      - Preencher 'municipio', 'uf' e 'localidade_detalhe' a partir de
    #        'local_origem' via decompor_localidade se não estiverem preenchidos.
    #      - Exibir 'Não informado' para partes ausentes na visão detalhada.
    #   2. Biometria e Relações:
    #      - Resolver objeto detalhado Especie e lista de Amostra associadas.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/animal_service.py'
    #     (preencher_nao_informados_e_relacionamentos / obter_animal_detalhes).
    # =========================================================================