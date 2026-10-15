from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Amostra import MaterialBiologico, FaseAmostra, StatusAmostra, DestinoAmostra, CondicaoArmazenamento

class AmostraCreate(BaseModel):
    """
    Schema de criação de uma nova amostra biológica (DTO de entrada):
    - Identificação e vínculo obrigatório com o animal de origem.
    - Datas de rastreamento com default dinâmico para a data atual.
    - Tipo e método de coleta (matriz biológica).
    - Status de triagem laboratorial, frações disponíveis e armazenamento.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos primários
    amostra_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: L 1, AMS001)")
    animal_id: str = Field(..., alias="animal", description="ID ou chave do animal vinculado (ex: AN001, A547)")

    # Datas de rastreamento
    data_coleta_amostra: Optional[date] = Field(
        default_factory=date.today,
        alias="data_coleta",
        description="Data em que a coleta foi realizada"
    )
    data_entrega: Optional[date] = Field(
        default_factory=date.today,
        alias="data_recebimento",
        description="Data em que a amostra deu entrada no LABVEPI"
    )

    # Tipo / Material biológico coletado
    material_biologico: Union[MaterialBiologico, str] = Field(
        default=MaterialBiologico.OUTRO,
        alias="metodo_coleta",
        description="Material biológico coletado"
    )

    # Status e Laudo
    status_amostra: StatusAmostra = Field(
        default=StatusAmostra.DISPONIVEL,
        description="Status inicial da amostra no acervo"
    )
    laudo_liberado: bool = Field(
        default=False,
        description="Indica se o laudo foi liberado"
    )

    # Campos de triagem / laboratório
    local_coleta_amostra: Optional[str] = Field(
        default=None,
        alias="local_coleta",
        description="Local específico da coleta"
    )
    nome_coletor: Optional[str] = Field(
        default=None,
        description="Nome do responsável pela coleta"
    )
    condicao_armazenamento: Optional[CondicaoArmazenamento] = Field(
        default=None,
        description="Condição física de armazenamento da amostra"
    )
    fase_amostra: Optional[FaseAmostra] = Field(
        default=FaseAmostra.EXTRACAO,
        description="Fase inicial da amostra no laboratório"
    )
    destino_amostra: Optional[DestinoAmostra] = Field(
        default=DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI,
        description="Destino ou instituição responsável pela custódia"
    )
    kit_utilizado: Optional[str] = Field(
        default=None,
        description="Kit de extração utilizado"
    )
    caixa_armazenamento: Optional[str] = Field(
        default=None,
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

    # Campos de projetos e geolocalização (opcionais)
    amostra_id_projeto: Optional[str] = Field(
        default=None,
        description="Identificador do projeto ao qual a amostra pertence"
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Coordenada de longitude do ponto de coleta"
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Coordenada de latitude do ponto de coleta"
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