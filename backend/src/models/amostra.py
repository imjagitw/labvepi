from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union

class MetodoColeta(str, Enum): 
    # Swabs
    SWAB_ORAL = 'Swab oral'
    SWAB_NASAL = 'Swab nasal'
    SWAB_CLOACAL = 'Swab cloacal'
    SWAB_ORAL_CLOACAL = 'Swab oral e cloacal'
    SWAB_RETAL = 'Swab retal'
    SWAB_TRAQUEAL = 'Swab traqueal'
    SWAB_OCULAR = 'Swab ocular'
    
    # Sangue e derivados
    SANGUE = 'Sangue'
    SANGUE_TOTAL = 'Sangue total'
    SANGUE_EDTA = 'Sangue (EDTA)'
    SORO = 'Soro'
    PAPEL_FILTRO = 'Papel filtro'
    ESFREGACO_SANGUINEO = 'Esfregaço sanguíneo'
    
    # Tecidos e órgãos
    TECIDO = 'Tecido'
    POOL_TECIDOS = 'Pool de tecidos'
    ORGAOS = 'Órgãos'
    BACO = 'Baço'
    FIGADO = 'Fígado'
    PULMAO = 'Pulmão'
    RIM = 'Rim'
    ENCEFALO = 'Encéfalo / Cérebro'
    CORACAO = 'Coração'
    
    # Excretas, secreções e outros
    FEZES = 'Fezes'
    ENEMA = 'Enema'
    LIQUOR = 'Líquor / LCR'
    ECTOPARASITA = 'Ectoparasita'
    PELE = 'Pele'
    PELO = 'Pelo'
    NECROPSIA = 'Necrópsia'
    OUTRO = 'Outro'

class CondicaoArmazenamento(str, Enum): 
    TEMPERATURA_AMBIENTE = 'Temperatura ambiente'
    REFRIGERADA = 'Refrigerada'
    CONGELADA = 'Congelada'
    SEM_IDENTIFICACAO = 'Sem identificação'
    COAGULADA = 'Coagulada'
    HEMOLISADA = 'Hemolisada'
    NITROGENIO_LIQUIDO = 'Nitrogênio líquido'
    GELO_SECO = 'Gelo seco'

class FaseAmostra(str, Enum): 
    EXTRACAO = 'Extração'
    PCR = 'PCR'
    ELETRO = 'ELETRO'

class DestinoAmostra(str, Enum): 
    BIOBANCO_UFPI = 'Biobanco UFPI'
    BIOBANCO_UFPA = 'Biobanco UFPA'
    FIOFRUZ_AM = 'Fiofruz AM'
    LASAN_UFPI = 'LASAN UFPI'
    LAPATO_UFPI = 'LAPATO UFPI'
    LAPATO_UFPA = 'LAPATO UFPA'
    LAB_VIGILANCIA_EPIZOOTIAS_UFPI = 'LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI'
    OUTRO = 'Outro'

class StatusAmostra(str, Enum): 
    DISPONIVEL = 'Disponível'
    RESERVADA = 'Reservada'
    EM_USO = 'Em uso'
    PERDIDA = 'Perdida'
    ESGOTADA = 'Esgotada'

class Amostra(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos primários
    id: Optional[int] = None  # Autoincrementado no banco
    amostra_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: L 1, AMS001)")    
    animal_id: str = Field(..., description="ID ou chave do animal vinculado (ex: AN001, A547)")
    
    # Datas de rastreamento
    data_coleta_amostra: Optional[date] = Field(default=None, alias="data_coleta", description="Data em que a coleta foi realizada")
    data_entrega: Optional[date] = Field(default=None, alias="data_recebimento", description="Data em que a amostra deu entrada no LABVEPI")
    
    # Tipo / Material biológico coletado
    metodo_coleta: Union[MetodoColeta, str] = Field(default=MetodoColeta.OUTRO, description="Tipo de amostra / método de coleta")
    
    # Status e Laudo
    status_amostra: StatusAmostra = StatusAmostra.DISPONIVEL  # nasce disponível
    laudo_liberado: Optional[str] = Field(default=None, description="Status de liberação do laudo da amostra (sim, não, pesquisa, óbito)")

    # Campos de triagem / laboratório (opcionais com defaults, ausentes na planilha histórica geral)
    local_coleta_amostra: Optional[str] = Field(default=None, alias="local_coleta", description="Local específico da coleta")
    nome_coletor: Optional[str] = None
    condicao_armazenamento: Optional[CondicaoArmazenamento] = None
    fase_amostra: Optional[FaseAmostra] = FaseAmostra.EXTRACAO
    destino_amostra: Optional[DestinoAmostra] = DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI
    kit_utilizado: Optional[str] = None # kit de extração
    caixa_armazenamento: Optional[str] = Field(default=None, alias="caixa", description="Caixa de armazenamento / freezer")
    
    # Disponibilidade de frações
    dna_disponivel: bool = False
    rna_disponivel: bool = False
    sequenciamento_disponivel: bool = Field(default=False, alias="sequenciamento")

    # Campos de projetos e geolocalização (opcionais)
    amostra_id_projeto: Optional[str] = None # id do projeto a que a amostra pertence
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    amostra_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Normalização heurística de 'metodo_coleta':
    #      - Converter strings recebidas de planilhas/formulários para o Enum
    #        'MetodoColeta' correspondente (busca case-insensitive).
    #      - Mapear termos frequentes de planilhas (ex: 'soro' -> MetodoColeta.SORO,
    #        'papel filtro' -> MetodoColeta.PAPEL_FILTRO, 'cloacal'/'oral' ->
    #        MetodoColeta.SWAB_ORAL_CLOACAL, 'sangue' -> MetodoColeta.SANGUE,
    #        'órgão'/'orgao' -> MetodoColeta.ORGAOS, 'tecido' -> MetodoColeta.TECIDO,
    #        'fezes' -> MetodoColeta.FEZES, etc.).
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/amostra_service.py' (ou
    #     rotina de ingestão/ETL de planilhas) antes de instanciar a entidade Amostra.
    #   - Camada de Controladores: 'backend/src/controllers/amostra_controller.py'
    #     ao receber e sanitizar os payloads dos endpoints HTTP.
    # =========================================================================