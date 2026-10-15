from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from src.models.Amostra import MaterialBiologico, FaseAmostra, StatusAmostra, DestinoAmostra, CondicaoArmazenamento

class AmostraUpdate(BaseModel):
    """
    Schema de atualização de uma amostra biológica existente (DTO de entrada):
    - Todos os campos são opcionais para suportar atualizações parciais (PATCH/PUT).
    - Preserva compatibilidade de aliases com o banco de dados e formulários.
    - Contém flag de confirmação de atualização.
    """
    model_config = ConfigDict(populate_by_name=True)

    # Identificação e vínculos
    animal_id: Optional[str] = Field(
        default=None,
        alias="animal",
        description="ID ou chave do animal vinculado (ex: AN001, A547)"
    )

    # Datas de rastreamento
    data_coleta_amostra: Optional[date] = Field(
        default=None,
        alias="data_coleta",
        description="Data em que a coleta foi realizada"
    )
    data_entrega: Optional[date] = Field(
        default=None,
        alias="data_recebimento",
        description="Data em que a amostra deu entrada no LABVEPI"
    )

    # Tipo / Material biológico coletado
    material_biologico: Optional[Union[MaterialBiologico, str]] = Field(
        default=None,
        alias='metodo_coleta',      
        description="Material biológico coletado"
    )

    # Status e Laudo
    status_amostra: Optional[StatusAmostra] = Field(
        default=None,
        description="Status da amostra no acervo"
    )
    laudo_liberado: Optional[bool] = Field(
        default=None,
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
        default=None,
        description="Fase atual da amostra no fluxo laboratorial"
    )
    destino_amostra: Optional[DestinoAmostra] = Field(
        default=None,
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
    dna_disponivel: Optional[bool] = Field(
        default=None,
        description="Indica se há fração de DNA disponível"
    )
    rna_disponivel: Optional[bool] = Field(
        default=None,
        description="Indica se há fração de RNA disponível"
    )
    sequenciamento_disponivel: Optional[bool] = Field(
        default=None,
        alias="sequenciamento",
        description="Indica se há material disponível para sequenciamento"
    )

    # Campos de projetos e geolocalização
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

    # Flags de controle
    confirmar_atualizacao_amostra: bool = Field(
        default=False,
        description="Confirmação explícita para atualização da amostra"
    )
