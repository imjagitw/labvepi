"""
Catálogo centralizado de respostas HTTP dos controllers.

Este módulo concentra:
1. O mapeamento de exceções de domínio/serviço -> status HTTP
   (aplicado automaticamente via ``criar_router`` / ``TratamentoErrosRoute``,
   pelo decorator ``tratar_erros`` ou pelos handlers globais de ``registrar_tratamento_erros``).
2. O catálogo de respostas HTTP possíveis (``RESPOSTAS``) e os conjuntos
   prontos por tipo de operação (``RESPOSTAS_CRIAR``, ``RESPOSTAS_OBTER``, ...),
   usados no parâmetro ``responses=`` das rotas para documentar o OpenAPI/Swagger.

Mapeamento de exceções:
    - NoContentError / SemConteudoError -> 204 No Content
    - ValueError                        -> 400 Bad Request
    - PermissionError                   -> 403 Forbidden
    - KeyError / FileNotFoundError      -> 404 Not Found
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Exceções semânticas
# ---------------------------------------------------------------------------
class NoContentError(Exception):
    """
    Exceção semântica de domínio/serviço para indicar que uma operação
    foi concluída com sucesso mas não deve retornar conteúdo (HTTP 204 No Content).
    """
    pass

SemConteudoError = NoContentError

# ---------------------------------------------------------------------------
# Schema padrão de erro
# ---------------------------------------------------------------------------
class ErroResposta(BaseModel):
    """Corpo padrão retornado pela API em respostas de erro."""
    detail: str

# ---------------------------------------------------------------------------
# Catálogo de respostas HTTP possíveis
# ---------------------------------------------------------------------------
RESPOSTAS: Dict[int, Dict[str, Any]] = {
    status.HTTP_200_OK: {
        "description": "Operação realizada com sucesso.",
    },
    status.HTTP_201_CREATED: {
        "description": "Recurso criado com sucesso.",
    },
    status.HTTP_204_NO_CONTENT: {
        "description": "Operação concluída com sucesso, sem conteúdo no corpo da resposta.",
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": ErroResposta,
        "description": "Requisição inválida: regra de negócio violada, dado duplicado ou confirmação ausente.",
        "content": {"application/json": {"example": {"detail": "Registro com ID 'X' já está cadastrado."}}},
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErroResposta,
        "description": "Ação não permitida.",
        "content": {"application/json": {"example": {"detail": "Ação não permitida para o usuário atual."}}},
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErroResposta,
        "description": "Recurso não encontrado.",
        "content": {"application/json": {"example": {"detail": "Registro com identificador 'X' não encontrado."}}},
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErroResposta,
        "description": "Erro interno inesperado no servidor.",
    },
}

def respostas(*codigos: int) -> Dict[Union[int, str], Dict[str, Any]]:
    """
    Monta o dicionário ``responses`` de uma rota a partir dos códigos HTTP
    informados, sempre incluindo 500 Internal Server Error.

    Exemplo:
        @router.get("/{id}", responses=respostas(404))
    """
    selecionados = {*codigos, status.HTTP_500_INTERNAL_SERVER_ERROR}
    return {codigo: RESPOSTAS[codigo] for codigo in sorted(selecionados)}

# Conjuntos prontos por tipo de operação dos controllers
RESPOSTAS_CRIAR = respostas(
    status.HTTP_201_CREATED,
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
)
RESPOSTAS_LISTAR = respostas(
    status.HTTP_400_BAD_REQUEST
)
RESPOSTAS_BUSCAR = respostas(
    status.HTTP_400_BAD_REQUEST, 
    status.HTTP_404_NOT_FOUND
)
RESPOSTAS_OBTER = respostas(
    status.HTTP_404_NOT_FOUND
)
RESPOSTAS_ATUALIZAR = respostas(
    status.HTTP_400_BAD_REQUEST, 
    status.HTTP_403_FORBIDDEN, 
    status.HTTP_404_NOT_FOUND
)
RESPOSTAS_DELETAR = respostas(
    status.HTTP_204_NO_CONTENT, 
    status.HTTP_403_FORBIDDEN, 
    status.HTTP_404_NOT_FOUND
)
RESPOSTAS_CONTAGEM = respostas()
RESPOSTAS_PROCESSAMENTO = respostas(
    status.HTTP_400_BAD_REQUEST, 
    status.HTTP_404_NOT_FOUND
)

# ---------------------------------------------------------------------------
# Mapeamento exceção -> status HTTP
# ---------------------------------------------------------------------------
EXCECOES_HTTP: Tuple[Tuple[Type[Exception], int], ...] = (
    (KeyError, status.HTTP_404_NOT_FOUND),
    (FileNotFoundError, status.HTTP_404_NOT_FOUND),
    (ValueError, status.HTTP_400_BAD_REQUEST),
    (PermissionError, status.HTTP_403_FORBIDDEN),
)

def _mensagem(exc: Exception) -> str:
    """Extrai a mensagem da exceção (KeyError adiciona aspas em str(), por isso usa args[0])."""
    if isinstance(exc, (KeyError, FileNotFoundError)) and exc.args:
        return str(exc.args[0])
    return str(exc)

def _status_da_excecao(exc: Exception) -> Optional[int]:
    for tipo, codigo in EXCECOES_HTTP:
        if isinstance(exc, tipo):
            return codigo
    return None

def _sem_conteudo() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)

def _converter_excecao(exc: Exception) -> Response:
    """
    Converte uma exceção capturada na resposta HTTP correspondente.
    Exceções não mapeadas são relançadas.
    """
    if isinstance(exc, NoContentError):
        return _sem_conteudo()
    if isinstance(exc, HTTPException):
        if exc.status_code == status.HTTP_204_NO_CONTENT:
            return _sem_conteudo()
        raise exc
    codigo = _status_da_excecao(exc)
    if codigo is None:
        raise exc
    raise HTTPException(status_code=codigo, detail=_mensagem(exc))

_EXCECOES_TRATADAS = (NoContentError, HTTPException) + tuple(tipo for tipo, _ in EXCECOES_HTTP)

# ---------------------------------------------------------------------------
# Route / Router
# ---------------------------------------------------------------------------
class TratamentoErrosRoute(APIRoute):
    """
    APIRoute customizada que intercepta automaticamente exceções de negócio
    da camada de serviços e as converte para as respostas HTTP correspondentes
    (ver ``EXCECOES_HTTP``).
    Além disso, define automaticamente status_code=204 No Content (sem corpo)
    para endpoints com método DELETE, eliminando a necessidade de declarar
    status_code=status.HTTP_204_NO_CONTENT em cada controlador.
    """

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        methods: Optional[Union[Set[str], List[str]]] = None,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        methods_set = set(methods) if methods else set()
        if "DELETE" in methods_set and status_code is None:
            status_code = status.HTTP_204_NO_CONTENT
            kwargs.setdefault("response_class", Response)
        super().__init__(path, endpoint, methods=methods, status_code=status_code, **kwargs)

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                response: Response = await original_route_handler(request)
            except _EXCECOES_TRATADAS as exc:
                return _converter_excecao(exc)

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return _sem_conteudo()
            corpo = getattr(response, "body", None)
            if request.method == "DELETE" and corpo in (None, b"null", b"None", b""):
                return _sem_conteudo()
            return response

        return custom_route_handler

def criar_router(**kwargs: Any) -> APIRouter:
    """
    Cria um APIRouter configurado com a classe TratamentoErrosRoute.
    Elimina a necessidade de blocos try/except repetitivos em cada endpoint.
    """
    kwargs.setdefault("route_class", TratamentoErrosRoute)
    return APIRouter(**kwargs)

# ---------------------------------------------------------------------------
# Decorator opcional
# ---------------------------------------------------------------------------
def _normalizar_resultado(res: Any) -> Any:
    if isinstance(res, Response) and res.status_code == status.HTTP_204_NO_CONTENT:
        return _sem_conteudo()
    return res

def tratar_erros(func: Callable) -> Callable:
    """
    Decorator opcional para funções e endpoints que captura exceções de domínio
    e converte para a resposta HTTP correspondente (ver ``EXCECOES_HTTP``).
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return _normalizar_resultado(await func(*args, **kwargs))
            except _EXCECOES_TRATADAS as exc:
                return _converter_excecao(exc)
        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return _normalizar_resultado(func(*args, **kwargs))
        except _EXCECOES_TRATADAS as exc:
            return _converter_excecao(exc)
    return sync_wrapper

# ---------------------------------------------------------------------------
# Handlers globais
# ---------------------------------------------------------------------------
def registrar_tratamento_erros(app: Any) -> None:
    """
    Registra os manipuladores globais de exceções no aplicativo FastAPI.
    Garante que qualquer exceção de domínio não tratada explicitamente
    seja convertida para o status HTTP adequado (ver ``EXCECOES_HTTP``).
    """
    @app.exception_handler(NoContentError)
    async def no_content_error_handler(request: Request, exc: NoContentError):
        return _sem_conteudo()

    @app.exception_handler(status.HTTP_204_NO_CONTENT)
    async def status_204_handler(request: Request, exc: Any):
        return _sem_conteudo()

    def _handler_para(codigo: int) -> Callable:
        async def handler(request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(status_code=codigo, content={"detail": _mensagem(exc)})
        return handler

    for tipo, codigo in EXCECOES_HTTP:
        app.add_exception_handler(tipo, _handler_para(codigo))

__all__ = [
    # Tratamento de erros
    "TratamentoErrosRoute",
    "criar_router",
    "tratar_erros",
    "registrar_tratamento_erros",
    "NoContentError",
    "SemConteudoError",
    "EXCECOES_HTTP",
    # Catálogo de respostas HTTP
    "ErroResposta",
    "RESPOSTAS",
    "respostas",
    "RESPOSTAS_CRIAR",
    "RESPOSTAS_LISTAR",
    "RESPOSTAS_BUSCAR",
    "RESPOSTAS_OBTER",
    "RESPOSTAS_ATUALIZAR",
    "RESPOSTAS_DELETAR",
    "RESPOSTAS_CONTAGEM",
    "RESPOSTAS_PROCESSAMENTO",
]