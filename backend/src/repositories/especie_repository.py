import re
from typing import Optional, List, Dict, Union, Any
from src.models.Especie import Especie, Classe
from src.utils.repositorio import (
    _normalizar,
    sanitizar_id_filtro,
    gerar_proximo_id_mongo,
    doc_para_mongo,
    preparar_doc_mongo,
)

class EspecieRepository:
    """
    Repositório de persistência e acesso a dados da entidade Especie.
    Responsabilidade exclusiva:
    - Armazenar, consultar, atualizar e remover espécies no MongoDB (com suporte a cache indexado em memória).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - Chaves primárias (id/_id) são gerenciadas e geradas exclusivamente pela camada de persistência.
    """
    COLLECTION_NAME = "especies"

    def __init__(
        self,
        especies: Optional[List[Especie]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[Union[int, str], Especie] = {}
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
        d = preparar_doc_mongo(doc)
        return Especie(**d)

    def _para_mongo(self, especie: Especie) -> dict:
        return doc_para_mongo(especie)

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
                    esp = self._do_mongo(doc)
                    self._indexar(esp)
                    if esp.id is not None and isinstance(esp.id, int) and esp.id >= self._proximo_id:
                        self._proximo_id = esp.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    def _indexar(self, especie: Especie) -> None:
        filtro_id = sanitizar_id_filtro(especie.id)
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
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

        if isinstance(filtro_id, int) and filtro_id >= self._proximo_id:
            self._proximo_id = filtro_id + 1

    def create(self, especie: Especie) -> Especie:
        """
        Persiste um novo registro de espécie no banco de dados MongoDB.
        A chave primária (id/_id) é SEMPRE gerada pela camada de persistência;
        qualquer valor pré-existente no objeto é descartado (conforme animal e amostra).
        """
        especie.id = self._gerar_proximo_id()

        filtro_id = sanitizar_id_filtro(especie.id)
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
            filtro_id = sanitizar_id_filtro(especie.id)
            if self.exists(filtro_id):
                return self.update(filtro_id, especie)
        return self.create(especie)

    def update(self, id_especie: Union[int, str], especie_atualizada: Especie) -> Especie:
        """Atualiza os dados de uma espécie persistida e sincroniza os índices."""
        filtro_id = sanitizar_id_filtro(id_especie)
        chave_id = filtro_id if isinstance(filtro_id, int) else hash(filtro_id)
        if not self.exists(filtro_id):
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
        filtro_id = sanitizar_id_filtro(id_especie)
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
        filtro_id = sanitizar_id_filtro(id_especie)
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
        filtro_id = sanitizar_id_filtro(id_especie)
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

__all__ = ["EspecieRepository", "especie_repository"]