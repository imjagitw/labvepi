import re
from typing import Any, Optional
from .comum import eh_nao_informado, _VALORES_NAO_INFORMADOS

_SIGLAS_UF = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

def normalizar_coordenada(valor: Any, eh_latitude: bool = True) -> Optional[float]:
    """
    Normaliza coordenadas geográficas heterogêneas para float decimal padrão WGS84.
    Suporta:
    - Floats e ints (ex: -5.089)
    - Strings com vírgula (ex: "-5,089")
    - Graus sexagesimais / DMS (ex: "05°05'21\"S", "42°48'35\"W")
    - Sentinelas ('-', 'NI', 'Não informado', etc.) -> None
    Valida limites geográficos ([-90, 90] para latitude, [-180, 180] para longitude).
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        val_f = float(valor)
    else:
        s = str(valor).strip()
        if eh_nao_informado(s) or s.lower() in _VALORES_NAO_INFORMADOS:
            return None

        # Padrão DMS (Graus, Minutos, Segundos) com direção opcional (N, S, E, W, L, O)
        dms_match = re.match(
            r"^([+-]?\d+(?:\.\d+)?)[°º\s]+(?:(\d+(?:\.\d+)?)[\x27′\s]+)?(?:(\d+(?:\.\d+)?)[″\"\s]*)?([NSEWLO])?$",
            s,
            re.IGNORECASE,
        )
        if dms_match:
            deg = float(dms_match.group(1))
            mins = float(dms_match.group(2) or 0)
            secs = float(dms_match.group(3) or 0)
            direction = (dms_match.group(4) or "").upper()
            decimal = abs(deg) + (mins / 60.0) + (secs / 3600.0)
            if deg < 0 or direction in ("S", "W", "O"):
                decimal = -decimal
            val_f = round(decimal, 6)
        else:
            s_clean = s.replace(",", ".").replace(" ", "")
            try:
                val_f = float(s_clean)
            except ValueError:
                raise ValueError(f"Coordenada geográfica inválida: '{valor}'.")

    # Validação de limites
    min_val, max_val = (-90.0, 90.0) if eh_latitude else (-180.0, 180.0)
    nome = "Latitude" if eh_latitude else "Longitude"
    if not (min_val <= val_f <= max_val):
        raise ValueError(f"{nome} fora do intervalo válido [{min_val}, {max_val}]: {val_f}")

    return val_f

def decompor_localidade(
    local_origem: Any = None,
    municipio: Any = None,
    uf: Any = None,
    localidade_detalhe: Any = None,
) -> tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Decompõe e estrutura informações de localidade e origem do animal.
    Retorna tupla: (municipio, uf, localidade_detalhe, local_origem_composto)
    """
    mun = str(municipio).strip() if (municipio and not eh_nao_informado(municipio)) else None
    sigla_uf = str(uf).strip().upper() if (uf and not eh_nao_informado(uf)) else None
    detalhe = str(localidade_detalhe).strip() if (localidade_detalhe and not eh_nao_informado(localidade_detalhe)) else None

    if (not mun or not sigla_uf) and local_origem and not eh_nao_informado(local_origem):
        loc = str(local_origem).strip()
        # Caso: "Fazenda Santa Luzia, Teresina/PI" ou "Bairro Centro, Teresina - PI"
        m_det = re.match(r"^(.*?),\s*(.*?)[/-]\s*([a-zA-Z]{2})$", loc)
        if m_det:
            detalhe = detalhe or m_det.group(1).strip()
            mun = mun or m_det.group(2).strip()
            cand_uf = m_det.group(3).strip().upper()
            if cand_uf in _SIGLAS_UF:
                sigla_uf = sigla_uf or cand_uf
        else:
            # Caso: "Teresina/PI" ou "Teresina - PI"
            m_uf = re.match(r"^(.*?)[/-]\s*([a-zA-Z]{2})$", loc)
            if m_uf:
                cand_uf = m_uf.group(2).strip().upper()
                if cand_uf in _SIGLAS_UF:
                    mun = mun or m_uf.group(1).strip()
                    sigla_uf = sigla_uf or cand_uf
                else:
                    mun = mun or loc
            else:
                mun = mun or loc

    # Composição do local_origem canônico
    partes = []
    if mun and sigla_uf:
        partes.append(f"{mun}/{sigla_uf}")
    elif mun:
        partes.append(mun)
    if detalhe:
        partes.insert(0, detalhe)

    local_origem_composto = ", ".join(partes) if partes else (str(local_origem).strip() if (local_origem and not eh_nao_informado(local_origem)) else "Não informado")

    return mun, sigla_uf, detalhe, local_origem_composto