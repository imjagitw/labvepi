import re
from typing import Optional, List, Dict, Union, Any
from src.models.EstoqueReagente import EstoqueReagente

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class EstoqueReagenteRepository:
    """
    Repositório de persistência e acesso a dados do modelo agregado EstoqueReagente.
    Responsabilidade exclusiva:
    - Armazenar, consultar, atualizar e remover agregações consolidadas de estoque por reagente no MongoDB (com cache indexado).
    - Atuar como camada de acesso a dados (DAO/Persistência) para visões de inventário unificado.
    - Suporta indexação O(1) por ID numérico e por nome normalizado do reagente.
    - NÃO contém fórmulas de conversão dimensional ou cálculos temporais (delegados ao ReagenteService).
    """
    COLLECTION_NAME = "estoque_reagentes"

    def __init__(
        self,
        estoques: Optional[List[EstoqueReagente]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, EstoqueReagente] = {}
        self._por_nome: Dict[str, EstoqueReagente] = {}
        self._por_codigo: Dict[str, List[EstoqueReagente]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not estoques:
            self._carregar_do_banco()

        for estoque in estoques or []:
            self.create(estoque)

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

    def _do_mongo(self, doc: dict) -> EstoqueReagente:
        d = dict(doc)
        if "_id" in d and not isinstance(d["_id"], int):
            if isinstance(d["_id"], str) and d["_id"].isdigit():
                d["_id"] = int(d["_id"])
            else:
                d["_id"] = None
        return EstoqueReagente(**d)

    def _para_mongo(self, estoque: EstoqueReagente) -> dict:
        doc = estoque.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "_id" not in doc and estoque.id is not None:
            doc["_id"] = int(estoque.id) if str(estoque.id).isdigit() else estoque.id
        return doc

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    e = self._do_mongo(doc)
                    self._indexar(e)
                    if e.id is not None and isinstance(e.id, int) and e.id >= self._proximo_id:
                        self._proximo_id = e.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, estoque: EstoqueReagente) -> None:
        if estoque.id is not None and isinstance(estoque.id, int):
            self._por_id[estoque.id] = estoque

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome:
            self._por_nome[chave_nome] = estoque

        if estoque.reagente_codigo:
            chave_cod = _normalizar(estoque.reagente_codigo)
            if chave_cod:
                self._por_codigo.setdefault(chave_cod, []).append(estoque)

        if estoque.id is not None and isinstance(estoque.id, int) and estoque.id >= self._proximo_id:
            self._proximo_id = estoque.id + 1

    def _desindexar(self, estoque: EstoqueReagente) -> None:
        if estoque.id is not None and isinstance(estoque.id, int):
            self._por_id.pop(estoque.id, None)

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome:
            self._por_nome.pop(chave_nome, None)

        if estoque.reagente_codigo:
            chave_cod = _normalizar(estoque.reagente_codigo)
            if chave_cod in self._por_codigo and estoque in self._por_codigo[chave_cod]:
                self._por_codigo[chave_cod].remove(estoque)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, estoque: EstoqueReagente) -> EstoqueReagente:
        """Persiste um novo registro consolidado de estoque de reagente."""
        if not estoque.reagente_nome:
            raise ValueError("O nome do reagente (reagente_nome) é obrigatório para o estoque.")

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome in self._por_nome or (
            self.collection is not None
            and self.collection.count_documents({"nome": {"$regex": f"^{re.escape(estoque.reagente_nome.strip())}$", "$options": "i"}}) > 0
        ):
            raise ValueError(f"Estoque para o reagente '{estoque.reagente_nome}' já está cadastrado.")

        if estoque.id is None:
            if self.collection is not None:
                try:
                    doc_max = self.collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
                    max_id = int(doc_max["_id"]) if doc_max and isinstance(doc_max.get("_id"), (int, float)) else 0
                    estoque.id = max(max_id + 1, self._proximo_id)
                except Exception:
                    estoque.id = self._proximo_id
            else:
                estoque.id = self._proximo_id
            self._proximo_id = estoque.id + 1
        else:
            chave_id = int(estoque.id)
            if chave_id in self._por_id or (
                self.collection is not None and self.collection.count_documents({"_id": chave_id}) > 0
            ):
                raise ValueError(f"Estoque com ID {chave_id} já existe no banco de dados.")
            if chave_id >= self._proximo_id:
                self._proximo_id = chave_id + 1

        if self.collection is not None:
            doc = self._para_mongo(estoque)
            self.collection.insert_one(doc)

        self._indexar(estoque)
        return estoque

    def save(self, estoque: EstoqueReagente) -> EstoqueReagente:
        """Persiste ou atualiza o estoque se já possuir ID ou nome registrado."""
        if estoque.id is not None and self.buscar_por_id(estoque.id):
            return self.update(estoque.id, estoque)

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome in self._por_nome or (
            self.collection is not None and self.buscar_por_nome(estoque.reagente_nome)
        ):
            return self.update(chave_nome, estoque)

        return self.create(estoque)

    def update(self, identificador: Union[int, str], estoque_atualizado: EstoqueReagente) -> EstoqueReagente:
        """Atualiza a visão consolidada de estoque de um reagente existente."""
        antigo = self.buscar_por_id(identificador) or self.buscar_por_nome(str(identificador))
        if not antigo:
            raise KeyError(f"Estoque para '{identificador}' não encontrado para atualização.")

        self._desindexar(antigo)

        # Preserva ID numérico consistente
        if estoque_atualizado.id is None:
            estoque_atualizado.id = antigo.id
        elif int(estoque_atualizado.id) != int(antigo.id):
            chave_nova = int(estoque_atualizado.id)
            if chave_nova in self._por_id:
                raise ValueError(f"Já existe outro estoque com ID {chave_nova}.")
            if chave_nova >= self._proximo_id:
                self._proximo_id = chave_nova + 1

        # Valida se o novo nome colide com outro registro
        chave_nome_nova = _normalizar(estoque_atualizado.reagente_nome)
        chave_nome_antiga = _normalizar(antigo.reagente_nome)
        if chave_nome_nova != chave_nome_antiga and chave_nome_nova in self._por_nome:
            raise ValueError(f"Já existe outro estoque com o nome '{estoque_atualizado.reagente_nome}'.")

        if self.collection is not None:
            doc = self._para_mongo(estoque_atualizado)
            filtro = (
                {"_id": int(antigo.id)}
                if antigo.id is not None
                else {"nome": {"$regex": f"^{re.escape(antigo.reagente_nome.strip())}$", "$options": "i"}}
            )
            self.collection.replace_one(filtro, doc, upsert=True)

        self._indexar(estoque_atualizado)
        return estoque_atualizado

    def delete(self, identificador: Union[int, str]) -> bool:
        """Exclui a visão de estoque consolidado pelo ID numérico ou pelo nome do reagente."""
        estoque = self.buscar_por_id(identificador) or self.buscar_por_nome(str(identificador))
        if not estoque:
            return False

        if self.collection is not None:
            if estoque.id is not None:
                self.collection.delete_one({"_id": int(estoque.id)})
            self.collection.delete_one({"nome": {"$regex": f"^{re.escape(estoque.reagente_nome.strip())}$", "$options": "i"}})

        self._desindexar(estoque)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[EstoqueReagente]:
        try:
            num = int(id_numerico)
            if num in self._por_id:
                return self._por_id[num]
            if self.collection is not None:
                doc = self.collection.find_one({"_id": num})
                if doc:
                    e = self._do_mongo(doc)
                    self._indexar(e)
                    return e
        except (ValueError, TypeError):
            pass
        return None

    def buscar_por_nome(self, nome: str) -> Optional[EstoqueReagente]:
        """Consulta estoque consolidado pela chave canônica do nome do reagente."""
        chave = _normalizar(nome)
        if not chave:
            return None
        if chave in self._por_nome:
            return self._por_nome[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"nome": {"$regex": f"^{re.escape(nome.strip())}$", "$options": "i"}})
            if doc:
                e = self._do_mongo(doc)
                self._indexar(e)
                return e
        return None

    def buscar_por_codigo(self, codigo: str) -> List[EstoqueReagente]:
        """Consulta registros de estoque que possuam o código de referência fornecido."""
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
                    e = self._do_mongo(d)
                    self._indexar(e)
                    res.append(e)
                except Exception:
                    pass
            return res
        return []

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        termo_busca: Optional[str] = None,
        apenas_com_lotes: Optional[bool] = None,
        ordenar_por: str = "nome",
        skip: int = 0,
        limit: int = 100,
    ) -> List[EstoqueReagente]:
        """Retorna lista de estoques aplicando busca textual, ordenação e paginação."""
        resultado_lista = list(self._por_nome.values())

        if apenas_com_lotes is not None:
            if apenas_com_lotes:
                resultado_lista = [e for e in resultado_lista if len(e.lotes) > 0]
            else:
                resultado_lista = [e for e in resultado_lista if len(e.lotes) == 0]

        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado_lista = [
                e for e in resultado_lista
                if (
                    termo in _normalizar(e.reagente_nome)
                    or (e.reagente_codigo and termo in _normalizar(e.reagente_codigo))
                    or any(termo in _normalizar(l.numero_lote) or termo in _normalizar(l.marca) for l in e.lotes)
                )
            ]

        # Ordenação
        if ordenar_por == "id":
            resultado_lista.sort(key=lambda e: (int(e.id) if e.id is not None else 0))
        elif ordenar_por == "quantidade":
            resultado_lista.sort(key=lambda e: e.quantidade_total_unidades, reverse=True)
        else:
            resultado_lista.sort(key=lambda e: e.reagente_nome.lower())

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
        """Retorna a quantidade total de tipos de reagentes com estoque registrado."""
        if self.collection is not None:
            try:
                c = self.collection.count_documents({})
                if c > 0:
                    return c
            except Exception:
                pass
        return len(self._por_nome)

    def contar(self) -> int:
        """Alias em português para count()."""
        return self.count()

    def exists(self, identificador: Union[int, str]) -> bool:
        """Verifica se existe um estoque registrado com o ID ou nome fornecido."""
        return self.buscar_por_id(identificador) is not None or self.buscar_por_nome(str(identificador)) is not None

    def clear(self) -> None:
        """Limpa todo o acervo de estoques agregados."""
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_nome.clear()
        self._por_codigo.clear()
        self._proximo_id = 1

estoque_reagente_repository = EstoqueReagenteRepository(use_mongo=True)