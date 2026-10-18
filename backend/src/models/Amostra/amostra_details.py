from datetime import date
from typing import Optional, Union, List
from pydantic import BaseModel, ConfigDict, Field
from src.models.Amostra import CondicaoArmazenamento, DestinoAmostra, FaseAmostra, MaterialBiologico, StatusAmostra
from src.models.Animal import Animal
from src.models.Exame.exame import Exame

class AmostraDetails(BaseModel):
    """
    Schema de resposta detalhada de uma amostra biológica:
    - Todas as informações da amostra cadastrada (com saneamento explícito de campos não informados).
    - Dados completos do animal de origem ao qual pertence.
    - Quantidade total e lista completa dos exames diagnósticos vinculados.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos
    id: Optional[int] = Field(default=None, alias="_id", description="Identificador sequencial do banco")
    amostra_id: str = Field(..., description="ID único do laboratório (ex: L 1, AMS001)")
    animal_id: str = Field(..., description="ID ou chave do animal vinculado (ex: AN001, A547)")
    animal: Optional[Animal] = Field(
        default=None, 
        description="Dados completos do animal de origem vinculado a esta amostra"
    )

    # Datas de rastreamento
    data_coleta_amostra: Optional[Union[date, str]] = Field(
        default_factory=date.today,
        alias="data_coleta",
        description="Data em que a coleta foi realizada ou 'Não informado'"
    )
    data_entrega: Optional[Union[date, str]] = Field(
        default_factory=date.today,
        alias="data_recebimento",
        description="Data de entrada no LABVEPI ou 'Não informado'"
    )

    # Tipo / Material biológico coletado
    material_biologico: Union[MaterialBiologico, str] = Field(
        default=MaterialBiologico.OUTRO,
        alias="metodo_coleta",
        description="Material biológico coletado"
    )

    # Status e Laudo
    status_amostra: Union[StatusAmostra, str] = Field(
        default=StatusAmostra.DISPONIVEL,
        description="Status da amostra no acervo"
    )
    laudo_liberado: bool = Field(
        default=False,
        description="Indica se o laudo foi emitido/liberado"
    )

    # Campos de triagem / laboratório (informando o que não foi informado)
    local_coleta_amostra: Optional[str] = Field(
        default="Não informado",
        alias="local_coleta",
        description="Local específico da coleta"
    )
    nome_coletor: Optional[str] = Field(
        default="Não informado",
        description="Nome do responsável pela coleta"
    )
    condicao_armazenamento: Optional[Union[CondicaoArmazenamento, str]] = Field(
        default="Não informado",
        description="Condição física de armazenamento da amostra"
    )
    fase_amostra: Optional[Union[FaseAmostra, str]] = Field(
        default=FaseAmostra.EXTRACAO,
        description="Fase atual no laboratório"
    )
    destino_amostra: Optional[Union[DestinoAmostra, str]] = Field(
        default=DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI,
        description="Destino ou instituição responsável pela custódia"
    )
    kit_utilizado: Optional[str] = Field(
        default="Não informado",
        description="Kit de extração utilizado"
    )
    caixa_armazenamento: Optional[str] = Field(
        default="Não informado",
        alias="caixa",
        description="Caixa de armazenamento / freezer"
    )

    # Disponibilidade de frações
    dna_disponivel: bool = Field(
        default=False,
        description="Indica se há fração de DNA disponível"
    )
    rna_disponivel: bool = Field(
        default=False,
        description="Indica se há fração de RNA disponível"
    )
    sequenciamento_disponivel: bool = Field(
        default=False,
        alias="sequenciamento",
        description="Indica se há material disponível para sequenciamento"
    )

    # Projetos, geolocalização e observações
    amostra_id_projeto: Optional[str] = Field(
        default="Não informado",
        description="Identificador do projeto ao qual a amostra pertence"
    )
    longitude: Optional[Union[float, str]] = Field(
        default="Não informado",
        description="Coordenada de longitude do ponto de coleta"
    )
    latitude: Optional[Union[float, str]] = Field(
        default="Não informado",
        description="Coordenada de latitude do ponto de coleta"
    )
    amostra_observacoes: Optional[str] = Field(
        default="Não informado",
        alias="observacoes",
        description="Observações e notas adicionais sobre a amostra"
    )

    # Exames associados
    quantidade_exames: int = Field(
        default=0,
        description="Quantidade total de exames laboratoriais vinculados a esta amostra"
    )
    exames: List[Exame] = Field(
        default_factory=list,
        description="Lista completa dos exames laboratoriais realizados a partir desta amostra"
    )

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Saneamento e Formatação para Exibição:
    #      - Preencher campos vazios/nulos com 'Não informado' na visão detalhada.
    #      - Converter coordenadas geográficas e datas em strings formatadas legíveis.
    #   2. Agregação de Relacionamentos:
    #      - Carregar entidade Animal vinculada via animal_service.obter_animal.
    #      - Carregar exames associados e calcular quantidade_exames via exame_repo.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/amostra_service.py'
    #     (preencher_nao_informados_e_relacionamentos / obter_amostra_detalhes).
    #   - Camada de Controladores: 'backend/src/controllers/amostra_controller.py'.
    # =========================================================================