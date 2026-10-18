from datetime import date
from typing import Optional, Union, List, Dict, Any
from src.models.Amostra import (
    Amostra,
    AmostraCreate,
    AmostraUpdate,
    AmostraDetails,
    CondicaoArmazenamento,
    DestinoAmostra,
    FaseAmostra,
    MaterialBiologico,
    StatusAmostra,
)
from src.models.Animal import Animal
from src.models.Exame.exame import Exame
from src.repositories.amostra_repository import AmostraRepository, amostra_repository
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_material_biologico,
    normalizar_data,
    normalizar_coordenada,
    normalizar_booleano,
    normalizar_enum,
)

# Aliases aceitos na entrada -> nome canônico do campo no model Amostra
_ALIASES_AMOSTRA = {
    "animal": "animal_id",
    "data_coleta": "data_coleta_amostra",
    "data_recebimento": "data_entrega",
    "metodo_coleta": "material_biologico",
    "local_coleta": "local_coleta_amostra",
    "condicao_amostra": "condicao_armazenamento",
    "caixa": "caixa_armazenamento",
    "sequenciamento": "sequenciamento_disponivel",
    "observacoes": "amostra_observacoes",
}

# Rótulos amigáveis para mensagens de erro de validação
_ROTULOS_CAMPOS = {
    "amostra_id": "ID da amostra (_id)",
    "animal_id": "animal vinculado (animal)",
    "data_coleta_amostra": "data de coleta (data_coleta)",
    "material_biologico": "material biológico (metodo_coleta)",
    "kit_utilizado": "kit utilizado",
    "status_amostra": "status da amostra",
    "laudo_liberado": "laudo liberado",
    "local_coleta_amostra": "local de coleta (local_coleta)",
    "nome_coletor": "nome do coletor",
    "condicao_armazenamento": "condição de armazenamento",
    "fase_amostra": "fase da amostra",
    "destino_amostra": "destino da amostra",
    "caixa_armazenamento": "caixa de armazenamento (caixa)",
    "dna_disponivel": "DNA disponível",
    "rna_disponivel": "RNA disponível",
    "sequenciamento_disponivel": "sequenciamento disponível (sequenciamento)",
}

# Campos booleanos obrigatórios
_CAMPOS_BOOLEANOS = {
    "laudo_liberado",
    "dna_disponivel",
    "rna_disponivel",
    "sequenciamento_disponivel",
}

_CAMPOS_OBRIGATORIOS_AMOSTRA = [
    "data_coleta_amostra",
    "material_biologico",
    "kit_utilizado",
    "status_amostra",
    "laudo_liberado",
    "local_coleta_amostra",
    "nome_coletor",
    "condicao_armazenamento",
    "fase_amostra",
    "destino_amostra",
    "caixa_armazenamento",
    "dna_disponivel",
    "rna_disponivel",
    "sequenciamento_disponivel",
]

class AmostraService:
    """
    Serviço responsável pelas regras de negócio e ciclo de vida da entidade Amostra:
    - [CREATE] Validação de identificador único, verificação do animal vinculado e persistência.
    - [READ] Obtenção por ID, listagem com filtros cruzados, busca textual e agregação em AmostraDetails.
    - [UPDATE] Atualização parcial com checagem de integridade e normalização de campos.
    - [DELETE] Exclusão com validação de existência.
    """

    def __init__(
        self,
        amostra_repo: Optional[AmostraRepository] = None,
        animal_service: Optional[Any] = None,
        exame_repo: Optional[Any] = None,
    ):
        self.amostra_repo = amostra_repo or amostra_repository
        self._animal_service = animal_service
        self._exame_repo = exame_repo

    @property
    def animal_service(self) -> Any:
        if self._animal_service is None:
            try:
                from src.services.animal_service import animal_service
                self._animal_service = animal_service
            except ImportError:
                self._animal_service = None
        return self._animal_service

    @property
    def exame_repo(self) -> Any:
        if self._exame_repo is None:
            try:
                from src.repositories.exame_repository import exame_repository
                self._exame_repo = exame_repository
            except ImportError:
                self._exame_repo = None
        return self._exame_repo

    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """Gancho para aplicação de controle de acesso baseado em papéis (RBAC)."""
        pass

    # -------------------------------------------------------------------------
    # NORMALIZAÇÃO DE CAMPOS E ENUMS:
    # -------------------------------------------------------------------------
    @staticmethod
    def normalizar_material_biologico(valor: Any) -> Any:
        return normalizar_material_biologico(valor)

    @staticmethod
    def normalizar_condicao_armazenamento(valor: Any) -> Any:
        return normalizar_enum(CondicaoArmazenamento, valor, default=None)

    @staticmethod
    def normalizar_fase_amostra(valor: Any) -> Any:
        return normalizar_enum(FaseAmostra, valor, default=FaseAmostra.EXTRACAO)

    @staticmethod
    def normalizar_destino_amostra(valor: Any) -> Any:
        return normalizar_enum(DestinoAmostra, valor, default=DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI)

    @staticmethod
    def normalizar_status_amostra(valor: Any) -> Any:
        return normalizar_enum(StatusAmostra, valor, default=StatusAmostra.DISPONIVEL)

    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases (animal, local_coleta, etc.) para os nomes canônicos."""
        normalizado: Dict[str, Any] = {}
        for chave, valor in payload.items():
            canonica = _ALIASES_AMOSTRA.get(chave, chave)
            if canonica in normalizado and chave != canonica:
                continue
            normalizado[canonica] = valor
        return normalizado

    def aplicar_obrigatoriedade(
        self,
        payload: Dict[str, Any],
        campos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aplica regras estritas e uniformes de obrigatoriedade sobre os campos da amostra.
        Rejeita com ValueError qualquer campo obrigatório ausente, vazio ou 'Não informado'.
        """
        verificar = set(campos) if campos is not None else set(_CAMPOS_OBRIGATORIOS_AMOSTRA)
        faltantes: List[str] = []

        for campo in sorted(verificar):
            valor = payload.get(campo)

            # 1. Campos booleanos
            if campo in _CAMPOS_BOOLEANOS:
                bool_val = normalizar_booleano(valor)
                if bool_val is not None:
                    payload[campo] = bool_val
                else:
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            # 2. Data de coleta
            if campo == "data_coleta_amostra":
                if eh_nao_informado(valor):
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                else:
                    try:
                        payload[campo] = normalizar_data(valor, permitir_none=False)
                    except ValueError:
                        faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            # 3. Demais campos (texto e enums)
            if eh_nao_informado(valor):
                faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))

        if faltantes:
            raise ValueError(
                "Campos obrigatórios da amostra ausentes ou 'Não informado': " + ", ".join(faltantes) + "."
            )

        # Normalizações complementares (data_entrega, coordenadas e enums)
        if "data_entrega" in payload:
            v_ent = payload.get("data_entrega")
            if eh_nao_informado(v_ent):
                payload["data_entrega"] = None
            else:
                try:
                    payload["data_entrega"] = normalizar_data(v_ent, permitir_none=True)
                except ValueError:
                    raise ValueError(f"Data de entrega (data_recebimento) inválida: '{v_ent}'.")

        for coord, eh_lat in [("latitude", True), ("longitude", False)]:
            if coord in payload:
                v_coord = payload.get(coord)
                if eh_nao_informado(v_coord):
                    payload[coord] = None
                else:
                    try:
                        payload[coord] = normalizar_coordenada(v_coord, eh_latitude=eh_lat)
                    except ValueError as e:
                        raise ValueError(str(e))

        if "material_biologico" in payload and payload["material_biologico"] is not None:
            payload["material_biologico"] = self.normalizar_material_biologico(payload["material_biologico"])
        if "condicao_armazenamento" in payload and payload["condicao_armazenamento"] is not None:
            payload["condicao_armazenamento"] = self.normalizar_condicao_armazenamento(payload["condicao_armazenamento"])
        if "fase_amostra" in payload and payload["fase_amostra"] is not None:
            payload["fase_amostra"] = self.normalizar_fase_amostra(payload["fase_amostra"])
        if "destino_amostra" in payload and payload["destino_amostra"] is not None:
            payload["destino_amostra"] = self.normalizar_destino_amostra(payload["destino_amostra"])
        if "status_amostra" in payload and payload["status_amostra"] is not None:
            payload["status_amostra"] = self.normalizar_status_amostra(payload["status_amostra"])

        return payload

    # -------------------------------------------------------------------------
    # CONSULTA DETALHADA E AGREGADOS (AmostraDetails):
    # -------------------------------------------------------------------------
    @classmethod
    def preencher_nao_informados_e_relacionamentos(
        cls,
        data: Any,
        animal: Optional[Animal] = None,
        exames: Optional[List[Exame]] = None,
    ) -> AmostraDetails:
        """Sanitiza os dados de uma amostra e constrói o schema detalhado AmostraDetails."""
        if hasattr(data, "model_dump"):
            payload = data.model_dump(by_alias=True)
        elif hasattr(data, "__dict__") and not isinstance(data, dict):
            payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados da amostra devem ser um dicionário ou objeto compatível.")

        if "amostra_id" not in payload and "_id" in payload and isinstance(payload["_id"], str):
            payload["amostra_id"] = payload["_id"]

        if "animal_id" not in payload and "animal" in payload and isinstance(payload["animal"], str):
            payload["animal_id"] = payload["animal"]

        # Campos textuais padrão
        for campo in [
            "local_coleta_amostra", "local_coleta", "nome_coletor",
            "condicao_armazenamento", "kit_utilizado", "caixa_armazenamento",
            "caixa", "amostra_id_projeto", "amostra_observacoes",
            "observacoes", "longitude", "latitude", "data_coleta_amostra",
            "data_coleta", "data_entrega", "data_recebimento",
        ]:
            if eh_nao_informado(payload.get(campo)):
                payload[campo] = "Não informado"

        # Enums com fallback
        if eh_nao_informado(payload.get("material_biologico")):
            payload["material_biologico"] = MaterialBiologico.OUTRO
        if eh_nao_informado(payload.get("status_amostra")):
            payload["status_amostra"] = StatusAmostra.DISPONIVEL
        if eh_nao_informado(payload.get("fase_amostra")):
            payload["fase_amostra"] = FaseAmostra.EXTRACAO
        if eh_nao_informado(payload.get("destino_amostra")):
            payload["destino_amostra"] = DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI

        if animal is not None:
            payload["animal"] = animal

        lista_exames = exames if exames is not None else payload.get("exames", [])
        payload["exames"] = lista_exames
        if payload.get("quantidade_exames") is None or payload.get("quantidade_exames") == 0:
            payload["quantidade_exames"] = len(lista_exames)

        return AmostraDetails(**payload)

    montar_amostra_detalhes = preencher_nao_informados_e_relacionamentos

    def obter_amostra_detalhes(self, amostra_id: str, usuario: Optional[Any] = None) -> AmostraDetails:
        """[READ] Retorna os detalhes completos de uma amostra agregando Animal e Exames."""
        self._verificar_permissao("obter_amostra", usuario)
        amostra = self.obter_amostra(amostra_id, usuario=usuario)

        animal_obj: Optional[Animal] = None
        if self.animal_service and hasattr(self.animal_service, "obter_animal"):
            try:
                animal_obj = self.animal_service.obter_animal(amostra.animal_id)
            except Exception:
                animal_obj = None

        exames_list: List[Exame] = []
        if self.exame_repo and hasattr(self.exame_repo, "buscar_por_amostra_id"):
            try:
                exames_list = self.exame_repo.buscar_por_amostra_id(amostra_id)
            except Exception:
                exames_list = []

        return self.preencher_nao_informados_e_relacionamentos(
            amostra,
            animal=animal_obj,
            exames=exames_list,
        )

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def criar_amostra(
        self,
        dados_amostra: Union[Dict[str, Any], AmostraCreate],
        confirmar_nova_amostra: bool = False,
        confirmar_novo_animal: bool = False,
        usuario: Optional[Any] = None,
    ) -> Amostra:
        """[CREATE] Valida e persiste uma nova amostra biológica."""
        self._verificar_permissao("criar_amostra", usuario)

        if isinstance(dados_amostra, AmostraCreate):
            payload = dados_amostra.model_dump(by_alias=True)
            conf_animal = dados_amostra.confirmar_novo_animal or confirmar_novo_animal
        else:
            payload = dict(dados_amostra)
            conf_animal = payload.pop("confirmar_novo_animal", False) or confirmar_novo_animal

        payload = self._normalizar_chaves(payload)

        amostra_id = payload.get("amostra_id")
        if eh_nao_informado(amostra_id):
            raise ValueError("O identificador único da amostra (amostra_id ou _id) é obrigatório.")
        amostra_id_str = str(amostra_id).strip()
        payload["amostra_id"] = amostra_id_str

        if self.amostra_repo.exists(amostra_id_str):
            raise ValueError(f"Já existe uma amostra cadastrada com o ID '{amostra_id_str}'.")

        animal_id = payload.get("animal_id")
        if eh_nao_informado(animal_id):
            raise ValueError("O identificador do animal vinculado (animal_id ou animal) é obrigatório.")
        animal_id_str = str(animal_id).strip()
        payload["animal_id"] = animal_id_str

        # Validação referencial do animal vinculado
        if self.animal_service and hasattr(self.animal_service, "obter_animal"):
            try:
                self.animal_service.obter_animal(animal_id_str)
            except KeyError:
                if not conf_animal:
                    raise ValueError(
                        f"Animal com ID '{animal_id_str}' não encontrado no acervo do laboratório. "
                        "Para cadastrar a amostra vinculada a um animal novo ainda não registrado, "
                        "confirme através da opção 'confirmar_novo_animal'."
                    )

        self.aplicar_obrigatoriedade(payload)

        amostra = Amostra(**payload)
        return self.amostra_repo.create(amostra)

    def obter_amostra(self, amostra_id: str, usuario: Optional[Any] = None) -> Amostra:
        """[READ] Recupera uma amostra cadastrada pelo seu identificador único."""
        self._verificar_permissao("obter_amostra", usuario)
        amostra = self.amostra_repo.buscar_por_amostra_id(amostra_id)
        if not amostra:
            raise KeyError(f"Amostra com ID '{amostra_id}' não encontrada.")
        return amostra

    def obter_amostra_por_id(self, id_numerico: Union[int, str], usuario: Optional[Any] = None) -> Amostra:
        """[READ] Recupera uma amostra pelo identificador sequencial numérico do banco."""
        self._verificar_permissao("obter_amostra", usuario)
        amostra = self.amostra_repo.buscar_por_id(id_numerico)
        if not amostra:
            raise KeyError(f"Amostra com ID numérico '{id_numerico}' não encontrada.")
        return amostra

    def listar_amostras(
        self,
        animal_id: Optional[str] = None,
        status_amostra: Optional[StatusAmostra] = None,
        fase_amostra: Optional[FaseAmostra] = None,
        condicao_armazenamento: Optional[CondicaoArmazenamento] = None,
        destino_amostra: Optional[DestinoAmostra] = None,
        material_biologico: Optional[MaterialBiologico] = None,
        termo_busca: Optional[str] = None,
        ordenar_por: str = 'id',
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[Amostra]:
        """[READ] Lista amostras aplicando filtros laboratoriais, busca textual e paginação."""
        self._verificar_permissao("listar_amostras", usuario)

        if termo_busca:
            resultado = self.amostra_repo.listar(
                animal_id=animal_id,
                status_amostra=status_amostra,
                fase_amostra=fase_amostra,
                condicao_armazenamento=condicao_armazenamento,
                destino_amostra=destino_amostra,
                material_biologico=material_biologico,
                ordenar_por=ordenar_por,
                skip=0,
                limit=0,
            )
            termo = termo_busca.strip().lower()
            filtrados = [
                a for a in resultado
                if any(
                    termo in str(val).lower()
                    for val in [
                        a.amostra_id, a.animal_id, a.amostra_observacoes,
                        a.local_coleta_amostra, a.nome_coletor,
                        a.caixa_armazenamento, a.amostra_id_projeto,
                    ]
                    if val
                )
            ]
            if skip > 0:
                filtrados = filtrados[skip:]
            if limit is not None and limit > 0:
                filtrados = filtrados[:limit]
            return filtrados

        return self.amostra_repo.listar(
            animal_id=animal_id,
            status_amostra=status_amostra,
            fase_amostra=fase_amostra,
            condicao_armazenamento=condicao_armazenamento,
            destino_amostra=destino_amostra,
            material_biologico=material_biologico,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )

    def listar_amostras_por_animal(self, animal_id: str, usuario: Optional[Any] = None) -> List[Amostra]:
        """[READ] Retorna todas as amostras biológicas vinculadas a um animal específico."""
        self._verificar_permissao("listar_amostras", usuario)
        return self.amostra_repo.buscar_por_animal_id(animal_id)

    def contar_amostras(self, usuario: Optional[Any] = None) -> int:
        """[READ] Retorna a quantidade total de amostras cadastradas."""
        self._verificar_permissao("contar_amostras", usuario)
        return self.amostra_repo.count()

    def existe_amostra(self, amostra_id: str, usuario: Optional[Any] = None) -> bool:
        """[READ] Verifica se uma amostra com o identificador fornecido existe."""
        self._verificar_permissao("obter_amostra", usuario)
        return self.amostra_repo.exists(amostra_id)

    def atualizar_amostra(
        self,
        amostra_id: str,
        dados_atualizacao: Union[Dict[str, Any], AmostraUpdate],
        confirmar_atualizacao_amostra: bool = False,
        confirmar_novo_animal: bool = False,
        usuario: Optional[Any] = None,
    ) -> Amostra:
        """[UPDATE] Atualização parcial de uma amostra existente."""
        self._verificar_permissao("atualizar_amostra", usuario)
        amostra_atual = self.obter_amostra(amostra_id, usuario=usuario)

        if isinstance(dados_atualizacao, AmostraUpdate):
            novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            conf_animal = dados_atualizacao.confirmar_atualizacao_amostra or confirmar_novo_animal
        else:
            novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            conf_animal = novos.pop("confirmar_novo_animal", False) or confirmar_novo_animal

        novos = self._normalizar_chaves(novos)
        for chave in ("amostra_id", "id", "confirmar_atualizacao_amostra", "confirmar_novo_animal"):
            novos.pop(chave, None)

        payload = self._normalizar_chaves(amostra_atual.model_dump(by_alias=True))

        novo_animal_id = novos.get("animal_id")
        if novo_animal_id and str(novo_animal_id).strip() != amostra_atual.animal_id:
            novo_animal_str = str(novo_animal_id).strip()
            if self.animal_service and hasattr(self.animal_service, "obter_animal"):
                try:
                    self.animal_service.obter_animal(novo_animal_str)
                except KeyError:
                    if not conf_animal:
                        raise ValueError(
                            f"Animal com ID '{novo_animal_str}' não encontrado no acervo do laboratório. "
                            "Confirme a vinculação através de 'confirmar_novo_animal'."
                        )
            novos["animal_id"] = novo_animal_str

        enviados = [c for c in novos if c in _CAMPOS_OBRIGATORIOS_AMOSTRA]
        if enviados:
            self.aplicar_obrigatoriedade(novos, campos=enviados)

        payload.update(novos)
        payload["amostra_id"] = amostra_id

        amostra_modificada = Amostra(**payload)
        return self.amostra_repo.update(amostra_id, amostra_modificada)

    def deletar_amostra(self, amostra_id: str, usuario: Optional[Any] = None) -> bool:
        """[DELETE] Remove uma amostra cadastrada no repositório."""
        self._verificar_permissao("deletar_amostra", usuario)
        self.obter_amostra(amostra_id, usuario=usuario)
        return self.amostra_repo.delete(amostra_id)


# Instância singleton para injeção de dependência simplificada
amostra_service = AmostraService()

__all__ = [
    "AmostraService",
    "amostra_service",
    "Amostra",
    "AmostraCreate",
    "AmostraUpdate",
    "AmostraDetails",
    "CondicaoArmazenamento",
    "DestinoAmostra",
    "FaseAmostra",
    "MaterialBiologico",
    "StatusAmostra",
    "Animal",
    "Exame",
]