from datetime import date
from enum import Enum
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
from src.domain.normalizacao import (
    eh_nao_informado,
    normalizar_material_biologico,
    normalizar_data,
    normalizar_coordenada,
)

# Valores (normalizados em minúsculo) tratados como "vazio / não informado".
_VALORES_NAO_INFORMADOS = {
    "", "-", "ni", "none", "null", "n/a", "na",
    "não informado", "nao informado",
}

# Aliases aceitos na entrada -> nome canônico do campo no model Amostra.
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

# Rótulos amigáveis para mensagens de erro
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

# Lista dos campos obrigatórios da entidade Amostra
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

# Valores padrão aplicados durante a carga de planilhas legadas
_PADRAO_LEGADO_AMOSTRA: Dict[str, Any] = {
    "data_coleta_amostra": date.today,
    "material_biologico": MaterialBiologico.OUTRO,
    "kit_utilizado": "Não informado",
    "status_amostra": StatusAmostra.DISPONIVEL,
    "laudo_liberado": False,
    "local_coleta_amostra": "Não informado",
    "nome_coletor": "Não informado",
    "condicao_armazenamento": None,
    "fase_amostra": FaseAmostra.EXTRACAO,
    "destino_amostra": DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI,
    "caixa_armazenamento": "Não informado",
    "dna_disponivel": False,
    "rna_disponivel": False,
    "sequenciamento_disponivel": False,
}


class AmostraService:
    """
    Serviço responsável pelas regras de negócio e ciclo de vida da entidade Amostra:
    - [CREATE] Validação de identificador único, verificação do animal vinculado,
      normalização heurística do método de coleta e persistência via AmostraRepository.
    - [READ] Obtenção por ID, listagem com filtros cruzados, contagem e consulta
      detalhada (AmostraDetails) agregando dados do animal e exames diagnósticos.
    - [UPDATE] Atualização com checagem de integridade, normalização e controle de alterações.
    - [DELETE] Exclusão com validação de existência.
    - Gancho preparado para regras de autorização/permissão de perfis (RBAC).
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

    # -------------------------------------------------------------------------
    # GANCHOS PARA REGRAS DE PERMISSÃO (RBAC):
    # -------------------------------------------------------------------------
    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """
        Gancho preparado para aplicação de controle de acesso baseado em papéis (RBAC).
        """
        pass

    # -------------------------------------------------------------------------
    # NORMALIZAÇÃO HEURÍSTICA DE MATERIAL BIOLÓGICO:
    # -------------------------------------------------------------------------
    @staticmethod
    def normalizar_material_biologico(valor: Union[MaterialBiologico, str]) -> Union[MaterialBiologico, str]:
        """Normaliza strings recebidas de planilhas/formulários para o Enum canônico MaterialBiologico."""
        return normalizar_material_biologico(valor)

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

    @staticmethod
    def _eh_nao_informado(valor: Any) -> bool:
        """True se o valor é nulo, vazio ou um sentinela 'Não informado'."""
        return eh_nao_informado(valor)

    @staticmethod
    def _converter_booleano(val: Any) -> Optional[bool]:
        """Converte strings (ex: 'Sim'/'Não', 'True'/'False') ou números para booleano estrito."""
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            v = val.strip().lower()
            if v in ("sim", "s", "true", "1", "t", "yes", "y"):
                return True
            if v in ("nao", "não", "n", "false", "0", "f", "no"):
                return False
        return None

    @staticmethod
    def normalizar_condicao_armazenamento(valor: Any) -> Any:
        if isinstance(valor, CondicaoArmazenamento) or valor is None:
            return valor
        if eh_nao_informado(valor):
            return None
        v_limpo = str(valor).strip().casefold()
        for item in CondicaoArmazenamento:
            if item.value.casefold() == v_limpo or item.name.casefold() == v_limpo:
                return item
        return valor

    @staticmethod
    def normalizar_fase_amostra(valor: Any) -> Any:
        if isinstance(valor, FaseAmostra) or valor is None:
            return valor
        if eh_nao_informado(valor):
            return FaseAmostra.EXTRACAO
        v_limpo = str(valor).strip().casefold()
        for item in FaseAmostra:
            if item.value.casefold() == v_limpo or item.name.casefold() == v_limpo:
                return item
        return valor

    @staticmethod
    def normalizar_destino_amostra(valor: Any) -> Any:
        if isinstance(valor, DestinoAmostra) or valor is None:
            return valor
        if eh_nao_informado(valor):
            return DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI
        v_limpo = str(valor).strip().casefold()
        for item in DestinoAmostra:
            if item.value.casefold() == v_limpo or item.name.casefold() == v_limpo:
                return item
        return valor

    @staticmethod
    def normalizar_status_amostra(valor: Any) -> Any:
        if isinstance(valor, StatusAmostra) or valor is None:
            return valor
        if eh_nao_informado(valor):
            return StatusAmostra.DISPONIVEL
        v_limpo = str(valor).strip().casefold()
        for item in StatusAmostra:
            if item.value.casefold() == v_limpo or item.name.casefold() == v_limpo:
                return item
        return valor

    def aplicar_obrigatoriedade(
        self,
        payload: Dict[str, Any],
        carga_legada: bool = False,
        campos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aplica as regras de obrigatoriedade sobre um payload com chaves canônicas:
        - carga_legada=False (padrão: API / novos cadastros): rejeita com ValueError
          qualquer campo obrigatório ausente, vazio ou 'Não informado'.
        - carga_legada=True (importação de planilhas antigas): preenche ausências
          automaticamente com valores padrão ('Não informado', OUTRO, etc.).
        """
        verificar = set(campos) if campos is not None else set(_CAMPOS_OBRIGATORIOS_AMOSTRA)
        faltantes: List[str] = []

        for campo in sorted(verificar):
            valor = payload.get(campo)

            # Campos booleanos
            if campo in _CAMPOS_BOOLEANOS:
                bool_val = self._converter_booleano(valor)
                if bool_val is not None:
                    payload[campo] = bool_val
                elif carga_legada:
                    payload[campo] = False
                else:
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            # Campo data_coleta_amostra
            if campo == "data_coleta_amostra":
                if self._eh_nao_informado(valor):
                    if carga_legada:
                        payload[campo] = date.today()
                    else:
                        faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                else:
                    try:
                        payload[campo] = normalizar_data(valor, permitir_none=False)
                    except ValueError:
                        if carga_legada:
                            payload[campo] = date.today()
                        else:
                            faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            # Demais campos (strings e enums)
            if self._eh_nao_informado(valor):
                if carga_legada:
                    padrao = _PADRAO_LEGADO_AMOSTRA.get(campo, "Não informado")
                    payload[campo] = padrao() if callable(padrao) else padrao
                else:
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))

        if faltantes:
            raise ValueError(
                "Campos obrigatórios da amostra ausentes ou 'Não informado': " + ", ".join(faltantes) + "."
            )

        # Normalização de data_entrega
        if "data_entrega" in payload:
            v_ent = payload.get("data_entrega")
            if self._eh_nao_informado(v_ent):
                payload["data_entrega"] = None
            else:
                try:
                    payload["data_entrega"] = normalizar_data(v_ent, permitir_none=True)
                except ValueError:
                    if carga_legada:
                        payload["data_entrega"] = None
                    else:
                        raise ValueError(f"Data de entrega (data_recebimento) inválida: '{v_ent}'.")

        # Normalização geoespacial (latitude e longitude)
        if "latitude" in payload:
            v_lat = payload.get("latitude")
            if self._eh_nao_informado(v_lat):
                payload["latitude"] = None
            else:
                try:
                    payload["latitude"] = normalizar_coordenada(v_lat, eh_latitude=True)
                except ValueError as e:
                    if carga_legada:
                        payload["latitude"] = None
                    else:
                        raise ValueError(str(e))

        if "longitude" in payload:
            v_lon = payload.get("longitude")
            if self._eh_nao_informado(v_lon):
                payload["longitude"] = None
            else:
                try:
                    payload["longitude"] = normalizar_coordenada(v_lon, eh_latitude=False)
                except ValueError as e:
                    if carga_legada:
                        payload["longitude"] = None
                    else:
                        raise ValueError(str(e))

        # Normalização de enums
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
    # OPERAÇÕES DE CONSULTA DETALHADA E SANITIZAÇÃO:
    # -------------------------------------------------------------------------
    @classmethod
    def preencher_nao_informados_e_relacionamentos(
        cls,
        data: Any,
        animal: Optional[Animal] = None,
        exames: Optional[List[Exame]] = None,
    ) -> AmostraDetails:
        """
        Sanitiza os dados de uma amostra e constrói o schema AmostraDetails:
        - Preenche campos ausentes/vazios com 'Não informado'.
        - Normaliza enums para seus valores de fallback padrão.
        - Vincula a entidade Animal de origem e a lista de exames associados.
        """
        if hasattr(data, "__dict__") and not isinstance(data, dict):
            if hasattr(data, "model_dump"):
                payload = data.model_dump(by_alias=True)
            else:
                payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados da amostra devem ser um dicionário ou objeto compatível.")

        # Suporte a alias de identificador único da amostra e do animal
        if "amostra_id" not in payload and "_id" in payload and isinstance(payload["_id"], str):
            payload["amostra_id"] = payload["_id"]

        if "animal_id" not in payload and "animal" in payload and isinstance(payload["animal"], str):
            payload["animal_id"] = payload["animal"]

        # Campos textuais que devem exibir 'Não informado' se nulos ou vazios
        campos_texto = [
            ("local_coleta_amostra", "Não informado"),
            ("local_coleta", "Não informado"),
            ("nome_coletor", "Não informado"),
            ("condicao_armazenamento", "Não informado"),
            ("kit_utilizado", "Não informado"),
            ("caixa_armazenamento", "Não informado"),
            ("caixa", "Não informado"),
            ("amostra_id_projeto", "Não informado"),
            ("amostra_observacoes", "Não informado"),
            ("observacoes", "Não informado"),
            ("longitude", "Não informado"),
            ("latitude", "Não informado"),
            ("data_coleta_amostra", "Não informado"),
            ("data_coleta", "Não informado"),
            ("data_entrega", "Não informado"),
            ("data_recebimento", "Não informado"),
        ]
        
        for campo, padrao in campos_texto:
            val = payload.get(campo)
            if val is None or (isinstance(val, str) and val.strip() in ["", "-", "NI", "ni", "None", "null"]):
                payload[campo] = padrao

        # Enums
        if payload.get("material_biologico") is None or str(payload.get("material_biologico")).strip() in ["", "-", "None"]:
            payload["material_biologico"] = MaterialBiologico.OUTRO
        if payload.get("status_amostra") is None or str(payload.get("status_amostra")).strip() in ["", "-", "None"]:
            payload["status_amostra"] = StatusAmostra.DISPONIVEL
        if payload.get("fase_amostra") is None or str(payload.get("fase_amostra")).strip() in ["", "-", "None"]:
            payload["fase_amostra"] = FaseAmostra.EXTRACAO
        if payload.get("destino_amostra") is None or str(payload.get("destino_amostra")).strip() in ["", "-", "None"]:
            payload["destino_amostra"] = DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI

        # Vinculação do animal
        if animal is not None:
            payload["animal"] = animal

        # Vinculação e contagem dos exames
        if exames is not None:
            payload["exames"] = exames
            payload["quantidade_exames"] = len(exames)
        else:
            lista_exames = payload.get("exames", [])
            payload["exames"] = lista_exames
            if payload.get("quantidade_exames") is None or payload.get("quantidade_exames") == 0:
                payload["quantidade_exames"] = len(lista_exames)

        return AmostraDetails(**payload)

    # Alias semântico
    montar_amostra_detalhes = preencher_nao_informados_e_relacionamentos

    def obter_amostra_detalhes(
        self,
        amostra_id: str,
        usuario: Optional[Any] = None,
    ) -> AmostraDetails:
        """
        [READ] Retorna os detalhes completos de uma amostra:
        - Dados da amostra com tratamento explícito de campos não informados.
        - Entidade Animal vinculada.
        - Quantidade total e lista completa de exames diagnósticos associados.
        """
        self._verificar_permissao("obter_amostra", usuario)
        amostra = self.obter_amostra(amostra_id, usuario=usuario)

        # Busca dados do animal vinculado
        animal_obj: Optional[Animal] = None
        if self.animal_service and hasattr(self.animal_service, "obter_animal"):
            try:
                animal_obj = self.animal_service.obter_animal(amostra.animal_id)
            except Exception:
                animal_obj = None

        # Busca exames laboratoriais vinculados à amostra
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
    # OPERAÇÕES DE CRUD DE AMOSTRA:
    # -------------------------------------------------------------------------
    def criar_amostra(
        self,
        dados_amostra: Union[Dict[str, Any], AmostraCreate],
        confirmar_nova_amostra: bool = False,
        confirmar_novo_animal: bool = False,
        usuario: Optional[Any] = None,
        carga_legada: bool = False,
    ) -> Amostra:
        """
        [CREATE] Cria e persiste uma nova amostra biológica.

        - carga_legada=False (padrão): novos cadastros. Exige identificação, animal_id,
          data de coleta, material biológico, kit, status, laudo, local de coleta, coletor,
          condição de armazenamento, fase, destino, caixa e disponibilidade de frações.
        - carga_legada=True: importação de planilhas antigas. Campos obrigatórios
          ausentes são preenchidos com 'Não informado' / defaults.
        """
        self._verificar_permissao("criar_amostra", usuario)

        if isinstance(dados_amostra, AmostraCreate):
            payload = dados_amostra.model_dump(by_alias=True)
            conf_animal = dados_amostra.confirmar_novo_animal or confirmar_novo_animal
        else:
            payload = dict(dados_amostra)
            conf_animal = payload.pop("confirmar_novo_animal", False) or confirmar_novo_animal

        payload = self._normalizar_chaves(payload)

        amostra_id = payload.get("amostra_id")
        if self._eh_nao_informado(amostra_id):
            raise ValueError("O identificador único da amostra (amostra_id ou _id) é obrigatório.")

        amostra_id_str = str(amostra_id).strip()
        payload["amostra_id"] = amostra_id_str

        # Validação de unicidade da amostra
        if self.amostra_repo.exists(amostra_id_str):
            raise ValueError(f"Já existe uma amostra cadastrada com o ID '{amostra_id_str}'.")

        animal_id = payload.get("animal_id")
        if self._eh_nao_informado(animal_id):
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

        # Validação de campos obrigatórios
        self.aplicar_obrigatoriedade(payload, carga_legada=carga_legada)

        # Normalização de enums
        if "material_biologico" in payload:
            payload["material_biologico"] = self.normalizar_material_biologico(payload["material_biologico"])
        if "condicao_armazenamento" in payload:
            payload["condicao_armazenamento"] = self.normalizar_condicao_armazenamento(payload["condicao_armazenamento"])
        if "fase_amostra" in payload:
            payload["fase_amostra"] = self.normalizar_fase_amostra(payload["fase_amostra"])
        if "destino_amostra" in payload:
            payload["destino_amostra"] = self.normalizar_destino_amostra(payload["destino_amostra"])
        if "status_amostra" in payload:
            payload["status_amostra"] = self.normalizar_status_amostra(payload["status_amostra"])

        amostra = Amostra(**payload)
        return self.amostra_repo.create(amostra)

    def obter_amostra(self, amostra_id: str, usuario: Optional[Any] = None) -> Amostra:
        """
        [READ] Recupera uma amostra cadastrada pelo seu identificador único.
        Lança KeyError caso não seja encontrada.
        """
        self._verificar_permissao("obter_amostra", usuario)
        amostra = self.amostra_repo.buscar_por_amostra_id(amostra_id)
        if not amostra:
            raise KeyError(f"Amostra com ID '{amostra_id}' não encontrada.")
        return amostra

    def obter_amostra_por_id(self, id_numerico: Union[int, str], usuario: Optional[Any] = None) -> Amostra:
        """
        [READ] Recupera uma amostra pelo identificador sequencial numérico do banco.
        """
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
        """
        [READ] Lista amostras aplicando filtros laboratoriais, busca textual e paginação.
        """
        self._verificar_permissao("listar_amostras", usuario)

        # Busca textual
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
            filtrados = []
            for a in resultado:
                amostra_id_match = termo in a.amostra_id.lower()
                animal_id_match = bool(a.animal_id and termo in a.animal_id.lower())
                obs_match = bool(a.amostra_observacoes and termo in a.amostra_observacoes.lower())
                local_match = bool(a.local_coleta_amostra and termo in a.local_coleta_amostra.lower())
                coletor_match = bool(a.nome_coletor and termo in a.nome_coletor.lower())
                caixa_match = bool(a.caixa_armazenamento and termo in a.caixa_armazenamento.lower())
                projeto_match = bool(a.amostra_id_projeto and termo in a.amostra_id_projeto.lower())

                if any([
                    amostra_id_match,
                    animal_id_match,
                    obs_match,
                    local_match,
                    coletor_match,
                    caixa_match,
                    projeto_match,
                ]):
                    filtrados.append(a)

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
        carga_legada: bool = False,
    ) -> Amostra:
        """
        [UPDATE] Atualização parcial de uma amostra existente.
        Apenas os campos enviados são alterados; campos obrigatórios enviados
        não podem ser vazios ou 'Não informado' (exceto com carga_legada=True).
        """
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

        # Validação de alteração de animal_id
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

        # Valida apenas os campos obrigatórios enviados
        enviados = [c for c in novos if c in _CAMPOS_OBRIGATORIOS_AMOSTRA]
        if enviados:
            self.aplicar_obrigatoriedade(novos, carga_legada=carga_legada, campos=enviados)

        # Normalizações dos enums enviados
        if "material_biologico" in novos:
            novos["material_biologico"] = self.normalizar_material_biologico(novos["material_biologico"])
        if "condicao_armazenamento" in novos:
            novos["condicao_armazenamento"] = self.normalizar_condicao_armazenamento(novos["condicao_armazenamento"])
        if "fase_amostra" in novos:
            novos["fase_amostra"] = self.normalizar_fase_amostra(novos["fase_amostra"])
        if "destino_amostra" in novos:
            novos["destino_amostra"] = self.normalizar_destino_amostra(novos["destino_amostra"])
        if "status_amostra" in novos:
            novos["status_amostra"] = self.normalizar_status_amostra(novos["status_amostra"])

        payload.update(novos)
        payload["amostra_id"] = amostra_id

        amostra_modificada = Amostra(**payload)
        return self.amostra_repo.update(amostra_id, amostra_modificada)

    def deletar_amostra(self, amostra_id: str, usuario: Optional[Any] = None) -> bool:
        """
        [DELETE] Remove uma amostra cadastrada no repositório.
        """
        self._verificar_permissao("deletar_amostra", usuario)
        self.obter_amostra(amostra_id, usuario=usuario)
        return self.amostra_repo.delete(amostra_id)


# Instância singleton para uso padrão na aplicação
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