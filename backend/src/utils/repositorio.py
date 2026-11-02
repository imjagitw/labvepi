from typing import Optional, Any, Union

# Campos de chave primária que nunca devem ser fornecidos pelo usuário em operações de criação ou atualização
_CAMPOS_PROIBIDOS_ENTRADA = ("id", "_id")


def normalizar_chave_busca(texto: Optional[str]) -> str:
    """
    Normaliza strings para indexação e consultas textuais em memória.
    Remove espaços redundantes e converte para minúsculas de forma uniforme.
    """
    if not texto:
        return ""
    return " ".join(str(texto).strip().split()).casefold()


# Alias para compatibilidade com repositórios existentes
_normalizar = normalizar_chave_busca


def extrair_id_numerico(id_val: Any) -> Optional[int]:
    """
    Converte um identificador para int se for puramente numérico.
    Retorna None caso contrário.
    """
    if id_val is None:
        return None
    if isinstance(id_val, int):
        return id_val
    s = str(id_val).strip()
    return int(s) if s.isdigit() else None


def sanitizar_id_filtro(id_val: Union[int, str]) -> Union[int, str]:
    """
    Converte o identificador para int se for dígito numérico, ou mantém str limpa.
    Padroniza consultas MongoDB e chaves em dicionários em memória.
    """
    num = extrair_id_numerico(id_val)
    if num is not None:
        return num
    return str(id_val).strip()


def gerar_proximo_id_mongo(collection: Any, proximo_id_atual: int = 1) -> int:
    """
    Gera a próxima chave primária autoincrementada baseada no maior _id numérico
    registrado no MongoDB ou no ponteiro corrente em memória (max(_id) + 1).
    """
    proximo = proximo_id_atual
    if collection is not None:
        try:
            doc_max = collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
            if doc_max and isinstance(doc_max.get("_id"), (int, float)):
                proximo = max(int(doc_max["_id"]) + 1, proximo)
        except Exception:
            pass
    return proximo


def doc_para_mongo(model: Any) -> dict:
    """
    Serializa um modelo Pydantic para inserção ou atualização no MongoDB,
    garantindo que o campo '_id' preserve tipagem numérica caso seja dígito.
    """
    doc = model.model_dump(mode="json", by_alias=True, exclude_none=True)
    if "_id" not in doc and getattr(model, "id", None) is not None:
        mid = model.id
        num = extrair_id_numerico(mid)
        doc["_id"] = num if num is not None else mid
    return doc


def preparar_doc_mongo(doc: dict, fallback_id_campo: Optional[str] = None) -> dict:
    """
    Ajusta tipos do documento retornado do MongoDB para instanciação segura no Pydantic:
    - Normaliza '_id' numérico quando aplicável.
    - Se especificado fallback_id_campo (ex: 'animal_id', 'amostra_id') e este estiver ausente,
      popula a partir do '_id'.
    """
    d = dict(doc)
    if fallback_id_campo and fallback_id_campo not in d and "_id" in d:
        d[fallback_id_campo] = str(d["_id"])
    if "_id" in d and not isinstance(d["_id"], int):
        num = extrair_id_numerico(d["_id"])
        if num is not None:
            d["_id"] = num
    return d


__all__ = [
    "_CAMPOS_PROIBIDOS_ENTRADA",
    "normalizar_chave_busca",
    "_normalizar",
    "extrair_id_numerico",
    "sanitizar_id_filtro",
    "gerar_proximo_id_mongo",
    "doc_para_mongo",
    "preparar_doc_mongo",
]
