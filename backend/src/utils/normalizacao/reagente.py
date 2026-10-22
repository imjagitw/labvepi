from datetime import date
from typing import Any, Optional, Union, Dict, List
from src.models.Reagente import UnidadeMedida, EtapaReagente
from .comum import eh_nao_informado, normalizar_enum

# Fatores para conversão dimensional para unidades base:
# Volume -> base 'ml'
# Massa -> base 'g'
# Unidade -> base 'un'
FATORES_CONVERSAO: Dict[str, tuple[str, float, str]] = {
    # Volume (base: ml)
    "ml": ("volume", 1.0, "ml"),
    "l": ("volume", 1000.0, "ml"),
    "µl": ("volume", 0.001, "ml"),
    "ul": ("volume", 0.001, "ml"),
    # Massa (base: g)
    "g": ("massa", 1.0, "g"),
    "mg": ("massa", 0.001, "g"),
    "kg": ("massa", 1000.0, "g"),
    # Unidade (base: un)
    "un": ("unidade", 1.0, "un"),
}

# Aliases aceitos na entrada da API -> nome canônico dos campos no model Reagente
_ALIASES_REAGENTE: Dict[str, str] = {
    "codigo": "reagente_codigo",
    "id_reagente": "reagente_id",
    "nome": "reagente_nome",
    "lote": "numero_lote",
    "fabricante": "marca",
    "validade": "data_validade",
    "quantidade": "quantidade_unidade",
    "unidades": "quantidade_unidade",
    "volume": "quantidade_volume",
    "massa": "quantidade_volume",
    "unidade": "unidade_medida",
    "etapa": "reagente_etapa",
    "local": "reagente_local_armazenamento",
    "local_armazenamento": "reagente_local_armazenamento",
    "armazenamento": "reagente_local_armazenamento",
    "observacoes": "reagente_observacoes",
    "observacao": "reagente_observacoes",
}

# Aliases aceitos na entrada da API -> nome canônico dos campos no model EstoqueReagente
_ALIASES_ESTOQUE: Dict[str, str] = {
    "nome": "reagente_nome",
    "codigo": "reagente_codigo",
    "lotes_reagente": "lotes",
    "itens": "lotes",
}

def normalizar_chaves_reagente(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Converte aliases aceitos na entrada para os nomes canônicos do domínio Reagente."""
    normalizado: Dict[str, Any] = {}
    for chave, valor in payload.items():
        if chave == "_id":
            if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
                canonica = "id"
                valor = int(valor)
            else:
                canonica = "reagente_id"
        else:
            canonica = _ALIASES_REAGENTE.get(chave, chave)

        if canonica in normalizado and chave != canonica:
            continue
        normalizado[canonica] = valor
    return normalizado

def normalizar_chaves_estoque(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Converte aliases aceitos na entrada para os nomes canônicos do domínio EstoqueReagente."""
    normalizado: Dict[str, Any] = {}
    for chave, valor in payload.items():
        if chave == "_id":
            if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
                canonica = "id"
                valor = int(valor)
            else:
                canonica = chave
        else:
            canonica = _ALIASES_ESTOQUE.get(chave, chave)

        if canonica in normalizado and chave != canonica:
            continue
        normalizado[canonica] = valor
    return normalizado

def normalizar_unidade_medida(valor: Any, default: Optional[UnidadeMedida] = UnidadeMedida.ML) -> Optional[UnidadeMedida]:
    """Normaliza variações textuais para o Enum canônico UnidadeMedida."""
    if valor is None or eh_nao_informado(valor):
        return default
    if isinstance(valor, UnidadeMedida):
        return valor

    s = str(valor).strip().lower()
    mapa = {
        "ml": UnidadeMedida.ML,
        "mililitro": UnidadeMedida.ML,
        "mililitros": UnidadeMedida.ML,
        "l": UnidadeMedida.L,
        "litro": UnidadeMedida.L,
        "litros": UnidadeMedida.L,
        "µl": UnidadeMedida.UL,
        "ul": UnidadeMedida.UL,
        "microlitro": UnidadeMedida.UL,
        "microlitros": UnidadeMedida.UL,
        "g": UnidadeMedida.G,
        "gr": UnidadeMedida.G,
        "grama": UnidadeMedida.G,
        "gramas": UnidadeMedida.G,
        "mg": UnidadeMedida.MG,
        "miligrama": UnidadeMedida.MG,
        "miligramas": UnidadeMedida.MG,
        "kg": UnidadeMedida.KG,
        "quilo": UnidadeMedida.KG,
        "quilos": UnidadeMedida.KG,
        "quilograma": UnidadeMedida.KG,
        "quilogramas": UnidadeMedida.KG,
        "un": UnidadeMedida.UNIDADE,
        "unidade": UnidadeMedida.UNIDADE,
        "unidades": UnidadeMedida.UNIDADE,
        "frasco": UnidadeMedida.UNIDADE,
        "frascos": UnidadeMedida.UNIDADE,
    }
    if s in mapa:
        return mapa[s]

    return normalizar_enum(UnidadeMedida, valor, default=default)

def normalizar_etapa_reagente(valor: Any, default: Optional[EtapaReagente] = None) -> Optional[EtapaReagente]:
    """Normaliza variações textuais para o Enum canônico EtapaReagente."""
    if valor is None or eh_nao_informado(valor):
        return default
    if isinstance(valor, EtapaReagente):
        return valor

    s = str(valor).strip().lower()
    if any(k in s for k in ["extra", "ext"]):
        return EtapaReagente.EXTRAÇÃO
    if any(k in s for k in ["pcr", "qpcr", "rt-pcr"]):
        return EtapaReagente.PCR
    if any(k in s for k in ["eletro", "gel", "agarose"]):
        return EtapaReagente.ELETRO

    return normalizar_enum(EtapaReagente, valor, default=default)

def normalizar_quantidade_unidade(valor: Any, default: int = 1) -> int:
    """Valida e normaliza a quantidade de unidades de reagente (deve ser >= 1)."""
    if valor is None or eh_nao_informado(valor):
        return default
    try:
        qtd = int(valor)
        if qtd < 1:
            raise ValueError("A quantidade de unidades deve ser maior ou igual a 1.")
        return qtd
    except (ValueError, TypeError) as e:
        if "maior ou igual a 1" in str(e):
            raise
        raise ValueError("Quantidade de unidades inválida.")

def normalizar_quantidade_volume(valor: Any) -> Optional[float]:
    """Valida e normaliza a quantidade de volume/massa (deve ser > 0 ou None se não informado)."""
    if valor is None or eh_nao_informado(valor):
        return None
    try:
        vol = float(valor)
        if vol <= 0:
            raise ValueError("A quantidade de volume/massa deve ser maior que zero.")
        return vol
    except (ValueError, TypeError) as e:
        if "maior que zero" in str(e):
            raise
        raise ValueError("Quantidade de volume/massa inválida.")

def validar_lotes_unicos(lotes: List[Any]) -> None:
    """Valida se não há números de lote duplicados para o mesmo reagente."""
    numeros_lotes = []
    for lote in lotes:
        num = lote.get("numero_lote") if isinstance(lote, dict) else getattr(lote, "numero_lote", None)
        if num:
            numeros_lotes.append(str(num).strip().casefold())
    if len(numeros_lotes) != len(set(numeros_lotes)):
        raise ValueError("Não pode haver números de lote repetidos para o mesmo reagente.")

def calcular_vencimento(lote_ou_data: Union[Any, date, str]) -> tuple[bool, int]:
    """
    Calcula os indicadores de vencimento para um lote de reagente ou data:
    Retorna (esta_vencido: bool, dias_para_vencer: int).
    """
    if isinstance(lote_ou_data, date):
        dt_validade = lote_ou_data
    elif hasattr(lote_ou_data, "data_validade"):
        dt_validade = lote_ou_data.data_validade
    elif isinstance(lote_ou_data, str):
        dt_validade = date.fromisoformat(lote_ou_data)
    else:
        raise ValueError("O parâmetro deve ser uma instância de Reagente ou um objeto date/str.")

    hoje = date.today()
    esta_vencido = dt_validade < hoje
    dias_para_vencer = (dt_validade - hoje).days
    return esta_vencido, dias_para_vencer

def calcular_metricas_estoque(
    lotes: List[Any],
) -> tuple[int, Optional[float], Dict[str, float], Dict[str, float], str]:
    """
    Consolida as métricas dimensionais de uma lista de lotes físicos:
    - Valida unicidade de lotes;
    - Calcula indicadores de vencimento para cada lote;
    - Agrega unidades e volumes segregados por unidade e convertidos para unidades base;
    - Determina o volume principal consolidado e o resumo textual.
    
    Retorna tupla:
    (quantidade_total_unidades, quantidade_total_volume, totais_por_unidade, totais_convertidos_base, resumo_estoque)
    """
    validar_lotes_unicos(lotes)

    qtd_unidades = 0
    totais_unidade: Dict[str, float] = {}
    totais_base: Dict[str, float] = {}

    for lote in lotes:
        is_dict = isinstance(lote, dict)
        raw_qtd = lote.get("quantidade_unidade", 1) if is_dict else getattr(lote, "quantidade_unidade", 1)
        qtd_un = normalizar_quantidade_unidade(raw_qtd)
        qtd_unidades += qtd_un

        # Enriquecimento com indicadores de vencimento
        dt_val = lote.get("data_validade") if is_dict else getattr(lote, "data_validade", None)
        if dt_val:
            vencido, dias = calcular_vencimento(dt_val)
            if is_dict:
                lote["esta_vencido"] = vencido
                lote["dias_para_vencer"] = dias
            else:
                setattr(lote, "esta_vencido", vencido)
                setattr(lote, "dias_para_vencer", dias)

        u_raw = lote.get("unidade_medida") if is_dict else getattr(lote, "unidade_medida", "ml")
        unidade_str = (u_raw.value if hasattr(u_raw, "value") else str(u_raw or "ml")).strip()

        vol_unitario = lote.get("quantidade_volume") if is_dict else getattr(lote, "quantidade_volume", None)
        vol_total_lote = (
            round(vol_unitario * qtd_un, 4)
            if vol_unitario is not None
            else float(qtd_un)
        )

        totais_unidade[unidade_str] = round(totais_unidade.get(unidade_str, 0.0) + vol_total_lote, 4)

        if vol_unitario is not None:
            unidade_lower = unidade_str.lower()
            if unidade_lower in FATORES_CONVERSAO:
                _, fator, base = FATORES_CONVERSAO[unidade_lower]
                convertido = round(vol_total_lote * fator, 4)
                totais_base[base] = round(totais_base.get(base, 0.0) + convertido, 4)
            else:
                totais_base[unidade_str] = round(totais_base.get(unidade_str, 0.0) + vol_total_lote, 4)

    # Determina o volume consolidado principal
    if not totais_base:
        qtd_volume = float(sum(
            ((l.get("quantidade_volume") if isinstance(l, dict) else getattr(l, "quantidade_volume", None)) or 0.0)
            * (l.get("quantidade_unidade", 1) if isinstance(l, dict) else getattr(l, "quantidade_unidade", 1))
            for l in lotes
        ))
    elif "ml" in totais_base:
        qtd_volume = totais_base["ml"]
    elif "g" in totais_base:
        qtd_volume = totais_base["g"]
    elif len(totais_base) == 1:
        qtd_volume = next(iter(totais_base.values()))
    else:
        qtd_volume = sum(totais_base.values())

    if qtd_volume is not None:
        qtd_volume = round(qtd_volume, 4)

    # Formata resumo legível
    partes_resumo = [f"{valor:g} {base}" for base, valor in totais_base.items()]
    resumo = ", ".join(partes_resumo) if partes_resumo else f"{qtd_unidades} un"

    return qtd_unidades, qtd_volume, totais_unidade, totais_base, resumo
