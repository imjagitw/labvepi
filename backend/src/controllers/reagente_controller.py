from typing import Optional, List
from fastapi import Query, status
from src.controllers.response_controller import (
    criar_router,
    RESPOSTAS_CRIAR,
    RESPOSTAS_LISTAR,
    RESPOSTAS_OBTER,
    RESPOSTAS_ATUALIZAR,
    RESPOSTAS_DELETAR,
    RESPOSTAS_CONTAGEM,
)
from src.services.reagente_service import (
    reagente_service,
    Reagente,
    ReagenteCreate,
    ReagenteUpdate,
    ReagenteDetails,
)

router = criar_router(prefix="/reagente", tags=["Reagente"])

@router.post(
    "/",
    response_model=Reagente,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Cadastrar novo lote de reagente",
    description=(
        "Registra um novo lote físico de reagente químico/biológico no laboratório, com validação de datas, unicidade de lote e sincronização automática de estoque. "
        "A chave primária (_id) é gerada automaticamente pelo banco e não deve ser informada."
    ),
)
def criar_reagente(
    reagente_input: ReagenteCreate,
    confirmar_novo_reagente: bool = Query(
        False, description="Confirmação explícita de cadastro de novo reagente/lote"
    ),
):
    return reagente_service.criar_reagente(
        dados_reagente=reagente_input,
        confirmar_novo_reagente=confirmar_novo_reagente,
    )

@router.get(
    "/",
    response_model=List[Reagente],
    responses=RESPOSTAS_LISTAR,
    summary="Listar lotes de reagentes",
    description="Retorna a listagem de lotes físicos cadastrados com suporte a filtros por nome, código, marca, local de armazenamento, vencimento, busca textual e paginação.",
)
def listar_reagentes(
    nome: Optional[str] = Query(None, description="Filtrar por nome do reagente"),
    codigo: Optional[str] = Query(None, description="Filtrar por código do reagente"),
    marca: Optional[str] = Query(None, description="Filtrar por fabricante ou marca"),
    local_armazenamento: Optional[str] = Query(None, description="Filtrar por local de armazenamento"),
    apenas_vencidos: Optional[bool] = Query(None, description="Filtrar apenas lotes com prazo de validade expirado"),
    termo_busca: Optional[str] = Query(None, description="Busca textual por código, nome, lote, marca ou observações"),
    ordenar_por: str = Query("id", description="Critério de ordenação ('id', 'nome', 'validade')"),
    skip: int = Query(0, ge=0, description="Quantidade de registros para pular"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    return reagente_service.listar_reagentes(
        nome=nome,
        codigo=codigo,
        marca=marca,
        local_armazenamento=local_armazenamento,
        apenas_vencidos=apenas_vencidos,
        termo_busca=termo_busca,
        ordenar_por=ordenar_por,
        skip=skip,
        limit=limit,
    )

@router.get(
    "/contagem",
    responses=RESPOSTAS_CONTAGEM,
    summary="Total de lotes de reagentes",
    description="Retorna a contagem total de lotes físicos registrados no laboratório.",
)
def contar_reagentes():
    return {"total": reagente_service.contar_reagentes()}

@router.get(
    "/lote/{numero_lote}",
    response_model=List[Reagente],
    responses=RESPOSTAS_LISTAR,
    summary="Buscar reagentes por número de lote",
    description="Recupera todos os registros de reagentes vinculados ao número identificador de lote informado.",
)
def listar_reagentes_por_lote(numero_lote: str):
    return reagente_service.listar_por_lote(numero_lote=numero_lote)

@router.get(
    "/{identificador}",
    response_model=Reagente,
    responses=RESPOSTAS_OBTER,
    summary="Obter lote de reagente",
    description="Recupera os dados de um lote físico pelo ID numérico ou pelo identificador único de laboratório (ex: 'REA_0001').",
)
def obter_reagente(identificador: str):
    return reagente_service.obter_reagente(identificador=identificador)

@router.get(
    "/{identificador}/detalhes",
    response_model=ReagenteDetails,
    responses=RESPOSTAS_OBTER,
    summary="Obter detalhes do reagente com status de validade",
    description="Retorna a visão enriquecida do lote de reagente com os indicadores calculados de vencimento ('esta_vencido' e 'dias_para_vencer').",
)
def obter_reagente_detalhes(identificador: str):
    return reagente_service.obter_reagente_detalhes(identificador=identificador)

@router.put(
    "/{identificador}",
    response_model=Reagente,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar lote de reagente",
    description=(
        "Atualiza os dados de um lote físico existente, permitindo alterar apenas um campo ou mais e deixando o restante inalterado. "
        "Recalcula indicadores de vencimento e sincroniza o estoque consolidado correspondente. "
        "O reagente é identificado na rota; a chave primária (_id) é imutável."
    ),
)
@router.patch(
    "/{identificador}",
    response_model=Reagente,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar lote de reagente (parcial)",
    description=(
        "Atualiza parcialmente os dados de um lote físico existente, permitindo alterar apenas os campos selecionados e deixando o restante inalterado. "
        "O reagente é identificado na rota; a chave primária (_id) é imutável."
    ),
)
def atualizar_reagente(
    identificador: str,
    reagente_update: ReagenteUpdate,
    confirmar_atualizacao_reagente: bool = Query(
        False, description="Confirma alteração de dados do reagente"
    ),
):
    return reagente_service.atualizar_reagente(
        identificador=identificador,
        dados_atualizacao=reagente_update,
        confirmar_atualizacao_reagente=confirmar_atualizacao_reagente,
    )

@router.delete(
    "/{identificador}",
    responses=RESPOSTAS_DELETAR,
    summary="Remover lote de reagente",
    description="Remove um lote físico de reagente cadastrado pelo seu identificador e atualiza a visão agregada de estoque.",
)
def deletar_reagente(identificador: str):
    reagente_service.deletar_reagente(identificador=identificador)
    return None