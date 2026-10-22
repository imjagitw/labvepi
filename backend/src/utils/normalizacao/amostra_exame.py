from typing import Any, Optional, Union
from enum import Enum
from src.models.Amostra.enums.MaterialBiologico import MaterialBiologico
from src.models.Exame import (
    ResultadoExame, TipoExame, TesteLaboratorial
)
from .comum import eh_nao_informado, normalizar_enum

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

def normalizar_resultado_exame(valor: Any, default: Optional[ResultadoExame] = None) -> Optional[ResultadoExame]:
    """
    Normalização heurística de resultados de ensaios laboratoriais para o Enum ResultadoExame:
    - Negativo: 'não reagente', 'negativo', 'indetectável', 'não detectado'
    - Positivo: 'reagente', 'positivo', 'detectável', 'detectado', '+'
    - Inconclusivo: 'inconclusivo', 'inespecífico', 'repetir', 'indeterminado', 'duvidoso'
    - Aguardando Resultado: 'aguardando', 'em andamento', 'pendente'
    - Não Realizado: 'não realizado', 'não feito', 'não testado', 'nr', ou sentinelas não informados
    """
    if valor is None:
        return default
    if isinstance(valor, ResultadoExame):
        return valor
    if eh_nao_informado(valor):
        return default or ResultadoExame.NAO_REALIZADO

    if isinstance(valor, Enum):
        valor = valor.value

    s = str(valor).strip().casefold()
    if s in {"nr", "não realizado", "nao realizado", "não testado", "nao testado", "não feito", "nao feito"}:
        return ResultadoExame.NAO_REALIZADO

    if any(k in s for k in ["não reagente", "nao reagente", "negativ", "indetect"]):
        return ResultadoExame.NEGATIVO
    if any(k in s for k in ["reagente", "positiv", "detect"]) or s == "+":
        return ResultadoExame.POSITIVO
    if any(k in s for k in ["inconclusiv", "inespec", "repetir", "indetermin", "duvidos"]):
        return ResultadoExame.INCONCLUSIVO
    if any(k in s for k in ["aguard", "andamento", "pendent"]):
        return ResultadoExame.AGUARDANDO

    res = normalizar_enum(ResultadoExame, valor, default=default)
    return res if isinstance(res, ResultadoExame) else default

def normalizar_tipo_exame(valor: Any, default: Optional[TipoExame] = None) -> Optional[TipoExame]:
    """Normaliza variações textuais de patógenos e painéis para o Enum canônico TipoExame."""
    if valor is None:
        return default
    if isinstance(valor, TipoExame):
        return valor
    if eh_nao_informado(valor):
        return default

    res = normalizar_enum(TipoExame, valor, default=None)
    if isinstance(res, TipoExame):
        return res

    if isinstance(valor, Enum):
        valor = valor.value

    s = str(valor).strip().casefold()
    if "covid" in s or "sars-cov" in s:
        if "ret" in s:
            return TipoExame.COVID_RETAL
        return TipoExame.COVID_ORAL
    if "amarela" in s:
        return TipoExame.FEBRE_AMARELA
    if "nilo" in s:
        return TipoExame.FEBRE_DO_NILO
    if "orthoflav" in s:
        return TipoExame.ORTHOFLAVIRIDAE
    if "flavi" in s:
        return TipoExame.FLAVIVIRUS
    if "herpes" in s:
        if "viridae" in s:
            return TipoExame.HERPESVIRIDAE
        return TipoExame.HERPESVIRUS
    if "plasmod" in s or "haemoproteus" in s or "hemoparasita" in s:
        return TipoExame.PLASMODIUM_HAEMOPROTEUS
    if "tripano" in s or "trypano" in s:
        return TipoExame.TRIPANOSTOMATIDAE
    if "resistencia" in s or "resistência" in s:
        return TipoExame.RESISTENCIA_BACTERIANA
    if "mycoplasma" in s or "micoplasma" in s:
        return TipoExame.MYCOPLASMA
    if "chlamydia" in s or "clamidia" in s:
        return TipoExame.CHLAMYDIA
    if "sarcocyst" in s:
        return TipoExame.SARCOCYSTIDAE
    if "hepatozoon" in s:
        return TipoExame.HEPATOZOON
    if "raiva" in s or "rabies" in s:
        return TipoExame.RAIVA
    if "aimes" in s:
        return TipoExame.AIMES
    return default or TipoExame.OUTRO

def normalizar_teste_laboratorial(
    valor: Any,
    default: Optional[TesteLaboratorial] = None,
) -> Optional[TesteLaboratorial]:
    """Normaliza metodologias e técnicas analíticas para o Enum canônico TesteLaboratorial."""
    if valor is None:
        return default
    if isinstance(valor, TesteLaboratorial):
        return valor
    if eh_nao_informado(valor):
        return default

    res = normalizar_enum(TesteLaboratorial, valor, default=None)
    if isinstance(res, TesteLaboratorial):
        return res

    if isinstance(valor, Enum):
        valor = valor.value

    s = str(valor).strip().casefold()
    if "pcr" in s or "molecular" in s or "rt-pcr" in s or "qpcr" in s:
        return TesteLaboratorial.PCR
    if "sorol" in s or "elisa" in s or "anticorpo" in s:
        return TesteLaboratorial.SOROLOGICO
    if "copro" in s or "fezes" in s:
        return TesteLaboratorial.COPROPARASITOLOGICO
    if "lamina" in s or "lâmina" in s or "esfregaço" in s or "esfregaco" in s or "gota espessa" in s:
        return TesteLaboratorial.HEMOPARASITO_EM_LAMINA
    return default or TesteLaboratorial.OUTRO