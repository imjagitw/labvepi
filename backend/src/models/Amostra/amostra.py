from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.models.Amostra import CondicaoArmazenamento, DestinoAmostra, FaseAmostra, MaterialBiologico, StatusAmostra

class Amostra(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos primários
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    amostra_id: str = Field(..., description="ID único do laboratório (ex: L 1, AMS001)")    
    animal_id: str = Field(..., description="ID ou chave do animal vinculado (ex: AN001, A547)")
    
    # Datas de rastreamento
    data_coleta_amostra: Optional[date] = Field(default_factory=date.today, alias="data_coleta", description="Data em que a coleta foi realizada")
    data_entrega: Optional[date] = Field(default_factory=date.today, alias="data_recebimento", description="Data em que a amostra deu entrada no LABVEPI")
    
    # Tipo / Material biológico coletado
    material_biologico: MaterialBiologico = Field(default=MaterialBiologico.OUTRO, alias="metodo_coleta", description="Material biológico coletado")
    
    # Status e Laudo
    status_amostra: StatusAmostra = StatusAmostra.DISPONIVEL  # nasce disponível
    laudo_liberado: bool = False 

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
    longitude: Optional[float] = Field(default=None, description="Coordenada decimal de longitude padrão WGS84")
    latitude: Optional[float] = Field(default=None, description="Coordenada decimal de latitude padrão WGS84")
    amostra_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Normalização de Datas de Coleta e Entrega:
    #      - Converter qualquer string válida (ISO 'AAAA-MM-DD', brasileira 'DD/MM/AAAA')
    #        ou objetos datetime para datetime.date.
    #      - Tratar sentinelas textuais ('NI', '-', 'Não informado') como None.
    #   2. Normalização Geoespacial de Coordenadas:
    #      - Converter coordenadas em float decimal, strings com vírgula ('-5,089'),
    #        ou graus sexagesimais DMS (ex: 05°05'21"S) para float decimal WGS84.
    #      - Tratar sentinelas ('-', 'NI') como None.
    #   3. Normalização Heurística de Enums (Carga Legada):
    #      - Normalizar termos textuais livres para os Enums estritos
    #        (MaterialBiologico, StatusAmostra, CondicaoArmazenamento, FaseAmostra, DestinoAmostra)
    #        apenas quando carga_legada=True. Em novos cadastros, exigir o Enum estrito.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/amostra_service.py' (criar_amostra,
    #     atualizar_amostra e aplicar_obrigatoriedade).
    #   - Camada de Domínio: 'backend/src/domain/normalizacao.py' (funções
    #     normalizar_data, normalizar_coordenada, normalizar_material_biologico).
    # =========================================================================