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
)
from src.models.EstoqueReagente import EstoqueReagente
from src.repositories.reagente_repository import ReagenteRepository, reagente_repository
from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_data,
    normalizar_enum,
)

# Garante compatibilidade dos atributos de estado no modelo Reagente em tempo de execução
if "esta_vencido" not in Reagente.model_fields:
    Reagente.model_fields["esta_vencido"] = FieldInfo(annotation=Optional[bool], default=None)
    Reagente.model_rebuild(force=True)
if "dias_para_vencer" not in Reagente.model_fields:
    Reagente.model_fields["dias_para_vencer"] = FieldInfo(annotation=Optional[int], default=None)
    Reagente.model_rebuild(force=True)

# Fatores para conversão dimensional para unidades base:
# Volume -> base 'ml'
# Massa -> base 'g'
# Unidade -> base 'un'
FATORES_CONVERSAO = {
    # Volume (base: ml)
    "ml": ("volume", 1.0, "ml"),
    "l": ("volume", 1000.0, "ml"),
    "µl": ("volume", 0.001, "ml"),
    "ul": ("volume", 0.001, "ml"),
    # Massa (base: g)
    "g": ("massa", 1.0, "g"),
    "mg": ("massa", 0.001, "g"),
    "kg": ("massa", 1000.0, "g"),
    # Unidade (base: un)
    "un": ("unidade", 1.0, "un"),
}

# Aliases aceitos na entrada da API -> nome canônico dos campos no model Reagente
_ALIASES_REAGENTE = {
    "codigo": "reagente_codigo",
    "id_reagente": "reagente_id",
    "nome": "reagente_nome",
    "lote": "numero_lote",
    "fabricante": "marca",
    "validade": "data_validade",
    "quantidade": "quantidade_unidade",
    "unidades": "quantidade_unidade",
    "volume": "quantidade_volume",
    "massa": "quantidade_volume",
    "unidade": "unidade_medida",
    "etapa": "reagente_etapa",
    "local": "reagente_local_armazenamento",
    "local_armazenamento": "reagente_local_armazenamento",
    "armazenamento": "reagente_local_armazenamento",
    "observacoes": "reagente_observacoes",
    "observacao": "reagente_observacoes",
}

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
    # NORMALIZAÇÃO DE CAMPOS E ENUMS:
    # -------------------------------------------------------------------------
    @staticmethod
    def normalizar_unidade_medida(valor: Any, default: Optional[UnidadeMedida] = UnidadeMedida.ML) -> Optional[UnidadeMedida]:
        """Normaliza variações textuais para o Enum canônico UnidadeMedida."""
        if valor is None or eh_nao_informado(valor):
            return default
        if isinstance(valor, UnidadeMedida):
            return valor

        s = str(valor).strip().lower()
        mapa = {
            "ml": UnidadeMedida.ML,
            "mililitro": UnidadeMedida.ML,
            "mililitros": UnidadeMedida.ML,
            "l": UnidadeMedida.L,
            "litro": UnidadeMedida.L,
            "litros": UnidadeMedida.L,
            "µl": UnidadeMedida.UL,
            "ul": UnidadeMedida.UL,
            "microlitro": UnidadeMedida.UL,
            "microlitros": UnidadeMedida.UL,
            "g": UnidadeMedida.G,
            "gr": UnidadeMedida.G,
            "grama": UnidadeMedida.G,
            "gramas": UnidadeMedida.G,
            "mg": UnidadeMedida.MG,
            "miligrama": UnidadeMedida.MG,
            "miligramas": UnidadeMedida.MG,
            "kg": UnidadeMedida.KG,
            "quilo": UnidadeMedida.KG,
            "quilos": UnidadeMedida.KG,
            "quilograma": UnidadeMedida.KG,
            "quilogramas": UnidadeMedida.KG,
            "un": UnidadeMedida.UNIDADE,
            "unidade": UnidadeMedida.UNIDADE,
            "unidades": UnidadeMedida.UNIDADE,
            "frasco": UnidadeMedida.UNIDADE,
            "frascos": UnidadeMedida.UNIDADE,
        }
        if s in mapa:
            return mapa[s]

        return normalizar_enum(UnidadeMedida, valor, default=default)

    @staticmethod
    def normalizar_etapa_reagente(valor: Any, default: Optional[EtapaReagente] = None) -> Optional[EtapaReagente]:
        """Normaliza variações textuais para o Enum canônico EtapaReagente."""
        if valor is None or eh_nao_informado(valor):
            return default
        if isinstance(valor, EtapaReagente):
            return valor

        s = str(valor).strip().lower()
        if any(k in s for k in ["extra", "ext"]):
            return EtapaReagente.EXTRAÇÃO
        if any(k in s for k in ["pcr", "qpcr", "rt-pcr"]):
            return EtapaReagente.PCR
        if any(k in s for k in ["eletro", "gel", "agarose"]):
            return EtapaReagente.ELETRO

        return normalizar_enum(EtapaReagente, valor, default=default)

    @staticmethod
    def normalizar_data(valor: Any, permitir_none: bool = False) -> Optional[date]:
        return normalizar_data(valor, permitir_none=permitir_none)

    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases aceitos na entrada para os nomes canônicos do domínio Reagente."""
        normalizado: Dict[str, Any] = {}
        for chave, valor in payload.items():
            if chave == "_id":
                if isinstance(valor, int) or (isinstance(valor, str) and valor.strip().isdigit()):
                    canonica = "id"
                    valor = int(valor)
                else:
                    canonica = "reagente_id"
            else:
                canonica = _ALIASES_REAGENTE.get(chave, chave)

            if canonica in normalizado and chave != canonica:
                continue
            normalizado[canonica] = valor
        return normalizado

    # -------------------------------------------------------------------------
    # REGRAS DE NEGÓCIO E CÁLCULOS MATEMÁTICOS / DIMENSIONAIS:
    # -------------------------------------------------------------------------
    @staticmethod
    def validar_lotes_unicos(lotes: List[Reagente]) -> None:
        """Valida se não há números de lote duplicados para o mesmo reagente."""
        numeros_lotes = [str(lote.numero_lote).strip().casefold() for lote in lotes if lote.numero_lote]
        if len(numeros_lotes) != len(set(numeros_lotes)):
            raise ValueError("Não pode haver números de lote repetidos para o mesmo reagente.")

    @staticmethod
    def calcular_vencimento(lote_ou_data: Union[Reagente, date, str]) -> tuple[bool, int]:
        """
        Calcula os indicadores de vencimento para um lote de reagente ou data:
        Retorna (esta_vencido: bool, dias_para_vencer: int).
        """
        if isinstance(lote_ou_data, date):
            dt_validade = lote_ou_data
        elif hasattr(lote_ou_data, "data_validade"):
            dt_validade = lote_ou_data.data_validade
        elif isinstance(lote_ou_data, str):
            dt_validade = date.fromisoformat(lote_ou_data)
        else:
            raise ValueError("O parâmetro deve ser uma instância de Reagente ou um objeto date/str.")

        hoje = date.today()
        esta_vencido = dt_validade < hoje
        dias_para_vencer = (dt_validade - hoje).days
        return esta_vencido, dias_para_vencer

    def calcular_status_validade(self, lote: Reagente) -> tuple[bool, int]:
        """Enriquece a instância de Reagente com os dados de vencimento calculados."""
        vencido, dias = self.calcular_vencimento(lote)
        lote.esta_vencido = vencido
        lote.dias_para_vencer = dias
        return vencido, dias

    @classmethod
    def consolidar_estoque(cls, nome: str, codigo: Optional[str], lotes: List[Reagente]) -> EstoqueReagente:
        """
        Consolida uma lista de lotes em uma instância da entidade EstoqueReagente,
        calculando totais segregados, conversões dimensionais seguras e resumo textual.
        """
        cls.validar_lotes_unicos(lotes)

        qtd_unidades = sum(lote.quantidade_unidade for lote in lotes)
        totais_unidade: Dict[str, float] = {}
        totais_base: Dict[str, float] = {}

        for lote in lotes:
            # Enriquecimento com indicadores de vencimento
            vencido, dias = cls.calcular_vencimento(lote)
            lote.esta_vencido = vencido
            lote.dias_para_vencer = dias

            unidade_raw = (
                lote.unidade_medida.value
                if hasattr(lote.unidade_medida, "value")
                else str(lote.unidade_medida or "ml")
            ).strip()

            # Quantidade total de volume/massa deste lote (multiplica volume unitário pela quantidade de frascos)
            vol_unitario = lote.quantidade_volume
            vol_total_lote = (
                round(vol_unitario * lote.quantidade_unidade, 4)
                if vol_unitario is not None
                else float(lote.quantidade_unidade)
            )

            totais_unidade[unidade_raw] = round(totais_unidade.get(unidade_raw, 0.0) + vol_total_lote, 4)

            if vol_unitario is not None:
                unidade_lower = unidade_raw.lower()
                if unidade_lower in FATORES_CONVERSAO:
                    _, fator, base = FATORES_CONVERSAO[unidade_lower]
                    convertido = round(vol_total_lote * fator, 4)
                    totais_base[base] = round(totais_base.get(base, 0.0) + convertido, 4)
                else:
                    totais_base[unidade_raw] = round(totais_base.get(unidade_raw, 0.0) + vol_total_lote, 4)

        # Determina o volume consolidado principal
        if not totais_base:
            qtd_volume = float(sum((lote.quantidade_volume or 0.0) * lote.quantidade_unidade for lote in lotes))
        elif "ml" in totais_base:
            qtd_volume = totais_base["ml"]
        elif "g" in totais_base:
            qtd_volume = totais_base["g"]
        elif len(totais_base) == 1:
            qtd_volume = next(iter(totais_base.values()))
        else:
            qtd_volume = sum(totais_base.values())

        if qtd_volume is not None:
            qtd_volume = round(qtd_volume, 4)

        # Formata resumo legível
        partes_resumo = [f"{valor:g} {base}" for base, valor in totais_base.items()]
        resumo = ", ".join(partes_resumo) if partes_resumo else f"{qtd_unidades} un"

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
            try:
                qtd_un = int(payload["quantidade_unidade"])
                if qtd_un < 1:
                    raise ValueError("A quantidade de unidades deve ser maior ou igual a 1.")
                payload["quantidade_unidade"] = qtd_un
            except (ValueError, TypeError) as e:
                if "maior ou igual a 1" in str(e):
                    raise
                raise ValueError("Quantidade de unidades inválida.")
        else:
            payload["quantidade_unidade"] = 1

        if "quantidade_volume" in payload and payload["quantidade_volume"] is not None:
            if not eh_nao_informado(payload["quantidade_volume"]):
                try:
                    vol = float(payload["quantidade_volume"])
                    if vol <= 0:
                        raise ValueError("A quantidade de volume/massa deve ser maior que zero.")
                    payload["quantidade_volume"] = vol
                except (ValueError, TypeError) as e:
                    if "maior que zero" in str(e):
                        raise
                    raise ValueError("Quantidade de volume/massa inválida.")
            else:
                payload["quantidade_volume"] = None

        # Normalizações de Enums
        if "unidade_medida" in payload and payload["unidade_medida"] is not None:
            payload["unidade_medida"] = self.normalizar_unidade_medida(payload["unidade_medida"])
        else:
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

        payload = self._normalizar_chaves(payload)

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
        apenas_vencidos: Optional[bool] = None,
        termo_busca: Optional[str] = None,
        ordenar_por: str = "id",
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[Reagente]:
        """[READ] Retorna lista de lotes aplicando filtros laboratoriais, busca textual, ordenação e paginação."""
        self._verificar_permissao("listar_reagentes", usuario)
        lotes = self.reagente_repo.listar(
            nome=nome,
            codigo=codigo,
            marca=marca,
            local_armazenamento=local_armazenamento,
            apenas_vencidos=apenas_vencidos,
            termo_busca=termo_busca,
            ordenar_por=ordenar_por,
            skip=skip,
            limit=limit,
        )
        for lote in lotes:
            self.calcular_status_validade(lote)
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

        novos = self._normalizar_chaves(novos)
        for chave in ("id", "confirmar_atualizacao_reagente", "confirmar_novo_reagente"):
            novos.pop(chave, None)

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
]