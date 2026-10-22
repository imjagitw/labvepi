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
from src.services.estoque_reagente_service import (
    estoque_reagente_service,
    EstoqueReagente,
    EstoqueReagenteCreate,
    EstoqueReagenteUpdate,
    EstoqueReagenteDetails,
)

router = criar_router(prefix="/estoque_reagente", tags=["EstoqueReagente"])

@router.post(
    "/",
    response_model=EstoqueReagente,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Cadastrar nova visão de estoque consolidado",
    description="Registra uma nova entidade agregada de estoque para um reagente químico/biológico, consolidando métricas e vinculando lotes iniciais caso fornecidos.",
)
def criar_estoque(
    estoque_input: EstoqueReagenteCreate,
    confirmar_novo_estoque: bool = Query(
        False, description="Confirmação explícita de criação de nova entrada consolidada de estoque"
    ),
):
    return estoque_reagente_service.criar_estoque(
        dados_estoque=estoque_input,
        confirmar_novo_estoque=confirmar_novo_estoque,
    )

@router.get(
    "/",
    response_model=List[EstoqueReagente],
    responses=RESPOSTAS_LISTAR,
    summary="Listar visões consolidadas de estoque",
    description="Retorna a listagem de estoques agregados com suporte a busca textual, ordenação, paginação e opção de sincronização com lotes físicos em tempo real.",
)
def listar_estoques(
    termo_busca: Optional[str] = Query(None, description="Busca textual por código ou nome do reagente"),
    apenas_com_lotes: Optional[bool] = Query(None, description="Filtrar apenas reagentes que possuem lotes cadastrados"),
    ordenar_por: str = Query("nome", description="Critério de ordenação ('nome' ou 'codigo')"),
    skip: int = Query(0, ge=0, description="Quantidade de registros para pular"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    return estoque_reagente_service.listar_estoques(
        termo_busca=termo_busca,
        apenas_com_lotes=apenas_com_lotes,
        ordenar_por=ordenar_por,
        skip=skip,
        limit=limit,
    )

@router.get(
    "/contagem",
    responses=RESPOSTAS_CONTAGEM,
    summary="Total de reagentes consolidados em estoque",
    description="Retorna a quantidade total de registros consolidados de reagentes gerenciados no estoque.",
)
def contar_estoques():
    return {"total": estoque_reagente_service.contar_estoques()}

@router.post(
    "/recalcular",
    responses=RESPOSTAS_CONTAGEM,
    summary="Recalcular todo o inventário de reagentes",
    description="Varre todos os lotes físicos registrados no laboratório e atualiza as visões agregadas de estoque correspondentes a cada reagente.",
)
def recalcular_todo_estoque():
    total = estoque_reagente_service.recalcular_todo_estoque()
    return {"reagentes_atualizados": total}

@router.post(
    "/sincronizar/{nome_reagente}",
    response_model=EstoqueReagente,
    responses=RESPOSTAS_OBTER,
    summary="Sincronizar estoque de um reagente específico",
    description="Recalcula as métricas consolidadas de estoque para um reagente com base em seus lotes físicos atuais registrados.",
)
def sincronizar_estoque(nome_reagente: str):
    resultado = estoque_reagente_service.sincronizar_lotes(nome_reagente=nome_reagente)
    if not resultado:
        raise KeyError(f"Nenhum lote físico ou registro de estoque encontrado para o reagente '{nome_reagente}'.")
    return resultado

@router.get(
    "/codigo/{codigo}",
    response_model=List[EstoqueReagente],
    responses=RESPOSTAS_LISTAR,
    summary="Buscar estoque por código do reagente",
    description="Recupera as entradas consolidadas de estoque associadas ao código informado.",
)
def obter_estoque_por_codigo(codigo: str):
    return estoque_reagente_service.obter_estoque_por_codigo(codigo=codigo)

@router.get(
    "/{identificador}",
    response_model=EstoqueReagente,
    responses=RESPOSTAS_OBTER,
    summary="Obter visão agregada de estoque",
    description="Recupera a visão consolidada de estoque pelo seu ID numérico sequencial ou pelo nome exato do reagente.",
)
def obter_estoque(
    identificador: str,
    sincronizar: bool = Query(True, description="Recalcula as métricas a partir dos lotes físicos em tempo real"),
):
    return estoque_reagente_service.obter_estoque(identificador=identificador, sincronizar=sincronizar)

@router.get(
    "/{identificador}/detalhes",
    response_model=EstoqueReagenteDetails,
    responses=RESPOSTAS_OBTER,
    summary="Obter detalhes de estoque com projeção completa de lotes",
    description="Retorna a visão detalhada de estoque com a listagem de todos os lotes físicos vinculados enriquecidos com indicadores de validade.",
)
def obter_estoque_detalhes(identificador: str):
    return estoque_reagente_service.obter_estoque_detalhes(identificador=identificador)

@router.put(
    "/{identificador}",
    response_model=EstoqueReagente,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar visão agregada de estoque",
    description="Atualiza os metadados de um estoque consolidado (como código ou nome) e sincroniza os volumes agregados.",
)
def atualizar_estoque(
    identificador: str,
    estoque_update: EstoqueReagenteUpdate,
    confirmar_atualizacao_estoque: bool = Query(
        False, description="Confirmação explícita de atualização do estoque consolidado"
    ),
):
    return estoque_reagente_service.atualizar_estoque(
        identificador=identificador,
        dados_atualizacao=estoque_update,
        confirmar_atualizacao_estoque=confirmar_atualizacao_estoque,
    )

@router.delete(
    "/{identificador}",
    responses=RESPOSTAS_DELETAR,
    summary="Remover registro de estoque consolidado",
    description="Remove a visão agregada de estoque do banco, com opção de remoção em cascata de todos os lotes físicos vinculados.",
)
def deletar_estoque(
    identificador: str,
    deletar_lotes_vinculados: bool = Query(
        False, description="Remove também todos os lotes físicos associados a este reagente"
    ),
):
    estoque_reagente_service.deletar_estoque(
        identificador=identificador,
        deletar_lotes_vinculados=deletar_lotes_vinculados,
    )
    return None