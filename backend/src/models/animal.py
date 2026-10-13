from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.especie import Classe

class Sexo(str, Enum): 
    MACHO = 'Macho'
    FEMEA = 'Fêmea'
    INDETERMINADO = 'Indeterminado'
    NAO_INFORMADO = 'Não informado'

class FaixaEtaria(str, Enum): 
    FILHOTE = 'Filhote'
    JUVENIL = 'Juvenil'
    JOVEM = 'Jovem'
    SUB_ADULTO = 'Sub Adulto'
    ADULTO = 'Adulto'
    SENIL = 'Senil'
    IDOSO = 'Idoso'
    POTRO = 'Potro'
    NINHEGO = 'Ninhego'
    NAO_INFORMADO = 'Não informado'

class Orgao(str, Enum): 
    UFPI = 'UFPI'
    HVU = 'HVU'
    CCZ = 'CCZ'
    NEPPAS = 'NEPPAS'
    IBAMA_CETAS_PI = 'IBAMA - CETAS - PI'
    IBAMA_CETAS_CE = 'IBAMA - CETAS - CE'
    IBAMA_CETAS_RN = 'IBAMA - CETAS - RN'
    SEMARH_CETAS_PI = 'SEMARH - CETAS - PI'
    UFPA = 'UFPA'
    UFRR = 'UFRR'
    UFAC = 'UFAC'
    UFOB = 'UFOB'
    DSEI_LESTE_AM = 'DSEI LESTE - AM'
    ZOOLOGICO_PI = 'ZOOLOGICO -PI'
    PARTICULAR = 'PARTICULAR'
    OUTRO = 'OUTRO'

class RegimeVida(str, Enum):
    VIDA_LIVRE = 'Vida livre'
    CATIVEIRO = 'Cativeiro'
    DOMICILIADO = 'Domiciliado'
    NAO_INFORMADO = 'Não informado'

class Funcao(str, Enum): 
    PET = 'Pet'
    TRABALHO = 'Trabalho'
    LAZER = 'Lazer'
    REPRODUCAO = 'Reprodução'
    CONSERVACAO = 'Conservação / Zoológico'
    OUTRO = 'Outro'
    NAO_APLICAVEL = 'Não aplicável'

class StatusVital(str, Enum): 
    VIVO = 'Vivo'
    MORTO = 'Morto'
    EUTANASIADO = 'Eutanasiado'
    NAO_INFORMADO = 'Não informado'

class Animal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # obrigatorios
    id: Optional[int] = None  # Autoincrementado no banco
    animal_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: AN001)")
    classe: Classe # definido com base na espécie
    nome_comum: str # nome comum da espécie
    nome_cientifico: str # nome científico da espécie
    sexo: Sexo = Sexo.NAO_INFORMADO
    
    # Peso: aceita float (padronizado em kg) ou a string literal 'Não aferido'
    peso: Union[float, str] = Field(
        default="Não aferido", 
        description="Peso em kg (se aferido) ou 'Não aferido'"
    )
    
    faixa_etaria: FaixaEtaria = FaixaEtaria.NAO_INFORMADO
    orgao_origem: Orgao = Field(..., alias="orgao", description="Orgao de origem do animal")
    local_origem: str # município ou localidade de procedência
    regime_vida: RegimeVida = Field(..., alias="status") # Condição ambiental / procedência ecológica (antigo 'status' da planilha e banco)
    status_vital: StatusVital  # Condição vital no momento da coleta ou desfecho clínico
    
    # opcionais
    animal_id_projeto: Optional[str] = None # id do projeto a que o animal pertence
    id_hvu: Optional[str] = None # id vindo do hvu # pode ser igual a microchip
    microchip: Optional[str] = None # microchip se houver # pode ser igual id_hvu
    funcao: Optional[Funcao] = None # aplicável a animais domésticos/equídeos/pets
    idade: Optional[str] = None # definir formato anos/meses
    suspeita_clinica: Optional[str] = None       
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Processamento e Sanitização de Peso ('peso'):
    #      - Tratar valores nulos, vazios, traço ou termos como "NI" / "Não informado",
    #        convertendo para o padrão 'Não aferido'.
    #      - Identificar sufixos de unidade (ex: regex r"^(\d+(?:\.\d+)?)\s*g$" para
    #        gramas) e converter para quilogramas (valor / 1000.0).
    #      - Tratar strings numéricas com vírgula decimal (ex: '12,5' -> 12.5).
    #   2. Validação de Regra de Negócio de Peso:
    #      - Garantir que qualquer peso numérico seja estritamente maior que zero
    #        (peso > 0), ou seja marcado explicitamente como 'Não aferido'.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/animal_service.py' (especificamente
    #     no método 'criar_animal' e 'atualizar_animal').
    #   - Camada de Controladores/UI: 'backend/src/controllers/animal_controller.py'
    #     e nos formulários de cadastro do Streamlit ('streamlit/forms/animal_form.py').
    # =========================================================================


class AnimalCreate(BaseModel):
    """Schema puro de entrada para criação de um animal."""
    model_config = ConfigDict(populate_by_name=True)

    animal_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: AN001)")
    nome_comum: Optional[str] = None
    nome_cientifico: Optional[str] = None
    classe: Optional[Classe] = None
    sexo: Sexo = Sexo.NAO_INFORMADO
    peso: Union[float, str] = Field(default="Não aferido")
    faixa_etaria: FaixaEtaria = FaixaEtaria.NAO_INFORMADO
    orgao_origem: Orgao = Field(..., alias="orgao")
    local_origem: str
    regime_vida: RegimeVida = Field(..., alias="status")
    status_vital: StatusVital
    animal_id_projeto: Optional[str] = None
    id_hvu: Optional[str] = None
    microchip: Optional[str] = None
    funcao: Optional[Funcao] = None
    idade: Optional[str] = None
    suspeita_clinica: Optional[str] = None
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_nova_especie: bool = False


class AnimalUpdate(BaseModel):
    """Schema puro de entrada para atualização parcial ou total de um animal."""
    model_config = ConfigDict(populate_by_name=True)

    classe: Optional[Classe] = None
    nome_comum: Optional[str] = None
    nome_cientifico: Optional[str] = None
    sexo: Optional[Sexo] = None
    peso: Optional[Union[float, str]] = None
    faixa_etaria: Optional[FaixaEtaria] = None
    orgao_origem: Optional[Orgao] = Field(default=None, alias="orgao")
    local_origem: Optional[str] = None
    regime_vida: Optional[RegimeVida] = Field(default=None, alias="status")
    status_vital: Optional[StatusVital] = None
    animal_id_projeto: Optional[str] = None
    id_hvu: Optional[str] = None
    microchip: Optional[str] = None
    funcao: Optional[Funcao] = None
    idade: Optional[str] = None
    suspeita_clinica: Optional[str] = None
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_nova_especie: bool = False