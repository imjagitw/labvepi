from datetime import date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
# Importação centralizada através da camada de serviço (não acessa repository e model diretamente)
from src.services.exame_service import (
    exame_service,
    Exame,
    ExameCreate,
    ExameUpdate,
    ExameDetails,
    TipoExame,
    ResultadoExame,
    TesteLaboratorial,
)

router = APIRouter(prefix="/exame", tags=["Exame"])

@router.post(
    "/",
    response_model=Exame,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar um novo exame laboratorial",
    description="Cadastra um novo exame no acervo laboratorial, validando campos obrigatórios, integridade com a amostra biológica e normalizando resultados heurísticos.",
)
def criar_exame(
    exame_input: ExameCreate,
    confirmar_novo_exame: bool = Query(
        False, description="Confirmação explícita de cadastro de novo exame"
    ),
    confirmar_nova_amostra: bool = Query(
        False, description="Confirma vínculo a amostra ainda não registrada no acervo do laboratório"
    ),
):
    try:
        return exame_service.criar_exame(
            dados_exame=exame_input,
            confirmar_novo_exame=confirmar_novo_exame,
            confirmar_nova_amostra=confirmar_nova_amostra,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/",
    response_model=List[Exame],
    summary="Listar exames com filtros laboratoriais",
    description="Retorna a lista de exames cadastrados com suporte a filtros cruzados por amostra, patógeno/tipo, resultado, teste laboratorial, data, responsável, busca textual e paginação.",
)
def listar_exames(
    amostra_id: Optional[str] = Query(None, description="Filtrar por ID da amostra vinculada"),
    tipo_exame: Optional[TipoExame] = Query(None, description="Filtrar por tipo de exame / patógeno investigado"),
    resultado: Optional[ResultadoExame] = Query(None, description="Filtrar por resultado do ensaio"),
    teste_laboratorial: Optional[TesteLaboratorial] = Query(None, description="Filtrar por teste laboratorial / metodologia"),
    data_realizacao: Optional[date] = Query(None, description="Filtrar por data de realização (AAAA-MM-DD)"),
    responsavel_exame: Optional[str] = Query(None, description="Filtrar por responsável pelo exame"),
    termo_busca: Optional[str] = Query(None, description="Busca textual por código do exame, amostra, responsável, protocolo, kit, etc."),
    ordenar_por: str = Query("id", description="Critério de ordenação ('id' ou 'data')"),
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    try:
        return exame_service.listar_exames(
            amostra_id=amostra_id,
            tipo_exame=tipo_exame,
            resultado=resultado,
            teste_laboratorial=teste_laboratorial,
            data_realizacao=data_realizacao,
            responsavel_exame=responsavel_exame,
            termo_busca=termo_busca,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/contagem",
    summary="Total de exames cadastrados",
    description="Retorna a quantidade total de exames laboratoriais registrados no acervo.",
)
def contar_exames():
    try:
        return {"total": exame_service.contar_exames()}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/amostra/{amostra_id}",
    response_model=List[Exame],
    summary="Buscar exames de uma amostra",
    description="Retorna todos os exames laboratoriais realizados para uma amostra biológica específica.",
)
def listar_exames_por_amostra(
    amostra_id: str,
    skip: int = Query(0, ge=0, description="Registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
):
    try:
        return exame_service.listar_exames(amostra_id=amostra_id, skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/{identificador}",
    response_model=Exame,
    summary="Buscar exame por ID ou código",
    description="Recupera um exame laboratorial pelo identificador sequencial numérico ou pelo código alfanumérico (exame_id).",
)
def obter_exame(identificador: str):
    try:
        return exame_service.obter_exame(identificador)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/{identificador}/detalhes",
    response_model=ExameDetails,
    summary="Buscar detalhes completos do exame",
    description="Recupera os detalhes completos do exame com schema ExameDetails, aplicando saneamento de valores não informados e sincronização de campos.",
)
def obter_exame_detalhes(identificador: str):
    try:
        return exame_service.obter_exame_detalhes(identificador)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.patch(
    "/{identificador}",
    response_model=Exame,
    summary="Atualizar exame",
    description="Atualiza dados de um exame existente, validando integridade com a amostra e re-normalizando campos.",
)
@router.put(
    "/{identificador}",
    response_model=Exame,
    summary="Atualizar exame (completo)",
    description="Atualiza os dados de um exame existente no laboratório.",
)
def atualizar_exame(
    identificador: str,
    exame_update: ExameUpdate,
    confirmar_atualizacao_exame: bool = Query(
        False, description="Confirmação explícita de atualização do exame"
    ),
    confirmar_nova_amostra: bool = Query(
        False, description="Confirma alteração para amostra ainda não cadastrada"
    ),
):
    try:
        return exame_service.atualizar_exame(
            identificador=identificador,
            dados_atualizacao=exame_update,
            confirmar_atualizacao_exame=confirmar_atualizacao_exame,
            confirmar_nova_amostra=confirmar_nova_amostra,
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.delete(
    "/{identificador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover exame",
    description="Remove um exame laboratorial cadastrado pelo seu identificador único.",
)
def deletar_exame(identificador: str):
    try:
        exame_service.deletar_exame(identificador)
        return None
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))