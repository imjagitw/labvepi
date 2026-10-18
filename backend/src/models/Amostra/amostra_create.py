from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from src.models.Amostra import MaterialBiologico, FaseAmostra, StatusAmostra, DestinoAmostra, CondicaoArmazenamento

class AmostraCreate(BaseModel):
    """
    Schema de criação de uma nova amostra biológica (DTO de entrada estrito):
    - Identificação e vínculo obrigatório com o animal de origem.
    - Campos laboratoriais e de rastreamento obrigatórios sem defaults permissivos.
    - Rejeição de valores 'Não informado' e sentinelas é validada em AmostraService.criar_amostra.
    - Cargas de planilhas são pré-processadas e canonicizadas pelo pipeline de ETL.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos primários
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    amostra_id: str = Field(..., description="ID único do laboratório (ex: L 1, AMS001)")
    animal_id: str = Field(..., alias="animal", description="ID ou chave do animal vinculado (ex: AN001, A547)")

    # Datas de rastreamento
    data_coleta_amostra: date = Field(
        ...,
        alias="data_coleta",
        description="Data em que a coleta foi realizada"
    )
    data_entrega: Optional[date] = Field(
        default=None,
        alias="data_recebimento",
        description="Data em que a amostra deu entrada no LABVEPI"
    )

    # Tipo / Material biológico coletado (Enum estrito em novos cadastros)
    material_biologico: MaterialBiologico = Field(
        ...,
        alias="metodo_coleta",
        description="Material biológico coletado"
    )

    # Status e Laudo
    status_amostra: StatusAmostra = Field(
        ...,
        description="Status inicial da amostra no acervo"
    )
    laudo_liberado: bool = Field(
        ...,
        description="Indica se o laudo foi liberado"
    )

    # Campos de triagem / laboratório
    local_coleta_amostra: str = Field(
        ...,
        alias="local_coleta",
        min_length=1,
        description="Local específico da coleta"
    )
    nome_coletor: str = Field(
        ...,
        min_length=1,
        description="Nome do responsável pela coleta"
    )
    condicao_armazenamento: CondicaoArmazenamento = Field(
        ...,
        description="Condição física de armazenamento da amostra"
    )
    fase_amostra: FaseAmostra = Field(
        ...,
        description="Fase inicial da amostra no laboratório"
    )
    destino_amostra: DestinoAmostra = Field(
        ...,
        description="Destino ou instituição responsável pela custódia"
    )
    kit_utilizado: str = Field(
        ...,
        min_length=1,
        description="Kit de extração utilizado"
    )
    caixa_armazenamento: str = Field(
        ...,
        alias="caixa",
        min_length=1,
        description="Caixa de armazenamento / freezer"
    )

    # Disponibilidade de frações
    dna_disponivel: bool = Field(
        ...,
        description="Indica se há fração de DNA disponível"
    )
    rna_disponivel: bool = Field(
        ...,
        description="Indica se há fração de RNA disponível"
    )
    sequenciamento_disponivel: bool = Field(
        ...,
        alias="sequenciamento",
        description="Indica se há material disponível para sequenciamento"
    )

    # Campos de projetos e geolocalização (opcionais)
    amostra_id_projeto: Optional[str] = Field(
        default=None,
        description="Identificador do projeto ao qual a amostra pertence"
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Coordenada de longitude do ponto de coleta (decimal WGS84)"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Coordenada de latitude do ponto de coleta (decimal WGS84)"
    )
    amostra_observacoes: Optional[str] = Field(
        default=None,
        alias="observacoes",
        description="Observações e notas adicionais sobre a amostra"
    )

    # Flags de controle de fluxo / confirmação
    confirmar_nova_amostra: bool = Field(
        default=False,
        description="Confirmação explícita de cadastro de nova amostra"
    )
    confirmar_novo_animal: bool = Field(
        default=False,
        description="Confirmação de vínculo a animal recém-cadastrado"
    )

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Parsing e Conversão de Datas e Coordenadas no Service:
    #      - Converter strings recebidas de datas ('AAAA-MM-DD', 'DD/MM/AAAA') para datetime.date.
    #      - Converter coordenadas com vírgula ('-5,089') ou DMS (05°05'21"S) para float decimal.
    #      - Tratar sentinelas textuais ('NI', '-', 'Não informado') como None.
    #   2. Cargas e Normalizações:
    #      - Assegurar compatibilidade de tipos e enums estritos. Planilhas legadas
    #        são normalizadas previamente pelos extratores ETL.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/amostra_service.py' (criar_amostra).
    #   - Camada de Controladores: 'backend/src/controllers/amostra_controller.py'.
    # =========================================================================