from typing import Optional, List, Dict, Union
from datetime import date
from src.models.Exame import (
    Exame,
    TipoExame,
    ResultadoExame,
    TesteLaboratorial,
)

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class ExameRepository:
    """
    Repositório de persistência e acesso a dados da entidade Exame.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover exames laboratoriais no banco de dados (ou memória).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - Suporta indexação em tempo constante O(1) por chave primária sequencial, exame_id e chave estrangeira amostra_id.
    - NÃO contém regras de negócio, interpretação heurística de laudos ou parsing de planilhas.
    """

    def __init__(self, exames: Optional[List[Exame]] = None):
        self._por_id: Dict[int, Exame] = {}
        self._por_exame_id: Dict[str, Exame] = {}
        # Relacionamento 1:N - uma amostra pode possuir múltiplos exames laboratoriais
        self._por_amostra_id: Dict[str, List[Exame]] = {}
        self._por_tipo_exame: Dict[TipoExame, List[Exame]] = {}
        self._por_resultado: Dict[ResultadoExame, List[Exame]] = {}
        self._por_teste_laboratorial: Dict[TesteLaboratorial, List[Exame]] = {}
        self._por_responsavel: Dict[str, List[Exame]] = {}
        self._proximo_id: int = 1

        for exame in exames or []:
            self.create(exame)

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, exame: Exame) -> None:
        if exame.id is not None:
            self._por_id[int(exame.id)] = exame

        if exame.exame_id:
            chave_exame = exame.exame_id.strip()
            self._por_exame_id[chave_exame] = exame

        if exame.amostra_id:
            chave_amostra = exame.amostra_id.strip()
            self._por_amostra_id.setdefault(chave_amostra, []).append(exame)

        if exame.tipo_exame:
            self._por_tipo_exame.setdefault(exame.tipo_exame, []).append(exame)

        if exame.resultado:
            self._por_resultado.setdefault(exame.resultado, []).append(exame)

        if exame.teste_laboratorial:
            self._por_teste_laboratorial.setdefault(exame.teste_laboratorial, []).append(exame)

        if exame.responsavel_exame:
            chave_resp = _normalizar(exame.responsavel_exame)
            if chave_resp:
                self._por_responsavel.setdefault(chave_resp, []).append(exame)

    def _desindexar(self, exame: Exame) -> None:
        if exame.id is not None:
            self._por_id.pop(int(exame.id), None)

        if exame.exame_id:
            chave_exame = exame.exame_id.strip()
            self._por_exame_id.pop(chave_exame, None)

        if exame.amostra_id:
            chave_amostra = exame.amostra_id.strip()
            if chave_amostra in self._por_amostra_id and exame in self._por_amostra_id[chave_amostra]:
                self._por_amostra_id[chave_amostra].remove(exame)

        if exame.tipo_exame in self._por_tipo_exame and exame in self._por_tipo_exame[exame.tipo_exame]:
            self._por_tipo_exame[exame.tipo_exame].remove(exame)

        if exame.resultado in self._por_resultado and exame in self._por_resultado[exame.resultado]:
            self._por_resultado[exame.resultado].remove(exame)

        if exame.teste_laboratorial in self._por_teste_laboratorial and exame in self._por_teste_laboratorial[exame.teste_laboratorial]:
            self._por_teste_laboratorial[exame.teste_laboratorial].remove(exame)

        if exame.responsavel_exame:
            chave_resp = _normalizar(exame.responsavel_exame)
            if chave_resp in self._por_responsavel and exame in self._por_responsavel[chave_resp]:
                self._por_responsavel[chave_resp].remove(exame)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, exame: Exame) -> Exame:
        """Persiste um novo exame com atribuição autoincremental de ID e atualização de índices."""
        if not exame.amostra_id:
            raise ValueError("O vínculo com o identificador da amostra (amostra_id) é obrigatório.")

        if exame.id is None:
            exame.id = self._proximo_id
            self._proximo_id += 1
        else:
            chave_id = int(exame.id)
            if chave_id in self._por_id:
                raise ValueError(f"Exame com ID {chave_id} já existe no banco de dados.")
            if chave_id >= self._proximo_id:
                self._proximo_id = chave_id + 1

        if not exame.exame_id:
            exame.exame_id = f"EX_{exame.id:04d}"
        else:
            chave_exame = exame.exame_id.strip()
            if chave_exame in self._por_exame_id:
                raise ValueError(f"Exame com exame_id '{chave_exame}' já existe no banco de dados.")

        self._indexar(exame)
        return exame

    def save(self, exame: Exame) -> Exame:
        """Persiste ou atualiza o exame se já possuir ID ou exame_id cadastrado."""
        if exame.id is not None and int(exame.id) in self._por_id:
            return self.update(exame.id, exame)
        if exame.exame_id and exame.exame_id.strip() in self._por_exame_id:
            return self.update(exame.exame_id.strip(), exame)
        return self.create(exame)

    def update(self, identificador: Union[int, str], exame_atualizado: Exame) -> Exame:
        """Atualiza um registro de exame existente e sincroniza todos os índices secundários."""
        exame_antigo = self.buscar_por_id(identificador) or self.buscar_por_exame_id(str(identificador))
        if not exame_antigo:
            raise KeyError(f"Exame com identificador '{identificador}' não encontrado para atualização.")

        self._desindexar(exame_antigo)

        # Preserva ID numérico consistente
        if exame_atualizado.id is None:
            exame_atualizado.id = exame_antigo.id
        elif int(exame_atualizado.id) != int(exame_antigo.id):
            chave_nova = int(exame_atualizado.id)
            if chave_nova in self._por_id:
                raise ValueError(f"Já existe outro exame com o ID {chave_nova}.")
            if chave_nova >= self._proximo_id:
                self._proximo_id = chave_nova + 1

        # Preserva exame_id
        if not exame_atualizado.exame_id:
            exame_atualizado.exame_id = exame_antigo.exame_id
        elif exame_atualizado.exame_id != exame_antigo.exame_id:
            chave_exame_nova = exame_atualizado.exame_id.strip()
            if chave_exame_nova in self._por_exame_id:
                raise ValueError(f"Já existe outro exame com exame_id '{chave_exame_nova}'.")

        self._indexar(exame_atualizado)
        return exame_atualizado

    def delete(self, identificador: Union[int, str]) -> bool:
        """Exclui o exame pelo ID numérico ou pelo exame_id."""
        exame = self.buscar_por_id(identificador) or self.buscar_por_exame_id(str(identificador))
        if not exame:
            return False

        self._desindexar(exame)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Exame]:
        try:
            return self._por_id.get(int(id_numerico))
        except (ValueError, TypeError):
            return None

    def buscar_por_exame_id(self, exame_id: str) -> Optional[Exame]:
        if not exame_id:
            return None
        return self._por_exame_id.get(str(exame_id).strip())

    def buscar_por_amostra_id(self, amostra_id: str) -> List[Exame]:
        """Retorna todos os exames associados a uma amostra biológica."""
        if not amostra_id:
            return []
        return list(self._por_amostra_id.get(str(amostra_id).strip(), []))

    def buscar_por_tipo_exame(self, tipo_exame: Union[TipoExame, str]) -> List[Exame]:
        """Consulta exames por patógeno ou painel investigado."""
        if not tipo_exame:
            return []
        if isinstance(tipo_exame, TipoExame):
            return list(self._por_tipo_exame.get(tipo_exame, []))
        for t in self._por_tipo_exame:
            if t.value.lower() == str(tipo_exame).strip().lower():
                return list(self._por_tipo_exame.get(t, []))
        return []

    def buscar_por_resultado(self, resultado: Union[ResultadoExame, str]) -> List[Exame]:
        """Consulta exames por resultado categorizado do ensaio."""
        if not resultado:
            return []
        if isinstance(resultado, ResultadoExame):
            return list(self._por_resultado.get(resultado, []))
        for r in self._por_resultado:
            if r.value.lower() == str(resultado).strip().lower():
                return list(self._por_resultado.get(r, []))
        return []

    def buscar_por_teste_laboratorial(self, teste_laboratorial: Union[TesteLaboratorial, str]) -> List[Exame]:
        """Consulta exames por metodologia/teste laboratorial."""
        if not teste_laboratorial:
            return []
        if isinstance(teste_laboratorial, TesteLaboratorial):
            return list(self._por_teste_laboratorial.get(teste_laboratorial, []))
        for t in self._por_teste_laboratorial:
            if t.value.lower() == str(teste_laboratorial).strip().lower():
                return list(self._por_teste_laboratorial.get(t, []))
        return []

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        amostra_id: Optional[str] = None,
        tipo_exame: Optional[Union[TipoExame, str]] = None,
        resultado: Optional[Union[ResultadoExame, str]] = None,
        teste_laboratorial: Optional[Union[TesteLaboratorial, str]] = None,
        data_realizacao: Optional[date] = None,
        responsavel_exame: Optional[str] = None,
        ordenar_por: str = "id",
        skip: int = 0,
        limit: int = 100,
    ) -> List[Exame]:
        """Retorna lista de exames aplicando filtros combinados, ordenação e paginação."""
        resultado_lista = list(self._por_id.values())

        if amostra_id:
            chave_amostra = amostra_id.strip()
            resultado_lista = [e for e in resultado_lista if e.amostra_id.strip() == chave_amostra]

        if tipo_exame:
            val_tipo = tipo_exame.value if isinstance(tipo_exame, TipoExame) else str(tipo_exame).strip().lower()
            resultado_lista = [
                e for e in resultado_lista
                if (e.tipo_exame.value.lower() if isinstance(e.tipo_exame, TipoExame) else str(e.tipo_exame).lower()) == val_tipo
            ]

        if resultado:
            val_res = resultado.value if isinstance(resultado, ResultadoExame) else str(resultado).strip().lower()
            resultado_lista = [
                e for e in resultado_lista
                if (e.resultado.value.lower() if isinstance(e.resultado, ResultadoExame) else str(e.resultado).lower()) == val_res
            ]

        if teste_laboratorial:
            val_teste = teste_laboratorial.value if isinstance(teste_laboratorial, TesteLaboratorial) else str(teste_laboratorial).strip().lower()
            resultado_lista = [
                e for e in resultado_lista
                if (e.teste_laboratorial.value.lower() if isinstance(e.teste_laboratorial, TesteLaboratorial) else str(e.teste_laboratorial).lower()) == val_teste
            ]

        if data_realizacao:
            resultado_lista = [e for e in resultado_lista if e.data_realizacao == data_realizacao]

        if responsavel_exame:
            chave_resp = _normalizar(responsavel_exame)
            resultado_lista = [e for e in resultado_lista if e.responsavel_exame and _normalizar(e.responsavel_exame) == chave_resp]

        # Ordenação
        if ordenar_por == "data":
            resultado_lista.sort(key=lambda e: e.data_realizacao, reverse=True)
        else:
            resultado_lista.sort(key=lambda e: (int(e.id) if e.id is not None else 0))

        # Paginação
        if skip > 0:
            resultado_lista = resultado_lista[skip:]
        if limit is not None and limit > 0:
            resultado_lista = resultado_lista[:limit]

        return resultado_lista

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONTROLE (COUNT, CONTAR, EXISTS, CLEAR):
    # -------------------------------------------------------------------------
    def count(self) -> int:
        """Retorna o número total de exames registrados."""
        return len(self._por_id)

    def contar(self) -> int:
        """Alias em português para count()."""
        return self.count()

    def exists(self, identificador: Union[int, str]) -> bool:
        """Verifica se existe um exame com o identificador fornecido."""
        return self.buscar_por_id(identificador) is not None or self.buscar_por_exame_id(str(identificador)) is not None

    def clear(self) -> None:
        """Limpa todo o armazenamento em memória do repositório."""
        self._por_id.clear()
        self._por_exame_id.clear()
        self._por_amostra_id.clear()
        self._por_tipo_exame.clear()
        self._por_resultado.clear()
        self._por_teste_laboratorial.clear()
        self._por_responsavel.clear()
        self._proximo_id = 1

exame_repository = ExameRepository()
