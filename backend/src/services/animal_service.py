import re
from enum import Enum
from typing import Optional, Union, List, Dict, Any
from src.models.Animal import (
    Animal,
    AnimalCreate,
    AnimalUpdate,
    AnimalDetails,
    Sexo,
    FaixaEtaria,
    RegimeVida,
    StatusVital,
    Orgao,
    Funcao,
    UnidadePeso,
    UnidadeIdade,
)
from src.models.Especie import Classe, Especie
from src.models.Amostra import Amostra
from src.services.especie_service import EspecieService, especie_service
from src.repositories.animal_repository import AnimalRepository, animal_repository
from src.domain.normalizacao import (
    eh_nao_informado,
    normalizar_peso,
    validar_peso,
    deduzir_faixa_etaria,
    normalizar_sexo,
    normalizar_status_vital,
    decompor_peso,
    decompor_idade,
    normalizar_unidade_peso,
    normalizar_unidade_idade,
    decompor_localidade,
)


# Valores (normalizados em minúsculo) tratados como "vazio / não informado".
_VALORES_NAO_INFORMADOS = {
    "", "-", "ni", "none", "null", "n/a", "na",
    "não informado", "nao informado",
}
_VALORES_NAO_AFERIDO = {"não aferido", "nao aferido"}

# Aliases aceitos na entrada -> nome canônico do campo no model Animal.
_ALIASES_ANIMAL = {
    "orgao": "orgao_origem",
    "status": "regime_vida",
    "observacoes": "animal_observacoes",
}

# Campos obrigatórios (exceto peso e faixa_etaria, que têm regras próprias)
# e o valor usado para preenchê-los na carga de planilhas legadas.
_OBRIGATORIOS_COM_PADRAO_LEGADO: Dict[str, Any] = {
    "sexo": Sexo.NAO_INFORMADO,
    "orgao_origem": Orgao.NAO_INFORMADO,
    "local_origem": "Não informado",
    "regime_vida": RegimeVida.NAO_INFORMADO,
    "status_vital": StatusVital.NAO_INFORMADO,
}

_ROTULOS_CAMPOS = {
    "sexo": "sexo",
    "orgao_origem": "órgão de origem (orgao)",
    "local_origem": "local de origem",
    "regime_vida": "regime de vida (status)",
    "status_vital": "status vital",
    "faixa_etaria": "faixa etária (ou idade)",
    "peso": "peso",
}


class AnimalService:
    """
    Serviço responsável pelas ações de negócio e ciclo de vida da entidade Animal:
    - [CREATE] Validação de ID único, resolução taxonômica via EspecieService,
      processamento/sanitização de peso e inferência de faixa etária.
    - [READ] Obtenção por ID, listagem com filtros e contagem.
    - [UPDATE] Atualização com revalidação de espécie, biometria e idade.
    - [DELETE] Exclusão com validação de existência.
    - Orquestração de persistência através do AnimalRepository.
    - Gancho preparado para regras de autorização/permissão de perfis (RBAC).
    """

    def __init__(
        self,
        especie_serv: Optional[EspecieService] = None,
        animal_repo: Optional[AnimalRepository] = None,
    ):
        self.especie_service = especie_serv or especie_service
        self.animal_repo = animal_repo or animal_repository

    # -------------------------------------------------------------------------
    # GANCHOS PARA REGRAS DE PERMISSÃO (EM BREVE):
    # -------------------------------------------------------------------------
    def _verificar_permissao(self, acao: str, usuario: Optional[Any] = None) -> None:
        """
        Gancho preparado para aplicação de controle de acesso baseado em papéis (RBAC).
        No momento, todas as ações são permitidas.
        """
        pass

    # -------------------------------------------------------------------------
    # TRATAMENTO DE BIOMETRIA E PESO:
    # -------------------------------------------------------------------------
    @staticmethod
    def processar_biometria_peso(
        peso: Any = None,
        peso_valor: Optional[float] = None,
        peso_unidade: Optional[Union[UnidadePeso, str]] = None,
    ) -> tuple[Union[float, str], Optional[float], Optional[UnidadePeso]]:
        """
        Decompõe e normaliza informações de peso retornando a tupla:
        (peso_canonico_kg, peso_valor, peso_unidade)
        """
        return decompor_peso(peso_bruto=peso, peso_valor=peso_valor, peso_unidade=peso_unidade)

    @staticmethod
    def processar_peso(v: Any) -> Union[float, str]:
        """Sanitiza e converte strings de peso para float em kg ou 'Não aferido'."""
        return normalizar_peso(v)

    @staticmethod
    def validar_peso(peso: Union[float, str]) -> None:
        """Garante que peso numérico seja estritamente maior que zero."""
        validar_peso(peso)

    # -------------------------------------------------------------------------
    # TRATAMENTO DE IDADE E FAIXA ETÁRIA:
    # -------------------------------------------------------------------------
    @staticmethod
    def processar_biometria_idade(
        idade: Optional[str] = None,
        idade_valor: Optional[float] = None,
        idade_unidade: Optional[Union[UnidadeIdade, str]] = None,
    ) -> tuple[Optional[str], Optional[float], Optional[UnidadeIdade]]:
        """
        Decompõe e normaliza informações de idade retornando a tupla:
        (idade_formatada, idade_valor, idade_unidade)
        """
        return decompor_idade(idade_str=idade, idade_valor=idade_valor, idade_unidade=idade_unidade)

    @staticmethod
    def deduzir_faixa_etaria(
        idade_str: Optional[str] = None,
        idade_valor: Optional[float] = None,
        idade_unidade: Optional[Union[UnidadeIdade, str]] = None,
    ) -> Optional[FaixaEtaria]:
        """Calcula a faixa etária com base na string de idade informada ou par valor + unidade."""
        return deduzir_faixa_etaria(idade_str=idade_str, idade_valor=idade_valor, idade_unidade=idade_unidade)

    # -------------------------------------------------------------------------
    # OBRIGATORIEDADE DE CAMPOS (NOVOS CADASTROS x CARGA LEGADA):
    # -------------------------------------------------------------------------
    @staticmethod
    def _normalizar_chaves(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Converte aliases (orgao, status, observacoes) para os nomes canônicos."""
        normalizado: Dict[str, Any] = {}
        for chave, valor in payload.items():
            canonica = _ALIASES_ANIMAL.get(chave, chave)
            # Se alias e nome canônico vierem juntos, prevalece o nome canônico.
            if canonica in normalizado and chave != canonica:
                continue
            normalizado[canonica] = valor
        return normalizado

    @staticmethod
    def _eh_nao_informado(valor: Any) -> bool:
        """True se o valor é nulo, vazio ou um sentinela 'Não informado'."""
        return eh_nao_informado(valor)

    def processar_peso_obrigatorio(
        self,
        v: Any = None,
        peso_valor: Optional[float] = None,
        peso_unidade: Optional[Union[UnidadePeso, str]] = None,
    ) -> tuple[Union[float, str], Optional[float], Optional[UnidadePeso]]:
        """
        Versão estrita de processamento de peso para novos cadastros:
        exige número > 0 (aceita valor + unidade, '400g', '2,5kg', etc.) ou a marcação explícita 'Não aferido'.
        Retorna a tupla (peso_canonico_kg, peso_valor, peso_unidade).
        Valores ausentes, vazios ou não reconhecidos são rejeitados.
        """
        if self._eh_nao_informado(v) and self._eh_nao_informado(peso_valor):
            raise ValueError(
                "O campo 'peso' é obrigatório: informe o peso em kg, g ou mg (> 0) ou 'Não aferido'."
            )
        explicito_nao_aferido = (
            (isinstance(v, str) and v.strip().casefold() in _VALORES_NAO_AFERIDO)
            or (isinstance(peso_valor, str) and str(peso_valor).strip().casefold() in _VALORES_NAO_AFERIDO)
        )
        peso_kg, val, unid = self.processar_biometria_peso(peso=v, peso_valor=peso_valor, peso_unidade=peso_unidade)
        if peso_kg == "Não aferido" and not explicito_nao_aferido:
            raise ValueError(
                f"Peso inválido: '{v or peso_valor}'. Informe o peso em kg, g ou mg (> 0) ou 'Não aferido'."
            )
        self.validar_peso(peso_kg)
        return peso_kg, val, unid

    def aplicar_obrigatoriedade(
        self,
        payload: Dict[str, Any],
        carga_legada: bool = False,
        campos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Aplica as regras de obrigatoriedade sobre um payload com chaves canônicas.

        - carga_legada=False (padrão: API / novos cadastros): rejeita com ValueError
          qualquer campo obrigatório ausente, vazio ou 'Não informado'.
          Peso deve ser > 0 ou 'Não aferido' explícito.
          Faixa etária deve ser informada ou deduzível a partir da idade.
        - carga_legada=True (importação de planilhas antigas): preenche as ausências
          com 'Não informado' / 'Não aferido'.

        `campos` restringe a verificação a um subconjunto (usado em atualizações parciais).
        """
        verificar = set(campos) if campos is not None else (
            set(_OBRIGATORIOS_COM_PADRAO_LEGADO) | {"peso", "faixa_etaria"}
        )

        # Peso
        if "peso" in verificar or "peso_valor" in verificar or "peso_unidade" in verificar:
            p_bruto = payload.get("peso")
            p_val = payload.get("peso_valor")
            p_unid = payload.get("peso_unidade")
            if carga_legada:
                peso_kg, val, unid = self.processar_biometria_peso(p_bruto, p_val, p_unid)
                self.validar_peso(peso_kg)
            else:
                peso_kg, val, unid = self.processar_peso_obrigatorio(p_bruto, p_val, p_unid)
            payload["peso"] = peso_kg
            payload["peso_valor"] = val
            payload["peso_unidade"] = unid

        # Idade estruturada
        idade_str = payload.get("idade")
        idade_val = payload.get("idade_valor")
        idade_unid = payload.get("idade_unidade")
        if idade_str is not None or idade_val is not None:
            fmt_i, val_i, unid_i = self.processar_biometria_idade(idade_str, idade_val, idade_unid)
            if fmt_i is not None:
                payload["idade"] = fmt_i
            payload["idade_valor"] = val_i
            payload["idade_unidade"] = unid_i

        # Faixa etária (dedução automática a partir da idade quando ausente)
        if "faixa_etaria" in verificar:
            if self._eh_nao_informado(payload.get("faixa_etaria")):
                faixa_deduzida = self.deduzir_faixa_etaria(
                    idade_str=payload.get("idade"),
                    idade_valor=payload.get("idade_valor"),
                    idade_unidade=payload.get("idade_unidade"),
                )
                if faixa_deduzida:
                    payload["faixa_etaria"] = faixa_deduzida

        # Decomposição e estruturação de localidade (municipio, uf, localidade_detalhe, local_origem)
        loc = payload.get("local_origem")
        mun = payload.get("municipio")
        uf_val = payload.get("uf")
        det = payload.get("localidade_detalhe")
        if loc or mun or uf_val or det:
            n_mun, n_uf, n_det, n_loc = decompor_localidade(loc, mun, uf_val, det)
            if n_mun:
                payload["municipio"] = n_mun
            if n_uf:
                payload["uf"] = n_uf
            if n_det:
                payload["localidade_detalhe"] = n_det
            if n_loc and not self._eh_nao_informado(n_loc):
                payload["local_origem"] = n_loc

        faltantes: List[str] = []
        for campo in sorted(verificar - {"peso", "peso_valor", "peso_unidade"}):
            if not self._eh_nao_informado(payload.get(campo)):
                continue
            if carga_legada:
                payload[campo] = (
                    FaixaEtaria.NAO_INFORMADO if campo == "faixa_etaria"
                    else _OBRIGATORIOS_COM_PADRAO_LEGADO[campo]
                )
            else:
                faltantes.append(_ROTULOS_CAMPOS.get(campo, campo))

        if faltantes:
            raise ValueError(
                "Campos obrigatórios ausentes ou 'Não informado': " + ", ".join(faltantes) + "."
            )
        return payload

    # -------------------------------------------------------------------------
    # RESOLUÇÃO TAXONÔMICA:
    # -------------------------------------------------------------------------
    def resolver_especie(
        self,
        nome_comum: Optional[str] = None,
        nome_cientifico: Optional[str] = None,
        classe: Optional[Union[Classe, str]] = None,
        confirmar_nova_especie: bool = False,
    ) -> tuple[str, str, Classe]:
        """Delega a resolução taxonômica para o EspecieService."""
        return self.especie_service.resolver_especie(
            nome_comum=nome_comum,
            nome_cientifico=nome_cientifico,
            classe=classe,
            confirmar_nova_especie=confirmar_nova_especie,
        )

    # -------------------------------------------------------------------------
    # OPERAÇÕES CRUD (CREATE, READ, UPDATE, DELETE):
    # -------------------------------------------------------------------------

    def criar_animal(
        self,
        dados_animal: Union[Dict[str, Any], AnimalCreate],
        confirmar_nova_especie: bool = False,
        usuario: Optional[Any] = None,
        carga_legada: bool = False,
    ) -> Animal:
        """
        [CREATE] Cria e persiste um novo animal resolvendo automaticamente sua taxonomia.

        - carga_legada=False (padrão): novos cadastros. Exige animal_id, espécie
          (classe/nome_comum/nome_cientifico, resolvidos via catálogo), sexo, peso
          (> 0 ou 'Não aferido'), faixa_etaria (ou idade), orgao_origem, local_origem,
          regime_vida e status_vital, todos diferentes de vazio/'Não informado'.
        - carga_legada=True: importação de planilhas antigas. Campos obrigatórios
          ausentes são preenchidos com 'Não informado' / 'Não aferido'.
        """
        self._verificar_permissao("criar_animal", usuario)

        if isinstance(dados_animal, AnimalCreate):
            payload = dados_animal.model_dump(by_alias=True)
            confirmar = dados_animal.confirmar_nova_especie or confirmar_nova_especie
        else:
            payload = dict(dados_animal)
            confirmar = payload.pop("confirmar_nova_especie", False) or confirmar_nova_especie

        payload = self._normalizar_chaves(payload)

        animal_id = payload.get("animal_id")
        if self._eh_nao_informado(animal_id):
            raise ValueError("O identificador único do animal (animal_id ou _id) é obrigatório.")

        animal_id_str = str(animal_id).strip()
        payload["animal_id"] = animal_id_str

        if self.animal_repo.exists(animal_id_str):
            raise ValueError(f"Já existe um animal cadastrado com o ID '{animal_id_str}'.")

        # Validação de obrigatoriedade ANTES da resolução taxonômica, para não
        # cadastrar uma espécie nova no catálogo e depois rejeitar o animal.
        self.aplicar_obrigatoriedade(payload, carga_legada=carga_legada)

        nome_comum = payload.get("nome_comum")
        nome_cientifico = payload.get("nome_cientifico")
        classe = payload.get("classe")

        nome_comum_res, nome_cientifico_res, classe_res = self.resolver_especie(
            nome_comum=nome_comum,
            nome_cientifico=nome_cientifico,
            classe=classe,
            confirmar_nova_especie=confirmar,
        )

        payload["nome_comum"] = nome_comum_res
        payload["nome_cientifico"] = nome_cientifico_res
        payload["classe"] = classe_res

        animal = Animal(**payload)
        return self.animal_repo.create(animal)

    def obter_animal(self, animal_id: str, usuario: Optional[Any] = None) -> Animal:
        self._verificar_permissao("obter_animal", usuario)
        animal = self.animal_repo.buscar_por_animal_id(animal_id)
        if not animal:
            raise KeyError(f"Animal com ID '{animal_id}' não encontrado.")
        return animal

    def obter_animal_detalhes(
        self,
        animal_id: str,
        usuario: Optional[Any] = None,
    ) -> AnimalDetails:
        self._verificar_permissao("obter_animal", usuario)
        animal = self.obter_animal(animal_id, usuario=usuario)

        amostras: List[Amostra] = []
        try:
            from src.repositories.amostra_repository import amostra_repository
            if hasattr(amostra_repository, "buscar_por_animal_id"):
                amostras = amostra_repository.buscar_por_animal_id(animal_id)
        except Exception:
            amostras = []

        return self.preencher_nao_informados_e_relacionamentos(animal, amostras=amostras)

    @classmethod
    def preencher_nao_informados_e_relacionamentos(
        cls,
        data: Any,
        amostras: Optional[List[Amostra]] = None,
    ) -> AnimalDetails:
        if hasattr(data, "__dict__") and not isinstance(data, dict):
            if hasattr(data, "model_dump"):
                payload = data.model_dump(by_alias=True)
            else:
                payload = dict(data.__dict__)
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            raise ValueError("Os dados do animal devem ser um dicionário ou objeto compatível.")

        if "animal_id" not in payload and "_id" in payload and isinstance(payload["_id"], str):
            payload["animal_id"] = payload["_id"]

        campos_texto = [
            ("local_origem", "Não informado"),
            ("municipio", "Não informado"),
            ("uf", "Não informado"),
            ("localidade_detalhe", "Não informado"),
            ("animal_id_projeto", "Não informado"),
            ("microchip", "Não informado"),
            ("idade", "Não informado"),
            ("suspeita_clinica", "Não informado"),
            ("animal_observacoes", "Não informado"),
            ("observacoes", "Não informado"),
            ("funcao", "Não informado"),
        ]
        for campo, padrao in campos_texto:
            val = payload.get(campo)
            if val is None or (isinstance(val, str) and val.strip() in ["", "-", "NI", "ni", "None", "null"]):
                payload[campo] = padrao

        # Sanitização e decomposição de localidade
        n_mun, n_uf, n_det, n_loc = decompor_localidade(
            payload.get("local_origem"),
            payload.get("municipio"),
            payload.get("uf"),
            payload.get("localidade_detalhe"),
        )
        if n_loc and not cls._eh_nao_informado(n_loc):
            payload["local_origem"] = n_loc
        if n_mun and not cls._eh_nao_informado(n_mun):
            payload["municipio"] = n_mun
        if n_uf and not cls._eh_nao_informado(n_uf):
            payload["uf"] = n_uf
        if n_det and not cls._eh_nao_informado(n_det):
            payload["localidade_detalhe"] = n_det

        # Sanitização de peso, valor e unidade
        peso_val = payload.get("peso")
        if peso_val is None or (isinstance(peso_val, str) and peso_val.strip() in ["", "-", "NI", "ni", "None", "null"]):
            payload["peso"] = "Não aferido"
            payload["peso_valor"] = None
            payload["peso_unidade"] = None
        else:
            p_kg, p_num, p_unid = decompor_peso(
                peso_bruto=payload.get("peso"),
                peso_valor=payload.get("peso_valor"),
                peso_unidade=payload.get("peso_unidade"),
            )
            payload["peso"] = p_kg
            payload["peso_valor"] = p_num
            payload["peso_unidade"] = p_unid

        # Sanitização de idade, valor e unidade
        idade_str = payload.get("idade")
        idade_num = payload.get("idade_valor")
        idade_u = payload.get("idade_unidade")
        if (idade_str and str(idade_str).strip() not in ["", "-", "NI", "ni", "None", "null", "Não informado"]) or idade_num is not None:
            fmt_i, val_i, unid_i = decompor_idade(
                idade_str=idade_str,
                idade_valor=idade_num,
                idade_unidade=idade_u,
            )
            payload["idade"] = fmt_i if fmt_i is not None else "Não informado"
            payload["idade_valor"] = val_i
            payload["idade_unidade"] = unid_i
        else:
            payload["idade"] = "Não informado"
            payload["idade_valor"] = None
            payload["idade_unidade"] = None

        if payload.get("sexo") is None or str(payload.get("sexo")).strip() in ["", "-", "NI", "None"]:
            payload["sexo"] = Sexo.NAO_INFORMADO

        if payload.get("faixa_etaria") is None or str(payload.get("faixa_etaria")).strip() in ["", "-", "NI", "None"]:
            payload["faixa_etaria"] = FaixaEtaria.NAO_INFORMADO

        if payload.get("status_vital") is None or str(payload.get("status_vital")).strip() in ["", "-", "NI", "None"]:
            payload["status_vital"] = StatusVital.NAO_INFORMADO

        if payload.get("regime_vida") is None or str(payload.get("regime_vida")).strip() in ["", "-", "NI", "None"]:
            payload["regime_vida"] = RegimeVida.NAO_INFORMADO
        if "status" in payload and (payload.get("status") is None or str(payload.get("status")).strip() in ["", "-", "NI", "None"]):
            payload["status"] = RegimeVida.NAO_INFORMADO

        if payload.get("orgao_origem") is None or str(payload.get("orgao_origem")).strip() in ["", "-", "NI", "None"]:
            payload["orgao_origem"] = Orgao.NAO_INFORMADO
        if "orgao" in payload and (payload.get("orgao") is None or str(payload.get("orgao")).strip() in ["", "-", "NI", "None"]):
            payload["orgao"] = Orgao.NAO_INFORMADO

        if not payload.get("especie"):
            nome_c = payload.get("nome_comum") or payload.get("nome")
            nome_cient = payload.get("nome_cientifico")
            classe_val = payload.get("classe")
            if nome_c and nome_cient and classe_val:
                payload["especie"] = Especie(
                    nome_comum=nome_c,
                    nome_cientifico=nome_cient,
                    classe=classe_val
                )

        if amostras is not None:
            payload["amostras"] = amostras
            payload["quantidade_amostras"] = len(amostras)
        else:
            lista_amostras = payload.get("amostras", [])
            payload["amostras"] = lista_amostras
            if payload.get("quantidade_amostras") is None or payload.get("quantidade_amostras") == 0:
                payload["quantidade_amostras"] = len(lista_amostras)

        return AnimalDetails(**payload)

    def listar_animais(
        self,
        classe: Optional[Classe] = None,
        sexo: Optional[Sexo] = None,
        regime_vida: Optional[RegimeVida] = None,
        status_vital: Optional[StatusVital] = None,
        termo_busca: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        usuario: Optional[Any] = None,
    ) -> List[Animal]:
        self._verificar_permissao("listar_animais", usuario)
        return self.animal_repo.listar(
            classe=classe,
            sexo=sexo,
            regime_vida=regime_vida,
            status_vital=status_vital,
            termo_busca=termo_busca,
            skip=skip,
            limit=limit,
        )

    def listar_animais_por_especie(
        self,
        nome_comum: Optional[str] = None,
        nome_cientifico: Optional[str] = None,
        usuario: Optional[Any] = None,
    ) -> List[Animal]:
        self._verificar_permissao("listar_animais", usuario)
        return self.animal_repo.buscar_por_especie(
            nome_comum=nome_comum,
            nome_cientifico=nome_cientifico,
        )

    def contar_animais(self, usuario: Optional[Any] = None) -> int:
        self._verificar_permissao("contar_animais", usuario)
        return self.animal_repo.count()

    def atualizar_animal(
        self,
        animal_id: str,
        dados_atualizacao: Union[Dict[str, Any], AnimalUpdate],
        confirmar_nova_especie: bool = False,
        usuario: Optional[Any] = None,
        carga_legada: bool = False,
    ) -> Animal:
        """
        [UPDATE] Atualização parcial. Apenas os campos enviados são alterados; os
        campos obrigatórios enviados não podem ser vazios / 'Não informado'
        (exceto com carga_legada=True). Registros legados com campos 'Não informado'
        podem ser atualizados sem precisar completar todos os campos de uma vez.
        """
        self._verificar_permissao("atualizar_animal", usuario)

        animal_atual = self.obter_animal(animal_id, usuario=usuario)

        if isinstance(dados_atualizacao, AnimalUpdate):
            dados_novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            confirmar = dados_atualizacao.confirmar_nova_especie or confirmar_nova_especie
        else:
            dados_novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            confirmar = dados_novos.pop("confirmar_nova_especie", False) or confirmar_nova_especie

        dados_novos = self._normalizar_chaves(dados_novos)
        for chave in ("animal_id", "id", "confirmar_atualizacao_animal", "confirmar_nova_especie"):
            dados_novos.pop(chave, None)

        payload = self._normalizar_chaves(animal_atual.model_dump(by_alias=True))

        # Atualização inteligente de peso
        if any(k in dados_novos for k in ["peso", "peso_valor", "peso_unidade"]):
            p_bruto = dados_novos.get("peso", payload.get("peso"))
            p_val = dados_novos.get("peso_valor")
            p_unid = dados_novos.get("peso_unidade")
            if carga_legada:
                p_kg, val_p, unid_p = self.processar_biometria_peso(p_bruto, p_val, p_unid)
                self.validar_peso(p_kg)
            else:
                p_kg, val_p, unid_p = self.processar_peso_obrigatorio(p_bruto, p_val, p_unid)
            dados_novos["peso"] = p_kg
            dados_novos["peso_valor"] = val_p
            dados_novos["peso_unidade"] = unid_p

        # Atualização inteligente de idade e dedução de faixa etária
        if any(k in dados_novos for k in ["idade", "idade_valor", "idade_unidade"]):
            fmt_i, val_i, unid_i = self.processar_biometria_idade(
                idade=dados_novos.get("idade"),
                idade_valor=dados_novos.get("idade_valor"),
                idade_unidade=dados_novos.get("idade_unidade"),
            )
            if fmt_i is not None:
                dados_novos["idade"] = fmt_i
            dados_novos["idade_valor"] = val_i
            dados_novos["idade_unidade"] = unid_i

            if "faixa_etaria" not in dados_novos:
                faixa_deduzida = self.deduzir_faixa_etaria(
                    idade_str=dados_novos.get("idade"),
                    idade_valor=val_i,
                    idade_unidade=unid_i,
                )
                if faixa_deduzida:
                    dados_novos["faixa_etaria"] = faixa_deduzida

        # Atualização inteligente de localidade
        if any(k in dados_novos for k in ["local_origem", "municipio", "uf", "localidade_detalhe"]):
            if "local_origem" in dados_novos and "municipio" not in dados_novos:
                n_mun, n_uf, n_det, n_loc = decompor_localidade(
                    local_origem=dados_novos.get("local_origem"),
                    municipio=None,
                    uf=dados_novos.get("uf"),
                    localidade_detalhe=dados_novos.get("localidade_detalhe"),
                )
            else:
                n_mun, n_uf, n_det, n_loc = decompor_localidade(
                    dados_novos.get("local_origem", payload.get("local_origem")),
                    dados_novos.get("municipio", payload.get("municipio")),
                    dados_novos.get("uf", payload.get("uf")),
                    dados_novos.get("localidade_detalhe", payload.get("localidade_detalhe")),
                )
            dados_novos["municipio"] = n_mun
            dados_novos["uf"] = n_uf
            dados_novos["localidade_detalhe"] = n_det
            if n_loc and not self._eh_nao_informado(n_loc):
                dados_novos["local_origem"] = n_loc

        # Valida apenas os campos obrigatórios enviados (antes de resolver espécie).
        campos_obrigatorios = set(_OBRIGATORIOS_COM_PADRAO_LEGADO) | {"peso", "faixa_etaria"}
        enviados = [c for c in dados_novos if c in campos_obrigatorios]
        if enviados:
            self.aplicar_obrigatoriedade(dados_novos, carga_legada=carga_legada, campos=enviados)

        mudou_especie = any(k in dados_novos for k in ["nome_comum", "nome_cientifico", "classe"])
        if mudou_especie:
            if "nome_comum" in dados_novos and "nome_cientifico" not in dados_novos:
                nome_comum = dados_novos["nome_comum"]
                nome_cientifico = None
            elif "nome_cientifico" in dados_novos and "nome_comum" not in dados_novos:
                nome_cientifico = dados_novos["nome_cientifico"]
                nome_comum = None
            else:
                nome_comum = dados_novos.get("nome_comum", payload.get("nome_comum"))
                nome_cientifico = dados_novos.get("nome_cientifico", payload.get("nome_cientifico"))

            classe = dados_novos.get("classe")

            nome_comum_res, nome_cientifico_res, classe_res = self.resolver_especie(
                nome_comum=nome_comum,
                nome_cientifico=nome_cientifico,
                classe=classe,
                confirmar_nova_especie=confirmar,
            )
            dados_novos["nome_comum"] = nome_comum_res
            dados_novos["nome_cientifico"] = nome_cientifico_res
            dados_novos["classe"] = classe_res

        payload.update(dados_novos)
        payload["animal_id"] = animal_id

        animal_atualizado = Animal(**payload)
        return self.animal_repo.update(animal_id, animal_atualizado)

    def deletar_animal(self, animal_id: str, usuario: Optional[Any] = None) -> bool:
        self._verificar_permissao("deletar_animal", usuario)
        self.obter_animal(animal_id, usuario=usuario)
        return self.animal_repo.delete(animal_id)


# Instância global para uso no projeto (injeção de dependência simplificada)
animal_service = AnimalService()

__all__ = [
    "AnimalService",
    "animal_service",
    "Animal",
    "AnimalCreate",
    "AnimalUpdate",
    "AnimalDetails",
    "Classe",
    "Especie",
    "Amostra",
    "Sexo",
    "FaixaEtaria",
    "RegimeVida",
    "StatusVital",
    "Orgao",
    "Funcao",
    "UnidadePeso",
    "UnidadeIdade",
]