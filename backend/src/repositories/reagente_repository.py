import re
from typing import Optional, List, Dict, Union, Any
from datetime import date, datetime
from src.models.Reagente import Reagente

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class ReagenteRepository:
    """
    Repositório de persistência e acesso a dados da entidade Reagente (lotes físicos).
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover lotes de reagentes no MongoDB (com cache indexado).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - Suporta indexação O(1) por ID numérico, reagente_id (_id), código, nome, lote, marca e local.
    - NÃO contém regras de negócio de consolidação dimensional ou ações temporais.
    """
    COLLECTION_NAME = "reagentes"

    def __init__(
        self,
        reagentes: Optional[List[Reagente]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, Reagente] = {}
        self._por_reagente_id: Dict[str, Reagente] = {}
        self._por_codigo: Dict[str, List[Reagente]] = {}
        self._por_nome: Dict[str, List[Reagente]] = {}
        self._por_lote: Dict[str, List[Reagente]] = {}
        self._por_marca: Dict[str, List[Reagente]] = {}
        self._por_local: Dict[str, List[Reagente]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not reagentes:
            self._carregar_do_banco()

        for reagente in reagentes or []:
            self.create(reagente)

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
                return None
        return None

    def _do_mongo(self, doc: dict) -> Reagente:
        d = dict(doc)
        if "_id" in d and not isinstance(d["_id"], int):
            if isinstance(d["_id"], str) and d["_id"].isdigit():
                d["_id"] = int(d["_id"])
            else:
                d["_id"] = None

        val = d.get("data_validade")
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    d["data_validade"] = datetime.strptime(val, fmt).date()
                    break
                except ValueError:
                    pass

        return Reagente(**d)

    def _para_mongo(self, reagente: Reagente) -> dict:
        doc = reagente.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "_id" not in doc and reagente.id is not None:
            doc["_id"] = int(reagente.id) if str(reagente.id).isdigit() else reagente.id
        return doc

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    r = self._do_mongo(doc)
                    self._indexar(r)
                    if r.id is not None and isinstance(r.id, int) and r.id >= self._proximo_id:
                        self._proximo_id = r.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, reagente: Reagente) -> None:
        if reagente.id is not None and isinstance(reagente.id, int):
            self._por_id[reagente.id] = reagente

        if reagente.reagente_id:
            chave_rid = reagente.reagente_id.strip()
            self._por_reagente_id[chave_rid] = reagente

        chave_cod = _normalizar(reagente.reagente_codigo)
        if chave_cod:
            self._por_codigo.setdefault(chave_cod, []).append(reagente)

        chave_nome = _normalizar(reagente.reagente_nome)
        if chave_nome:
            self._por_nome.setdefault(chave_nome, []).append(reagente)

        chave_lote = _normalizar(reagente.numero_lote)
        if chave_lote:
            self._por_lote.setdefault(chave_lote, []).append(reagente)

        chave_marca = _normalizar(reagente.marca)
        if chave_marca:
            self._por_marca.setdefault(chave_marca, []).append(reagente)

        chave_local = _normalizar(reagente.reagente_local_armazenamento)
        if chave_local:
            self._por_local.setdefault(chave_local, []).append(reagente)

        if reagente.id is not None and isinstance(reagente.id, int) and reagente.id >= self._proximo_id:
            self._proximo_id = reagente.id + 1

    def _desindexar(self, reagente: Reagente) -> None:
        if reagente.id is not None and isinstance(reagente.id, int):
            self._por_id.pop(reagente.id, None)

        if reagente.reagente_id:
            chave_rid = reagente.reagente_id.strip()
            self._por_reagente_id.pop(chave_rid, None)

        chave_cod = _normalizar(reagente.reagente_codigo)
        if chave_cod in self._por_codigo and reagente in self._por_codigo[chave_cod]:
            self._por_codigo[chave_cod].remove(reagente)

        chave_nome = _normalizar(reagente.reagente_nome)
        if chave_nome in self._por_nome and reagente in self._por_nome[chave_nome]:
            self._por_nome[chave_nome].remove(reagente)

        chave_lote = _normalizar(reagente.numero_lote)
        if chave_lote in self._por_lote and reagente in self._por_lote[chave_lote]:
            self._por_lote[chave_lote].remove(reagente)

        chave_marca = _normalizar(reagente.marca)
        if chave_marca in self._por_marca and reagente in self._por_marca[chave_marca]:
            self._por_marca[chave_marca].remove(reagente)

        chave_local = _normalizar(reagente.reagente_local_armazenamento)
        if chave_local in self._por_local and reagente in self._por_local[chave_local]:
            self._por_local[chave_local].remove(reagente)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, reagente: Reagente) -> Reagente:
        """Persiste um novo lote de reagente com ID sequencial e indexação."""
        if not reagente.reagente_nome or not reagente.reagente_codigo:
            raise ValueError("O nome e o código do reagente são campos obrigatórios.")

        if not reagente.numero_lote:
            raise ValueError("O número do lote (numero_lote) é obrigatório.")

        # Validação de lote duplicado para o mesmo reagente
        existente = self.buscar_por_nome_e_lote(reagente.reagente_nome, reagente.numero_lote)
        if existente:
            raise ValueError(f"Lote '{reagente.numero_lote}' já cadastrado para o reagente '{reagente.reagente_nome}'.")

        if reagente.id is None:
            if self.collection is not None:
                try:
                    doc_max = self.collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
                    max_id = int(doc_max["_id"]) if doc_max and isinstance(doc_max.get("_id"), (int, float)) else 0
                    reagente.id = max(max_id + 1, self._proximo_id)
                except Exception:
                    reagente.id = self._proximo_id
            else:
                reagente.id = self._proximo_id
            self._proximo_id = reagente.id + 1
        else:
            chave_id = int(reagente.id)
            if chave_id in self._por_id or (
                self.collection is not None and self.collection.count_documents({"_id": chave_id}) > 0
            ):
                raise ValueError(f"Reagente com ID {chave_id} já existe no banco de dados.")
            if chave_id >= self._proximo_id:
                self._proximo_id = chave_id + 1

        if not reagente.reagente_id:
            reagente.reagente_id = f"REA_{reagente.id:04d}"
        else:
            chave_rid = reagente.reagente_id.strip()
            if chave_rid in self._por_reagente_id or (
                self.collection is not None and self.collection.count_documents({"reagente_id": chave_rid}) > 0
            ):
                raise ValueError(f"Reagente com _id '{chave_rid}' já existe no banco de dados.")

        if self.collection is not None:
            doc = self._para_mongo(reagente)
            self.collection.insert_one(doc)

        self._indexar(reagente)
        return reagente

    def save(self, reagente: Reagente) -> Reagente:
        """Persiste ou atualiza o lote de reagente se já possuir identificador registrado."""
        if reagente.id is not None and self.buscar_por_id(reagente.id):
            return self.update(reagente.id, reagente)
        if reagente.reagente_id and self.buscar_por_reagente_id(reagente.reagente_id.strip()):
            return self.update(reagente.reagente_id.strip(), reagente)
        return self.create(reagente)

    def update(self, identificador: Union[int, str], reagente_atualizado: Reagente) -> Reagente:
        """Atualiza os dados de um lote de reagente e sincroniza os índices."""
        antigo = self.buscar_por_id(identificador) or self.buscar_por_reagente_id(str(identificador))
        if not antigo:
            raise KeyError(f"Reagente com identificador '{identificador}' não encontrado para atualização.")

        self._desindexar(antigo)

        # Preserva ID numérico consistente
        if reagente_atualizado.id is None:
            reagente_atualizado.id = antigo.id
        elif int(reagente_atualizado.id) != int(antigo.id):
            chave_nova = int(reagente_atualizado.id)
            if chave_nova in self._por_id:
                raise ValueError(f"Já existe outro reagente com o ID {chave_nova}.")
            if chave_nova >= self._proximo_id:
                self._proximo_id = chave_nova + 1

        # Preserva reagente_id
        if not reagente_atualizado.reagente_id:
            reagente_atualizado.reagente_id = antigo.reagente_id
        elif reagente_atualizado.reagente_id != antigo.reagente_id:
            chave_rid_nova = reagente_atualizado.reagente_id.strip()
            if chave_rid_nova in self._por_reagente_id:
                raise ValueError(f"Já existe outro reagente com reagente_id '{chave_rid_nova}'.")

        if self.collection is not None:
            doc = self._para_mongo(reagente_atualizado)
            filtro = (
                {"_id": int(antigo.id)}
                if antigo.id is not None
                else {"reagente_id": antigo.reagente_id}
            )
            self.collection.replace_one(filtro, doc, upsert=True)

        self._indexar(reagente_atualizado)
        return reagente_atualizado

    def delete(self, identificador: Union[int, str]) -> bool:
        """Exclui o lote de reagente pelo ID numérico ou pelo reagente_id (_id)."""
        reagente = self.buscar_por_id(identificador) or self.buscar_por_reagente_id(str(identificador))
        if not reagente:
            return False

        if self.collection is not None:
            if reagente.id is not None:
                self.collection.delete_one({"_id": int(reagente.id)})
            if reagente.reagente_id:
                self.collection.delete_one({"reagente_id": reagente.reagente_id})

        self._desindexar(reagente)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Reagente]:
        try:
            num = int(id_numerico)
            if num in self._por_id:
                return self._por_id[num]
            if self.collection is not None:
                doc = self.collection.find_one({"_id": num})
                if doc:
                    r = self._do_mongo(doc)
                    self._indexar(r)
                    return r
        except (ValueError, TypeError):
            pass
        return None

    def buscar_por_reagente_id(self, reagente_id: str) -> Optional[Reagente]:
        if not reagente_id:
            return None
        chave = str(reagente_id).strip()
        if chave in self._por_reagente_id:
            return self._por_reagente_id[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"reagente_id": chave})
            if doc:
                r = self._do_mongo(doc)
                self._indexar(r)
                return r
        return None

    def buscar_por_codigo(self, codigo: str) -> List[Reagente]:
        """Consulta todos os lotes que possuem o código especificado."""
        chave = _normalizar(codigo)
        if not chave:
            return []
        if chave in self._por_codigo:
            return list(self._por_codigo[chave])
        if self.collection is not None:
            docs = self.collection.find({"codigo": {"$regex": f"^{re.escape(codigo.strip())}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    r = self._do_mongo(d)
                    self._indexar(r)
                    res.append(r)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_nome(self, nome: str) -> List[Reagente]:
        """Consulta todos os lotes correspondentes a um determinado nome de reagente."""
        chave = _normalizar(nome)
        if not chave:
            return []
        if chave in self._por_nome:
            return list(self._por_nome[chave])
        if self.collection is not None:
            docs = self.collection.find({"nome": {"$regex": f"^{re.escape(nome.strip())}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    r = self._do_mongo(d)
                    self._indexar(r)
                    res.append(r)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_lote(self, numero_lote: str) -> List[Reagente]:
        """Consulta lotes pelo identificador textual do lote."""
        chave = _normalizar(numero_lote)
        if not chave:
            return []
        if chave in self._por_lote:
            return list(self._por_lote[chave])
        if self.collection is not None:
            docs = self.collection.find({"numero_lote": {"$regex": f"^{re.escape(numero_lote.strip())}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    r = self._do_mongo(d)
                    self._indexar(r)
                    res.append(r)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_nome_e_lote(self, nome: str, numero_lote: str) -> Optional[Reagente]:
        """Consulta um lote específico através da chave composta (nome, numero_lote)."""
        chave_nome = _normalizar(nome)
        chave_lote = _normalizar(numero_lote)
        for r in self._por_nome.get(chave_nome, []):
            if _normalizar(r.numero_lote) == chave_lote:
                return r
        if self.collection is not None:
            doc = self.collection.find_one({
                "nome": {"$regex": f"^{re.escape(nome.strip())}$", "$options": "i"},
                "numero_lote": {"$regex": f"^{re.escape(numero_lote.strip())}$", "$options": "i"}
            })
            if doc:
                r = self._do_mongo(doc)
                self._indexar(r)
                return r
        return None

    def buscar_por_marca(self, marca: str) -> List[Reagente]:
        """Consulta lotes fornecidos por uma determinada marca ou fabricante."""
        chave = _normalizar(marca)
        if not chave:
            return []
        return list(self._por_marca.get(chave, []))

    def buscar_por_local(self, local_armazenamento: str) -> List[Reagente]:
        """Consulta lotes alocados em um determinado local de armazenamento."""
        chave = _normalizar(local_armazenamento)
        if not chave:
            return []
        return list(self._por_local.get(chave, []))

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        nome: Optional[str] = None,
        codigo: Optional[str] = None,
        marca: Optional[str] = None,
        local_armazenamento: Optional[str] = None,
        apenas_vencidos: Optional[bool] = None,
        termo_busca: Optional[str] = None,
        ordenar_por: str = "id",
        skip: int = 0,
        limit: int = 100,
    ) -> List[Reagente]:
        """Retorna lista de lotes aplicando filtros, busca textual, ordenação e paginação."""
        resultado_lista = list(self._por_id.values())

        if nome:
            chave_nome = _normalizar(nome)
            resultado_lista = [r for r in resultado_lista if _normalizar(r.reagente_nome) == chave_nome]

        if codigo:
            chave_cod = _normalizar(codigo)
            resultado_lista = [r for r in resultado_lista if _normalizar(r.reagente_codigo) == chave_cod]

        if marca:
            chave_marca = _normalizar(marca)
            resultado_lista = [r for r in resultado_lista if _normalizar(r.marca) == chave_marca]

        if local_armazenamento:
            chave_loc = _normalizar(local_armazenamento)
            resultado_lista = [r for r in resultado_lista if _normalizar(r.reagente_local_armazenamento) == chave_loc]

        if apenas_vencidos is not None:
            hoje = date.today()
            if apenas_vencidos:
                resultado_lista = [r for r in resultado_lista if r.data_validade < hoje]
            else:
                resultado_lista = [r for r in resultado_lista if r.data_validade >= hoje]

        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado_lista = [
                r for r in resultado_lista
                if (
                    termo in _normalizar(r.reagente_nome)
                    or termo in _normalizar(r.reagente_codigo)
                    or termo in _normalizar(r.numero_lote)
                    or termo in _normalizar(r.marca)
                    or termo in _normalizar(r.reagente_local_armazenamento)
                )
            ]

        # Ordenação
        if ordenar_por == "validade":
            resultado_lista.sort(key=lambda r: r.data_validade)
        elif ordenar_por == "nome":
            resultado_lista.sort(key=lambda r: r.reagente_nome.lower())
        else:
            resultado_lista.sort(key=lambda r: (int(r.id) if r.id is not None else 0))

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
        """Retorna o número total de lotes físicos armazenados."""
        if self.collection is not None:
            try:
                c = self.collection.count_documents({})
                if c > 0:
                    return c
            except Exception:
                pass
        return len(self._por_id)

    def contar(self) -> int:
        """Alias em português para count()."""
        return self.count()

    def exists(self, identificador: Union[int, str]) -> bool:
        """Verifica se existe um lote com o identificador numérico ou reagente_id."""
        return self.buscar_por_id(identificador) is not None or self.buscar_por_reagente_id(str(identificador)) is not None

    def clear(self) -> None:
        """Limpa todo o acervo de lotes de reagentes."""
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_reagente_id.clear()
        self._por_codigo.clear()
        self._por_nome.clear()
        self._por_lote.clear()
        self._por_marca.clear()
        self._por_local.clear()
        self._proximo_id = 1

reagente_repository = ReagenteRepository(use_mongo=True)
