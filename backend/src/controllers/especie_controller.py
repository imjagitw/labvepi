from typing import Optional, List, Union
from fastapi import APIRouter, HTTPException, Query, status
from src.services.especie_service import especie_service
from src.models.Especie import Especie, EspecieCreate, EspecieUpdate, EspecieDetails

router = APIRouter(prefix="/especies", tags=["Espécies"])

@router.post(
    "/cadastro",
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
        classe=classe
    )
    
    if not resultados and any([nome_comum, nome_cientifico, classe]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma espécie encontrada com os filtros informados."
        )

    return resultados

@router.get(
    "/{id}",
    response_model=EspecieDetails,
    summary="Obter detalhes da espécie e animais associados",
    description="Retorna os dados da espécie mais a contagem e listagem de animais relacionados.",
)
def obter_especie_detalhes(id: Union[int, str]):
    try:
        return especie_service.obter_especie_detalhes(id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put(
    "/{id}",
    response_model=Especie,
    summary="Atualizar espécie",
    description="Atualiza os dados taxonômicos repassando a validação de regras de negócio ao Service.",
)
def atualizar_especie(id: Union[int, str], especie_in: EspecieUpdate):
    try:
        return especie_service.atualizar_especie(id, especie_in)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete(
    "/{id}",
    summary="Deletar espécie",
    description="Remove a espécie do acervo via Service.",
)
def deletar_especie(id: Union[int, str]):
    try:
        especie_service.deletar_especie(id)
        return {"message": "Espécie removida com sucesso", "id": id}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post(
    "/importar-catalogo",
    summary="Importar tabela CSV de espécies",
    description="Delega a ingestão e formatação do CSV para o fluxo de serviço.",
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