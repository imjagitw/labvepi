from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class UnidadeMedida(str, Enum):
    ML = 'ml'
    L = 'L'
    UL = 'µl'
    G = 'g'
    MG = 'mg'
    KG = 'kg'
    UNIDADE = 'un'

class Reagente(BaseModel):
    """
    Entidade representativa de um lote físico de reagente no laboratório.
    Contém apenas atributos e tipagens declarativas, sem ações temporais,
    resolução dinâmica de sinônimos ou validadores heurísticos.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    # Obrigatórios
    id: Optional[int] = None # Gerado automaticamente autoincrementado
    reagente_codigo: str = Field(..., alias="codigo", description="Código do reagente")
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")
    numero_lote: str = Field(..., description="Número identificador do lote")
    marca: str = Field(..., description="Marca ou fabricante do reagente")
    data_validade: date = Field(..., description="Data de validade do lote")
    quantidade_unidade: int = Field(default=1, alias="quantidade_unidade", description="Quantidade de frascos/unidades")
    reagente_local_armazenamento: str = Field(..., alias="local_armazenamento", description="Local físico de armazenamento")
    
    # Opcionais
    reagente_id: Optional[str] = Field(default=None, alias="_id", description="Identificador único padrão do laboratório")
    quantidade_volume: Optional[float] = Field(default=None, description="Volume ou massa contida em cada unidade")
    unidade_medida: str = Field(default="ml", alias="unidade", description="Unidade de medida (ex: ml, L, g)")
    reagente_etapa: Optional[str] = Field(default=None, alias="etapa", description="Etapa laboratorial em que é empregado")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes", description="Observações complementares")

    # Atributos de dados calculados pelo serviço (puros campos para transporte de estado):
    esta_vencido: Optional[bool] = Field(default=None, description="Indicação se o lote está vencido (calculado pelo serviço)")
    dias_para_vencer: Optional[int] = Field(default=None, description="Dias restantes até o vencimento (calculado pelo serviço)")

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Parsing de 'data_validade':
    #      - Converter strings em formatos locais (ex: DD/MM/AAAA) para o tipo 'datetime.date'.
    #   2. Normalização de 'unidade_medida':
    #      - Tratar e converter sinônimos textuais ('litros' -> 'L', 'gramas' -> 'g',
    #        'cx' -> 'cx', 'frascos' -> 'frasco', 'tubos' -> 'tubo', etc.) para unidades canônicas.
    #   3. Resolução de Sinônimos de Payloads Legados:
    #      - Adaptar payloads de importação/APIs antigas onde 'quantidade' mapeava para
    #        'quantidade_unidade' e 'fabricante' mapeava para 'marca'.
    #   4. Ações e Cálculos Temporais de Validade:
    #      - Calcular se o lote está vencido: 'data_validade < date.today()'.
    #      - Calcular dias restantes: '(data_validade - date.today()).days'.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/reagente_service.py' (em métodos
    #     como 'processar_lote_reagente', 'verificar_validade_lotes', etc.).
    #   - Camada de Controladores: 'backend/src/controllers/reagente_controller.py'
    #     e scripts de importação ('streamlit/pages/4_Importar.py') antes da instanciação do modelo.
    # =========================================================================