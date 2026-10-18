from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Especie.enums.Classe import Classe
from src.models.Animal import Funcao, Orgao, RegimeVida, Sexo, StatusVital, FaixaEtaria, UnidadeIdade, UnidadePeso

class AnimalCreate(BaseModel):
    """
    Schema de entrada para NOVOS cadastros (estrito).
    Os campos obrigatórios não possuem valor padrão: devem ser enviados explicitamente.
    O peso pode ser informado como número com unidade (peso_valor + peso_unidade),
    como string com unidade ('400g', '2.5kg'), float em kg ou 'Não aferido'.
    A idade pode ser informada estruturada (idade_valor + idade_unidade),
    textual ('6 meses') ou diretamente via faixa_etaria.
    Cargas legadas (planilhas) chamam o service com carga_legada=True.
    """
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    animal_id: str = Field(..., min_length=1, description="ID único do laboratório (ex: AN001)")

    # Espécie: basta nome_comum OU nome_cientifico se a espécie estiver no catálogo;
    # o service resolve os demais. Para espécie nova, os três são exigidos pelo service.
    classe: Optional[Classe] = None
    nome_comum: Optional[str] = None
    nome_cientifico: Optional[str] = None

    # obrigatórios
    sexo: Sexo
    peso: Optional[Union[float, str]] = Field(
        default=None, 
        description="Peso em kg (> 0), string com unidade ('400g') ou 'Não aferido'"
    )
    peso_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico do peso aferido"
    )
    peso_unidade: Optional[UnidadePeso] = Field(
        default=None, 
        description="Unidade do peso ('kg', 'g' ou 'mg')"
    )
    orgao_origem: Orgao = Field(..., alias="orgao")
    
    # Localidade / Procedência
    local_origem: Optional[str] = Field(default=None, description="Local de procedência textual ou composto (ex: 'Teresina/PI')")
    municipio: Optional[str] = Field(default=None, description="Município de procedência")
    uf: Optional[str] = Field(default=None, max_length=2, description="Sigla da UF de 2 letras (ex: 'PI')")
    localidade_detalhe: Optional[str] = Field(default=None, description="Bairro, parque, fazenda ou ponto de resgate")
    
    regime_vida: RegimeVida = Field(..., alias="status")
    status_vital: StatusVital

    # obrigatório: faixa_etaria informada OU idade para dedução automática
    faixa_etaria: Optional[FaixaEtaria] = None
    idade: Optional[str] = Field(
        default=None, 
        description="Idade em formato textual (ex: '6 meses', '2 anos')"
    )
    idade_valor: Optional[float] = Field(
        default=None, 
        description="Valor numérico da idade"
    )
    idade_unidade: Optional[UnidadeIdade] = Field(
        default=None, 
        description="Unidade temporal da idade ('anos', 'meses', 'semanas', 'dias')"
    )

    # opcionais
    animal_id_projeto: Optional[str] = None
    microchip: Optional[str] = None
    funcao: Optional[Funcao] = Funcao.NAO_APLICAVEL
    suspeita_clinica: Optional[str] = None
    animal_observacoes: Optional[str] = Field(default=None, alias="observacoes")
    confirmar_novo_animal: bool = False
    confirmar_nova_especie: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação e Decomposição de Localidade:
    #      - Exigir 'local_origem' OU ('municipio' e 'uf').
    #      - Se 'local_origem' for enviado, decompor automaticamente em municipio,
    #        uf e localidade_detalhe.
    #      - Se 'municipio' e 'uf' forem enviados, compor 'local_origem'.
    #   2. Validação Biometria e Obrigatoriedade:
    #      - Validação de peso (> 0 ou 'Não aferido') e idade no service.
    #      - Rejeição de valores sentinelas ('Não informado', '', etc.) em novos cadastros.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/animal_service.py' (criar_animal).
    #   - Camada de Controladores: 'backend/src/controllers/animal_controller.py'.
    # =========================================================================