from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Union
from src.models.Amostra import CondicaoArmazenamento, DestinoAmostra, FaseAmostra, MaterialBiologico, StatusAmostra

class Amostra(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos primários
    id: Optional[int] = None  # Autoincrementado no banco
    amostra_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: L 1, AMS001)")    
    animal_id: str = Field(..., description="ID ou chave do animal vinculado (ex: AN001, A547)")
    
    # Datas de rastreamento
    data_coleta_amostra: Optional[date] = Field(default_factory=date.today, alias="data_coleta", description="Data em que a coleta foi realizada")
    data_entrega: Optional[date] = Field(default_factory=date.today, alias="data_recebimento", description="Data em que a amostra deu entrada no LABVEPI")
    
    # Tipo / Material biológico coletado
    material_biologico: Union[MaterialBiologico, str] = Field(default=MaterialBiologico.OUTRO, alias="metodo_coleta", description="Material biológico coletado")
    
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
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    amostra_observacoes: Optional[str] = Field(default=None, alias="observacoes")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Normalização heurística de 'material_biologico':
    #      - Converter strings recebidas de planilhas/formulários para o Enum
    #        'MaterialBiologico' correspondente (busca case-insensitive).
    #      - Mapear termos frequentes de planilhas (ex: 'soro' -> MaterialBiologico.SORO,
    #        'papel filtro' -> MaterialBiologico.PAPEL_FILTRO, 'cloacal'/'oral' ->
    #        MaterialBiologico.SWAB_ORAL_CLOACAL, 'sangue' -> MaterialBiologico.SANGUE,
    #        'órgão'/'orgao' -> MaterialBiologico.ORGAOS, 'tecido' -> MaterialBiologico.TECIDO,
    #        'fezes' -> MaterialBiologico.FEZES, etc.).
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/amostra_service.py' (ou
    #     rotina de ingestão/ETL de planilhas) antes de instanciar a entidade Amostra.
    #   - Camada de Controladores: 'backend/src/controllers/amostra_controller.py'
    #     ao receber e sanitizar os payloads dos endpoints HTTP.
    # =========================================================================