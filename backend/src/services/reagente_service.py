from datetime import date
from typing import Optional, Union, List, Dict, Any
from collections import defaultdict
from pydantic.fields import FieldInfo
from src.models.Reagente import (
    Reagente,
    ReagenteCreate,
    ReagenteUpdate,
    ReagenteDetails,
    EtapaReagente,
    UnidadeMedida,
    StatusReagente,
)
from src.models.EstoqueReagente import EstoqueReagente
from src.repositories.reagente_repository import ReagenteRepository, reagente_repository
from src.utils.repositorio import _CAMPOS_PROIBIDOS_ENTRADA
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_data,
    normalizar_unidade_medida,
    normalizar_etapa_reagente,
    normalizar_status_reagente,
    normalizar_quantidade_unidade,
    normalizar_quantidade_volume,
    normalizar_chaves_reagente,
    validar_lotes_unicos,
    calcular_vencimento,
    calcular_metricas_estoque,
    FATORES_CONVERSAO,
)

# Garante compatibilidade dos atributos de estado no modelo Reagente em tempo de execução
if "esta_vencido" not in Reagente.model_fields:
    Reagente.model_fields["esta_vencido"] = FieldInfo(annotation=Optional[bool], default=None)
    Reagente.model_rebuild(force=True)
if "dias_para_vencer" not in Reagente.model_fields:
    Reagente.model_fields["dias_para_vencer"] = FieldInfo(annotation=Optional[int], default=None)
    Reagente.model_rebuild(force=True)

# Rótulos amigáveis para mensagens de erro de validação
_ROTULOS_CAMPOS = {
    "reagente_codigo": "código do reagente (codigo)",
    "reagente_nome": "nome do reagente (nome)",
    "numero_lote": "número do lote (numero_lote)",
    "marca": "marca / fabricante (marca)",
    "data_validade": "data de validade (data_validade)",
    "quantidade_unidade": "quantidade de unidades (quantidade_unidade)",
    "reagente_local_armazenamento": "local de armazenamento (local_armazenamento)",
    "reagente_id": "identificador padrão do laboratório (reagente_id)",
    "quantidade_volume": "quantidade de volume/massa (quantidade_volume)",
    "unidade_medida": "unidade de medida (unidade_medida)",
    "reagente_etapa": "etapa do reagente (reagente_etapa)",
    "reagente_observacoes": "observações do reagente (reagente_observacoes)",
}

_CAMPOS_OBRIGATORIOS_REAGENTE = [
    "reagente_codigo",
    "reagente_nome",
    "numero_lote",
    "marca",
    "data_validade",
    "reagente_local_armazenamento",
]

class ReagenteService:
    """
    Serviço responsável pelas regras de negócio e ciclo de vida da entidade Reagente (lotes físicos):
    - [CREATE] Validação de campos obrigatórios, datas de validade, integridade de lote por reagente,
      cálculo de status de vencimento e sincronização com a visão agregada de EstoqueReagente.
    - [READ] Consultas por ID numérico ou código do laboratório (reagente_id), listagem com múltiplos
      filtros combinados, busca textual e enriquecimento em ReagenteDetails.
    - [UPDATE] Atualização com checagem de integridade referencial, recalculo de validade e sincronização
      do estoque agregado correspondente.
    - [DELETE] Remoção com validação de existência e sincronização automática do estoque consolidado.
    - [CONSOLIDAÇÃO] Fórmulas de conversão dimensional e unificação de estoques por nome de reagente.
    """

    def __init__(
        self,
        reagente_repo: Optional[ReagenteRepository] = None,
        estoque_service: Optional[Any] = None,
        estoque_repo: Optional[Any] = None,
    ):
        self.reagente_repo = reagente_repo or reagente_repository
        self._estoque_service = estoque_service
        self._estoque_repo = estoque_repo

    @property
    def estoque_service(self) -> Any:
        if self._estoque_service is None:
            try:
                from src.services.estoque_reagente_service import estoque_reagente_service
                self._estoque_service = estoque_reagente_service
            except ImportError:
                self._estoque_service = None
        return self._estoque_service

    @property
    def estoque_repo(self) -> Any:
        if self._estoque_repo is None:
            try:
                from src.repositories.estoque_reagente_repository import estoque_reagente_repository
                self._estoque_repo = estoque_reagente_repository
            except ImportError:
                self._estoque_repo = None
        return self._estoque_repo

    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """Gancho para aplicação de controle de acesso baseado em papéis (RBAC)."""
        pass

    # -------------------------------------------------------------------------
    # NORMALIZAÇÃO DE CAMPOS E ENUMS (Delegação direta para src.utils.normalizacao):
    # -------------------------------------------------------------------------
    @staticmethod
    def normalizar_unidade_medida(valor: Any, default: Optional[UnidadeMedida] = UnidadeMedida.ML) -> Optional[UnidadeMedida]:
        """Normaliza variações textuais para o Enum canônico UnidadeMedida."""
        return normalizar_unidade_medida(valor, default=default)

    @staticmethod
    def normalizar_etapa_reagente(valor: Any, default: Optional[EtapaReagente] = None) -> Optional[EtapaReagente]:
        """Normaliza variações textuais para o Enum canônico EtapaReagente."""
        return normalizar_etapa_reagente(valor, default=default)

    @staticmethod
    def normalizar_status_reagente(valor: Any, default: Optional[StatusReagente] = StatusReagente.DISPONIVEL) -> Optional[StatusReagente]:
        """Normaliza variações textuais para o Enum canônico StatusReagente."""
        return normalizar_status_reagente(valor, default=default)

    @staticmethod
    def normalizar_data(valor: Any, permitir_none: bool = False) -> Optional[date]:
        return normalizar_data(valor, permitir_none=permitir_none)

    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases aceitos na entrada para os nomes canônicos do domínio Reagente."""
        return normalizar_chaves_reagente(payload)

    # -------------------------------------------------------------------------
    # REGRAS DE NEGÓCIO E CÁLCULOS MATEMÁTICOS / DIMENSIONAIS:
    # -------------------------------------------------------------------------
    @staticmethod
    def validar_lotes_unicos(lotes: List[Reagente]) -> None:
        """Valida se não há números de lote duplicados para o mesmo reagente."""
        validar_lotes_unicos(lotes)

    @staticmethod
    def calcular_vencimento(lote_ou_data: Union[Reagente, date, str]) -> tuple[bool, int]:
        """
        Calcula os indicadores de vencimento para um lote de reagente ou data:
        Retorna (esta_vencido: bool, dias_para_vencer: int).
        """
        return calcular_vencimento(lote_ou_data)

    def calcular_status_validade(self, lote: Reagente) -> tuple[bool, int]:
        """
        Enriquece a instância de Reagente com os dados de vencimento calculados.
        Regra de status automático:
        - Se o lote estiver vencido:
            * Se o status for 'Esgotado', NÃO vira 'Vencido'.
            * Se for 'Disponível' ou 'Reservado', vira 'Vencido' automaticamente.
        """
        vencido, dias = self.calcular_vencimento(lote)
        lote.esta_vencido = vencido
        lote.dias_para_vencer = dias

        if vencido and lote.status_reagente != StatusReagente.ESGOTADO:
            lote.status_reagente = StatusReagente.VENCIDO

        return vencido, dias

    @classmethod
    def consolidar_estoque(cls, nome: str, codigo: Optional[str], lotes: List[Reagente]) -> EstoqueReagente:
        """
        Consolida uma lista de lotes em uma instância da entidade EstoqueReagente,
        calculando totais segregados, conversões dimensionais seguras e resumo textual.
        """
        qtd_unidades, qtd_volume, totais_unidade, totais_base, resumo = calcular_metricas_estoque(lotes)
        return EstoqueReagente(
            reagente_nome=nome,
            reagente_codigo=codigo,
            lotes=lotes,
            quantidade_total_unidades=qtd_unidades,
            quantidade_total_volume=qtd_volume,
            totais_por_unidade=totais_unidade,
            totais_convertidos_base=totais_base,
            resumo_estoque=resumo,
        )

    @classmethod
    def agrupar_por_nome(cls, reagentes: List[Reagente]) -> Dict[str, EstoqueReagente]:
        """
        Recebe uma lista de instâncias de Reagente (lotes) e agrupa por nome.
        Retorna um dicionário mapeando o nome do reagente para EstoqueReagente consolidado.
        """
        grupos: Dict[str, List[Reagente]] = defaultdict(list)
        for r in reagentes:
            grupos[r.reagente_nome].append(r)

        estoque: Dict[str, EstoqueReagente] = {}
        for nome, lotes in grupos.items():
            codigo = lotes[0].reagente_codigo if lotes else None
            estoque[nome] = cls.consolidar_estoque(nome=nome, codigo=codigo, lotes=lotes)
        return estoque

    # -------------------------------------------------------------------------
    # VALIDAÇÃO DE CAMPOS E OBRIGATORIEDADE:
    # -------------------------------------------------------------------------
    def aplicar_obrigatoriedade(
        self,
        payload: Dict[str, Any],
        campos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aplica regras estritas e uniformes de obrigatoriedade sobre os campos do lote de reagente.
        Rejeita com ValueError qualquer campo obrigatório ausente, vazio ou 'Não informado'.
        """
        verificar = set(campos) if campos is not None else set(_CAMPOS_OBRIGATORIOS_REAGENTE)
        faltantes: List[str] = []

        for campo in sorted(verificar):
            valor = payload.get(campo)

            if campo == "data_validade":
                if eh_nao_informado(valor):
                    faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                else:
                    try:
                        payload[campo] = self.normalizar_data(valor, permitir_none=False)
                    except ValueError:
                        faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))
                continue

            if eh_nao_informado(valor):
                faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))

        if faltantes:
            raise ValueError(
                "Campos obrigatórios do reagente ausentes ou 'Não informado': " + ", ".join(faltantes) + "."
            )

        # Validação numérica de quantidades
        if "quantidade_unidade" in payload and payload["quantidade_unidade"] is not None:
            payload["quantidade_unidade"] = normalizar_quantidade_unidade(payload["quantidade_unidade"])
        elif campos is None:
            payload["quantidade_unidade"] = 1

        if "quantidade_volume" in payload and payload["quantidade_volume"] is not None:
            payload["quantidade_volume"] = normalizar_quantidade_volume(payload["quantidade_volume"])

        # Normalizações de Enums
        if "unidade_medida" in payload and payload["unidade_medida"] is not None:
            payload["unidade_medida"] = self.normalizar_unidade_medida(payload["unidade_medida"])
        elif campos is None:
            payload["unidade_medida"] = UnidadeMedida.ML

        if "reagente_etapa" in payload and payload["reagente_etapa"] is not None:
            payload["reagente_etapa"] = self.normalizar_etapa_reagente(payload["reagente_etapa"])

        return payload

    # -------------------------------------------------------------------------
    # CONSULTA DETALHADA E CONSTRUÇÃO DE SCHEMAS (ReagenteDetails):
    # -------------------------------------------------------------------------
    @classmethod
    def preencher_nao_informados(cls, data: Any) -> ReagenteDetails:
        """Sanitiza os dados de um lote de reagente e constrói o schema detalhado ReagenteDetails."""
        if hasattr(data, "model_dump"):
            payload = data.model_dump(by_alias=True)
        elif hasattr(data, "__dict__") and not isinstance(data, dict):
            payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados do reagente devem ser um dicionário ou objeto compatível.")

        payload = cls._normalizar_chaves(payload)

        # Preserva reagente_id caso venha via _id ou id numérico
        if not payload.get("reagente_id"):
            if "_id" in payload and isinstance(payload["_id"], str):
                payload["reagente_id"] = payload["_id"]
            elif "id" in payload and payload["id"] is not None:
                payload["reagente_id"] = f"REA_{int(payload['id']):04d}"

        # Enriquecimento com indicadores de vencimento calculados
        if payload.get("data_validade"):
            vencido, dias = cls.calcular_vencimento(payload["data_validade"])
            payload["esta_vencido"] = vencido
            payload["dias_para_vencer"] = dias

        # Sincronização entre observacoes e reagente_observacoes
        if "observacoes" in payload and not payload.get("reagente_observacoes"):
            payload["reagente_observacoes"] = payload["observacoes"]

        # Campos opcionais limpos
        for campo in ["reagente_observacoes", "quantidade_volume", "reagente_etapa"]:
            if eh_nao_informado(payload.get(campo)):
                payload[campo] = None

        st_raw = payload.get("status_reagente") or payload.get("status")
        if st_raw:
            st = normalizar_status_reagente(st_raw)
        else:
            st = StatusReagente.DISPONIVEL

        if payload.get("esta_vencido") and st != StatusReagente.ESGOTADO:
            st = StatusReagente.VENCIDO

        payload["status_reagente"] = st

        return ReagenteDetails(**payload)

    montar_reagente_detalhes = preencher_nao_informados

    def obter_reagente_detalhes(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> ReagenteDetails:
        """[READ] Retorna os detalhes estruturados de um lote físico com status de vencimento enriquecido."""
        self._verificar_permissao("obter_reagente", usuario)
        reagente = self.obter_reagente(identificador, usuario=usuario)
        return self.preencher_nao_informados(reagente)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def criar_reagente(
        self,
        dados_reagente: Union[Dict[str, Any], ReagenteCreate],
        confirmar_novo_reagente: bool = False,
        usuario: Optional[Any] = None,
    ) -> Reagente:
        """[CREATE] Valida e persiste um novo lote físico de reagente e sincroniza o estoque consolidado."""
        self._verificar_permissao("criar_reagente", usuario)

        if isinstance(dados_reagente, ReagenteCreate):
            payload = dados_reagente.model_dump(by_alias=True)
            conf_reagente = dados_reagente.confirmar_novo_reagente or confirmar_novo_reagente
        else:
            payload = dict(dados_reagente)
            conf_reagente = payload.pop("confirmar_novo_reagente", False) or confirmar_novo_reagente

        # A chave primária (id/_id) é gerada automaticamente pelo banco/repositório:
        # nunca é aceita na entrada do usuário.
        for chave in _CAMPOS_PROIBIDOS_ENTRADA:
            payload.pop(chave, None)

        payload = self._normalizar_chaves(payload)
        for chave in (*_CAMPOS_PROIBIDOS_ENTRADA, "confirmar_novo_reagente"):
            payload.pop(chave, None)

        # Checagem de unicidade do reagente_id se informado explicitamente
        rid = payload.get("reagente_id")
        if rid and not eh_nao_informado(rid):
            rid_str = str(rid).strip()
            if self.reagente_repo.exists(rid_str):
                raise ValueError(f"Já existe um reagente cadastrado com o identificador '{rid_str}'.")
            payload["reagente_id"] = rid_str

        self.aplicar_obrigatoriedade(payload)

        # Validação de lote duplicado para o mesmo reagente
        nome = payload["reagente_nome"].strip()
        lote_num = payload["numero_lote"].strip()
        existente = self.reagente_repo.buscar_por_nome_e_lote(nome, lote_num)
        if existente:
            raise ValueError(f"Lote '{lote_num}' já cadastrado para o reagente '{nome}'.")

        # Calcula status de vencimento inicial
        vencido, dias = self.calcular_vencimento(payload["data_validade"])
        payload["esta_vencido"] = vencido
        payload["dias_para_vencer"] = dias

        # Regras de validação e atribuição de StatusReagente:
        st_input = payload.get("status_reagente") or payload.get("status")
        if st_input is not None:
            st_norm = normalizar_status_reagente(st_input)
        else:
            st_norm = StatusReagente.DISPONIVEL

        # O usuário não deve poder colocar como vencido um reagente que não está vencido
        if st_norm == StatusReagente.VENCIDO and not vencido:
            raise ValueError("Não é permitido definir o status como Vencido para um reagente cuja data de validade não expirou.")

        # Status alterado automaticamente para vencido se expirado (exceto se esgotado)
        if vencido and st_norm != StatusReagente.ESGOTADO:
            st_norm = StatusReagente.VENCIDO

        payload["status_reagente"] = st_norm

        reagente = Reagente(**payload)
        reagente_salvo = self.reagente_repo.create(reagente)

        # Dispara sincronização / consolidação automática na visão de EstoqueReagente
        self.sincronizar_estoque(reagente_salvo.reagente_nome)

        return reagente_salvo

    def obter_reagente(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> Reagente:
        """[READ] Recupera um lote de reagente pelo ID sequencial numérico ou pelo código único (reagente_id)."""
        self._verificar_permissao("obter_reagente", usuario)
        reagente = self.reagente_repo.buscar_por_id(identificador) or self.reagente_repo.buscar_por_reagente_id(str(identificador))
        if not reagente:
            raise KeyError(f"Reagente com identificador '{identificador}' não encontrado.")

        self.calcular_status_validade(reagente)
        return reagente

    def obter_reagente_por_id(self, id_numerico: Union[int, str], usuario: Optional[Any] = None) -> Reagente:
        """[READ] Recupera um lote de reagente pelo identificador sequencial numérico do banco."""
        self._verificar_permissao("obter_reagente", usuario)
        reagente = self.reagente_repo.buscar_por_id(id_numerico)
        if not reagente:
            raise KeyError(f"Reagente com ID numérico '{id_numerico}' não encontrado.")

        self.calcular_status_validade(reagente)
        return reagente

    def obter_reagente_por_reagente_id(self, reagente_id: str, usuario: Optional[Any] = None) -> Reagente:
        """[READ] Recupera um lote de reagente pelo identificador padrão de laboratório (ex: 'REA_0001')."""
        self._verificar_permissao("obter_reagente", usuario)
        reagente = self.reagente_repo.buscar_por_reagente_id(reagente_id)
        if not reagente:
            raise KeyError(f"Reagente com reagente_id '{reagente_id}' não encontrado.")

        self.calcular_status_validade(reagente)
        return reagente

    def listar_reagentes(
        self,
        nome: Optional[str] = None,
        codigo: Optional[str] = None,
        marca: Optional[str] = None,
        local_armazenamento: Optional[str] = None,
        status: Optional[Union[StatusReagente, str]] = None,
        apenas_vencidos: Optional[bool] = None,
        termo_busca: Optional[str] = None,
        ordenar_por: str = "id",
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[Reagente]:
        """[READ] Retorna lista de lotes aplicando filtros laboratoriais, busca textual, ordenação e paginação."""
        self._verificar_permissao("listar_reagentes", usuario)
        status_norm = normalizar_status_reagente(status) if status else None
        lotes = self.reagente_repo.listar(
            nome=nome,
            codigo=codigo,
            marca=marca,
            local_armazenamento=local_armazenamento,
            status=status_norm,
            apenas_vencidos=apenas_vencidos,
            termo_busca=termo_busca,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )
        for lote in lotes:
            self.calcular_status_validade(lote)
        if status_norm:
            lotes = [l for l in lotes if l.status_reagente == status_norm]
        return lotes

    def listar_por_lote(self, numero_lote: str, usuario: Optional[Any] = None) -> List[Reagente]:
        """[READ] Retorna todos os lotes que possuem o número identificador de lote informado."""
        self._verificar_permissao("listar_reagentes", usuario)
        lotes = self.reagente_repo.buscar_por_lote(numero_lote)
        for lote in lotes:
            self.calcular_status_validade(lote)
        return lotes

    def contar_reagentes(self, usuario: Optional[Any] = None) -> int:
        """[READ] Retorna o total de lotes físicos registrados no banco."""
        self._verificar_permissao("contar_reagentes", usuario)
        return self.reagente_repo.count()

    def existe_reagente(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> bool:
        """[READ] Verifica se existe um lote físico registrado com o identificador fornecido."""
        self._verificar_permissao("obter_reagente", usuario)
        return self.reagente_repo.exists(identificador)

    def atualizar_reagente(
        self,
        identificador: Union[int, str],
        dados_atualizacao: Union[Dict[str, Any], ReagenteUpdate],
        confirmar_atualizacao_reagente: bool = False,
        usuario: Optional[Any] = None,
    ) -> Reagente:
        """[UPDATE] Atualização parcial de lote físico existente e ressincronização do estoque agregado."""
        self._verificar_permissao("atualizar_reagente", usuario)
        reagente_atual = self.obter_reagente(identificador, usuario=usuario)
        nome_antigo = reagente_atual.reagente_nome

        if isinstance(dados_atualizacao, ReagenteUpdate):
            novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
        else:
            novos = {k: v for k, v in dados_atualizacao.items() if v is not None}

        for chave in _CAMPOS_PROIBIDOS_ENTRADA:
            novos.pop(chave, None)

        novos = self._normalizar_chaves(novos)
        for chave in (*_CAMPOS_PROIBIDOS_ENTRADA, "confirmar_atualizacao_reagente", "confirmar_novo_reagente"):
            novos.pop(chave, None)
        novos = {k: v for k, v in novos.items() if v is not None}

        payload = self._normalizar_chaves(reagente_atual.model_dump(by_alias=True))

        # Se alterar o reagente_id, valida unicidade
        novo_rid = novos.get("reagente_id")
        if novo_rid and hasattr(reagente_atual, "reagente_id") and novo_rid != getattr(reagente_atual, "reagente_id"):
            rid_str = str(novo_rid).strip()
            if self.reagente_repo.exists(rid_str):
                raise ValueError(f"Já existe outro reagente cadastrado com o identificador '{rid_str}'.")
            novos["reagente_id"] = rid_str

        # Se alterar número do lote ou nome, verifica duplicata de lote
        novo_nome = novos.get("reagente_nome", reagente_atual.reagente_nome)
        novo_num_lote = novos.get("numero_lote", reagente_atual.numero_lote)
        if novo_nome != reagente_atual.reagente_nome or novo_num_lote != reagente_atual.numero_lote:
            lote_existente = self.reagente_repo.buscar_por_nome_e_lote(novo_nome, novo_num_lote)
            if lote_existente and int(lote_existente.id) != int(reagente_atual.id):
                raise ValueError(f"Lote '{novo_num_lote}' já cadastrado para o reagente '{novo_nome}'.")

        # Valida campos enviados
        enviados = [c for c in novos if c in _CAMPOS_OBRIGATORIOS_REAGENTE or c in ("quantidade_unidade", "quantidade_volume")]
        if enviados:
            self.aplicar_obrigatoriedade(novos, campos=enviados)

        payload.update(novos)

        # Garante integridade de identificadores
        if reagente_atual.id is not None:
            payload["id"] = reagente_atual.id
        if getattr(reagente_atual, "reagente_id", None):
            payload["reagente_id"] = getattr(reagente_atual, "reagente_id")

        # Recalcula indicadores de vencimento
        vencido, dias = self.calcular_vencimento(payload["data_validade"])
        payload["esta_vencido"] = vencido
        payload["dias_para_vencer"] = dias

        # Verificação e regras de transição de status:
        status_atual = reagente_atual.status_reagente
        novo_status = novos.get("status_reagente") or novos.get("status")

        if novo_status is not None:
            novo_status = normalizar_status_reagente(novo_status)

            # Regra: se estiver como esgotado ele não vira vencido e se estiver como vencido ele não vira esgotado
            if status_atual == StatusReagente.VENCIDO and novo_status == StatusReagente.ESGOTADO:
                raise ValueError("Reagente com status Vencido não pode ser alterado para Esgotado.")

            if status_atual == StatusReagente.ESGOTADO and novo_status == StatusReagente.VENCIDO:
                raise ValueError("Reagente com status Esgotado não pode ser alterado para Vencido.")

            # Regra: o usuário não deve poder colocar como vencido um reagente que não está vencido
            if novo_status == StatusReagente.VENCIDO and not vencido:
                raise ValueError("Não é permitido definir o status como Vencido para um reagente cuja data de validade não expirou.")

            # Se venceu e não é esgotado, atualiza automaticamente para Vencido
            if vencido and novo_status != StatusReagente.ESGOTADO:
                novo_status = StatusReagente.VENCIDO

            payload["status_reagente"] = novo_status
        else:
            # Novo status não informado explicitamente no update:
            # Se já era ESGOTADO, não vira VENCIDO mesmo expirado
            if status_atual == StatusReagente.ESGOTADO:
                payload["status_reagente"] = StatusReagente.ESGOTADO
            elif vencido:
                payload["status_reagente"] = StatusReagente.VENCIDO
            elif status_atual == StatusReagente.VENCIDO and not vencido:
                # Caso a validade tenha sido estendida para o futuro: deixa de ser Vencido
                payload["status_reagente"] = StatusReagente.DISPONIVEL
            else:
                payload["status_reagente"] = status_atual

        reagente_modificado = Reagente(**payload)
        reagente_salvo = self.reagente_repo.update(identificador, reagente_modificado)

        # Ressincroniza o estoque agregado
        self.sincronizar_estoque(nome_antigo)
        if reagente_salvo.reagente_nome != nome_antigo:
            self.sincronizar_estoque(reagente_salvo.reagente_nome)

        return reagente_salvo

    def deletar_reagente(self, identificador: Union[int, str], usuario: Optional[Any] = None) -> bool:
        """[DELETE] Remove um lote físico do acervo e recalcula a consolidação de estoque."""
        self._verificar_permissao("deletar_reagente", usuario)
        reagente = self.obter_reagente(identificador, usuario=usuario)
        nome = reagente.reagente_nome

        removido = self.reagente_repo.delete(identificador)
        if removido:
            self.sincronizar_estoque(nome)
        return removido

    def sincronizar_estoque(self, nome_reagente: str) -> Optional[Any]:
        """Sincroniza o estoque consolidado correspondente ao reagente após alterações em seus lotes."""
        if not nome_reagente:
            return None
        if self.estoque_service and hasattr(self.estoque_service, "sincronizar_lotes"):
            try:
                return self.estoque_service.sincronizar_lotes(nome_reagente)
            except Exception:
                pass
        return None

# Instância singleton para injeção de dependência centralizada
reagente_service = ReagenteService()

__all__ = [
    "ReagenteService",
    "reagente_service",
    "FATORES_CONVERSAO",
    "Reagente",
    "ReagenteCreate",
    "ReagenteUpdate",
    "ReagenteDetails",
    "EtapaReagente",
    "UnidadeMedida",
    "StatusReagente",
]