import unicodedata
from datetime import datetime
from typing import Optional, Union, Dict, Any
from src.models.Usuario.enums.Perfil import Perfil
from .comum import eh_nao_informado

# Aliases de compatibilidade de API (conforme definidos em UsuarioCreate/UsuarioUpdate)
_ALIASES_USUARIO: Dict[str, str] = {
    "usuario": "username",
    "nome": "name",
    "senha": "password",
}

# Mapeamento de termos legados, sinonímias e variações para o enum canônico Perfil
_MAPA_PERFIL_LEGADO: Dict[str, Perfil] = {
    "professor": Perfil.DOCENTE,
    "prof": Perfil.DOCENTE,
    "doscente": Perfil.DOCENTE,
    "docente": Perfil.DOCENTE,
    "pos_docente": Perfil.DOCENTE,
    "pos-docente": Perfil.DOCENTE,
    "mestrando": Perfil.POS_GRADUANDO,
    "doutorando": Perfil.POS_GRADUANDO,
    "pos_graduacao": Perfil.POS_GRADUANDO,
    "pos-graduacao": Perfil.POS_GRADUANDO,
    "pos_graduando": Perfil.POS_GRADUANDO,
    "pos-graduando": Perfil.POS_GRADUANDO,
    "mestrado": Perfil.POS_GRADUANDO,
    "doutorado": Perfil.POS_GRADUANDO,
    "bolsista_pibiti": Perfil.BOLSISTA_PIBITI,
    "bolsista_pibit": Perfil.BOLSISTA_PIBITI,
    "pibiti": Perfil.BOLSISTA_PIBITI,
    "pibit": Perfil.BOLSISTA_PIBITI,
    "bolsista_pibic": Perfil.BOLSISTA_PIBIC,
    "pibic": Perfil.BOLSISTA_PIBIC,
    "bolsista_externo": Perfil.BOLSISTA_EXTERNO,
    "externo": Perfil.BOLSISTA_EXTERNO,
}

def normalizar_perfil(perfil: Union[Perfil, str]) -> Perfil:
    """
    Sanitiza strings recebidas e mapeia termos legados e variações para o Enum Perfil canônico.
    Remove acentos, espaços e hifens para uma correspondência resiliente.
    """
    if isinstance(perfil, Perfil):
        return perfil
    if eh_nao_informado(perfil):
        raise ValueError("O perfil do usuário é obrigatório.")

    # Remove acentuação e padroniza separadores
    s = str(perfil).strip().casefold()
    s_sem_acento = (
        unicodedata.normalize("NFKD", s)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    chave = s_sem_acento.replace(" ", "_").replace("-", "_")

    if chave in _MAPA_PERFIL_LEGADO:
        return _MAPA_PERFIL_LEGADO[chave]

    for p in Perfil:
        p_val_limpo = (
            unicodedata.normalize("NFKD", p.value)
            .encode("ascii", "ignore")
            .decode("utf-8")
            .casefold()
        )
        if p_val_limpo == chave or p.name.casefold() == chave:
            return p

    opcoes = [p.value for p in Perfil]
    raise ValueError(f"Perfil de usuário inválido: '{perfil}'. Opções aceitas: {', '.join(opcoes)}.")

def normalizar_matricula(matricula: Any) -> Optional[str]:
    """
    Padroniza matrícula institucional como string limpa, tratando sentinelas como None
    e preservando zeros à esquerda.
    """
    if eh_nao_informado(matricula):
        return None
    s = str(matricula).strip()
    if eh_nao_informado(s) or s.casefold() in {"-", "ni", "none", "null", "n/a", "na"}:
        return None
    return s

def normalizar_last_login(last_login: Any) -> Optional[datetime]:
    """
    Converte sentinelas ('Nunca', vazios) para None e realiza parsing resiliente de strings datetime.
    """
    if eh_nao_informado(last_login):
        return None
    if isinstance(last_login, datetime):
        return last_login
    if isinstance(last_login, str):
        s = last_login.strip()
        if s.casefold() in {"nunca", "-", "ni", "none", "null", "n/a", ""}:
            return None
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d/%m/%Y",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    pass
            raise ValueError(f"Formato de data e hora de último acesso inválido: '{last_login}'.")
    return None

from src.models.Usuario.enums.StatusUsuario import StatusUsuario

_MAPA_STATUS_USUARIO: Dict[str, StatusUsuario] = {
    "ativo": StatusUsuario.ATIVO,
    "active": StatusUsuario.ATIVO,
    "inativo": StatusUsuario.INATIVO,
    "inactive": StatusUsuario.INATIVO,
    "desativado": StatusUsuario.INATIVO,
    "pendente": StatusUsuario.PENDENTE,
    "pending": StatusUsuario.PENDENTE,
    "aguardando": StatusUsuario.PENDENTE,
    "bloqueado": StatusUsuario.BLOQUEADO,
    "blocked": StatusUsuario.BLOQUEADO,
}

def normalizar_status_usuario(status: Union[StatusUsuario, str, None]) -> StatusUsuario:
    """Normaliza strings ou enums para o StatusUsuario canônico."""
    if status is None:
        return StatusUsuario.PENDENTE
    if isinstance(status, StatusUsuario):
        return status
    s = str(status).strip().casefold()
    if s in _MAPA_STATUS_USUARIO:
        return _MAPA_STATUS_USUARIO[s]
    for st in StatusUsuario:
        if st.value.casefold() == s or st.name.casefold() == s:
            return st
    opcoes = [st.value for st in StatusUsuario]
    raise ValueError(f"Status de usuário inválido: '{status}'. Opções aceitas: {', '.join(opcoes)}.")

def normalizar_chaves_usuario(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Converte aliases aceitos na API para os nomes canônicos do modelo de Usuário."""
    normalizado: Dict[str, Any] = {}
    for chave, valor in payload.items():
        canonica = _ALIASES_USUARIO.get(chave, chave)
        if canonica in normalizado and chave != canonica:
            continue
        normalizado[canonica] = valor
    return normalizado

# Alias de compatibilidade
_normalizar_chaves = normalizar_chaves_usuario

__all__ = [
    "_ALIASES_USUARIO",
    "_MAPA_PERFIL_LEGADO",
    "_MAPA_STATUS_USUARIO",
    "normalizar_perfil",
    "normalizar_matricula",
    "normalizar_last_login",
    "normalizar_status_usuario",
    "normalizar_chaves_usuario",
    "_normalizar_chaves",
]