from typing import Optional, List, Dict, Union, Any
from src.models.Amostra import (
    Amostra,
    CondicaoArmazenamento,
    DestinoAmostra,
    FaseAmostra,
    MaterialBiologico,
    StatusAmostra,
)

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class AmostraRepository:
    """
    Repositório de persistência e acesso a dados da entidade Amostra.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover amostras no MongoDB (com cache indexado).
    """
    COLLECTION_NAME = "amostras"

    def __init__(
        self,
        amostras: Optional[List[Amostra]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, Amostra] = {}
        self._por_amostra_id: Dict[str, Amostra] = {}
        self._por_animal_id: Dict[str, List[Amostra]] = {}
        self._por_condicao_armazenamento: Dict[CondicaoArmazenamento, List[Amostra]] = {}
        self._por_destino_amostra: Dict[DestinoAmostra, List[Amostra]] = {}
        self._por_fase_amostra: Dict[FaseAmostra, List[Amostra]] = {}
        self._por_material_biologico: Dict[MaterialBiologico, List[Amostra]] = {}
        self._por_status_amostra: Dict[StatusAmostra, List[Amostra]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not amostras:
            self._carregar_do_banco()

        for amostra in amostras or []:
            self.create(amostra)

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

    def _do_mongo(self, doc: dict) -> Amostra:
        d = dict(doc)
        if "amostra_id" not in d and "_id" in d:
            d["amostra_id"] = str(d["_id"])
        if "_id" in d and not isinstance(d["_id"], int):
            if isinstance(d["_id"], str) and d["_id"].isdigit():
                d["_id"] = int(d["_id"])
            else:
                d["_id"] = None
        return Amostra(**d)

    def _para_mongo(self, amostra: Amostra) -> dict:
        doc = amostra.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "_id" not in doc and amostra.id is not None:
            doc["_id"] = int(amostra.id) if str(amostra.id).isdigit() else amostra.id
        return doc

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    am = self._do_mongo(doc)
                    self._indexar(am)
                    if am.id is not None and isinstance(am.id, int) and am.id >= self._proximo_id:
                        self._proximo_id = am.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, amostra: Amostra) -> None:
        chave_id = amostra.amostra_id.strip()
        self._por_amostra_id[chave_id] = amostra

        if amostra.id is not None and isinstance(amostra.id, int):
            self._por_id[amostra.id] = amostra

        if amostra.animal_id:
            chave_animal = amostra.animal_id.strip()
            self._por_animal_id.setdefault(chave_animal, []).append(amostra)

        if amostra.condicao_armazenamento:
            self._por_condicao_armazenamento.setdefault(amostra.condicao_armazenamento, []).append(amostra)
        if amostra.destino_amostra:
            self._por_destino_amostra.setdefault(amostra.destino_amostra, []).append(amostra)
        if amostra.fase_amostra:
            self._por_fase_amostra.setdefault(amostra.fase_amostra, []).append(amostra)
        if amostra.material_biologico:
            self._por_material_biologico.setdefault(amostra.material_biologico, []).append(amostra)
        if amostra.status_amostra:
            self._por_status_amostra.setdefault(amostra.status_amostra, []).append(amostra)

        if amostra.id is not None and isinstance(amostra.id, int) and amostra.id >= self._proximo_id:
            self._proximo_id = amostra.id + 1

    def _desindexar(self, amostra: Amostra) -> None:
        chave_id = amostra.amostra_id.strip()
        self._por_amostra_id.pop(chave_id, None)

        if amostra.id is not None and isinstance(amostra.id, int):
            self._por_id.pop(amostra.id, None)

        if amostra.animal_id:
            chave_animal = amostra.animal_id.strip()
            if amostra in self._por_animal_id.get(chave_animal, []):
                self._por_animal_id[chave_animal].remove(amostra)

        if amostra.condicao_armazenamento in self._por_condicao_armazenamento:
            if amostra in self._por_condicao_armazenamento[amostra.condicao_armazenamento]:
                self._por_condicao_armazenamento[amostra.condicao_armazenamento].remove(amostra)

        if amostra.destino_amostra in self._por_destino_amostra:
            if amostra in self._por_destino_amostra[amostra.destino_amostra]:
                self._por_destino_amostra[amostra.destino_amostra].remove(amostra)

        if amostra.fase_amostra in self._por_fase_amostra:
            if amostra in self._por_fase_amostra[amostra.fase_amostra]:
                self._por_fase_amostra[amostra.fase_amostra].remove(amostra)

        if amostra.material_biologico in self._por_material_biologico:
            if amostra in self._por_material_biologico[amostra.material_biologico]:
                self._por_material_biologico[amostra.material_biologico].remove(amostra)

        if amostra.status_amostra in self._por_status_amostra:
            if amostra in self._por_status_amostra[amostra.status_amostra]:
                self._por_status_amostra[amostra.status_amostra].remove(amostra)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, amostra: Amostra) -> Amostra:
        if not amostra.amostra_id:
            raise ValueError("O identificador único da amostra (amostra_id) é obrigatório.")

        chave_id = amostra.amostra_id.strip()
        if chave_id in self._por_amostra_id or (
            self.collection is not None and self.collection.count_documents({"amostra_id": chave_id}) > 0
        ):
            raise ValueError(f"Amostra com ID '{chave_id}' já está cadastrada.")

        if amostra.id is None:
            if self.collection is not None:
                try:
                    doc_max = self.collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
                    max_id = int(doc_max["_id"]) if doc_max and isinstance(doc_max.get("_id"), (int, float)) else 0
                    amostra.id = max(max_id + 1, self._proximo_id)
                except Exception:
                    amostra.id = self._proximo_id
            else:
                amostra.id = self._proximo_id
            self._proximo_id = amostra.id + 1
        elif isinstance(amostra.id, int) and amostra.id >= self._proximo_id:
            self._proximo_id = amostra.id + 1

        if self.collection is not None:
            doc = self._para_mongo(amostra)
            self.collection.insert_one(doc)

        self._indexar(amostra)
        return amostra

    def save(self, amostra: Amostra) -> Amostra:
        chave = amostra.amostra_id.strip()
        if self.exists(chave):
            return self.update(chave, amostra)
        return self.create(amostra)

    def update(self, amostra_id: str, amostra_atualizada: Amostra) -> Amostra:
        chave = amostra_id.strip()
        if not self.exists(chave):
            raise KeyError(f"Amostra com ID '{chave}' não encontrada.")

        amostra_antiga = self._por_amostra_id.get(chave)
        if not amostra_antiga and self.collection is not None:
            doc = self.collection.find_one({"amostra_id": chave})
            if doc:
                amostra_antiga = self._do_mongo(doc)

        if amostra_antiga and amostra_antiga.amostra_id != amostra_atualizada.amostra_id:
            raise ValueError("Não é permitido alterar o identificador único da amostra.")

        if amostra_antiga:
            self._desindexar(amostra_antiga)
            if amostra_atualizada.id is None:
                amostra_atualizada.id = amostra_antiga.id
            elif amostra_atualizada.id != amostra_antiga.id:
                if amostra_atualizada.id in self._por_id:
                    raise ValueError(f"Já existe uma amostra com o ID '{amostra_atualizada.id}'.")
                if isinstance(amostra_atualizada.id, int) and amostra_atualizada.id >= self._proximo_id:
                    self._proximo_id = amostra_atualizada.id + 1

        if self.collection is not None:
            doc = self._para_mongo(amostra_atualizada)
            self.collection.replace_one({"amostra_id": chave}, doc, upsert=True)

        self._indexar(amostra_atualizada)
        return amostra_atualizada

    def delete(self, amostra_id: str) -> bool:
        chave = amostra_id.strip()
        existe_mem = chave in self._por_amostra_id
        existe_banco = False

        if self.collection is not None:
            res = self.collection.delete_one({"amostra_id": chave})
            existe_banco = res.deleted_count > 0

        if not existe_mem and not existe_banco:
            return False

        if existe_mem:
            amostra = self._por_amostra_id[chave]
            self._desindexar(amostra)

        return True

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        animal_id: Optional[str] = None,
        status_amostra: Optional[StatusAmostra] = None,
        fase_amostra: Optional[FaseAmostra] = None,
        condicao_armazenamento: Optional[CondicaoArmazenamento] = None,
        destino_amostra: Optional[DestinoAmostra] = None,
        material_biologico: Optional[MaterialBiologico] = None,
        ordenar_por: str = 'id',
        skip: int = 0,
        limit: int = 100,
    ) -> List[Amostra]:
        resultado = list(self._por_amostra_id.values())

        # Aplicação de Filtros
        if animal_id:
            chave_animal = animal_id.strip()
            resultado = [a for a in resultado if a.animal_id and a.animal_id.strip() == chave_animal]
        if status_amostra:
            resultado = [a for a in resultado if a.status_amostra == status_amostra]
        if fase_amostra:
            resultado = [a for a in resultado if a.fase_amostra == fase_amostra]
        if condicao_armazenamento:
            resultado = [a for a in resultado if a.condicao_armazenamento == condicao_armazenamento]
        if destino_amostra:
            resultado = [a for a in resultado if a.destino_amostra == destino_amostra]
        if material_biologico:
            resultado = [a for a in resultado if a.material_biologico == material_biologico]

        # Paginação
        if skip > 0:
            resultado = resultado[skip:]
        if limit is not None and limit > 0:
            resultado = resultado[:limit]

        return resultado

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Amostra]:
        try:
            num = int(id_numerico)
            if num in self._por_id:
                return self._por_id[num]
            if self.collection is not None:
                doc = self.collection.find_one({"_id": num})
                if doc:
                    am = self._do_mongo(doc)
                    self._indexar(am)
                    return am
        except (ValueError, TypeError):
            pass
        return None

    def buscar_por_amostra_id(self, amostra_id: str) -> Optional[Amostra]:
        if not amostra_id:
            return None
        chave = amostra_id.strip()
        if chave in self._por_amostra_id:
            return self._por_amostra_id[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"amostra_id": chave})
            if doc:
                am = self._do_mongo(doc)
                self._indexar(am)
                return am
        return None

    def buscar_por_animal_id(self, animal_id: str) -> List[Amostra]:
        if not animal_id:
            return []
        chave = animal_id.strip()
        if chave in self._por_animal_id:
            return list(self._por_animal_id[chave])
        if self.collection is not None:
            docs = self.collection.find({"animal_id": chave})
            res = []
            for d in docs:
                try:
                    am = self._do_mongo(d)
                    self._indexar(am)
                    res.append(am)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_condicao_armazenamento(self, condicao_armazenamento: CondicaoArmazenamento) -> List[Amostra]:
        return list(self._por_condicao_armazenamento.get(condicao_armazenamento, []))

    def buscar_por_destino_amostra(self, destino_amostra: DestinoAmostra) -> List[Amostra]:
        return list(self._por_destino_amostra.get(destino_amostra, []))

    def buscar_por_fase_amostra(self, fase_amostra: FaseAmostra) -> List[Amostra]:
        return list(self._por_fase_amostra.get(fase_amostra, []))

    def buscar_por_material_biologico(self, material_biologico: MaterialBiologico) -> List[Amostra]:
        return list(self._por_material_biologico.get(material_biologico, []))

    def buscar_por_status_amostra(self, status_amostra: StatusAmostra) -> List[Amostra]:
        return list(self._por_status_amostra.get(status_amostra, []))

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
        return len(self._por_amostra_id)

    def exists(self, amostra_id: str) -> bool:
        if not amostra_id:
            return False
        chave = amostra_id.strip()
        if chave in self._por_amostra_id:
            return True
        if self.collection is not None:
            return self.collection.count_documents({"amostra_id": chave}) > 0
        return False

    def clear(self) -> None:
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_amostra_id.clear()
        self._por_animal_id.clear()
        self._por_condicao_armazenamento.clear()
        self._por_destino_amostra.clear()
        self._por_fase_amostra.clear()
        self._por_material_biologico.clear()
        self._por_status_amostra.clear()
        self._proximo_id = 1

amostra_repository = AmostraRepository(use_mongo=True)