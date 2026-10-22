from typing import Optional, Any
from enum import Enum
from datetime import date, datetime

_VALORES_NAO_INFORMADOS = {
    "", "-", "ni", "none", "null", "n/a", "na",
    "não informado", "nao informado", "não identificado", "nao identificado",
}

_VALORES_NAO_AFERIDO = {"não aferido", "nao aferido"}

def eh_nao_informado(valor: Any) -> bool:
    """Verifica se um valor é nulo, vazio ou um sentinela textual de 'Não informado'."""
    if valor is None:
        return True
    if isinstance(valor, bool):
        return False
    if isinstance(valor, Enum):
        valor = valor.value
    if isinstance(valor, str):
        return valor.strip().casefold() in _VALORES_NAO_INFORMADOS
    return False

def normalizar_booleano(valor: Any) -> Optional[bool]:
    """
    Normaliza valores heterogêneos para bool estrito (True/False) ou None.
    Reconhece:
    - Booleanos: True, False
    - Inteiros/Floats: 1 -> True, 0 -> False
    - Strings em pt/en: 'sim', 's', 'true', 'yes', 'y', '1' -> True
                        'nao', 'não', 'n', 'false', 'no', '0' -> False
    - Nulos e sentinelas -> None
    """
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    if isinstance(valor, str):
        v = valor.strip().casefold()
        if v in {"sim", "s", "true", "1", "t", "yes", "y"}:
            return True
        if v in {"nao", "não", "n", "false", "0", "f", "no"}:
            return False
    return None

def normalizar_enum(enum_cls: Any, valor: Any, default: Any = None) -> Any:
    """
    Normaliza entradas heterogêneas (strings, enum members) para o Enum canônico.
    Compara de forma case-insensitive contra o .value e o .name de cada membro.
    Retorna `default` se o valor for nulo/vazio ou sentinela não informado.
    """
    if isinstance(valor, enum_cls) or valor is None:
        return valor
    if eh_nao_informado(valor):
        return default
    v_limpo = str(valor).strip().casefold()
    for item in enum_cls:
        if item.value.casefold() == v_limpo or item.name.casefold() == v_limpo:
            return item
    return valor

def normalizar_data(valor: Any, permitir_none: bool = True) -> Optional[date]:
    """
    Normaliza entradas heterogêneas de datas para datetime.date ou None.
    Suporta:
    - Objetos date e datetime
    - Strings ISO (ex: '2022-01-28')
    - Formatos brasileiros (ex: '28/01/2022', '28-01-2022')
    - Sentinelas ('NI', '-', 'Não informado', '', etc.) -> None se permitir_none=True
    """
    if valor is None:
        if permitir_none:
            return None
        raise ValueError("Data não informada.")

    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor

    if eh_nao_informado(valor):
        if permitir_none:
            return None
        raise ValueError("Data não informada.")

    s = str(valor).strip()
    if s.lower() in _VALORES_NAO_INFORMADOS:
        if permitir_none:
            return None
        raise ValueError("Data não informada.")

    # Tentativa formato ISO
    try:
        return date.fromisoformat(s)
    except ValueError:
        pass

    # Formatos comuns (brasileiro, barras, traços)
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Formato de data inválido: '{valor}'. Use o formato AAAA-MM-DD ou DD/MM/AAAA.")