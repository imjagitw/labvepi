from datetime import date
from typing import Optional, Union, List, Dict, Any
from pydantic.fields import FieldInfo
from src.models.Exame import (
    Exame,
    ExameCreate,
    ExameUpdate,
    ExameDetails,
    TipoExame,
    ResultadoExame,
    TesteLaboratorial,
)
from src.repositories.exame_repository import ExameRepository, exame_repository
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_data,
    normalizar_material_biologico,
    normalizar_resultado_exame,
    normalizar_tipo_exame,
    normalizar_teste_laboratorial,
)

# Garante compatibilidade dos atributos no modelo Exame em tempo de execução
if "exame_id" not in Exame.model_fields:
    Exame.model_fields["exame_id"] = FieldInfo(annotation=Optional[str], default=None)
    Exame.model_rebuild(force=True)
if "exame_observacoes" not in Exame.model_fields:
    Exame.model_fields["exame_observacoes"] = FieldInfo(annotation=Optional[str], default=None)
    Exame.model_rebuild(force=True)

# Aliases aceitos na API/requisição -> nome canônico dos campos no model Exame
_ALIASES_EXAME = {
    "exame": "exame_id",
    "id_exame": "exame_id",
    "amostra": "amostra_id",
    "tipo_teste": "teste_laboratorial",
    "metodo": "teste_laboratorial",
    "patogeno": "tipo_exame",
    "resultado_detalhado": "resultado",
    "resultado_qualitativo": "resultado",
    "data_exame": "data_realizacao",
    "data": "data_realizacao",
    "responsavel_tecnico": "responsavel_exame",
    "responsavel": "responsavel_exame",
    "laboratorio": "laboratorio_realizador",
    "metodo_coleta": "material_biologico",
    "observacoes": "exame_observacoes",
    "protocolo": "protocolo_exame",
}

# Rótulos amigáveis para mensagens de erro de validação
_ROTULOS_CAMPOS = {
    "exame_id": "código do exame (_id)",
    "amostra_id": "amostra vinculada (amostra_id)",
    "tipo_exame": "tipo de exame / patógeno investigado (tipo_exame)",
    "resultado": "resultado do exame (resultado)",
    "data_realizacao": "data de realização (data_realizacao)",
    "teste_laboratorial": "teste laboratorial / metodologia (teste_laboratorial)",
    "material_biologico": "material biológico (material_biologico)",
    "responsavel_exame": "responsável pelo exame (responsavel_exame)",
    "laboratorio_realizador": "laboratório realizador (laboratorio_realizador)",
    "kit_utilizado": "kit utilizado",
    "protocolo_exame": "protocolo do exame",
    "exame_observacoes": "observações do exame",
}

_CAMPOS_OBRIGATORIOS_EXAME = [
    "amostra_id",
    "tipo_exame",
    "resultado",
    "data_realizacao",
    "teste_laboratorial",
]

class ExameService:
    """
    Serviço responsável pelas regras de negócio e ciclo de vida da entidade Exame:
    - [CREATE] Validação de amostra vinculada, normalização heurística de resultados e patógenos,
      herança de material biológico da amostra e persistência transacional.
    - [READ] Obtenção por ID sequencial ou código alfanumérico (exame_id), listagem com múltiplos
      filtros combinados, busca textual e agregação em ExameDetails.
    - [UPDATE] Atualização parcial com verificação de integridade referencial e unicidade.
    - [DELETE] Exclusão com validação de existência.
    """

    def __init__(
        self,
        exame_repo: Optional[ExameRepository] = None,
        amostra_service: Optional[Any] = None,
        amostra_repo: Optional[Any] = None,
    ):
        self.exame_repo = exame_repo or exame_repository
        self._amostra_service = amostra_service
        self._amostra_repo = amostra_repo

    @property
    def amostra_service(self) -> Any:
        if self._amostra_service is None:
            try:
                from src.services.amostra_service import amostra_service
                self._amostra_service = amostra_service
            except ImportError:
                self._amostra_service = None
        return self._amostra_service

    @property
    def amostra_repo(self) -> Any:
        if self._amostra_repo is None:
            try:
                from src.repositories.amostra_repository import amostra_repository
                self._amostra_repo = amostra_repository
            except ImportError:
                self._amostra_repo = None
        return self._amostra_repo

    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """Gancho para aplicação de controle de acesso baseado em papéis (RBAC)."""
        pass

    # -------------------------------------------------------------------------
    # NORMALIZAÇÃO DE CAMPOS E ENUMS (Delegação direta para src.utils.normalizacao):
    # -------------------------------------------------------------------------
    @staticmethod
    def normalizar_resultado(valor: Any, default: Optional[ResultadoExame] = None) -> Optional[ResultadoExame]:
        return normalizar_resultado_exame(valor, default=default)

    @staticmethod
    def normalizar_tipo_exame(valor: Any, default: Optional[TipoExame] = None) -> Optional[TipoExame]:
        return normalizar_tipo_exame(valor, default=default)

    @staticmethod
    def normalizar_teste_laboratorial(
        valor: Any,
        default: Optional[TesteLaboratorial] = None,
    ) -> Optional[TesteLaboratorial]:
        return normalizar_teste_laboratorial(valor, default=default)

    @staticmethod
    def normalizar_material_biologico(valor: Any) -> Any:
        return normalizar_material_biologico(valor)

    @staticmethod
    def normalizar_data(valor: Any, permitir_none: bool = False) -> Optional[date]:
        return normalizar_data(valor, permitir_none=permitir_none)

    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases aceitos na entrada para os nomes canônicos do domínio."""
        normalizado: Dict[str, Any] = {}
        for chave, valor in payload.items():
            if chave == "_id":
                if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
                    canonica = "id"
                    valor = int(valor)
                else:
                    canonica = "exame_id"
            else:
                canonica = _ALIASES_EXAME.get(chave, chave)

            if canonica in normalizado and chave != canonica:
                continue
            normalizado[canonica] = valor
        return normalizado

    def _verificar_amostra_existente(self, amostra_id: str, confirmar_nova_amostra: bool = False) -> Optional[Any]:
        """Valida a integridade referencial da amostra vinculada ao exame."""
        amostra_id_str = str(amostra_id).strip()
        amostra_obj = None

        if self.amostra_service and hasattr(self.amostra_service, "obter_amostra"):
            try:
                amostra_obj = self.amostra_service.obter_amostra(amostra_id_str)
            except KeyError:
                amostra_obj = None

        if not amostra_obj and self.amostra_repo and hasattr(self.amostra_repo, "buscar_por_amostra_id"):
            amostra_obj = self.amostra_repo.buscar_por_amostra_id(amostra_id_str)

        if not amostra_obj and not confirmar_nova_amostra:
            raise ValueError(
                f"Amostra com ID '{amostra_id_str}' não encontrada no acervo do laboratório. "
                "Para cadastrar o exame vinculado a uma amostra ainda não registrada, "
                "confirme através da opção 'confirmar_nova_amostra'."
            )
        return amostra_obj

    def aplicar_obrigatoriedade(
        self,
        payload: Dict[str, Any],
        campos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aplica regras estritas e uniformes de obrigatoriedade sobre os campos do exame.
        Rejeita com ValueError qualquer campo obrigatório ausente, vazio ou 'Não informado'.
        """
        verificar = set(campos) if campos is not None else set(_CAMPOS_OBRIGATORIOS_EXAME)
        faltantes: List[str] = []

        for campo in sorted(verificar):
            valor = payload.get(campo)

            # 1. Data de realização
            if campo == "data_realizacao":
                if eh_nao_informado(valor):
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                else:
                    try:
                        payload[campo] = self.normalizar_data(valor, permitir_none=False)
                    except ValueError:
                        faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            # 2. Demais campos obrigatórios
            if eh_nao_informado(valor):
                faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))

        if faltantes:
            raise ValueError(
                "Campos obrigatórios do exame ausentes ou 'Não informado': " + ", ".join(faltantes) + "."
            )

        # Normalizações de enums se presentes no payload
        if "resultado" in payload and payload["resultado"] is not None:
            norm_res = self.normalizar_resultado(payload["resultado"])
            if norm_res is None:
                raise ValueError(f"Resultado de exame inválido: '{payload['resultado']}'.")
            payload["resultado"] = norm_res

        if "tipo_exame" in payload and payload["tipo_exame"] is not None:
            norm_tipo = self.normalizar_tipo_exame(payload["tipo_exame"])
            if norm_tipo is None:
                raise ValueError(f"Tipo de exame/patógeno inválido: '{payload['tipo_exame']}'.")
            payload["tipo_exame"] = norm_tipo

        if "teste_laboratorial" in payload and payload["teste_laboratorial"] is not None:
            norm_teste = self.normalizar_teste_laboratorial(payload["teste_laboratorial"])
            if norm_teste is None:
                raise ValueError(f"Teste laboratorial/metodologia inválida: '{payload['teste_laboratorial']}'.")
            payload["teste_laboratorial"] = norm_teste

        if "material_biologico" in payload and payload["material_biologico"] is not None:
            payload["material_biologico"] = self.normalizar_material_biologico(payload["material_biologico"])

        return payload

    # -------------------------------------------------------------------------
    # CONSULTA DETALHADA E CONSTRUÇÃO DE SCHEMAS (ExameDetails):
    # -------------------------------------------------------------------------
    @classmethod
    def preencher_nao_informados(cls, data: Any) -> ExameDetails:
        """Sanitiza os dados de um exame e constrói o schema detalhado ExameDetails."""
        if hasattr(data, "model_dump"):
            payload = data.model_dump(by_alias=True)
        elif hasattr(data, "__dict__") and not isinstance(data, dict):
            payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados do exame devem ser um dicionário ou objeto compatível.")

        payload = cls._normalizar_chaves(payload)

        # Preserva exame_id caso venha via _id ou id numérico
        if not payload.get("exame_id"):
            if "_id" in payload and isinstance(payload["_id"], str):
                payload["exame_id"] = payload["_id"]
            elif "id" in payload and payload["id"] is not None:
                payload["exame_id"] = f"EX_{int(payload['id']):04d}"

        # Sincronização entre resultado e resultado_detalhado
        if "resultado" not in payload and "resultado_detalhado" in payload:
            payload["resultado"] = payload["resultado_detalhado"]

        # Sincronização entre observações livres e exame_observacoes
        if "observacoes" in payload and not payload.get("exame_observacoes"):
            payload["exame_observacoes"] = payload["observacoes"]

        # Campos textuais opcionais
        for campo in [
            "laboratorio_realizador",
            "responsavel_exame",
            "kit_utilizado",
            "protocolo_exame",
            "material_biologico",
            "exame_observacoes",
        ]:
            if eh_nao_informado(payload.get(campo)):
                payload[campo] = None

        return ExameDetails(**payload)

    montar_exame_detalhes = preencher_nao_informados

    def obter_exame_detalhes(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> ExameDetails:
        """[READ] Retorna os detalhes estruturados de um exame."""
        self._verificar_permissao("obter_exame", usuario)
        exame = self.obter_exame(identificador, usuario=usuario)
        return self.preencher_nao_informados(exame)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def criar_exame(
        self,
        dados_exame: Union[Dict[str, Any], ExameCreate],
        confirmar_novo_exame: bool = False,
        confirmar_nova_amostra: bool = False,
        usuario: Optional[Any] = None,
    ) -> Exame:
        """[CREATE] Valida e persiste um novo exame laboratorial no banco de dados."""
        self._verificar_permissao("criar_exame", usuario)

        if isinstance(dados_exame, ExameCreate):
            payload = dados_exame.model_dump(by_alias=True)
            conf_amostra = confirmar_nova_amostra
            conf_exame = dados_exame.confirmar_novo_exame or confirmar_novo_exame
        else:
            payload = dict(dados_exame)
            conf_amostra = payload.pop("confirmar_nova_amostra", False) or confirmar_nova_amostra
            conf_exame = payload.pop("confirmar_novo_exame", False) or confirmar_novo_exame

        payload = self._normalizar_chaves(payload)

        # Validação do vínculo com a amostra
        amostra_id = payload.get("amostra_id")
        if eh_nao_informado(amostra_id):
            raise ValueError("O vínculo com o identificador da amostra (amostra_id) é obrigatório.")
        amostra_id_str = str(amostra_id).strip()
        payload["amostra_id"] = amostra_id_str

        # Integridade referencial com o repositório/serviço de amostras
        amostra_obj = self._verificar_amostra_existente(amostra_id_str, confirmar_nova_amostra=conf_amostra)

        # Herança de material biológico da amostra caso omitido no exame
        if eh_nao_informado(payload.get("material_biologico")) and amostra_obj:
            mat = getattr(amostra_obj, "material_biologico", None)
            if mat:
                payload["material_biologico"] = mat.value if hasattr(mat, "value") else str(mat)

        # Checagem de unicidade do exame_id se informado explicitamente
        exame_id = payload.get("exame_id")
        if exame_id and not eh_nao_informado(exame_id):
            exame_id_str = str(exame_id).strip()
            if self.exame_repo.exists(exame_id_str):
                raise ValueError(f"Já existe um exame cadastrado com o identificador '{exame_id_str}'.")
            payload["exame_id"] = exame_id_str

        self.aplicar_obrigatoriedade(payload)

        exame = Exame(**payload)
        return self.exame_repo.create(exame)

    def obter_exame(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> Exame:
        """[READ] Recupera um exame cadastrado pelo ID numérico ou pelo código alfanumérico (exame_id)."""
        self._verificar_permissao("obter_exame", usuario)
        exame = self.exame_repo.buscar_por_id(identificador) or self.exame_repo.buscar_por_exame_id(str(identificador))
        if not exame:
            raise KeyError(f"Exame com identificador '{identificador}' não encontrado.")
        return exame

    def obter_exame_por_id(self, id_numerico: Union[int, str], usuario: Optional[Any] = None) -> Exame:
        """[READ] Recupera um exame pelo identificador sequencial numérico do banco."""
        self._verificar_permissao("obter_exame", usuario)
        exame = self.exame_repo.buscar_por_id(id_numerico)
        if not exame:
            raise KeyError(f"Exame com ID numérico '{id_numerico}' não encontrado.")
        return exame

    def obter_exame_por_exame_id(self, exame_id: str, usuario: Optional[Any] = None) -> Exame:
        """[READ] Recupera um exame pelo código identificador (ex: 'EX_0001')."""
        self._verificar_permissao("obter_exame", usuario)
        exame = self.exame_repo.buscar_por_exame_id(exame_id)
        if not exame:
            raise KeyError(f"Exame com exame_id '{exame_id}' não encontrado.")
        return exame

    def listar_exames(
        self,
        amostra_id: Optional[str] = None,
        tipo_exame: Optional[Union[TipoExame, str]] = None,
        resultado: Optional[Union[ResultadoExame, str]] = None,
        teste_laboratorial: Optional[Union[TesteLaboratorial, str]] = None,
        data_realizacao: Optional[Union[date, str]] = None,
        responsavel_exame: Optional[str] = None,
        termo_busca: Optional[str] = None,
        ordenar_por: str = "id",
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[Exame]:
        """[READ] Lista exames aplicando filtros laboratoriais, busca textual e paginação."""
        self._verificar_permissao("listar_exames", usuario)

        data_filtro: Optional[date] = None
        if data_realizacao:
            try:
                data_filtro = self.normalizar_data(data_realizacao, permitir_none=True)
            except ValueError:
                data_filtro = None

        tipo_norm = self.normalizar_tipo_exame(tipo_exame) if tipo_exame else None
        res_norm = self.normalizar_resultado(resultado) if resultado else None
        teste_norm = self.normalizar_teste_laboratorial(teste_laboratorial) if teste_laboratorial else None

        if termo_busca:
            resultado_lista = self.exame_repo.listar(
                amostra_id=amostra_id,
                tipo_exame=tipo_norm,
                resultado=res_norm,
                teste_laboratorial=teste_norm,
                data_realizacao=data_filtro,
                responsavel_exame=responsavel_exame,
                ordenar_por=ordenar_por,
                skip=0,
                limit=0,
            )
            termo = termo_busca.strip().lower()
            filtrados = [
                e for e in resultado_lista
                if any(
                    termo in str(val).lower()
                    for val in [
                        getattr(e, "exame_id", None),
                        e.amostra_id,
                        getattr(e, "responsavel_exame", None),
                        getattr(e, "laboratorio_realizador", None),
                        getattr(e, "kit_utilizado", None),
                        getattr(e, "protocolo_exame", None),
                        getattr(e, "material_biologico", None),
                        getattr(e, "exame_observacoes", None),
                    ]
                    if val
                )
            ]
            if skip > 0:
                filtrados = filtrados[skip:]
            if limit is not None and limit > 0:
                filtrados = filtrados[:limit]
            return filtrados

        return self.exame_repo.listar(
            amostra_id=amostra_id,
            tipo_exame=tipo_norm,
            resultado=res_norm,
            teste_laboratorial=teste_norm,
            data_realizacao=data_filtro,
            responsavel_exame=responsavel_exame,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )

    def contar_exames(self, usuario: Optional[Any] = None) -> int:
        """[READ] Retorna a contagem total de exames registrados."""
        self._verificar_permissao("contar_exames", usuario)
        return self.exame_repo.count()

    def existe_exame(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> bool:
        """[READ] Verifica se um exame com o identificador fornecido existe."""
        self._verificar_permissao("obter_exame", usuario)
        return self.exame_repo.exists(identificador)

    def atualizar_exame(
        self,
        identificador: Union[int, str],
        dados_atualizacao: Union[Dict[str, Any], ExameUpdate],
        confirmar_atualizacao_exame: bool = False,
        confirmar_nova_amostra: bool = False,
        usuario: Optional[Any] = None,
    ) -> Exame:
        """[UPDATE] Atualização parcial de um registro de exame existente."""
        self._verificar_permissao("atualizar_exame", usuario)
        exame_atual = self.obter_exame(identificador, usuario=usuario)

        if isinstance(dados_atualizacao, ExameUpdate):
            novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            conf_amostra = confirmar_nova_amostra
        else:
            novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            conf_amostra = novos.pop("confirmar_nova_amostra", False) or confirmar_nova_amostra

        novos = self._normalizar_chaves(novos)
        for chave in ("id", "confirmar_atualizacao_exame", "confirmar_novo_exame", "confirmar_nova_amostra"):
            novos.pop(chave, None)

        payload = self._normalizar_chaves(exame_atual.model_dump(by_alias=True))

        # Se alterar a amostra vinculada, valida a integridade referencial
        novo_amostra_id = novos.get("amostra_id")
        if novo_amostra_id and str(novo_amostra_id).strip() != exame_atual.amostra_id:
            amostra_nova_str = str(novo_amostra_id).strip()
            self._verificar_amostra_existente(amostra_nova_str, confirmar_nova_amostra=conf_amostra)
            novos["amostra_id"] = amostra_nova_str

        # Se alterar o exame_id, valida unicidade
        novo_exame_id = novos.get("exame_id")
        if novo_exame_id and hasattr(exame_atual, "exame_id") and novo_exame_id != getattr(exame_atual, "exame_id"):
            novo_exame_str = str(novo_exame_id).strip()
            if self.exame_repo.exists(novo_exame_str):
                raise ValueError(f"Já existe outro exame cadastrado com o código '{novo_exame_str}'.")
            novos["exame_id"] = novo_exame_str

        # Valida campos enviados
        enviados = [c for c in novos if c in _CAMPOS_OBRIGATORIOS_EXAME]
        if enviados:
            self.aplicar_obrigatoriedade(novos, campos=enviados)

        payload.update(novos)

        # Garante integridade de identificadores
        if exame_atual.id is not None:
            payload["id"] = exame_atual.id
        if getattr(exame_atual, "exame_id", None):
            payload["exame_id"] = getattr(exame_atual, "exame_id")

        exame_modificado = Exame(**payload)
        return self.exame_repo.update(identificador, exame_modificado)

    def deletar_exame(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> bool:
        """[DELETE] Remove um registro de exame laboratorial."""
        self._verificar_permissao("deletar_exame", usuario)
        self.obter_exame(identificador, usuario=usuario)
        return self.exame_repo.delete(identificador)


# Instância singleton para injeção de dependência simplificada
exame_service = ExameService()

__all__ = [
    "ExameService",
    "exame_service",
    "Exame",
    "ExameCreate",
    "ExameUpdate",
    "ExameDetails",
    "TipoExame",
    "ResultadoExame",
    "TesteLaboratorial",
]