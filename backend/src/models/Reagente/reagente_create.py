from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from src.models.Reagente import EtapaReagente, UnidadeMedida

class ReagenteCreate(BaseModel):
    """
    Entidade representativa de um lote físico de reagente no laboratório.
    Contém apenas atributos e tipagens declarativas, sem ações temporais,
    resolução dinâmica de sinônimos ou validadores heurísticos.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    # Obrigatórios
    id: Optional[int] = Field(default=None, alias="_id", description="Chave primária autoincrementada no banco")
    reagente_codigo: str = Field(..., alias="codigo", description="Código do reagente")
    reagente_nome: str = Field(..., alias="nome", description="Nome do reagente")
    numero_lote: str = Field(..., description="Número identificador do lote")
    marca: str = Field(..., description="Marca ou fabricante do reagente")
    data_validade: date = Field(..., description="Data de validade do lote")
    quantidade_unidade: int = Field(default=1, alias="quantidade_unidade", description="Quantidade de frascos/unidades")
    reagente_local_armazenamento: str = Field(..., alias="local_armazenamento", description="Local físico de armazenamento")
    
    # Opcionais
    reagente_id: Optional[str] = Field(default=None, description="Identificador único padrão do laboratório")
    quantidade_volume: Optional[float] = Field(default=None, description="Volume ou massa contida em cada unidade")
    unidade_medida: UnidadeMedida = Field(default="ml", alias="unidade", description="Unidade de medida (ex: ml, L, g)")
    reagente_etapa: Optional[EtapaReagente] = Field(default=None, alias="etapa", description="Etapa laboratorial em que é empregado")
    reagente_observacoes: Optional[str] = Field(default=None, alias="observacoes", description="Observações complementares")

    confirmar_novo_reagente: bool = False

    # =========================================================================
    # AÇÕES / VALIDAÇÕES / SERVICES RETIRADOS DESTE MODEL:
    # -------------------------------------------------------------------------
    # O QUE FAZER:
    #   1. Validação de Lote e Cadastro Inicial:
    #      - Verificar existência prévia do lote no banco de dados.
    #      - Validar integridade da data de validade e quantidades positivas.
    #   2. Vinculação com Estoque Agregado:
    #      - Localizar ou criar a entidade agregada EstoqueReagente associada ao
    #        'reagente_nome' / 'reagente_codigo' e atualizar as métricas consolidadas.
    #
    # ONDE FAZER:
    #   - Camada de Serviços: 'backend/src/services/reagente_service.py' (criar_reagente).
    #   - Camada de Controladores: 'backend/src/controllers/reagente_controller.py'.
    # =========================================================================