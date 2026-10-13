import re
from typing import Optional, Union, List, Dict, Any
from src.models.animal import (
    Animal,
    AnimalCreate,
    AnimalUpdate,
    Sexo,
    FaixaEtaria,
    RegimeVida,
    StatusVital,
)
from src.models.especie import Classe
from src.services.especie_service import EspecieService, especie_service
from src.repositories.animal_repository import AnimalRepository, animal_repository

class AnimalService:
    """
    Serviço responsável pelo ciclo de vida completo (CRUD) e regras de negócio
    da entidade Animal no LABVEPI:
    - Resolução taxonômica e automação de espécie orquestrada via EspecieService.
    - Processamento, conversão dimensional e validação de peso (biometria).
    - Dedução inteligente de faixa etária a partir da idade cronológica.
    - Operações de Create, Read, Update e Delete orquestradas junto ao AnimalRepository.
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
        No momento, todas as ações são permitidas. Em breve, validará o perfil do usuário
        (ex: Docente, Bolsista PIBITI, Bolsista PIBIC) contra a matriz de permissões.
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
        [CREATE] Cria e persiste um novo animal:
        - Verifica unicidade do ID do laboratório via AnimalRepository.
        - Resolve e automatiza os dados taxonômicos via EspecieService.
        - Sanitiza e valida o peso corporal.
        - Deduz automaticamente a faixa etária caso apenas a idade tenha sido informada.
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

        # Validação de unicidade no repositório
        if self.animal_repo.existe(animal_id_str):
            raise ValueError(f"Já existe um animal cadastrado com o ID '{animal_id_str}'.")

        # Automação e resolução de espécie a partir do serviço de espécies
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

        # Processamento e validação de biometria / peso
        peso_raw = payload.get("peso", "Não aferido")
        peso_proc = self.processar_peso(peso_raw)
        self.validar_peso(peso_proc)
        payload["peso"] = peso_proc

        # Dedução de Faixa Etária a partir de Idade se não informada
        faixa = payload.get("faixa_etaria")
        idade = payload.get("idade")
        if (not faixa or faixa == FaixaEtaria.NAO_INFORMADO) and idade:
            faixa_deduzida = self.deduzir_faixa_etaria(idade)
            if faixa_deduzida:
                payload["faixa_etaria"] = faixa_deduzida

        # Criação da entidade e persistência via AnimalRepository
        animal = Animal(**payload)
        return self.animal_repo.salvar(animal)

    def obter_animal(self, animal_id: str, usuario: Optional[Any] = None) -> Animal:
        """
        [READ] Recupera um animal cadastrado pelo seu identificador único.
        """
        self._verificar_permissao("obter_animal", usuario)
        animal = self.animal_repo.buscar_por_animal_id(animal_id)
        if not animal:
            raise KeyError(f"Animal com ID '{animal_id}' não encontrado.")
        return animal

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
        """
        [READ] Lista animais aplicando filtros e paginação através do repositório.
        """
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

    def atualizar_animal(
        self,
        animal_id: str,
        dados_atualizacao: Union[Dict[str, Any], AnimalUpdate],
        confirmar_nova_especie: bool = False,
        usuario: Optional[Any] = None,
    ) -> Animal:
        """
        [UPDATE] Atualiza os dados de um animal existente:
        - Reavalia espécie e classe automaticamente caso novos nomes sejam passados.
        - Reprocessa e valida peso caso informado.
        - Atualiza faixa etária se nova idade for fornecida.
        """
        self._verificar_permissao("atualizar_animal", usuario)

        animal_atual = self.obter_animal(animal_id, usuario=usuario)

        if isinstance(dados_atualizacao, AnimalUpdate):
            dados_novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
            confirmar = dados_atualizacao.confirmar_nova_especie or confirmar_nova_especie
        else:
            dados_novos = {k: v for k, v in dados_atualizacao.items() if v is not None}
            confirmar = dados_novos.pop("confirmar_nova_especie", False) or confirmar_nova_especie

        payload = animal_atual.model_dump(by_alias=True)

        # Se houver alteração em dados taxonômicos, re-resolve espécie
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

        # Se houver alteração de peso
        if "peso" in dados_novos:
            peso_proc = self.processar_peso(dados_novos["peso"])
            self.validar_peso(peso_proc)
            dados_novos["peso"] = peso_proc

        # Se houver alteração de idade sem faixa etária explícita
        if "idade" in dados_novos and "faixa_etaria" not in dados_novos:
            faixa_deduzida = self.deduzir_faixa_etaria(dados_novos["idade"])
            if faixa_deduzida:
                dados_novos["faixa_etaria"] = faixa_deduzida

        payload.update(dados_novos)
        payload["animal_id"] = animal_id
        payload["_id"] = animal_id

        animal_atualizado = Animal(**payload)
        return self.animal_repo.atualizar(animal_id, animal_atualizado)

    def deletar_animal(self, animal_id: str, usuario: Optional[Any] = None) -> bool:
        """
        [DELETE] Remove um animal do sistema através do AnimalRepository.
        """
        self._verificar_permissao("deletar_animal", usuario)
        self.obter_animal(animal_id, usuario=usuario)
        return self.animal_repo.remover(animal_id)


# Instância singleton para uso padrão na aplicação
animal_service = AnimalService()
