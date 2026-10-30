import re
from typing import Optional, List, Dict, Union, Any
from src.models.Animal import (
    Animal,
    Sexo,
    RegimeVida,
    StatusVital,
    Orgao,
    Funcao,
    FaixaEtaria,
    UnidadePeso,
    UnidadeIdade,
)
from src.models.Especie import Classe

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class AnimalRepository:
    """
    Repositório de persistência e acesso a dados da entidade Animal.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover animais no banco de dados MongoDB (com cache indexado).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - NÃO contém regras de negócio, validações taxonômicas, biometria ou parsing de arquivos.
    """
    COLLECTION_NAME = "animais"

    def __init__(
        self,
        animais: Optional[List[Animal]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[int, Animal] = {}
        self._por_animal_id: Dict[str, Animal] = {}
        self._por_projeto_id: Dict[str, List[Animal]] = {}
        self._por_microchip: Dict[str, Animal] = {}
        self._por_nome_comum: Dict[str, List[Animal]] = {}
        self._por_nome_cientifico: Dict[str, List[Animal]] = {}
        self._por_classe: Dict[Classe, List[Animal]] = {}
        self._por_sexo: Dict[Sexo, List[Animal]] = {}
        self._por_faixa_etaria: Dict[FaixaEtaria, List[Animal]] = {}
        self._por_orgao_origem: Dict[Orgao, List[Animal]] = {}
        self._por_regime_vida: Dict[RegimeVida, List[Animal]] = {}
        self._por_status_vital: Dict[StatusVital, List[Animal]] = {}
        self._por_funcao: Dict[Funcao, List[Animal]] = {}
        self._por_peso_unidade: Dict[UnidadePeso, List[Animal]] = {}
        self._por_idade_unidade: Dict[UnidadeIdade, List[Animal]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not animais:
            self._carregar_do_banco()

        for animal in animais or []:
            self.create(animal)

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

    def _do_mongo(self, doc: dict) -> Animal:
        d = dict(doc)
        if "animal_id" not in d and "_id" in d:
            d["animal_id"] = str(d["_id"])
        if "_id" in d and not isinstance(d["_id"], int):
            if isinstance(d["_id"], str) and d["_id"].isdigit():
                d["_id"] = int(d["_id"])
            else:
                d["_id"] = None
        return Animal(**d)

    def _para_mongo(self, animal: Animal) -> dict:
        doc = animal.model_dump(mode="json", by_alias=True, exclude_none=True)
        if "_id" not in doc and animal.id is not None:
            doc["_id"] = int(animal.id) if str(animal.id).isdigit() else animal.id
        return doc

    def _carregar_do_banco(self) -> None:
        if self.collection is None:
            return
        try:
            for doc in self.collection.find():
                try:
                    a = self._do_mongo(doc)
                    self._indexar(a)
                    if a.id is not None and isinstance(a.id, int) and a.id >= self._proximo_id:
                        self._proximo_id = a.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------

    def _indexar(self, animal: Animal) -> None:
        chave_lab = animal.animal_id.strip()
        self._por_animal_id[chave_lab] = animal

        if animal.id is not None and isinstance(animal.id, int):
            self._por_id[animal.id] = animal

        if animal.animal_id_projeto:
            chave_proj = animal.animal_id_projeto.strip()
            self._por_projeto_id.setdefault(chave_proj, []).append(animal)

        if animal.microchip:
            self._por_microchip[animal.microchip.strip()] = animal

        norm_comum = _normalizar(animal.nome_comum)
        if norm_comum:
            self._por_nome_comum.setdefault(norm_comum, []).append(animal)

        norm_cient = _normalizar(animal.nome_cientifico)
        if norm_cient:
            self._por_nome_cientifico.setdefault(norm_cient, []).append(animal)

        self._por_classe.setdefault(animal.classe, []).append(animal)
        self._por_sexo.setdefault(animal.sexo, []).append(animal)
        self._por_faixa_etaria.setdefault(animal.faixa_etaria, []).append(animal)
        self._por_orgao_origem.setdefault(animal.orgao_origem, []).append(animal)
        self._por_regime_vida.setdefault(animal.regime_vida, []).append(animal)
        self._por_status_vital.setdefault(animal.status_vital, []).append(animal)
        if animal.funcao:
            self._por_funcao.setdefault(animal.funcao, []).append(animal)
        if animal.peso_unidade:
            self._por_peso_unidade.setdefault(animal.peso_unidade, []).append(animal)
        if animal.idade_unidade:
            self._por_idade_unidade.setdefault(animal.idade_unidade, []).append(animal)

        if animal.id is not None and isinstance(animal.id, int) and animal.id >= self._proximo_id:
            self._proximo_id = animal.id + 1

    def _desindexar(self, animal: Animal) -> None:
        chave_lab = animal.animal_id.strip()
        self._por_animal_id.pop(chave_lab, None)

        if animal.id is not None and isinstance(animal.id, int):
            self._por_id.pop(animal.id, None)

        if animal.animal_id_projeto:
            chave_proj = animal.animal_id_projeto.strip()
            if animal in self._por_projeto_id.get(chave_proj, []):
                self._por_projeto_id[chave_proj].remove(animal)

        if animal.microchip:
            self._por_microchip.pop(animal.microchip.strip(), None)

        norm_comum = _normalizar(animal.nome_comum)
        if norm_comum and animal in self._por_nome_comum.get(norm_comum, []):
            self._por_nome_comum[norm_comum].remove(animal)

        norm_cient = _normalizar(animal.nome_cientifico)
        if norm_cient and animal in self._por_nome_cientifico.get(norm_cient, []):
            self._por_nome_cientifico[norm_cient].remove(animal)

        colecoes = [
            self._por_classe.get(animal.classe),
            self._por_sexo.get(animal.sexo),
            self._por_faixa_etaria.get(animal.faixa_etaria),
            self._por_orgao_origem.get(animal.orgao_origem),
            self._por_regime_vida.get(animal.regime_vida),
            self._por_status_vital.get(animal.status_vital),
            self._por_funcao.get(animal.funcao) if animal.funcao else None,
            self._por_peso_unidade.get(animal.peso_unidade) if animal.peso_unidade else None,
            self._por_idade_unidade.get(animal.idade_unidade) if animal.idade_unidade else None,
        ]
        for lista in colecoes:
            if lista and animal in lista:
                lista.remove(animal)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------

    def create(self, animal: Animal) -> Animal:
        if not animal.animal_id:
            raise ValueError("O identificador único do animal (animal_id) é obrigatório.")

        chave_id = animal.animal_id.strip()
        if chave_id in self._por_animal_id or (
            self.collection is not None and self.collection.count_documents({"animal_id": chave_id}) > 0
        ):
            raise ValueError(f"Animal com ID '{chave_id}' já está cadastrado.")

        if animal.id is None:
            if self.collection is not None:
                try:
                    doc_max = self.collection.find_one({"_id": {"$type": "number"}}, sort=[("_id", -1)])
                    max_id = int(doc_max["_id"]) if doc_max and isinstance(doc_max.get("_id"), (int, float)) else 0
                    animal.id = max(max_id + 1, self._proximo_id)
                except Exception:
                    animal.id = self._proximo_id
            else:
                animal.id = self._proximo_id
            self._proximo_id = animal.id + 1
        elif isinstance(animal.id, int) and animal.id >= self._proximo_id:
            self._proximo_id = animal.id + 1

        if self.collection is not None:
            doc = self._para_mongo(animal)
            self.collection.insert_one(doc)

        self._indexar(animal)
        return animal

    def save(self, animal: Animal) -> Animal:
        chave = animal.animal_id.strip()
        if self.exists(chave):
            return self.update(chave, animal)
        return self.create(animal)

    def update(self, animal_id: str, animal_atualizado: Animal) -> Animal:
        chave = animal_id.strip()
        if not self.exists(chave):
            raise KeyError(f"Animal com ID '{chave}' não encontrado para atualização.")

        antigo = self._por_animal_id.get(chave)
        if not antigo and self.collection is not None:
            doc = self.collection.find_one({"animal_id": chave})
            if doc:
                antigo = self._do_mongo(doc)

        if antigo:
            self._desindexar(antigo)
            if animal_atualizado.id is None and antigo.id is not None:
                animal_atualizado.id = antigo.id

        animal_atualizado.animal_id = chave

        if self.collection is not None:
            doc = self._para_mongo(animal_atualizado)
            self.collection.replace_one({"animal_id": chave}, doc, upsert=True)

        self._indexar(animal_atualizado)
        return animal_atualizado

    def delete(self, animal_id: str) -> bool:
        chave = animal_id.strip()
        if not self.exists(chave):
            raise KeyError(f"Animal com ID '{chave}' não encontrado para exclusão.")

        antigo = self._por_animal_id.get(chave)
        if not antigo and self.collection is not None:
            doc = self.collection.find_one({"animal_id": chave})
            if doc:
                antigo = self._do_mongo(doc)

        if self.collection is not None:
            self.collection.delete_one({"animal_id": chave})

        if antigo:
            self._desindexar(antigo)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------

    def buscar_por_animal_id(self, animal_id: str) -> Optional[Animal]:
        if not animal_id:
            return None
        chave = animal_id.strip()
        if chave in self._por_animal_id:
            return self._por_animal_id[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"animal_id": chave})
            if doc:
                a = self._do_mongo(doc)
                self._indexar(a)
                return a
        return None

    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Animal]:
        try:
            num = int(id_numerico)
            if num in self._por_id:
                return self._por_id[num]
            if self.collection is not None:
                doc = self.collection.find_one({"_id": num})
                if doc:
                    a = self._do_mongo(doc)
                    self._indexar(a)
                    return a
        except (ValueError, TypeError):
            pass
        return None

    def buscar_por_projeto_id(self, projeto_id: str) -> List[Animal]:
        if not projeto_id:
            return []
        chave = projeto_id.strip()
        if chave in self._por_projeto_id:
            return list(self._por_projeto_id[chave])
        if self.collection is not None:
            docs = self.collection.find({"animal_id_projeto": {"$regex": f"^{re.escape(chave)}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    a = self._do_mongo(d)
                    self._indexar(a)
                    res.append(a)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_microchip(self, microchip: str) -> Optional[Animal]:
        if not microchip:
            return None
        chave = microchip.strip()
        if chave in self._por_microchip:
            return self._por_microchip[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"microchip": chave})
            if doc:
                a = self._do_mongo(doc)
                self._indexar(a)
                return a
        return None

    def buscar_por_nome_comum(self, nome_comum: str) -> List[Animal]:
        if not nome_comum:
            return []
        chave = _normalizar(nome_comum)
        if chave in self._por_nome_comum:
            return list(self._por_nome_comum[chave])
        if self.collection is not None:
            docs = self.collection.find({"nome_comum": {"$regex": f"^{re.escape(nome_comum.strip())}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    a = self._do_mongo(d)
                    self._indexar(a)
                    res.append(a)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> List[Animal]:
        if not nome_cientifico:
            return []
        chave = _normalizar(nome_cientifico)
        if chave in self._por_nome_cientifico:
            return list(self._por_nome_cientifico[chave])
        if self.collection is not None:
            docs = self.collection.find({"nome_cientifico": {"$regex": f"^{re.escape(nome_cientifico.strip())}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    a = self._do_mongo(d)
                    self._indexar(a)
                    res.append(a)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_classe(self, classe: Union[Classe, str]) -> List[Animal]:
        if not classe:
            return []
        if isinstance(classe, Classe) and classe in self._por_classe:
            return list(self._por_classe[classe])
        alvo = classe.value if isinstance(classe, Classe) else str(classe).strip()
        for c in self._por_classe:
            if c.value.lower() == alvo.lower():
                return list(self._por_classe[c])
        if self.collection is not None:
            docs = self.collection.find({"classe": {"$regex": f"^{re.escape(alvo)}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    a = self._do_mongo(d)
                    self._indexar(a)
                    res.append(a)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_sexo(self, sexo: Sexo) -> List[Animal]:
        if sexo in self._por_sexo:
            return list(self._por_sexo[sexo])
        if self.collection is not None:
            val = sexo.value if isinstance(sexo, Sexo) else str(sexo)
            docs = self.collection.find({"sexo": val})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_faixa_etaria(self, faixa_etaria: FaixaEtaria) -> List[Animal]:
        if faixa_etaria in self._por_faixa_etaria:
            return list(self._por_faixa_etaria[faixa_etaria])
        if self.collection is not None:
            val = faixa_etaria.value if isinstance(faixa_etaria, FaixaEtaria) else str(faixa_etaria)
            docs = self.collection.find({"faixa_etaria": val})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_orgao_origem(self, orgao_origem: Orgao) -> List[Animal]:
        if orgao_origem in self._por_orgao_origem:
            return list(self._por_orgao_origem[orgao_origem])
        if self.collection is not None:
            val = orgao_origem.value if isinstance(orgao_origem, Orgao) else str(orgao_origem)
            docs = self.collection.find({"$or": [{"orgao": val}, {"orgao_origem": val}]})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_local_origem(self, local_origem: str) -> List[Animal]:
        if not local_origem:
            return []
        norm = _normalizar(local_origem)
        locais = [a for a in self._por_animal_id.values() if _normalizar(a.local_origem) == norm]
        if locais:
            return locais
        if self.collection is not None:
            docs = self.collection.find({"local_origem": {"$regex": f"^{re.escape(local_origem.strip())}$", "$options": "i"}})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_regime_vida(self, regime_vida: RegimeVida) -> List[Animal]:
        if regime_vida in self._por_regime_vida:
            return list(self._por_regime_vida[regime_vida])
        if self.collection is not None:
            val = regime_vida.value if isinstance(regime_vida, RegimeVida) else str(regime_vida)
            docs = self.collection.find({"$or": [{"status": val}, {"regime_vida": val}]})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_status_vital(self, status_vital: StatusVital) -> List[Animal]:
        if status_vital in self._por_status_vital:
            return list(self._por_status_vital[status_vital])
        if self.collection is not None:
            val = status_vital.value if isinstance(status_vital, StatusVital) else str(status_vital)
            docs = self.collection.find({"status_vital": val})
            return [self._do_mongo(d) for d in docs]
        return []

    def buscar_por_funcao(self, funcao: Funcao) -> List[Animal]:
        return list(self._por_funcao.get(funcao, []))

    def buscar_por_unidade_peso(self, unidade_peso: UnidadePeso) -> List[Animal]:
        return list(self._por_peso_unidade.get(unidade_peso, []))

    def buscar_por_unidade_idade(self, unidade_idade: UnidadeIdade) -> List[Animal]:
        return list(self._por_idade_unidade.get(unidade_idade, []))

    def buscar_por_faixa_peso(
        self,
        min_kg: Optional[float] = None,
        max_kg: Optional[float] = None,
    ) -> List[Animal]:
        resultado = []
        for a in self._por_animal_id.values():
            if isinstance(a.peso, (int, float)):
                if min_kg is not None and a.peso < min_kg:
                    continue
                if max_kg is not None and a.peso > max_kg:
                    continue
                resultado.append(a)
        return resultado

    def buscar_por_especie(
        self,
        nome_comum: Optional[str] = None,
        nome_cientifico: Optional[str] = None,
    ) -> List[Animal]:
        norm_comum = _normalizar(nome_comum) if nome_comum else None
        norm_cient = _normalizar(nome_cientifico) if nome_cientifico else None

        resultado = []
        for a in self._por_animal_id.values():
            if norm_comum and _normalizar(a.nome_comum) == norm_comum:
                resultado.append(a)
            elif norm_cient and _normalizar(a.nome_cientifico) == norm_cient:
                resultado.append(a)
        return resultado

    def listar(
        self,
        classe: Optional[Classe] = None,
        sexo: Optional[Sexo] = None,
        regime_vida: Optional[RegimeVida] = None,
        status_vital: Optional[StatusVital] = None,
        termo_busca: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Animal]:
        resultado = list(self._por_animal_id.values())

        if classe:
            resultado = [a for a in resultado if a.classe == classe]
        if sexo:
            resultado = [a for a in resultado if a.sexo == sexo]
        if regime_vida:
            resultado = [a for a in resultado if a.regime_vida == regime_vida]
        if status_vital:
            resultado = [a for a in resultado if a.status_vital == status_vital]
        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado = [
                a for a in resultado
                if termo in _normalizar(a.animal_id)
                or termo in _normalizar(a.nome_comum)
                or termo in _normalizar(a.nome_cientifico)
                or termo in _normalizar(a.local_origem)
                or (a.animal_id_projeto and termo in _normalizar(a.animal_id_projeto))
                or (a.microchip and termo in _normalizar(a.microchip))
            ]

        resultado.sort(key=lambda a: (a.id or 0, a.animal_id))

        if skip > 0:
            resultado = resultado[skip:]
        if limit is not None and limit > 0:
            resultado = resultado[:limit]

        return resultado

    def count(self) -> int:
        if self.collection is not None:
            try:
                c = self.collection.count_documents({})
                if c > 0:
                    return c
            except Exception:
                pass
        return len(self._por_animal_id)

    def exists(self, animal_id: str) -> bool:
        if not animal_id:
            return False
        chave = animal_id.strip()
        if chave in self._por_animal_id:
            return True
        if self.collection is not None:
            return self.collection.count_documents({"animal_id": chave}) > 0
        return False

    def clear(self) -> None:
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_animal_id.clear()
        self._por_projeto_id.clear()
        self._por_microchip.clear()
        self._por_nome_comum.clear()
        self._por_nome_cientifico.clear()
        self._por_classe.clear()
        self._por_sexo.clear()
        self._por_faixa_etaria.clear()
        self._por_orgao_origem.clear()
        self._por_regime_vida.clear()
        self._por_status_vital.clear()
        self._por_funcao.clear()
        self._por_peso_unidade.clear()
        self._por_idade_unidade.clear()
        self._proximo_id = 1

animal_repository = AnimalRepository(use_mongo=True)