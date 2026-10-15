from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status

# Importação da INSTÂNCIA do serviço e dos modelos
from src.services.animal_service import (
    animal_service,
    Animal,
    AnimalCreate,
    AnimalUpdate,
    AnimalDetails,
    Classe,
    Sexo,
    RegimeVida,
    StatusVital,
)

router = APIRouter(prefix="/animal", tags=["Animal"])

@router.post(
    "/",
    response_model=Animal,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo animal",
    description="Cria um novo animal automatizando espécie e classe a partir do catálogo do laboratório.",
)
def criar_animal(
    animal_input: AnimalCreate,
    confirmar_nova_especie: bool = Query(
        False, description="Confirma cadastro de nova espécie caso não esteja no catálogo"
    ),
):
    try:
        return animal_service.criar_animal(
            dados_animal=animal_input,
            confirmar_nova_especie=confirmar_nova_especie,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/",
    response_model=List[Animal],
    summary="Listar animais com filtros",
    description="Retorna a lista de animais cadastrados com suporte a filtros taxonômicos, status e busca.",
)
def listar_animais(
    classe: Optional[Classe] = Query(None, description="Filtrar por classe taxonômica"),
    sexo: Optional[Sexo] = Query(None, description="Filtrar por sexo"),
    regime_vida: Optional[RegimeVida] = Query(None, alias="status", description="Filtrar por regime de vida"),
    status_vital: Optional[StatusVital] = Query(None, description="Filtrar por status vital"),
    termo_busca: Optional[str] = Query(None, description="Busca textual por ID, nome, local, etc."),
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    return animal_service.listar_animais(
        classe=classe,
        sexo=sexo,
        regime_vida=regime_vida,
        status_vital=status_vital,
        termo_busca=termo_busca,
        skip=skip,
        limit=limit,
    )

@router.get(
    "/{animal_id}",
    response_model=Animal,
    summary="Buscar animal por ID",
    description="Recupera um animal cadastrado pelo seu ID único de laboratório.",
)
def obter_animal(animal_id: str):
    try:
        return animal_service.obter_animal(animal_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get(
    "/{animal_id}/detalhes",
    response_model=AnimalDetails,
    summary="Buscar detalhes completos do animal por ID",
    description="Recupera os detalhes completos do animal, incluindo padronização de campos não informados, dados da espécie e lista de amostras associadas.",
)
def obter_animal_detalhes(animal_id: str):
    try:
        return animal_service.obter_animal_detalhes(animal_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{animal_id}",
    response_model=Animal,
    summary="Atualizar animal",
    description="Atualiza dados de um animal existente, re-resolvendo espécie automaticamente se necessário.",
)
def atualizar_animal(
    animal_id: str,
    animal_update: AnimalUpdate,
    confirmar_nova_especie: bool = Query(
        False, description="Confirma cadastro de nova espécie caso não esteja no catálogo"
    ),
):
    try:
        return animal_service.atualizar_animal(
            animal_id=animal_id,
            dados_atualizacao=animal_update,
            confirmar_nova_especie=confirmar_nova_especie,
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete(
    "/{animal_id}",
    summary="Remover animal",
    description="Remove um animal cadastrado pelo seu ID único de laboratório.",
)
def deletar_animal(animal_id: str):
    try:
        animal_service.deletar_animal(animal_id)
        return {"message": "Animal removido com sucesso", "animal_id": animal_id}
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))