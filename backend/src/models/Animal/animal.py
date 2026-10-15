from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union
from src.models.Animal import Funcao, Orgao, RegimeVida, Sexo, StatusVital, FaixaEtaria
from src.models.Especie.enums.Classe import Classe

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
    microchip: Optional[str] = None # microchip se houver
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