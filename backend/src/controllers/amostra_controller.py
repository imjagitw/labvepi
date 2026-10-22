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
from src.services.amostra_service import (
    amostra_service,
    Amostra,
    AmostraCreate,
    AmostraUpdate,
    AmostraDetails,
    CondicaoArmazenamento,
    DestinoAmostra,
    FaseAmostra,
    MaterialBiologico,
    StatusAmostra,
)

router = criar_router(prefix="/amostra", tags=["Amostra"])

@router.post(
    "/",
    response_model=Amostra,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Cadastrar uma nova amostra biológica",
    description="Cadastra uma nova amostra no acervo, validando o identificador único e o animal de origem vinculado.",
)
def criar_amostra(
    amostra_input: AmostraCreate,
    confirmar_nova_amostra: bool = Query(
        False, description="Confirmação explícita de cadastro de nova amostra"
    ),
    confirmar_novo_animal: bool = Query(
        False, description="Confirma vínculo a animal ainda não cadastrado no catálogo"
    ),
):
    return amostra_service.criar_amostra(
        dados_amostra=amostra_input,
        confirmar_nova_amostra=confirmar_nova_amostra,
        confirmar_novo_animal=confirmar_novo_animal,
    )

@router.get(
    "/",
    response_model=List[Amostra],
    responses=RESPOSTAS_LISTAR,
    summary="Listar amostras com filtros",
    description="Retorna a lista de amostras biológicas cadastradas com suporte a múltiplos filtros analíticos, busca e paginação.",
)
def listar_amostras(
    animal_id: Optional[str] = Query(None, description="Filtrar por ID do animal vinculado"),
    status_amostra: Optional[StatusAmostra] = Query(None, description="Filtrar por status no acervo"),
    fase_amostra: Optional[FaseAmostra] = Query(None, description="Filtrar por fase atual no laboratório"),
    condicao_armazenamento: Optional[CondicaoArmazenamento] = Query(None, description="Filtrar por condição de armazenamento"),
    destino_amostra: Optional[DestinoAmostra] = Query(None, description="Filtrar por instituição responsável / custodiante"),
    material_biologico: Optional[MaterialBiologico] = Query(None, description="Filtrar por tipo de matriz / material biológico"),
    termo_busca: Optional[str] = Query(None, description="Busca textual por ID, observações, local, coletor, etc."),
    ordenar_por: str = Query("id", description="Critério de ordenação"),
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    return amostra_service.listar_amostras(
        animal_id=animal_id,
        status_amostra=status_amostra,
        fase_amostra=fase_amostra,
        condicao_armazenamento=condicao_armazenamento,
        destino_amostra=destino_amostra,
        material_biologico=material_biologico,
        termo_busca=termo_busca,
        ordenar_por=ordenar_por,
        skip=skip,
        limit=limit,
    )

@router.get(
    "/contagem",
    responses=RESPOSTAS_CONTAGEM,
    summary="Total de amostras cadastradas",
    description="Retorna a quantidade total de amostras biológicas registradas no acervo do laboratório.",
)
def contar_amostras():
    return {"total": amostra_service.contar_amostras()}


@router.get(
    "/animal/{animal_id}",
    response_model=List[Amostra],
    responses=RESPOSTAS_LISTAR,
    summary="Buscar amostras de um animal",
    description="Retorna todas as amostras biológicas coletadas de um animal específico.",
)
def listar_amostras_por_animal(
    animal_id: str,
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    return amostra_service.listar_amostras(animal_id=animal_id, skip=skip, limit=limit)

@router.get(
    "/{amostra_id}",
    response_model=Amostra,
    responses=RESPOSTAS_OBTER,
    summary="Buscar amostra por ID",
    description="Recupera uma amostra biológica pelo seu identificador único laboratorial.",
)
def obter_amostra(amostra_id: str):
    return amostra_service.obter_amostra(amostra_id)

@router.get(
    "/{amostra_id}/detalhes",
    response_model=AmostraDetails,
    responses=RESPOSTAS_OBTER,
    summary="Buscar detalhes completos da amostra por ID",
    description="Recupera os detalhes completos da amostra, incluindo saneamento de campos não informados, dados do animal de origem e lista dos exames realizados.",
)
def obter_amostra_detalhes(amostra_id: str):
    return amostra_service.obter_amostra_detalhes(amostra_id)

@router.patch(
    "/{amostra_id}",
    response_model=Amostra,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar amostra",
    description="Atualiza os dados de uma amostra existente, mantendo integridade com o animal de origem e re-normalizando matriz biológica.",
)
def atualizar_amostra(
    amostra_id: str,
    amostra_update: AmostraUpdate,
    confirmar_atualizacao_amostra: bool = Query(
        False, description="Confirmação explícita de atualização da amostra"
    ),
    confirmar_novo_animal: bool = Query(
        False, description="Confirma alteração para animal ainda não cadastrado"
    ),
):
    return amostra_service.atualizar_amostra(
        amostra_id=amostra_id,
        dados_atualizacao=amostra_update,
        confirmar_atualizacao_amostra=confirmar_atualizacao_amostra,
        confirmar_novo_animal=confirmar_novo_animal,
    )

@router.delete(
    "/{amostra_id}",
    responses=RESPOSTAS_DELETAR,
    summary="Remover amostra",
    description="Remove uma amostra biológica cadastrada pelo seu identificador único de laboratório.",
)
def deletar_amostra(amostra_id: str):
    amostra_service.deletar_amostra(amostra_id)
    return None