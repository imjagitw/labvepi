from typing import Optional, List, Dict, Union, Any
from datetime import date
from src.models.Exame import (
    Exame,
    TipoExame,
    ResultadoExame,
    TesteLaboratorial,
)
from src.utils.repositorio import (
    _normalizar,
    gerar_proximo_id_mongo,
    doc_para_mongo,
    preparar_doc_mongo,
)

class ExameRepository:
    """
    Repositório de persistência e acesso a dados da entidade Exame.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover exames laboratoriais no MongoDB (com cache indexado).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - Suporta indexação em tempo constante O(1) por chave primária sequencial, exame_id e chave estrangeira amostra_id.
    - NÃO contém regras de negócio, interpretação heurística de laudos ou parsing de planilhas.
    """
    COLLECTION_NAME = "exames"

    def __init__(
        self,
        exames: Optional[List[Exame]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, Exame] = {}
        self._por_exame_id: Dict[str, Exame] = {}
        self._por_amostra_id: Dict[str, List[Exame]] = {}
        self._por_tipo_exame: Dict[TipoExame, List[Exame]] = {}
        self._por_resultado: Dict[ResultadoExame, List[Exame]] = {}
        self._por_teste_laboratorial: Dict[TesteLaboratorial, List[Exame]] = {}
        self._por_responsavel: Dict[str, List[Exame]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not exames:
            self._carregar_do_banco()

        for exame in exames or []:
            self.create(exame)

    @property
    def collection(self):
        if self._collection is not None:
            return self._collection
        if self._db is not None:
            self._collection = self._db[self.COLLECTION_NAME]
            return self._collection
        if self._use_mongo:
            try:
                from src.data.connection import get_db
                self._collection = get_db()[self.COLLECTION_NAME]
                return self._collection
            except Exception:
                self._use_mongo = False
                return None
        return None

    def _do_mongo(self, doc: dict) -> Exame:
        d = preparar_doc_mongo(doc, fallback_id_campo="exame_id")
        if "_id" in d and not isinstance(d["_id"], int):
            d["_id"] = None
        return Exame(**d)

    def _para_mongo(self, exame: Exame) -> dict:
        return doc_para_mongo(exame)

    def _gerar_proximo_id(self) -> int:
        """Gera a próxima chave primária autoincrementada (max(_id) + 1)."""
        proximo = gerar_proximo_id_mongo(self.collection, self._proximo_id)
        self._proximo_id = proximo + 1
        return proximo

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    ex = self._do_mongo(doc)
                    self._indexar(ex)
                    if ex.id is not None and isinstance(ex.id, int) and ex.id >= self._proximo_id:
                        self._proximo_id = ex.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, exame: Exame) -> None:
        if exame.id is not None and isinstance(exame.id, int):
            self._por_id[exame.id] = exame

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

        if exame.id is not None and isinstance(exame.id, int) and exame.id >= self._proximo_id:
            self._proximo_id = exame.id + 1

    def _desindexar(self, exame: Exame) -> None:
        if exame.id is not None and isinstance(exame.id, int):
            self._por_id.pop(exame.id, None)

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

        # A chave primária (id/_id) é SEMPRE gerada pela camada de persistência;
        # qualquer valor pré-existente no objeto é descartado.
        exame.id = self._gerar_proximo_id()

        if not exame.exame_id:
            exame.exame_id = f"EX_{exame.id:04d}"
        else:
            chave_exame = exame.exame_id.strip()
            if chave_exame in self._por_exame_id or (
                self.collection is not None and self.collection.count_documents({"exame_id": chave_exame}) > 0
            ):
                raise ValueError(f"Exame com exame_id '{chave_exame}' já existe no banco de dados.")

        if self.collection is not None:
            doc = self._para_mongo(exame)
            self.collection.insert_one(doc)

        self._indexar(exame)
        return exame

    def save(self, exame: Exame) -> Exame:
        """Persiste ou atualiza o exame se já possuir ID ou exame_id cadastrado."""
        if exame.id is not None and self.buscar_por_id(exame.id):
            return self.update(exame.id, exame)
        if exame.exame_id and self.buscar_por_exame_id(exame.exame_id.strip()):
            return self.update(exame.exame_id.strip(), exame)
        return self.create(exame)

    def update(self, identificador: Union[int, str], exame_atualizado: Exame) -> Exame:
        """Atualiza um registro de exame existente e sincroniza todos os índices secundários."""
        exame_antigo = self.buscar_por_id(identificador) or self.buscar_por_exame_id(str(identificador))
        if not exame_antigo:
            raise KeyError(f"Exame com identificador '{identificador}' não encontrado para atualização.")

        self._desindexar(exame_antigo)

        # A chave primária é imutável: sempre preserva o id já persistido.
        exame_atualizado.id = exame_antigo.id

        # Preserva exame_id
        if not exame_atualizado.exame_id:
            exame_atualizado.exame_id = exame_antigo.exame_id
        elif exame_atualizado.exame_id != exame_antigo.exame_id:
            chave_exame_nova = exame_atualizado.exame_id.strip()
            if chave_exame_nova in self._por_exame_id:
                raise ValueError(f"Já existe outro exame com exame_id '{chave_exame_nova}'.")

        if self.collection is not None:
            doc = self._para_mongo(exame_atualizado)
            filtro = (
                {"_id": int(exame_antigo.id)}
                if exame_antigo.id is not None
                else {"exame_id": exame_antigo.exame_id}
            )
            self.collection.replace_one(filtro, doc, upsert=True)

        self._indexar(exame_atualizado)
        return exame_atualizado

    def delete(self, identificador: Union[int, str]) -> bool:
        """Exclui o exame pelo ID numérico ou pelo exame_id."""
        exame = self.buscar_por_id(identificador) or self.buscar_por_exame_id(str(identificador))
        if not exame:
            return False

        if self.collection is not None:
            if exame.id is not None:
                self.collection.delete_one({"_id": int(exame.id)})
            if exame.exame_id:
                self.collection.delete_one({"exame_id": exame.exame_id})

        self._desindexar(exame)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Exame]:
        try:
            num = int(id_numerico)
            if num in self._por_id:
                return self._por_id[num]
            if self.collection is not None:
                doc = self.collection.find_one({"_id": num})
                if doc:
                    ex = self._do_mongo(doc)
                    self._indexar(ex)
                    return ex
        except (ValueError, TypeError):
            pass
        return None

    def buscar_por_exame_id(self, exame_id: str) -> Optional[Exame]:
        if not exame_id:
            return None
        chave = str(exame_id).strip()
        if chave in self._por_exame_id:
            return self._por_exame_id[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"exame_id": chave})
            if doc:
                ex = self._do_mongo(doc)
                self._indexar(ex)
                return ex
        return None

    def buscar_por_amostra_id(self, amostra_id: str) -> List[Exame]:
        """Retorna todos os exames associados a uma amostra biológica."""
        if not amostra_id:
            return []
        chave = str(amostra_id).strip()
        if chave in self._por_amostra_id:
            return list(self._por_amostra_id[chave])
        if self.collection is not None:
            docs = self.collection.find({"amostra_id": chave})
            res = []
            for d in docs:
                try:
                    ex = self._do_mongo(d)
                    self._indexar(ex)
                    res.append(ex)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_tipo_exame(self, tipo_exame: Union[TipoExame, str]) -> List[Exame]:
        """Consulta exames por patógeno ou painel investigado."""
        if not tipo_exame:
            return []
        if isinstance(tipo_exame, TipoExame) and tipo_exame in self._por_tipo_exame:
            return list(self._por_tipo_exame[tipo_exame])
        alvo = tipo_exame.value if isinstance(tipo_exame, TipoExame) else str(tipo_exame).strip()
        for t in self._por_tipo_exame:
            if t.value.lower() == alvo.lower():
                return list(self._por_tipo_exame[t])
        return []

    def buscar_por_resultado(self, resultado: Union[ResultadoExame, str]) -> List[Exame]:
        """Consulta exames por resultado categorizado do ensaio."""
        if not resultado:
            return []
        if isinstance(resultado, ResultadoExame) and resultado in self._por_resultado:
            return list(self._por_resultado[resultado])
        alvo = resultado.value if isinstance(resultado, ResultadoExame) else str(resultado).strip()
        for r in self._por_resultado:
            if r.value.lower() == alvo.lower():
                return list(self._por_resultado[r])
        return []

    def buscar_por_teste_laboratorial(self, teste_laboratorial: Union[TesteLaboratorial, str]) -> List[Exame]:
        """Consulta exames por metodologia/teste laboratorial."""
        if not teste_laboratorial:
            return []
        if isinstance(teste_laboratorial, TesteLaboratorial) and teste_laboratorial in self._por_teste_laboratorial:
            return list(self._por_teste_laboratorial[teste_laboratorial])
        alvo = teste_laboratorial.value if isinstance(teste_laboratorial, TesteLaboratorial) else str(teste_laboratorial).strip()
        for t in self._por_teste_laboratorial:
            if t.value.lower() == alvo.lower():
                return list(self._por_teste_laboratorial[t])
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
            norm_resp = _normalizar(responsavel_exame)
            resultado_lista = [e for e in resultado_lista if _normalizar(e.responsavel_exame) == norm_resp]

        resultado_lista.sort(key=lambda e: (e.id or 0, e.exame_id or ""))

        if skip > 0:
            resultado_lista = resultado_lista[skip:]
        if limit is not None and limit > 0:
            resultado_lista = resultado_lista[:limit]

        return resultado_lista

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONTROLE (COUNT, EXISTS, CLEAR):
    # -------------------------------------------------------------------------
    def count(self) -> int:
        if self.collection is not None:
            try:
                c = self.collection.count_documents({})
                if c > 0:
                    return c
            except Exception:
                pass
        return len(self._por_id)

    def exists(self, identificador: Union[int, str]) -> bool:
        """Verifica existência por ID numérico ou pelo exame_id."""
        if self.buscar_por_id(identificador) or self.buscar_por_exame_id(str(identificador)):
            return True
        return False

    def clear(self) -> None:
        """Limpa todo o armazenamento do banco de dados."""
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_exame_id.clear()
        self._por_amostra_id.clear()
        self._por_tipo_exame.clear()
        self._por_resultado.clear()
        self._por_teste_laboratorial.clear()
        self._por_responsavel.clear()
        self._proximo_id = 1

exame_repository = ExameRepository(use_mongo=True)
