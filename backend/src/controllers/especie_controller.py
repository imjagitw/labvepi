from typing import Optional, List, Union
from fastapi import Query, status
from src.controllers.response_controller import (
    criar_router,
    RESPOSTAS_CRIAR,
    RESPOSTAS_BUSCAR,
    RESPOSTAS_OBTER,
    RESPOSTAS_ATUALIZAR,
    RESPOSTAS_DELETAR,
    RESPOSTAS_PROCESSAMENTO,
)
from src.services.especie_service import (
    especie_service,
    Especie,
    EspecieCreate,
    EspecieUpdate,
    EspecieDetails,
)

router = criar_router(prefix="/especie", tags=["Espécie"])

@router.post(
    "/cadastro",
    response_model=Especie,
    status_code=status.HTTP_201_CREATED,
    responses=RESPOSTAS_CRIAR,
    summary="Cadastrar espécie",
    description="Cadastra uma nova espécie taxonômica no catálogo do laboratório.",
)
def cadastrar_especie(especie_in: EspecieCreate):
    return especie_service.cadastrar_especie(especie_in)

@router.get(
    "/",
    response_model=List[Especie],
    responses=RESPOSTAS_BUSCAR,
    summary="Listar ou filtrar espécies",
    description="Retorna todas as espécies ou aplica filtros cruzados por nome e classe.",
)
def listar_ou_buscar_especies(
    nome_comum: Optional[str] = Query(None, description="Filtrar por nome comum/popular"),
    nome_cientifico: Optional[str] = Query(None, description="Filtrar por nome científico formal"),
    classe: Optional[str] = Query(None, description="Filtrar por classe taxonômica"),
):
    resultados = especie_service.filtrar_especies(
        nome_comum=nome_comum,
        nome_cientifico=nome_cientifico,
        classe=classe,
    )
    if not resultados and any([nome_comum, nome_cientifico, classe]):
        raise KeyError("Nenhuma espécie encontrada com os filtros informados.")

    return resultados

@router.get(
    "/{id}",
    response_model=EspecieDetails,
    responses=RESPOSTAS_OBTER,
    summary="Obter detalhes da espécie e animais associados",
    description="Retorna os dados da espécie mais a contagem e listagem de animais relacionados.",
)
def obter_especie_detalhes(id: Union[int, str]):
    return especie_service.obter_especie_detalhes(id)

@router.put(
    "/{id}",
    response_model=Especie,
    responses=RESPOSTAS_ATUALIZAR,
    summary="Atualizar espécie",
    description="Atualiza os dados taxonômicos repassando a validação de regras de negócio ao Service.",
)
def atualizar_especie(id: Union[int, str], especie_in: EspecieUpdate):
    return especie_service.atualizar_especie(id, especie_in)

@router.delete(
    "/{id}",
    responses=RESPOSTAS_DELETAR,
    summary="Deletar espécie",
    description="Remove a espécie do acervo via Service.",
)
def deletar_especie(id: Union[int, str]):
    especie_service.deletar_especie(id)
    return None

@router.post(
    "/importar-catalogo",
    responses=RESPOSTAS_PROCESSAMENTO,
    summary="Importar tabela CSV de espécies",
    description="Delega a ingestão e formatação do CSV para o fluxo de serviço.",
)
def importar_catalogo_csv(caminho_arquivo: str = Query(..., description="Caminho do arquivo CSV no servidor")):
    total = especie_service.importar_tabela_csv(caminho_arquivo)
    return {
        "message": "Catálogo de espécies importado com sucesso",
        "novas_especies": total,
    }