from typing import Optional, Union, List, Dict, Any
from pydantic.fields import FieldInfo
from src.models.EstoqueReagente import (
    EstoqueReagente,
    EstoqueReagenteCreate,
    EstoqueReagenteUpdate,
    EstoqueReagenteDetails,
)
from src.models.Reagente import (
    Reagente,
    ReagenteCreate,
    ReagenteUpdate,
    ReagenteDetails,
)
from src.repositories.estoque_reagente_repository import (
    EstoqueReagenteRepository,
    estoque_reagente_repository,
)
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_chaves_estoque,
    calcular_metricas_estoque,
    _ALIASES_ESTOQUE,
)

# Rótulos amigáveis para mensagens de erro de validação
_ROTULOS_CAMPOS = {
    "reagente_nome": "nome do reagente (nome)",
    "reagente_codigo": "código do reagente (codigo)",
    "lotes": "lotes associados (lotes)",
}

class EstoqueReagenteService:
    """
    Serviço responsável pela gestão de inventário e consolidação de estoque de Reagentes:
    - [CREATE] Cadastro de visões agregadas de estoque, vinculação inicial de lotes físicos
      e cálculo de totais consolidados em unidades base.
    - [READ] Obtenção por ID numérico ou nome do reagente, listagem com busca textual,
      ordenação e projeção detalhada em EstoqueReagenteDetails.
    - [UPDATE] Atualização de metadados do reagente, sincronização de lotes vinculados
      e recálculo dimensional dos volumes agregados.
    - [DELETE] Remoção da visão agregada de estoque com opção de deleção em cascata dos lotes.
    - [SINCRONIZAÇÃO] Integração bidirecional em tempo real com o ReagenteRepository/ReagenteService.
    """

    def __init__(
        self,
        estoque_repo: Optional[EstoqueReagenteRepository] = None,
        reagente_service: Optional[Any] = None,
        reagente_repo: Optional[Any] = None,
    ):
        self.estoque_repo = estoque_repo or estoque_reagente_repository
        self._reagente_service = reagente_service
        self._reagente_repo = reagente_repo

    @property
    def reagente_service(self) -> Any:
        if self._reagente_service is None:
            try:
                from src.services.reagente_service import reagente_service
                self._reagente_service = reagente_service
            except ImportError:
                self._reagente_service = None
        return self._reagente_service

    @property
    def reagente_repo(self) -> Any:
        if self._reagente_repo is None:
            try:
                from src.repositories.reagente_repository import reagente_repository
                self._reagente_repo = reagente_repository
            except ImportError:
                self._reagente_repo = None
        return self._reagente_repo

    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """Gancho para aplicação de controle de acesso baseado em papéis (RBAC)."""
        pass

    # -------------------------------------------------------------------------
    # NORMALIZAÇÃO DE CAMPOS E CHAVES:
    # -------------------------------------------------------------------------
    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases aceitos na entrada para os nomes canônicos do domínio EstoqueReagente."""
        return normalizar_chaves_estoque(payload)

    def aplicar_obrigatoriedade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Valida campos obrigatórios da entidade EstoqueReagente."""
        nome = payload.get("reagente_nome")
        if eh_nao_informado(nome):
            raise ValueError("O nome do reagente (reagente_nome) é obrigatório para o estoque.")
        payload["reagente_nome"] = str(nome).strip()

        if "reagente_codigo" in payload and payload["reagente_codigo"] is not None:
            if eh_nao_informado(payload["reagente_codigo"]):
                payload["reagente_codigo"] = None
            else:
                payload["reagente_codigo"] = str(payload["reagente_codigo"]).strip()

        return payload

    # -------------------------------------------------------------------------
    # SINCRONIZAÇÃO E CONSOLIDAÇÃO MÉTRICA:
    # -------------------------------------------------------------------------
    def consolidar_estoque(
        self,
        nome: str,
        codigo: Optional[str] = None,
        lotes: Optional[List[Reagente]] = None,
    ) -> EstoqueReagente:
        """
        Calcula as métricas de estoque consolidado para um determinado reagente
        delegando o cálculo dimensional para o ReagenteService.
        """
        if lotes is None and self.reagente_repo:
            lotes = self.reagente_repo.buscar_por_nome(nome)
        lotes = lotes or []

        if self.reagente_service:
            return self.reagente_service.consolidar_estoque(nome=nome, codigo=codigo, lotes=lotes)

        # Fallback de consolidação com cálculo dimensional completo
        qtd_unidades, qtd_volume, totais_un, totais_base, resumo = calcular_metricas_estoque(lotes)
        return EstoqueReagente(
            reagente_nome=nome,
            reagente_codigo=codigo,
            lotes=lotes,
            quantidade_total_unidades=qtd_unidades,
            quantidade_total_volume=qtd_volume,
            totais_por_unidade=totais_un,
            totais_convertidos_base=totais_base,
            resumo_estoque=resumo,
        )

    def sincronizar_lotes(self, nome_reagente: str) -> Optional[EstoqueReagente]:
        """
        Recalcula as métricas consolidadas de estoque para um determinado reagente,
        consultando todos os seus lotes físicos registrados no ReagenteRepository.
        """
        if not nome_reagente:
            return None

        nome_limpo = str(nome_reagente).strip()
        lotes = self.reagente_repo.buscar_por_nome(nome_limpo) if self.reagente_repo else []
        estoque_existente = self.estoque_repo.buscar_por_nome(nome_limpo)

        # Se não há lotes físicos e nem registro prévio de estoque, não cria registro órfão
        if not lotes and not estoque_existente:
            return None

        # Determina o código do reagente a partir do estoque existente ou do primeiro lote físico
        codigo = None
        if estoque_existente and estoque_existente.reagente_codigo:
            codigo = estoque_existente.reagente_codigo
        elif lotes and lotes[0].reagente_codigo:
            codigo = lotes[0].reagente_codigo

        consolidado = self.consolidar_estoque(nome=nome_limpo, codigo=codigo, lotes=lotes)

        if estoque_existente:
            consolidado.id = estoque_existente.id
            return self.estoque_repo.update(estoque_existente.id, consolidado)
        else:
            return self.estoque_repo.create(consolidado)

    def recalcular_todo_estoque(self) -> int:
        """
        Varre todos os lotes físicos cadastrados no ReagenteRepository e sincroniza
        as visões agregadas de EstoqueReagente para cada nome único de reagente.
        Retorna o total de grupos de reagentes atualizados.
        """
        if not self.reagente_repo:
            return 0

        lotes = self.reagente_repo.listar(limit=0)
        nomes_unicos = {l.reagente_nome.strip() for l in lotes if l.reagente_nome}

        for nome in nomes_unicos:
            self.sincronizar_lotes(nome)

        return len(nomes_unicos)

    # -------------------------------------------------------------------------
    # CONSULTA DETALHADA E CONSTRUÇÃO DE SCHEMAS (EstoqueReagenteDetails):
    # -------------------------------------------------------------------------
    def preencher_nao_informados(
        self,
        data: Any,
        lotes_detalhados: Optional[List[Any]] = None,
    ) -> EstoqueReagenteDetails:
        """Sanitiza os dados de um estoque consolidado e constrói o schema detalhado EstoqueReagenteDetails."""
        if hasattr(data, "model_dump"):
            payload = data.model_dump(by_alias=True)
        elif hasattr(data, "__dict__") and not isinstance(data, dict):
            payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados do estoque devem ser um dicionário ou objeto compatível.")

        payload = self._normalizar_chaves(payload)

        # Monta a lista de lotes físicos detalhados com indicadores de vencimento enriquecidos
        lotes_in = lotes_detalhados if lotes_detalhados is not None else payload.get("lotes", [])
        lotes_out = []
        for lote in lotes_in:
            if isinstance(lote, ReagenteDetails):
                lotes_out.append(lote)
            elif self.reagente_service:
                lotes_out.append(self.reagente_service.preencher_nao_informados(lote))
            elif isinstance(lote, Reagente):
                lotes_out.append(lote)
            elif isinstance(lote, dict):
                lotes_out.append(ReagenteDetails(**lote))

        payload["lotes"] = lotes_out
        payload["quantidade_lotes"] = len(lotes_out)

        return EstoqueReagenteDetails(**payload)

    montar_estoque_detalhes = preencher_nao_informados

    def obter_estoque_detalhes(
        self,
        identificador: Union[int, str],
        usuario: Optional[Any] = None,
    ) -> EstoqueReagenteDetails:
        """[READ] Retorna a visão agregada com todos os lotes físicos detalhados e status de validade."""
        self._verificar_permissao("obter_estoque", usuario)
        estoque = self.obter_estoque(identificador, sincronizar=True, usuario=usuario)

        # Obtém os lotes físicos atualizados do repositório de reagentes
        lotes_fisicos = (
            self.reagente_repo.buscar_por_nome(estoque.reagente_nome)
            if self.reagente_repo
            else estoque.lotes
        )

        lotes_detalhados = []
        for lote in lotes_fisicos:
            if self.reagente_service:
                lotes_detalhados.append(self.reagente_service.obter_reagente_detalhes(lote.id or lote.reagente_id))
            else:
                lotes_detalhados.append(lote)

        return self.preencher_nao_informados(estoque, lotes_detalhados=lotes_detalhados)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def criar_estoque(
        self,
        dados_estoque: Union[Dict[str, Any], EstoqueReagenteCreate],
        confirmar_novo_estoque: bool = False,
        confirmar_novo_reagente: bool = False,
        usuario: Optional[Any] = None,
    ) -> EstoqueReagente:
        """[CREATE] Cadastra uma nova visão agregada de estoque e vincula lotes físicos iniciais."""
        self._verificar_permissao("criar_estoque", usuario)

        if isinstance(dados_estoque, EstoqueReagenteCreate):
            payload = dados_estoque.model_dump(by_alias=True)
            conf_estoque = dados_estoque.confirmar_novo_estoque or confirmar_novo_estoque
            conf_reagente = dados_estoque.confirmar_novo_reagente or confirmar_novo_reagente
        else:
            payload = dict(dados_estoque)
            conf_estoque = payload.pop("confirmar_novo_estoque", False) or confirmar_novo_estoque
            conf_reagente = payload.pop("confirmar_novo_reagente", False) or confirmar_novo_reagente

        payload = self._normalizar_chaves(payload)
        self.aplicar_obrigatoriedade(payload)

        nome = payload["reagente_nome"]
        codigo = payload.get("reagente_codigo")
        lotes_payload = payload.get("lotes") or []

        # Validação de estoque já cadastrado
        existente = self.estoque_repo.buscar_por_nome(nome)
        if existente:
            if not conf_estoque:
                raise ValueError(
                    f"Estoque para o reagente '{nome}' já está cadastrado. "
                    "Para atualizar o estoque existente, confirme através de 'confirmar_novo_estoque'."
                )
            # Atualiza registro existente vinculando novos lotes
            if lotes_payload and self.reagente_service:
                for item_lote in lotes_payload:
                    if isinstance(item_lote, (dict, ReagenteCreate)):
                        dados_lote = item_lote.model_dump() if isinstance(item_lote, ReagenteCreate) else dict(item_lote)
                        dados_lote["reagente_nome"] = nome
                        if codigo and not dados_lote.get("reagente_codigo"):
                            dados_lote["reagente_codigo"] = codigo
                        self.reagente_service.criar_reagente(dados_lote, confirmar_novo_reagente=conf_reagente)
            return self.sincronizar_lotes(nome) or existente

        # Se lotes físicos iniciais foram fornecidos, cadastra via ReagenteService / ReagenteRepository
        lotes_criados: List[Reagente] = []
        if lotes_payload:
            for item_lote in lotes_payload:
                if isinstance(item_lote, Reagente):
                    if self.reagente_repo:
                        lotes_criados.append(self.reagente_repo.save(item_lote))
                    else:
                        lotes_criados.append(item_lote)
                elif isinstance(item_lote, (dict, ReagenteCreate)):
                    dados_lote = item_lote.model_dump() if isinstance(item_lote, ReagenteCreate) else dict(item_lote)
                    dados_lote["reagente_nome"] = nome
                    if codigo and not dados_lote.get("reagente_codigo"):
                        dados_lote["reagente_codigo"] = codigo
                    if self.reagente_service:
                        novo_lote = self.reagente_service.criar_reagente(dados_lote, confirmar_novo_reagente=conf_reagente)
                        lotes_criados.append(novo_lote)

        # Consolida e persiste a visão agregada
        estoque_consolidado = self.consolidar_estoque(nome=nome, codigo=codigo, lotes=lotes_criados)
        return self.estoque_repo.create(estoque_consolidado)

    def obter_estoque(
        self,
        identificador: Union[int, str],
        sincronizar: bool = True,
        usuario: Optional[Any] = None,
    ) -> EstoqueReagente:
        """[READ] Recupera a visão de estoque consolidado por ID numérico ou nome do reagente."""
        self._verificar_permissao("obter_estoque", usuario)
        estoque = self.estoque_repo.buscar_por_id(identificador) or self.estoque_repo.buscar_por_nome(str(identificador))

        # Se não encontrado diretamente no estoque, verifica se há lotes cadastrados com esse nome no acervo
        if not estoque and self.reagente_repo:
            lotes = self.reagente_repo.buscar_por_nome(str(identificador))
            if lotes:
                estoque = self.sincronizar_lotes(str(identificador))

        if not estoque:
            raise KeyError(f"Estoque para '{identificador}' não encontrado.")

        if sincronizar:
            atualizado = self.sincronizar_lotes(estoque.reagente_nome)
            if atualizado:
                estoque = atualizado

        return estoque

    def obter_estoque_por_id(self, id_numerico: Union[int, str], usuario: Optional[Any] = None) -> EstoqueReagente:
        """[READ] Recupera a visão consolidada de estoque pelo ID sequencial do banco."""
        self._verificar_permissao("obter_estoque", usuario)
        estoque = self.estoque_repo.buscar_por_id(id_numerico)
        if not estoque:
            raise KeyError(f"Estoque com ID '{id_numerico}' não encontrado.")
        return estoque

    def obter_estoque_por_nome(self, nome: str, usuario: Optional[Any] = None) -> EstoqueReagente:
        """[READ] Recupera a visão consolidada de estoque pelo nome do reagente."""
        self._verificar_permissao("obter_estoque", usuario)
        return self.obter_estoque(nome, sincronizar=True, usuario=usuario)

    def obter_estoque_por_codigo(self, codigo: str, usuario: Optional[Any] = None) -> List[EstoqueReagente]:
        """[READ] Retorna visões de estoque associadas a um determinado código de referência."""
        self._verificar_permissao("obter_estoque", usuario)
        return self.estoque_repo.buscar_por_codigo(codigo)

    def listar_estoques(
        self,
        termo_busca: Optional[str] = None,
        apenas_com_lotes: Optional[bool] = None,
        ordenar_por: str = "nome",
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[EstoqueReagente]:
        """[READ] Retorna a listagem de estoques aplicando busca textual, ordenação e paginação."""
        self._verificar_permissao("listar_estoques", usuario)
        return self.estoque_repo.listar(
            termo_busca=termo_busca,
            apenas_com_lotes=apenas_com_lotes,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )

    def contar_estoques(self, usuario: Optional[Any] = None) -> int:
        """[READ] Retorna a contagem total de tipos de reagentes com estoque registrado."""
        self._verificar_permissao("contar_estoques", usuario)
        return self.estoque_repo.count()

    def existe_estoque(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> bool:
        """[READ] Verifica se existe estoque registrado para o ID ou nome fornecido."""
        self._verificar_permissao("obter_estoque", usuario)
        return self.estoque_repo.exists(identificador)

    def atualizar_estoque(
        self,
        identificador: Union[int, str],
        dados_atualizacao: Union[Dict[str, Any], EstoqueReagenteUpdate],
        confirmar_atualizacao_estoque: bool = False,
        usuario: Optional[Any] = None,
    ) -> EstoqueReagente:
        """[UPDATE] Atualiza metadados do reagente e recalcula a consolidação de estoque."""
        self._verificar_permissao("atualizar_estoque", usuario)
        estoque_atual = self.obter_estoque(identificador, sincronizar=False, usuario=usuario)
        nome_antigo = estoque_atual.reagente_nome

        if isinstance(dados_atualizacao, EstoqueReagenteUpdate):
            novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
        else:
            novos = {k: v for k, v in dados_atualizacao.items() if v is not None}

        novos = self._normalizar_chaves(novos)
        for chave in ("id", "confirmar_atualizacao_estoque", "confirmar_atualizacao_reagente"):
            novos.pop(chave, None)

        payload = self._normalizar_chaves(estoque_atual.model_dump(by_alias=True))
        payload.update(novos)
        self.aplicar_obrigatoriedade(payload)

        novo_nome = payload["reagente_nome"]
        novo_codigo = payload.get("reagente_codigo")

        # Se o nome do reagente foi alterado, propaga a alteração para os lotes físicos vinculados
        if novo_nome != nome_antigo and self.reagente_repo:
            lotes_antigos = self.reagente_repo.buscar_por_nome(nome_antigo)
            for lote in lotes_antigos:
                lote.reagente_nome = novo_nome
                if novo_codigo and not lote.reagente_codigo:
                    lote.reagente_codigo = novo_codigo
                self.reagente_repo.update(lote.id or lote.reagente_id, lote)

        # Se lotes foram enviados na carga útil de atualização, cria/atualiza os lotes
        lotes_payload = payload.get("lotes") or []
        if lotes_payload and self.reagente_service:
            for item in lotes_payload:
                if isinstance(item, (dict, ReagenteCreate, ReagenteUpdate)):
                    dados_lote = item.model_dump() if hasattr(item, "model_dump") else dict(item)
                    dados_lote["reagente_nome"] = novo_nome
                    if novo_codigo and not dados_lote.get("reagente_codigo"):
                        dados_lote["reagente_codigo"] = novo_codigo
                    if "numero_lote" in dados_lote and self.reagente_repo:
                        lote_exist = self.reagente_repo.buscar_por_nome_e_lote(novo_nome, dados_lote["numero_lote"])
                        if lote_exist:
                            self.reagente_service.atualizar_reagente(lote_exist.id, dados_lote)
                        else:
                            self.reagente_service.criar_reagente(dados_lote)

        # Recalcula consolidação
        lotes_atualizados = self.reagente_repo.buscar_por_nome(novo_nome) if self.reagente_repo else []
        estoque_consolidado = self.consolidar_estoque(nome=novo_nome, codigo=novo_codigo, lotes=lotes_atualizados)
        estoque_consolidado.id = estoque_atual.id

        # Se o nome mudou, remove chave antiga do repositório
        if novo_nome != nome_antigo:
            self.estoque_repo.delete(nome_antigo)

        return self.estoque_repo.save(estoque_consolidado)

    def deletar_estoque(
        self,
        identificador: Union[int, str],
        deletar_lotes_vinculados: bool = False,
        usuario: Optional[Any] = None,
    ) -> bool:
        """[DELETE] Remove o registro consolidado de estoque com opção de deleção dos lotes físicos."""
        self._verificar_permissao("deletar_estoque", usuario)
        estoque = self.obter_estoque(identificador, sincronizar=False, usuario=usuario)
        nome = estoque.reagente_nome

        if deletar_lotes_vinculados and self.reagente_repo:
            lotes = self.reagente_repo.buscar_por_nome(nome)
            for lote in lotes:
                self.reagente_repo.delete(lote.id or lote.reagente_id)

        return self.estoque_repo.delete(identificador)

# Instância singleton para injeção de dependência centralizada
estoque_reagente_service = EstoqueReagenteService()

__all__ = [
    "EstoqueReagenteService",
    "estoque_reagente_service",
    "EstoqueReagente",
    "EstoqueReagenteCreate",
    "EstoqueReagenteUpdate",
    "EstoqueReagenteDetails",
]