import re
from typing import Optional, List, Dict, Union, Any
from src.models.Usuario.usuario import Usuario
from src.models.Usuario.enums.Perfil import Perfil
from src.models.Usuario.enums.StatusUsuario import StatusUsuario
from src.utils.repositorio import (
    _normalizar,
    gerar_proximo_id_mongo,
    doc_para_mongo,
    preparar_doc_mongo,
)

class UsuarioRepository:
    """
    Repositório de persistência e acesso a dados da entidade Usuario.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover usuários no banco de dados MongoDB (com cache indexado).
    - Atuar como camada de acesso a dados (DAO/Persistência) no modo dual (MongoDB ativo ou isolado em memória).
    - NÃO contém regras de negócio, criptografia de senhas ou emissão de tokens.
    """
    COLLECTION_NAME = "usuarios"

    def __init__(
        self,
        usuarios: Optional[List[Usuario]] = None,
        db: Optional[Any] = None,
        use_mongo: bool = False,
    ):
        self._por_id: Dict[Union[int, str], Usuario] = {}
        self._por_username: Dict[str, Usuario] = {}
        self._por_email: Dict[str, Usuario] = {}
        self._por_matricula: Dict[str, Usuario] = {}
        self._por_perfil: Dict[Perfil, List[Usuario]] = {}
        self._por_status: Dict[StatusUsuario, List[Usuario]] = {}
        self._proximo_id: int = 1
        self._db = db
        self._use_mongo = True if db is not None else use_mongo
        self._collection = None

        if self.collection is not None and not usuarios:
            self._carregar_do_banco()

        for usuario in usuarios or []:
            self.create(usuario)

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

    def _do_mongo(self, doc: dict) -> Usuario:
        d = preparar_doc_mongo(doc)
        if "_id" in d and not isinstance(d["_id"], int):
            d["_id"] = str(d["_id"])
        if "status" not in d or d["status"] is None:
            d["status"] = StatusUsuario.PENDENTE
        return Usuario(**d)

    def _para_mongo(self, usuario: Usuario) -> dict:
        return doc_para_mongo(usuario)

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
                    u = self._do_mongo(doc)
                    self._indexar(u)
                    if u.id is not None and isinstance(u.id, int) and u.id >= self._proximo_id:
                        self._proximo_id = u.id + 1
                except Exception:
                    pass
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------

    def _indexar(self, usuario: Usuario) -> None:
        chave_user = _normalizar(usuario.username)
        self._por_username[chave_user] = usuario

        if usuario.id is not None:
            chave_id = int(usuario.id) if str(usuario.id).isdigit() else str(usuario.id)
            self._por_id[chave_id] = usuario
            if isinstance(chave_id, int) and chave_id >= self._proximo_id:
                self._proximo_id = chave_id + 1

        chave_email = _normalizar(usuario.email)
        if chave_email:
            self._por_email[chave_email] = usuario

        if usuario.matricula:
            chave_matr = _normalizar(usuario.matricula)
            if chave_matr:
                self._por_matricula[chave_matr] = usuario

        if usuario.perfil:
            self._por_perfil.setdefault(usuario.perfil, [])
            if usuario not in self._por_perfil[usuario.perfil]:
                self._por_perfil[usuario.perfil].append(usuario)

        if usuario.status:
            self._por_status.setdefault(usuario.status, [])
            if usuario not in self._por_status[usuario.status]:
                self._por_status[usuario.status].append(usuario)

    def _desindexar(self, usuario: Usuario) -> None:
        chave_user = _normalizar(usuario.username)
        self._por_username.pop(chave_user, None)

        if usuario.id is not None:
            chave_id = int(usuario.id) if str(usuario.id).isdigit() else str(usuario.id)
            self._por_id.pop(chave_id, None)

        chave_email = _normalizar(usuario.email)
        self._por_email.pop(chave_email, None)

        if usuario.matricula:
            chave_matr = _normalizar(usuario.matricula)
            self._por_matricula.pop(chave_matr, None)

        if usuario.perfil and usuario.perfil in self._por_perfil:
            if usuario in self._por_perfil[usuario.perfil]:
                self._por_perfil[usuario.perfil].remove(usuario)

        if usuario.status and usuario.status in self._por_status:
            if usuario in self._por_status[usuario.status]:
                self._por_status[usuario.status].remove(usuario)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------

    def create(self, usuario: Usuario) -> Usuario:
        if not usuario.username:
            raise ValueError("O nome de usuário (username) é obrigatório.")
        if not usuario.email:
            raise ValueError("O e-mail do usuário é obrigatório.")

        chave_user = _normalizar(usuario.username)
        if chave_user in self._por_username or (
            self.collection is not None and self.collection.count_documents({
                "$or": [{"username": usuario.username}, {"usuario": usuario.username}]
            }) > 0
        ):
            raise ValueError(f"Usuário com username '{usuario.username}' já está cadastrado.")

        chave_email = _normalizar(usuario.email)
        if chave_email in self._por_email or (
            self.collection is not None and self.collection.count_documents({"email": usuario.email}) > 0
        ):
            raise ValueError(f"Usuário com e-mail '{usuario.email}' já está cadastrado.")

        # A chave primária (id/_id) é SEMPRE gerada pela camada de persistência;
        # qualquer valor pré-existente no objeto é descartado.
        usuario.id = self._gerar_proximo_id()

        if self.collection is not None:
            doc = self._para_mongo(usuario)
            self.collection.insert_one(doc)

        self._indexar(usuario)
        return usuario

    def save(self, usuario: Usuario) -> Usuario:
        if self.exists_username(usuario.username):
            return self.update(usuario.username, usuario)
        if usuario.id is not None and self.exists_id(usuario.id):
            return self.update(usuario.id, usuario)
        return self.create(usuario)

    def update(self, identificador: Union[str, int], usuario_atualizado: Usuario) -> Usuario:
        antigo = self.buscar_por_username(str(identificador)) if isinstance(identificador, str) else None
        if not antigo:
            antigo = self.buscar_por_id(identificador)

        if not antigo:
            raise KeyError(f"Usuário com identificador '{identificador}' não encontrado para atualização.")

        self._desindexar(antigo)

        # A chave primária é imutável: sempre preserva o id já persistido.
        usuario_atualizado.id = antigo.id

        if self.collection is not None:
            doc = self._para_mongo(usuario_atualizado)
            filtro = (
                {"_id": antigo.id}
                if antigo.id is not None
                else {"$or": [{"username": antigo.username}, {"usuario": antigo.username}]}
            )
            self.collection.replace_one(filtro, doc, upsert=True)

        self._indexar(usuario_atualizado)
        return usuario_atualizado

    def delete(self, identificador: Union[str, int]) -> bool:
        antigo = self.buscar_por_username(str(identificador)) if isinstance(identificador, str) else None
        if not antigo:
            antigo = self.buscar_por_id(identificador)

        if not antigo:
            raise KeyError(f"Usuário com identificador '{identificador}' não encontrado para exclusão.")

        if self.collection is not None:
            filtro = (
                {"_id": antigo.id}
                if antigo.id is not None
                else {"$or": [{"username": antigo.username}, {"usuario": antigo.username}]}
            )
            self.collection.delete_one(filtro)

        self._desindexar(antigo)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------

    def buscar_por_id(self, id_usuario: Union[int, str]) -> Optional[Usuario]:
        if id_usuario is None:
            return None
        chave = int(id_usuario) if str(id_usuario).isdigit() else str(id_usuario)
        if chave in self._por_id:
            return self._por_id[chave]
        if self.collection is not None:
            filtro = {"_id": int(id_usuario)} if str(id_usuario).isdigit() else {"_id": str(id_usuario)}
            doc = self.collection.find_one(filtro)
            if doc:
                u = self._do_mongo(doc)
                self._indexar(u)
                return u
        return None

    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        if not username:
            return None
        chave = _normalizar(username)
        if chave in self._por_username:
            return self._por_username[chave]
        if self.collection is not None:
            doc = self.collection.find_one({
                "$or": [
                    {"username": {"$regex": f"^{re.escape(username.strip())}$", "$options": "i"}},
                    {"usuario": {"$regex": f"^{re.escape(username.strip())}$", "$options": "i"}}
                ]
            })
            if doc:
                u = self._do_mongo(doc)
                self._indexar(u)
                return u
        return None

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        if not email:
            return None
        chave = _normalizar(email)
        if chave in self._por_email:
            return self._por_email[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}})
            if doc:
                u = self._do_mongo(doc)
                self._indexar(u)
                return u
        return None

    def buscar_por_matricula(self, matricula: str) -> Optional[Usuario]:
        if not matricula:
            return None
        chave = _normalizar(matricula)
        if chave in self._por_matricula:
            return self._por_matricula[chave]
        if self.collection is not None:
            doc = self.collection.find_one({"matricula": {"$regex": f"^{re.escape(matricula.strip())}$", "$options": "i"}})
            if doc:
                u = self._do_mongo(doc)
                self._indexar(u)
                return u
        return None

    def buscar_por_perfil(self, perfil: Union[Perfil, str]) -> List[Usuario]:
        if not perfil:
            return []
        if isinstance(perfil, Perfil) and perfil in self._por_perfil:
            return list(self._por_perfil[perfil])
        alvo = perfil.value if isinstance(perfil, Perfil) else str(perfil).strip().lower()
        for p, usuarios in self._por_perfil.items():
            if p.value.lower() == alvo:
                return list(usuarios)
        if self.collection is not None:
            docs = self.collection.find({"perfil": {"$regex": f"^{re.escape(alvo)}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    u = self._do_mongo(d)
                    self._indexar(u)
                    res.append(u)
                except Exception:
                    pass
            return res
        return []

    def buscar_por_status(self, status: Union[StatusUsuario, str]) -> List[Usuario]:
        """Consulta todos os usuários associados a um determinado status."""
        if not status:
            return []
        if isinstance(status, StatusUsuario) and status in self._por_status:
            return list(self._por_status[status])
        alvo = status.value if isinstance(status, StatusUsuario) else str(status).strip()
        for st, usuarios in self._por_status.items():
            if st.value.casefold() == alvo.casefold():
                return list(usuarios)
        if self.collection is not None:
            docs = self.collection.find({"status": {"$regex": f"^{re.escape(alvo)}$", "$options": "i"}})
            res = []
            for d in docs:
                try:
                    u = self._do_mongo(d)
                    self._indexar(u)
                    res.append(u)
                except Exception:
                    pass
            return res
        return []

    def listar_pendentes(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Retorna todos os usuários com status PENDENTE de aprovação."""
        pendentes = self.buscar_por_status(StatusUsuario.PENDENTE)
        pendentes.sort(key=lambda u: (u.created_at or 0, u.username))
        if skip > 0:
            pendentes = pendentes[skip:]
        if limit is not None and limit > 0:
            pendentes = pendentes[:limit]
        return pendentes

    def listar(
        self,
        perfil: Optional[Union[Perfil, str]] = None,
        status: Optional[Union[StatusUsuario, str]] = None,
        termo_busca: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Usuario]:
        resultado = list(self._por_username.values())

        if perfil:
            alvo = perfil.value if isinstance(perfil, Perfil) else str(perfil).strip().lower()
            resultado = [u for u in resultado if u.perfil.value.lower() == alvo]

        if status:
            alvo_st = status.value if isinstance(status, StatusUsuario) else str(status).strip().casefold()
            resultado = [
                u for u in resultado
                if (u.status.value if isinstance(u.status, StatusUsuario) else str(u.status)).casefold() == alvo_st
            ]

        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado = [
                u for u in resultado
                if termo in _normalizar(u.username)
                or (u.name and termo in _normalizar(u.name))
                or termo in _normalizar(u.email)
                or (u.matricula and termo in _normalizar(u.matricula))
            ]

        resultado.sort(key=lambda u: (u.id if isinstance(u.id, int) else 0, u.username))

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
        return len(self._por_username)

    def exists(self, identificador: Union[str, int]) -> bool:
        if identificador is None:
            return False
        if isinstance(identificador, str):
            if self.exists_username(identificador):
                return True
            if self.exists_email(identificador):
                return True
        return self.exists_id(identificador)

    def exists_username(self, username: str) -> bool:
        if not username:
            return False
        chave = _normalizar(username)
        if chave in self._por_username:
            return True
        if self.collection is not None:
            return self.collection.count_documents({
                "$or": [
                    {"username": {"$regex": f"^{re.escape(username.strip())}$", "$options": "i"}},
                    {"usuario": {"$regex": f"^{re.escape(username.strip())}$", "$options": "i"}}
                ]
            }) > 0
        return False

    def exists_email(self, email: str) -> bool:
        if not email:
            return False
        chave = _normalizar(email)
        if chave in self._por_email:
            return True
        if self.collection is not None:
            return self.collection.count_documents({
                "email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}
            }) > 0
        return False

    def exists_id(self, id_usuario: Union[int, str]) -> bool:
        if id_usuario is None:
            return False
        chave = int(id_usuario) if str(id_usuario).isdigit() else str(id_usuario)
        if chave in self._por_id:
            return True
        if self.collection is not None:
            filtro = {"_id": int(id_usuario)} if str(id_usuario).isdigit() else {"_id": str(id_usuario)}
            return self.collection.count_documents(filtro) > 0
        return False

    def clear(self) -> None:
        if self.collection is not None:
            try:
                self.collection.delete_many({})
            except Exception:
                pass
        self._por_id.clear()
        self._por_username.clear()
        self._por_email.clear()
        self._por_matricula.clear()
        self._por_perfil.clear()
        self._por_status.clear()
        self._proximo_id = 1

usuario_repository = UsuarioRepository(use_mongo=True)