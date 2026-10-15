import re
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
)
from src.models.Especie import Classe, Especie
from src.models.Amostra import Amostra
from src.services.especie_service import EspecieService, especie_service
from src.repositories.animal_repository import AnimalRepository, animal_repository


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
    def processar_peso(v: Any) -> Union[float, str]:
        """
        Sanitiza e converte strings de peso em gramas ou kg para float (kg)
        ou padroniza para 'Não aferido'.
        """
        if v is None or v == "" or str(v).strip() in ["-", "NI", "ni", "Não informado", "N/A"]:
            return "Não aferido"

        if isinstance(v, str):
            v_clean = v.strip().lower().replace(",", ".")
            if "não aferido" in v_clean or "nao aferido" in v_clean:
                return "Não aferido"
            match_g = re.match(r"^(\d+(?:\.\d+)?)\s*g$", v_clean)
            if match_g:
                return round(float(match_g.group(1)) / 1000.0, 4)
            match_kg = re.match(r"^(\d+(?:\.\d+)?)\s*kg$", v_clean)
            if match_kg:
                return float(match_kg.group(1))
            try:
                return float(v_clean)
            except ValueError:
                return "Não aferido"

        if isinstance(v, (int, float)):
            return float(v)

        return v

    @staticmethod
    def validar_peso(peso: Union[float, str]) -> None:
        """Garante que peso numérico seja estritamente maior que zero."""
        if isinstance(peso, (int, float)) and peso <= 0:
            raise ValueError("O peso deve ser maior que zero ou marcado como 'Não aferido'.")

    # -------------------------------------------------------------------------
    # DEDUÇÃO INTELIGENTE DE FAIXA ETÁRIA:
    # -------------------------------------------------------------------------
    @staticmethod
    def deduzir_faixa_etaria(idade_str: Optional[str]) -> Optional[FaixaEtaria]:
        """
        Calcula a faixa etária com base na string de idade informada.
        Exemplos: '6 meses', '1.5 anos', '3 anos', '10', 'Filhote'.
        """
        if not idade_str:
            return None

        idade_clean = idade_str.strip().lower()

        if "filhote" in idade_clean:
            return FaixaEtaria.FILHOTE
        if "ninhego" in idade_clean:
            return FaixaEtaria.NINHEGO
        if "potro" in idade_clean:
            return FaixaEtaria.POTRO
        if "juvenil" in idade_clean:
            return FaixaEtaria.JUVENIL
        if "jovem" in idade_clean:
            return FaixaEtaria.JOVEM
        if "sub" in idade_clean:
            return FaixaEtaria.SUB_ADULTO
        if "adulto" in idade_clean:
            return FaixaEtaria.ADULTO
        if "senil" in idade_clean:
            return FaixaEtaria.SENIL
        if "idoso" in idade_clean:
            return FaixaEtaria.IDOSO

        match = re.search(r"(\d+(?:[\.,]\d+)?)", idade_clean)
        if not match:
            return None

        num_val = float(match.group(1).replace(",", "."))

        if any(unit in idade_clean for unit in ["mês", "mes", "meses", "m"]):
            anos = num_val / 12.0
        elif any(unit in idade_clean for unit in ["dia", "dias", "d"]):
            anos = num_val / 365.0
        elif any(unit in idade_clean for unit in ["semana", "semanas", "sem"]):
            anos = num_val / 52.0
        else:
            anos = num_val

        if anos < 1.0:
            return FaixaEtaria.FILHOTE
        elif anos < 2.0:
            return FaixaEtaria.JUVENIL
        elif anos < 4.0:
            return FaixaEtaria.SUB_ADULTO
        elif anos < 10.0:
            return FaixaEtaria.ADULTO
        else:
            return FaixaEtaria.SENIL

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
    ) -> Animal:
        """
        [CREATE] Cria e persiste um novo animal resolvendo automaticamente sua taxonomia.
        """
        self._verificar_permissao("criar_animal", usuario)

        if isinstance(dados_animal, AnimalCreate):
            payload = dados_animal.model_dump(by_alias=True)
            confirmar = dados_animal.confirmar_nova_especie or confirmar_nova_especie
        else:
            payload = dict(dados_animal)
            confirmar = payload.pop("confirmar_nova_especie", False) or confirmar_nova_especie

        animal_id = payload.get("animal_id") or payload.get("_id")
        if not animal_id:
            raise ValueError("O identificador único do animal (animal_id ou _id) é obrigatório.")

        animal_id_str = str(animal_id).strip()
        payload["animal_id"] = animal_id_str
        payload["_id"] = animal_id_str

        if self.animal_repo.exists(animal_id_str):
            raise ValueError(f"Já existe um animal cadastrado com o ID '{animal_id_str}'.")

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

        peso_raw = payload.get("peso", "Não aferido")
        peso_proc = self.processar_peso(peso_raw)
        self.validar_peso(peso_proc)
        payload["peso"] = peso_proc

        faixa = payload.get("faixa_etaria")
        idade = payload.get("idade")
        if (not faixa or faixa == FaixaEtaria.NAO_INFORMADO) and idade:
            faixa_deduzida = self.deduzir_faixa_etaria(idade)
            if faixa_deduzida:
                payload["faixa_etaria"] = faixa_deduzida

        animal = Animal(**payload)
        return self.animal_repo.save(animal)

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

        peso_val = payload.get("peso")
        if peso_val is None or (isinstance(peso_val, str) and peso_val.strip() in ["", "-", "NI", "ni", "None", "null"]):
            payload["peso"] = "Não aferido"

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
    ) -> Animal:
        self._verificar_permissao("atualizar_animal", usuario)

        animal_atual = self.obter_animal(animal_id, usuario=usuario)

        if isinstance(dados_atualizacao, AnimalUpdate):
            dados_novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            confirmar = dados_atualizacao.confirmar_nova_especie or confirmar_nova_especie
        else:
            dados_novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            confirmar = dados_novos.pop("confirmar_nova_especie", False) or confirmar_nova_especie

        payload = animal_atual.model_dump(by_alias=True)

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

        if "peso" in dados_novos:
            peso_proc = self.processar_peso(dados_novos["peso"])
            self.validar_peso(peso_proc)
            dados_novos["peso"] = peso_proc

        if "idade" in dados_novos and "faixa_etaria" not in dados_novos:
            faixa_deduzida = self.deduzir_faixa_etaria(dados_novos["idade"])
            if faixa_deduzida:
                dados_novos["faixa_etaria"] = faixa_deduzida

        payload.update(dados_novos)
        payload["animal_id"] = animal_id
        payload["_id"] = animal_id

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
]