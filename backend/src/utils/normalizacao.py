import re
from datetime import date, datetime
from typing import Any, Optional, Union
from enum import Enum

from src.models.Animal.enums.Sexo import Sexo
from src.models.Animal.enums.StatusVital import StatusVital
from src.models.Animal.enums.FaixaEtaria import FaixaEtaria
from src.models.Animal.enums.UnidadePeso import UnidadePeso
from src.models.Animal.enums.UnidadeIdade import UnidadeIdade
from src.models.Amostra.enums.MaterialBiologico import MaterialBiologico

# Sentinelas e aliases textuais para valores nulos/não informados
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


def normalizar_unidade_peso(v: Any) -> Optional[UnidadePeso]:
    """Normaliza strings ou enums para UnidadePeso (kg, g ou mg)."""
    if v is None or eh_nao_informado(v):
        return None
    if isinstance(v, UnidadePeso):
        return v
    s = str(v).strip().lower()
    if s in {"kg", "quilo", "quilos", "quilograma", "quilogramas", "kilo", "kilos"}:
        return UnidadePeso.KG
    if s in {"g", "gr", "grama", "gramas"}:
        return UnidadePeso.G
    if s in {"mg", "milig", "miligramas", "miligrama"}:
        return UnidadePeso.MG
    return None


def normalizar_unidade_idade(v: Any) -> Optional[UnidadeIdade]:
    """Normaliza strings ou enums para UnidadeIdade (anos, meses, semanas, dias)."""
    if v is None or eh_nao_informado(v):
        return None
    if isinstance(v, UnidadeIdade):
        return v
    s = str(v).strip().lower()
    if s in {"ano", "anos", "a"}:
        return UnidadeIdade.ANOS
    if s in {"mês", "mes", "meses", "m"}:
        return UnidadeIdade.MESES
    if s in {"semana", "semanas", "sem", "s"}:
        return UnidadeIdade.SEMANAS
    if s in {"dia", "dias", "d"}:
        return UnidadeIdade.DIAS
    return None


def decompor_peso(
    peso_bruto: Any = None,
    peso_valor: Optional[float] = None,
    peso_unidade: Optional[Union[UnidadePeso, str]] = None,
) -> tuple[Union[float, str], Optional[float], Optional[UnidadePeso]]:
    """
    Decompõe e normaliza informações de peso retornando a tupla:
    (peso_canonico_kg, peso_valor, peso_unidade)
    
    Aceita:
    - peso_valor e peso_unidade explícitos (ex: 500, 'mg' -> 0.0005 kg; 400, 'g' -> 0.4 kg)
    - peso_bruto como string com unidade (ex: '500mg' -> 0.0005 kg; '400g' -> 0.4 kg, 400.0, UnidadePeso.G)
    - peso_bruto numérico float/int (ex: 4.5 -> 4.5 kg, 4.5, UnidadePeso.KG)
    - Sentinelas ('Não aferido', None, 'NI') -> ('Não aferido', None, None)
    """
    unidade_norm = normalizar_unidade_peso(peso_unidade)

    # 1. Se peso_valor explícito foi fornecido
    if peso_valor is not None and not eh_nao_informado(peso_valor):
        try:
            val_num = float(peso_valor)
            if val_num <= 0:
                raise ValueError("O peso deve ser maior que zero.")
            u = unidade_norm or UnidadePeso.KG
            if u == UnidadePeso.MG:
                peso_kg = round(val_num / 1_000_000.0, 6)
            elif u == UnidadePeso.G:
                peso_kg = round(val_num / 1000.0, 4)
            else:
                peso_kg = val_num
            return peso_kg, val_num, u
        except (ValueError, TypeError) as e:
            if "maior que zero" in str(e):
                raise
            pass

    # 2. Se peso_bruto foi fornecido
    if peso_bruto is None or eh_nao_informado(peso_bruto):
        return "Não aferido", None, None

    if isinstance(peso_bruto, str):
        v_clean = peso_bruto.strip().lower().replace(",", ".")
        if "não aferido" in v_clean or "nao aferido" in v_clean:
            return "Não aferido", None, None

        # Ex: "500mg"
        match_mg = re.match(r"^(\d+(?:\.\d+)?)\s*mg$", v_clean)
        if match_mg:
            val = float(match_mg.group(1))
            return round(val / 1_000_000.0, 6), val, UnidadePeso.MG

        # Ex: "400g"
        match_g = re.match(r"^(\d+(?:\.\d+)?)\s*g$", v_clean)
        if match_g:
            val = float(match_g.group(1))
            return round(val / 1000.0, 4), val, UnidadePeso.G

        # Ex: "2.5kg"
        match_kg = re.match(r"^(\d+(?:\.\d+)?)\s*kg$", v_clean)
        if match_kg:
            val = float(match_kg.group(1))
            return val, val, UnidadePeso.KG

        # String numérica pura
        try:
            val = float(v_clean)
            u = unidade_norm or UnidadePeso.KG
            if u == UnidadePeso.MG:
                peso_kg = round(val / 1_000_000.0, 6)
            elif u == UnidadePeso.G:
                peso_kg = round(val / 1000.0, 4)
            else:
                peso_kg = val
            return peso_kg, val, u
        except ValueError:
            return "Não aferido", None, None

    if isinstance(peso_bruto, (int, float)):
        val = float(peso_bruto)
        u = unidade_norm or UnidadePeso.KG
        if u == UnidadePeso.MG:
            peso_kg = round(val / 1_000_000.0, 6)
        elif u == UnidadePeso.G:
            peso_kg = round(val / 1000.0, 4)
        else:
            peso_kg = val
        return peso_kg, val, u

    return "Não aferido", None, None


def normalizar_peso(v: Any) -> Union[float, str]:
    """
    Sanitiza e converte pesos para float em kg ou para o padrão 'Não aferido'.
    Mantém compatibilidade total com a interface legada.
    """
    peso_kg, _, _ = decompor_peso(peso_bruto=v)
    return peso_kg


def validar_peso(peso: Union[float, str]) -> None:
    """Garante que qualquer peso numérico seja estritamente maior que zero."""
    if isinstance(peso, (int, float)) and peso <= 0:
        raise ValueError("O peso deve ser maior que zero ou marcado como 'Não aferido'.")


def decompor_idade(
    idade_str: Optional[str] = None,
    idade_valor: Optional[float] = None,
    idade_unidade: Optional[Union[UnidadeIdade, str]] = None,
) -> tuple[Optional[str], Optional[float], Optional[UnidadeIdade]]:
    """
    Decompõe e normaliza informações de idade retornando a tupla:
    (idade_formatada, idade_valor, idade_unidade)
    """
    u_norm = normalizar_unidade_idade(idade_unidade)

    # 1. Se valor numérico e unidade explícitos foram passados
    if idade_valor is not None and not eh_nao_informado(idade_valor):
        try:
            val_num = float(idade_valor)
            u = u_norm or UnidadeIdade.ANOS
            val_fmt = int(val_num) if val_num.is_integer() else val_num
            # Ajuste de singular/plural
            rotulo = u.value
            if val_num == 1:
                if u == UnidadeIdade.ANOS:
                    rotulo = "ano"
                elif u == UnidadeIdade.MESES:
                    rotulo = "mês"
                elif u == UnidadeIdade.SEMANAS:
                    rotulo = "semana"
                elif u == UnidadeIdade.DIAS:
                    rotulo = "dia"
            return f"{val_fmt} {rotulo}", val_num, u
        except (ValueError, TypeError):
            pass

    # 2. Se idade textual foi passada
    if not idade_str or eh_nao_informado(idade_str):
        return None, None, None

    idade_clean = str(idade_str).strip()

    # Regex para número + unidade textual
    match = re.match(
        r"^(\d+(?:[\.,]\d+)?)\s*(ano|anos|mês|mes|meses|semana|semanas|dia|dias|a|m|sem|d)$",
        idade_clean.lower(),
    )
    if match:
        val_num = float(match.group(1).replace(",", "."))
        u = normalizar_unidade_idade(match.group(2)) or u_norm or UnidadeIdade.ANOS
        val_fmt = int(val_num) if val_num.is_integer() else val_num
        rotulo = u.value
        if val_num == 1:
            if u == UnidadeIdade.ANOS:
                rotulo = "ano"
            elif u == UnidadeIdade.MESES:
                rotulo = "mês"
            elif u == UnidadeIdade.SEMANAS:
                rotulo = "semana"
            elif u == UnidadeIdade.DIAS:
                rotulo = "dia"
        return f"{val_fmt} {rotulo}", val_num, u

    # Se for apenas número sem unidade textual
    match_num = re.match(r"^(\d+(?:[\.,]\d+)?)$", idade_clean)
    if match_num:
        val_num = float(match_num.group(1).replace(",", "."))
        u = u_norm or UnidadeIdade.ANOS
        val_fmt = int(val_num) if val_num.is_integer() else val_num
        return f"{val_fmt} {u.value}", val_num, u

    # Se for termo categórico (ex: 'Filhote', 'Ninhego', 'Potro')
    return idade_clean, None, None


def deduzir_faixa_etaria(
    idade_str: Optional[str] = None,
    idade_valor: Optional[float] = None,
    idade_unidade: Optional[Union[UnidadeIdade, str]] = None,
) -> Optional[FaixaEtaria]:
    """
    Deduz heurísticamente a faixa etária com base na string de idade ou
    no par valor + unidade.
    
    Exemplos aceitos:
    - '6 meses', '1.5 anos', '3 anos', '10', 'Filhote', 'Ninhego', 'Potro'
    - valor=6, unidade=UnidadeIdade.MESES
    """
    # Se valor numérico e unidade foram informados
    if idade_valor is not None and not eh_nao_informado(idade_valor):
        try:
            val_num = float(idade_valor)
            u = normalizar_unidade_idade(idade_unidade) or UnidadeIdade.ANOS
            if u == UnidadeIdade.DIAS:
                anos = val_num / 365.0
            elif u == UnidadeIdade.SEMANAS:
                anos = val_num / 52.0
            elif u == UnidadeIdade.MESES:
                anos = val_num / 12.0
            else:
                anos = val_num

            if anos < 1.0:
                return FaixaEtaria.FILHOTE
            elif anos < 2.0:
                return FaixaEtaria.JUVENIL
            elif anos < 4.0:
                return FaixaEtaria.SUB_ADULTO
            elif anos < 10.0:
                return FaixaEtaria.ADULTO
            else:
                return FaixaEtaria.SENIL
        except (ValueError, TypeError):
            pass

    if not idade_str:
        return None

    idade_clean = str(idade_str).strip().lower()

    if "filhote" in idade_clean:
        return FaixaEtaria.FILHOTE
    if "ninhego" in idade_clean:
        return FaixaEtaria.NINHEGO
    if "potro" in idade_clean:
        return FaixaEtaria.POTRO
    if "juvenil" in idade_clean:
        return FaixaEtaria.JUVENIL
    if "jovem" in idade_clean:
        return FaixaEtaria.JOVEM
    if "sub" in idade_clean:
        return FaixaEtaria.SUB_ADULTO
    if "adulto" in idade_clean:
        return FaixaEtaria.ADULTO
    if "senil" in idade_clean:
        return FaixaEtaria.SENIL
    if "idoso" in idade_clean:
        return FaixaEtaria.IDOSO

    # Tenta decompor número e unidade da string
    _, val_extraido, u_extraido = decompor_idade(idade_str=idade_clean)
    if val_extraido is not None and u_extraido is not None:
        return deduzir_faixa_etaria(idade_valor=val_extraido, idade_unidade=u_extraido)

    match = re.search(r"(\d+(?:[\.,]\d+)?)", idade_clean)
    if not match:
        return None

    num_val = float(match.group(1).replace(",", "."))

    if any(unit in idade_clean for unit in ["mês", "mes", "meses", "m"]):
        anos = num_val / 12.0
    elif any(unit in idade_clean for unit in ["dia", "dias", "d"]):
        anos = num_val / 365.0
    elif any(unit in idade_clean for unit in ["semana", "semanas", "sem"]):
        anos = num_val / 52.0
    else:
        anos = num_val

    if anos < 1.0:
        return FaixaEtaria.FILHOTE
    elif anos < 2.0:
        return FaixaEtaria.JUVENIL
    elif anos < 4.0:
        return FaixaEtaria.SUB_ADULTO
    elif anos < 10.0:
        return FaixaEtaria.ADULTO
    else:
        return FaixaEtaria.SENIL


def normalizar_sexo(valor: Any) -> Sexo:
    """Normaliza strings ou enums para o Enum Sexo canônico."""
    if isinstance(valor, Sexo):
        return valor
    if valor is None or eh_nao_informado(valor):
        return Sexo.NAO_INFORMADO

    v_clean = str(valor).strip().casefold()

    if v_clean in {"m", "macho", "male", "masculino", "1"}:
        return Sexo.MACHO
    if v_clean in {"f", "femea", "fêmea", "female", "feminino", "2"}:
        return Sexo.FEMEA
    if v_clean in {"i", "indeterminado", "ind", "indet", "?"}:
        return Sexo.INDETERMINADO

    for s in Sexo:
        if s.value.casefold() == v_clean:
            return s

    return Sexo.NAO_INFORMADO


def normalizar_status_vital(valor: Any) -> StatusVital:
    """Normaliza strings ou enums para o Enum StatusVital canônico."""
    if isinstance(valor, StatusVital):
        return valor
    if valor is None or eh_nao_informado(valor):
        return StatusVital.NAO_INFORMADO

    v_clean = str(valor).strip().casefold()

    if v_clean in {"vivo", "v", "alive", "live", "1"}:
        return StatusVital.VIVO
    if v_clean in {"morto", "m", "óbito", "obito", "dead", "2"}:
        return StatusVital.MORTO
    if v_clean in {"eutanasiado", "eutanásia", "eutanasia", "eut", "3"}:
        return StatusVital.EUTANASIADO

    for sv in StatusVital:
        if sv.value.casefold() == v_clean:
            return sv

    return StatusVital.NAO_INFORMADO


def normalizar_material_biologico(valor: Union[MaterialBiologico, str]) -> Union[MaterialBiologico, str]:
    """
    Normaliza strings recebidas de planilhas/formulários para o Enum canônico MaterialBiologico.
    Prioriza termos mais específicos antes de genéricos (ex: 'swab oral e cloacal' antes de 'swab oral').
    """
    if isinstance(valor, MaterialBiologico):
        return valor
    if not valor or eh_nao_informado(valor):
        return MaterialBiologico.OUTRO

    v_limpo = str(valor).strip().casefold()

    termos_ordenados = [
        ("swab oral e cloacal", MaterialBiologico.SWAB_ORAL_CLOACAL),
        ("oral e cloacal", MaterialBiologico.SWAB_ORAL_CLOACAL),
        ("swab traqueal", MaterialBiologico.SWAB_TRAQUEAL),
        ("swab cloacal", MaterialBiologico.SWAB_CLOACAL),
        ("swab ocular", MaterialBiologico.SWAB_OCULAR),
        ("swab retal", MaterialBiologico.SWAB_RETAL),
        ("swab nasal", MaterialBiologico.SWAB_NASAL),
        ("swab oral", MaterialBiologico.SWAB_ORAL),
        ("esfregaço sanguíneo", MaterialBiologico.ESFREGACO_SANGUINEO),
        ("esfregaco sanguineo", MaterialBiologico.ESFREGACO_SANGUINEO),
        ("esfregaço", MaterialBiologico.ESFREGACO_SANGUINEO),
        ("esfregaco", MaterialBiologico.ESFREGACO_SANGUINEO),
        ("pool de tecidos", MaterialBiologico.POOL_TECIDOS),
        ("sangue (edta)", MaterialBiologico.SANGUE_EDTA),
        ("sangue total", MaterialBiologico.SANGUE_TOTAL),
        ("sangue edta", MaterialBiologico.SANGUE_EDTA),
        ("papel filtro", MaterialBiologico.PAPEL_FILTRO),
        ("papel-filtro", MaterialBiologico.PAPEL_FILTRO),
        ("filtro", MaterialBiologico.PAPEL_FILTRO),
        ("edta", MaterialBiologico.SANGUE_EDTA),
        ("sangue", MaterialBiologico.SANGUE),
        ("soro", MaterialBiologico.SORO),
        ("órgãos", MaterialBiologico.ORGAOS),
        ("orgaos", MaterialBiologico.ORGAOS),
        ("órgão", MaterialBiologico.ORGAOS),
        ("orgao", MaterialBiologico.ORGAOS),
        ("tecido", MaterialBiologico.TECIDO),
        ("baço", MaterialBiologico.BACO),
        ("baco", MaterialBiologico.BACO),
        ("fígado", MaterialBiologico.FIGADO),
        ("figado", MaterialBiologico.FIGADO),
        ("pulmão", MaterialBiologico.PULMAO),
        ("pulmao", MaterialBiologico.PULMAO),
        ("rim", MaterialBiologico.RIM),
        ("rins", MaterialBiologico.RIM),
        ("encéfalo", MaterialBiologico.ENCEFALO),
        ("encefalo", MaterialBiologico.ENCEFALO),
        ("cérebro", MaterialBiologico.ENCEFALO),
        ("cerebro", MaterialBiologico.ENCEFALO),
        ("coração", MaterialBiologico.CORACAO),
        ("coracao", MaterialBiologico.CORACAO),
        ("fezes", MaterialBiologico.FEZES),
        ("enema", MaterialBiologico.ENEMA),
        ("líquor", MaterialBiologico.LIQUOR),
        ("liquor", MaterialBiologico.LIQUOR),
        ("lcr", MaterialBiologico.LIQUOR),
        ("ectoparasita", MaterialBiologico.ECTOPARASITA),
        ("pele", MaterialBiologico.PELE),
        ("pelo", MaterialBiologico.PELO),
        ("necrópsia", MaterialBiologico.NECROPSIA),
        ("necropsia", MaterialBiologico.NECROPSIA),
        ("outro", MaterialBiologico.OUTRO),
    ]

    for termo, enum_item in termos_ordenados:
        if termo in v_limpo:
            return enum_item

    for m in MaterialBiologico:
        if m.value.casefold() == v_limpo:
            return m

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


_SIGLAS_UF = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


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

