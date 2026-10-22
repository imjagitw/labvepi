import re
from typing import Any, Optional, Union
from src.models.Animal import (
    Sexo, StatusVital, FaixaEtaria, UnidadePeso, UnidadeIdade
)
from .comum import eh_nao_informado

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