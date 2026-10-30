import re
from typing import Optional, List, Dict, Union, Any
from src.models.Especie import Especie, Classe

def _normalizar(texto: str) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class EspecieRepository:
    """
    Repositório de persistência e acesso a dados da entidade Especie.
    Responsabilidade exclusiva:
    - Armazenar, consultar, atualizar e remover espécies no MongoDB (com suporte a cache indexado em memória).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - NÃO contém regras de negócio, validações taxonômicas ou parsing de arquivos.
    """
    COLLECTION_NAME = "especies"

    def __init__(
        self,
        especies: Optional[List[Especie]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, Especie] = {}
        self._por_comum: Dict[str, Especie] = {}
        self._por_cientifico: Dict[str, Especie] = {}
        self._por_classe: Dict[Classe, List[Especie]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not especies:
            self._carregar_do_banco()

        for especie in especies or []:
            self.create(especie)

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

    def _do_mongo(self, doc: dict) -> Especie:
        d = dict(doc)
        if "_id" in d and not isinstance(d["_id"], int):
            if isinstance(d["_id"], str) and d["_id"].isdigit():
                d["_id"] = int(d["_id"])
        return Especie(**d)

    def _para_mongo(self, especie: Especie) -> dict:
        doc = especie.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "_id" not in doc and especie.id is not None:
            doc["_id"] = int(especie.id) if str(especie.id).isdigit() else especie.id
        return doc

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    esp = self._do_mongo(doc)
                    self._indexar(esp)
                    if esp.id is not None and isinstance(esp.id, int) and esp.id >= self._proximo_id:
                        self._proximo_id = esp.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    def _indexar(self, especie: Especie) -> None:
        chave_id = int(especie.id) if str(especie.id).isdigit() else hash(especie.id)
        chave_comum = _normalizar(especie.nome_comum)
        chave_cient = _normalizar(especie.nome_cientifico)
        chave_classe = especie.classe

        self._por_id[chave_id] = especie
        if chave_comum:
            self._por_comum[chave_comum] = especie
        if chave_cient:
            self._por_cientifico[chave_cient] = especie

        if chave_classe not in self._por_classe:
            self._por_classe[chave_classe] = []
        if especie not in self._por_classe[chave_classe]:
            self._por_classe[chave_classe].append(especie)

        if isinstance(chave_id, int) and chave_id >= self._proximo_id:
            self._proximo_id = chave_id + 1

    def create(self, especie: Especie) -> Especie:
        """Persiste um novo registro de espécie no banco de dados MongoDB."""
        if especie.id is None:
            if self.collection is not None:
                try:
                    doc_max = self.collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
                    max_id = int(doc_max["_id"]) if doc_max and isinstance(doc_max.get("_id"), (int, float)) else 0
                    especie.id = max(max_id + 1, self._proximo_id)
                except Exception:
                    especie.id = self._proximo_id
            else:
                especie.id = self._proximo_id
            self._proximo_id = int(especie.id) + 1

        filtro_id = int(especie.id) if str(especie.id).isdigit() else especie.id
        especie.id = filtro_id
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
        if chave_id in self._por_id or (self.collection is not None and self.collection.count_documents({"_id": filtro_id}) > 0):
            raise ValueError(f"Registro com ID {especie.id} já existe no banco de dados.")

        if self.collection is not None:
            doc = self._para_mongo(especie)
            self.collection.insert_one(doc)

        self._indexar(especie)
        return especie

    def save(self, especie: Especie) -> Especie:
        """Alias para persistir a espécie (create ou update se já possuir ID cadastrado)."""
        if especie.id is not None:
            try:
                filtro_id = int(especie.id) if str(especie.id).isdigit() else especie.id
                chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
                if chave_id in self._por_id or (self.collection is not None and self.collection.count_documents({"_id": filtro_id}) > 0):
                    return self.update(filtro_id, especie)
            except (ValueError, TypeError):
                pass
        return self.create(especie)

    def update(self, id_especie: Union[int, str], especie_atualizada: Especie) -> Especie:
        """Atualiza os dados de uma espécie persistida e sincroniza os índices."""
        filtro_id = int(id_especie) if str(id_especie).isdigit() else id_especie
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
        if chave_id not in self._por_id and (self.collection is None or self.collection.count_documents({"_id": filtro_id}) == 0):
            raise KeyError(f"Espécie com ID {id_especie} não encontrada no banco de dados.")

        antiga = self._por_id.get(chave_id)
        if not antiga and self.collection is not None:
            doc = self.collection.find_one({"_id": filtro_id})
            if doc:
                antiga = self._do_mongo(doc)

        if antiga:
            chave_comum_antiga = _normalizar(antiga.nome_comum)
            chave_cient_antiga = _normalizar(antiga.nome_cientifico)
            self._por_comum.pop(chave_comum_antiga, None)
            self._por_cientifico.pop(chave_cient_antiga, None)

            if antiga.classe in self._por_classe and antiga in self._por_classe[antiga.classe]:
                self._por_classe[antiga.classe].remove(antiga)

        especie_atualizada.id = filtro_id
        if self.collection is not None:
            doc = self._para_mongo(especie_atualizada)
            self.collection.replace_one({"_id": filtro_id}, doc, upsert=False)

        self._indexar(especie_atualizada)
        return especie_atualizada

    def buscar_por_id(self, id_especie: Union[int, str]) -> Optional[Especie]:
        """Recupera o registro pela chave primária ID."""
        filtro_id = int(id_especie) if str(id_especie).isdigit() else id_especie
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
        if chave_id in self._por_id:
            return self._por_id[chave_id]
        if self.collection is not None:
            doc = self.collection.find_one({"_id": filtro_id})
            if doc:
                esp = self._do_mongo(doc)
                self._indexar(esp)
                return esp
        return None

    def buscar_por_nome_comum(self, nome_comum: str) -> Optional[Especie]:
        """Consulta registro por índice de nome comum."""
        if not nome_comum:
            return None
        norm = _normalizar(nome_comum)
        if norm in self._por_comum:
            return self._por_comum[norm]
        if self.collection is not None:
            doc = self.collection.find_one({"nome": {"$regex": f"^{re.escape(nome_comum.strip())}$", "$options": "i"}})
            if doc:
                esp = self._do_mongo(doc)
                self._indexar(esp)
                return esp
        return None

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> Optional[Especie]:
        """Consulta registro por índice de nome científico."""
        if not nome_cientifico:
            return None
        norm = _normalizar(nome_cientifico)
        if norm in self._por_cientifico:
            return self._por_cientifico[norm]
        if self.collection is not None:
            doc = self.collection.find_one({"nome_cientifico": {"$regex": f"^{re.escape(nome_cientifico.strip())}$", "$options": "i"}})
            if doc:
                esp = self._do_mongo(doc)
                self._indexar(esp)
                return esp
        return None

    def buscar_por_classe(self, classe: Union[Classe, str]) -> List[Especie]:
        """Consulta registros pelo índice de classe taxonômica."""
        if not classe:
            return []
        if isinstance(classe, Classe):
            if classe in self._por_classe:
                return list(self._por_classe.get(classe, []))
            alvo = classe.value
        else:
            alvo = str(classe).strip()
            for c in self._por_classe:
                if c.value.lower() == alvo.lower():
                    return list(self._por_classe.get(c, []))

        if self.collection is not None:
            docs = self.collection.find({"classe": {"$regex": f"^{re.escape(alvo)}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    esp = self._do_mongo(d)
                    self._indexar(esp)
                    res.append(esp)
                except Exception:
                    pass
            return res
        return []

    def listar(self) -> List[Especie]:
        """Retorna todos os registros armazenados ordenados por ID."""
        if self.collection is not None:
            docs = self.collection.find().sort("_id", 1)
            res = []
            for d in docs:
                try:
                    esp = self._do_mongo(d)
                    self._indexar(esp)
                    res.append(esp)
                except Exception:
                    pass
            if res:
                return res
        return sorted(self._por_id.values(), key=lambda e: (int(e.id) if str(e.id).isdigit() else 0))

    def delete(self, id_especie: Union[int, str]) -> bool:
        """Exclui o registro do banco de dados pelo ID."""
        filtro_id = int(id_especie) if str(id_especie).isdigit() else id_especie
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)

        if chave_id not in self._por_id and self.collection is not None:
            doc = self.collection.find_one({"_id": filtro_id})
            if doc:
                esp_loaded = self._do_mongo(doc)
                self._indexar(esp_loaded)

        existe_mem = chave_id in self._por_id
        existe_banco = False

        if self.collection is not None:
            res = self.collection.delete_one({"_id": filtro_id})
            existe_banco = res.deleted_count > 0

        if not existe_mem and not existe_banco:
            return False

        if existe_mem:
            esp = self._por_id.pop(chave_id, None)
            if esp:
                self._por_comum.pop(_normalizar(esp.nome_comum), None)
                self._por_cientifico.pop(_normalizar(esp.nome_cientifico), None)
                if esp.classe in self._por_classe and esp in self._por_classe[esp.classe]:
                    self._por_classe[esp.classe].remove(esp)

        return True

    def count(self) -> int:
        """Retorna a contagem de registros armazenados."""
        if self.collection is not None:
            try:
                return self.collection.count_documents({})
            except Exception:
                pass
        return len(self._por_id)

    def exists(self, id_especie: Union[int, str]) -> bool:
        """Verifica se existe registro com o ID fornecido."""
        filtro_id = int(id_especie) if str(id_especie).isdigit() else id_especie
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
        if chave_id in self._por_id:
            return True
        if self.collection is not None:
            return self.collection.count_documents({"_id": filtro_id}) > 0
        return False

    def clear(self) -> None:
        """Limpa todo o armazenamento do banco de dados."""
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_comum.clear()
        self._por_cientifico.clear()
        self._por_id.clear()
        self._por_classe.clear()
        self._proximo_id = 1

especie_repository = EspecieRepository(use_mongo=True)