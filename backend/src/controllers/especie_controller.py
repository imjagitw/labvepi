from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from src.models.especie import Especie, EspecieCreate
from src.services.especie_service import especie_service

router = APIRouter(prefix="/especies", tags=["Espécies"])

@router.post(
    "/",
    response_model=Especie,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar espécie",
    description="Cadastra uma nova espécie taxonômica no catálogo do laboratório.",
)
def cadastrar_especie(especie_in: EspecieCreate):
    try:
        return especie_service.cadastrar_especie(especie_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=List[Especie],
    summary="Listar espécies",
    description="Retorna todas as espécies cadastradas no acervo taxonômico.",
)
def listar_especies():
    return especie_service.listar_especies()


@router.get(
    "/buscar",
    response_model=Especie,
    summary="Buscar espécie por nome",
    description="Recupera uma espécie pelo nome comum ou nome científico.",
)
def buscar_especie(
    nome_comum: Optional[str] = Query(None, description="Nome comum/popular da espécie"),
    nome_cientifico: Optional[str] = Query(None, description="Nome científico formal"),
):
    if not nome_comum and not nome_cientifico:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe 'nome_comum' ou 'nome_cientifico' para realizar a busca.",
        )

    especie = None
    if nome_cientifico:
        especie = especie_service.buscar_por_nome_cientifico(nome_cientifico)
    if not especie and nome_comum:
        especie = especie_service.buscar_por_nome_comum(nome_comum)

    if not especie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Espécie não encontrada no catálogo.",
        )

    return especie


@router.post(
    "/importar-catalogo",
    summary="Importar tabela CSV de espécies",
    description="Importa uma tabela CSV contendo nomes comuns, científicos e classes recomendadas pelo laboratório.",
)
def importar_catalogo_csv(caminho_arquivo: str = Query(..., description="Caminho do arquivo CSV no servidor")):
    try:
        total = especie_service.importar_tabela_csv(caminho_arquivo)
        return {
            "message": "Catálogo de espécies importado com sucesso",
            "novas_especies": total,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
