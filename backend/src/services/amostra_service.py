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
        """
        Normaliza strings recebidas de planilhas/formulários para o Enum canônico MaterialBiologico.
        Prioriza termos mais específicos antes de genéricos (ex: 'swab oral e cloacal' antes de 'swab oral').
        """
        if isinstance(valor, MaterialBiologico):
            return valor
        if not valor:
            return MaterialBiologico.OUTRO

        v_limpo = str(valor).strip().casefold()

        # Mapeamento ordenado por especificidade (termos mais longos primeiro)
        termos_ordenados = [
            ("swab oral e cloacal", MaterialBiologico.SWAB_ORAL_CLOACAL),
            ("oral e cloacal", MaterialBiologico.SWAB_ORAL_CLOACAL),
            ("swab traqueal", MaterialBiologico.SWAB_TRAQUEAL),
            ("swab cloacal", MaterialBiologico.SWAB_CLOACAL),
            ("swab ocular", MaterialBiologico.SWAB_OCULAR),
            ("swab retal", MaterialBiologico.SWAB_RETAL),
            ("swab nasal", MaterialBiologico.SWAB_NASAL),
            ("swab oral", MaterialBiologico.SWAB_ORAL),
            ("esfregaço sanguíneo", MaterialBiologico.ESFREGACO_SANGUINEO),
            ("esfregaco sanguineo", MaterialBiologico.ESFREGACO_SANGUINEO),
            ("esfregaço", MaterialBiologico.ESFREGACO_SANGUINEO),
            ("esfregaco", MaterialBiologico.ESFREGACO_SANGUINEO),
            ("pool de tecidos", MaterialBiologico.POOL_TECIDOS),
            ("sangue (edta)", MaterialBiologico.SANGUE_EDTA),
            ("sangue total", MaterialBiologico.SANGUE_TOTAL),
            ("sangue edta", MaterialBiologico.SANGUE_EDTA),
            ("papel filtro", MaterialBiologico.PAPEL_FILTRO),
            ("papel-filtro", MaterialBiologico.PAPEL_FILTRO),
            ("filtro", MaterialBiologico.PAPEL_FILTRO),
            ("edta", MaterialBiologico.SANGUE_EDTA),
            ("sangue", MaterialBiologico.SANGUE),
            ("soro", MaterialBiologico.SORO),
            ("órgãos", MaterialBiologico.ORGAOS),
            ("orgaos", MaterialBiologico.ORGAOS),
            ("órgão", MaterialBiologico.ORGAOS),
            ("orgao", MaterialBiologico.ORGAOS),
            ("tecido", MaterialBiologico.TECIDO),
            ("baço", MaterialBiologico.BACO),
            ("baco", MaterialBiologico.BACO),
            ("fígado", MaterialBiologico.FIGADO),
            ("figado", MaterialBiologico.FIGADO),
            ("pulmão", MaterialBiologico.PULMAO),
            ("pulmao", MaterialBiologico.PULMAO),
            ("rim", MaterialBiologico.RIM),
            ("rins", MaterialBiologico.RIM),
            ("encéfalo", MaterialBiologico.ENCEFALO),
            ("encefalo", MaterialBiologico.ENCEFALO),
            ("cérebro", MaterialBiologico.ENCEFALO),
            ("cerebro", MaterialBiologico.ENCEFALO),
            ("coração", MaterialBiologico.CORACAO),
            ("coracao", MaterialBiologico.CORACAO),
            ("fezes", MaterialBiologico.FEZES),
            ("enema", MaterialBiologico.ENEMA),
            ("líquor", MaterialBiologico.LIQUOR),
            ("liquor", MaterialBiologico.LIQUOR),
            ("lcr", MaterialBiologico.LIQUOR),
            ("ectoparasita", MaterialBiologico.ECTOPARASITA),
            ("pele", MaterialBiologico.PELE),
            ("pelo", MaterialBiologico.PELO),
            ("necrópsia", MaterialBiologico.NECROPSIA),
            ("necropsia", MaterialBiologico.NECROPSIA),
            ("outro", MaterialBiologico.OUTRO),
        ]

        for termo, enum_item in termos_ordenados:
            if termo in v_limpo:
                return enum_item

        for m in MaterialBiologico:
            if m.value.casefold() == v_limpo:
                return m

        return valor

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
    ) -> Amostra:
        """
        [CREATE] Cria e persiste uma nova amostra.
        """
        self._verificar_permissao("criar_amostra", usuario)

        if isinstance(dados_amostra, AmostraCreate):
            payload = dados_amostra.model_dump(by_alias=True)
            conf_animal = dados_amostra.confirmar_novo_animal or confirmar_novo_animal
        else:
            payload = dict(dados_amostra)
            conf_animal = payload.pop("confirmar_novo_animal", False) or confirmar_novo_animal

        amostra_id = payload.get("amostra_id") or payload.get("_id")
        if not amostra_id:
            raise ValueError("O identificador único da amostra (amostra_id ou _id) é obrigatório.")

        animal_id = payload.get("animal_id") or payload.get("animal")
        if not animal_id:
            raise ValueError("O identificador do animal vinculado (animal_id ou animal) é obrigatório.")

        amostra_id_str = str(amostra_id).strip()
        animal_id_str = str(animal_id).strip()

        payload["amostra_id"] = amostra_id_str
        payload["_id"] = amostra_id_str
        payload["animal_id"] = animal_id_str

        # Validação de unicidade da amostra
        if self.amostra_repo.exists(amostra_id_str):
            raise ValueError(f"Já existe uma amostra cadastrada com o ID '{amostra_id_str}'.")

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

        # Normalização do material
        if "material_biologico" in payload:
            payload["material_biologico"] = self.normalizar_material_biologico(payload["material_biologico"])

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
    ) -> Amostra:
        """
        [UPDATE] Atualiza dados de uma amostra existente no repositório.
        """
        self._verificar_permissao("atualizar_amostra", usuario)
        amostra_atual = self.obter_amostra(amostra_id, usuario=usuario)
        payload = amostra_atual.model_dump(by_alias=True)

        if isinstance(dados_atualizacao, AmostraUpdate):
            novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            conf_animal = dados_atualizacao.confirmar_atualizacao_amostra or confirmar_novo_animal
        else:
            novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            conf_animal = novos.pop("confirmar_novo_animal", False) or confirmar_novo_animal

        # Validação de alteração de animal_id
        novo_animal_id = novos.get("animal_id") or novos.get("animal")
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

        if "material_biologico" in novos:
            novos["material_biologico"] = self.normalizar_material_biologico(novos["material_biologico"])

        payload.update(novos)
        payload["amostra_id"] = amostra_id
        payload["_id"] = amostra_id

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