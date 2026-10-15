from typing import Optional, List, Dict, Union
from src.models.Animal import (
    Animal,
    Sexo,
    RegimeVida,
    StatusVital,
    Orgao,
    Funcao,
    FaixaEtaria,
)
from src.models.Especie import Classe

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class AnimalRepository:
    """
    Repositório de persistência e acesso a dados da entidade Animal.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover animais no banco de dados (ou memória).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - NÃO contém regras de negócio, validações taxonômicas, biometria ou parsing de arquivos.
    """

    def __init__(self, animais: Optional[List[Animal]] = None):
        self._por_id: Dict[int, Animal] = {}
        self._por_animal_id: Dict[str, Animal] = {}
        self._por_projeto_id: Dict[str, List[Animal]] = {}
        self._por_microchip: Dict[str, Animal] = {}
        # Correção: Diferentes animais partilham o mesmo nome, portanto devem ser listas.
        self._por_nome_comum: Dict[str, List[Animal]] = {}
        self._por_nome_cientifico: Dict[str, List[Animal]] = {}
        self._por_classe: Dict[Classe, List[Animal]] = {}
        self._por_sexo: Dict[Sexo, List[Animal]] = {}
        self._por_faixa_etaria: Dict[FaixaEtaria, List[Animal]] = {}
        self._por_orgao_origem: Dict[Orgao, List[Animal]] = {}
        self._por_regime_vida: Dict[RegimeVida, List[Animal]] = {}
        self._por_status_vital: Dict[StatusVital, List[Animal]] = {}
        self._por_funcao: Dict[Funcao, List[Animal]] = {}
        self._proximo_id: int = 1

        for animal in animais or []:
            self.create(animal)

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------

    def _indexar(self, animal: Animal) -> None:
        chave_lab = animal.animal_id.strip()
        self._por_animal_id[chave_lab] = animal

        if animal.id is not None:
            self._por_id[animal.id] = animal

        if animal.animal_id_projeto:
            chave_proj = animal.animal_id_projeto.strip()
            self._por_projeto_id.setdefault(chave_proj, []).append(animal)

        if animal.microchip:
            self._por_microchip[animal.microchip.strip()] = animal

        norm_comum = _normalizar(animal.nome_comum)
        if norm_comum:
            self._por_nome_comum.setdefault(norm_comum, []).append(animal)

        norm_cient = _normalizar(animal.nome_cientifico)
        if norm_cient:
            self._por_nome_cientifico.setdefault(norm_cient, []).append(animal)

        self._por_classe.setdefault(animal.classe, []).append(animal)
        self._por_sexo.setdefault(animal.sexo, []).append(animal)
        self._por_faixa_etaria.setdefault(animal.faixa_etaria, []).append(animal)
        self._por_orgao_origem.setdefault(animal.orgao_origem, []).append(animal)
        self._por_regime_vida.setdefault(animal.regime_vida, []).append(animal)
        self._por_status_vital.setdefault(animal.status_vital, []).append(animal)
        if animal.funcao:
            self._por_funcao.setdefault(animal.funcao, []).append(animal)

    def _desindexar(self, animal: Animal) -> None:
        chave_lab = animal.animal_id.strip()
        self._por_animal_id.pop(chave_lab, None)

        if animal.id is not None:
            self._por_id.pop(animal.id, None)

        if animal.animal_id_projeto:
            chave_proj = animal.animal_id_projeto.strip()
            if animal in self._por_projeto_id.get(chave_proj, []):
                self._por_projeto_id[chave_proj].remove(animal)

        if animal.microchip:
            self._por_microchip.pop(animal.microchip.strip(), None)

        norm_comum = _normalizar(animal.nome_comum)
        if norm_comum and animal in self._por_nome_comum.get(norm_comum, []):
            self._por_nome_comum[norm_comum].remove(animal)

        norm_cient = _normalizar(animal.nome_cientifico)
        if norm_cient and animal in self._por_nome_cientifico.get(norm_cient, []):
            self._por_nome_cientifico[norm_cient].remove(animal)

        colecoes = [
            self._por_classe.get(animal.classe),
            self._por_sexo.get(animal.sexo),
            self._por_faixa_etaria.get(animal.faixa_etaria),
            self._por_orgao_origem.get(animal.orgao_origem),
            self._por_regime_vida.get(animal.regime_vida),
            self._por_status_vital.get(animal.status_vital),
            self._por_funcao.get(animal.funcao) if animal.funcao else None,
        ]
        for lista in colecoes:
            if lista and animal in lista:
                lista.remove(animal)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------

    def create(self, animal: Animal) -> Animal:
        if not animal.animal_id:
            raise ValueError("O identificador único do animal (animal_id) é obrigatório.")

        chave_id = animal.animal_id.strip()
        if chave_id in self._por_animal_id:
            raise ValueError(f"Animal com ID '{chave_id}' já está cadastrado.")

        if animal.id is None:
            animal.id = self._proximo_id
            self._proximo_id += 1
        elif animal.id >= self._proximo_id:
            self._proximo_id = animal.id + 1

        self._indexar(animal)
        return animal

    def save(self, animal: Animal) -> Animal:
        chave = animal.animal_id.strip()
        if chave in self._por_animal_id:
            return self.update(chave, animal)
        return self.create(animal)

    def update(self, animal_id: str, animal_atualizado: Animal) -> Animal:
        chave = animal_id.strip()
        if chave not in self._por_animal_id:
            raise KeyError(f"Animal com ID '{chave}' não encontrado para atualização.")

        antigo = self._por_animal_id[chave]
        self._desindexar(antigo)

        if animal_atualizado.id is None and antigo.id is not None:
            animal_atualizado.id = antigo.id

        animal_atualizado.animal_id = chave
        self._indexar(animal_atualizado)
        return animal_atualizado

    def delete(self, animal_id: str) -> bool:
        chave = animal_id.strip()
        if chave not in self._por_animal_id:
            raise KeyError(f"Animal com ID '{chave}' não encontrado para exclusão.")

        antigo = self._por_animal_id[chave]
        self._desindexar(antigo)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------

    def buscar_por_animal_id(self, animal_id: str) -> Optional[Animal]:
        if not animal_id:
            return None
        return self._por_animal_id.get(animal_id.strip())

    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Animal]:
        try:
            return self._por_id.get(int(id_numerico))
        except (ValueError, TypeError):
            return None

    def buscar_por_projeto_id(self, projeto_id: str) -> List[Animal]:
        if not projeto_id:
            return []
        return list(self._por_projeto_id.get(projeto_id.strip(), []))

    def buscar_por_microchip(self, microchip: str) -> Optional[Animal]:
        if not microchip:
            return None
        return self._por_microchip.get(microchip.strip())

    def buscar_por_nome_comum(self, nome_comum: str) -> List[Animal]:
        if not nome_comum:
            return []
        return list(self._por_nome_comum.get(_normalizar(nome_comum), []))

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> List[Animal]:
        if not nome_cientifico:
            return []
        return list(self._por_nome_cientifico.get(_normalizar(nome_cientifico), []))

    def buscar_por_classe(self, classe: Union[Classe, str]) -> List[Animal]:
        if not classe:
            return []
        if isinstance(classe, Classe):
            return list(self._por_classe.get(classe, []))
        for c in self._por_classe:
            if c.value.lower() == str(classe).strip().lower():
                return list(self._por_classe.get(c, []))
        return []

    def buscar_por_sexo(self, sexo: Sexo) -> List[Animal]:
        return list(self._por_sexo.get(sexo, []))

    def buscar_por_faixa_etaria(self, faixa_etaria: FaixaEtaria) -> List[Animal]:
        return list(self._por_faixa_etaria.get(faixa_etaria, []))

    def buscar_por_orgao_origem(self, orgao_origem: Orgao) -> List[Animal]:
        return list(self._por_orgao_origem.get(orgao_origem, []))

    def buscar_por_local_origem(self, local_origem: str) -> List[Animal]:
        if not local_origem:
            return []
        norm = _normalizar(local_origem)
        return [a for a in self._por_animal_id.values() if _normalizar(a.local_origem) == norm]

    def buscar_por_regime_vida(self, regime_vida: RegimeVida) -> List[Animal]:
        return list(self._por_regime_vida.get(regime_vida, []))

    def buscar_por_status_vital(self, status_vital: StatusVital) -> List[Animal]:
        return list(self._por_status_vital.get(status_vital, []))

    def buscar_por_funcao(self, funcao: Funcao) -> List[Animal]:
        return list(self._por_funcao.get(funcao, []))

    def buscar_por_especie(
        self,
        nome_comum: Optional[str] = None,
        nome_cientifico: Optional[str] = None,
    ) -> List[Animal]:
        norm_comum = _normalizar(nome_comum) if nome_comum else None
        norm_cient = _normalizar(nome_cientifico) if nome_cientifico else None

        resultado = []
        for a in self._por_animal_id.values():
            if norm_comum and _normalizar(a.nome_comum) == norm_comum:
                resultado.append(a)
            elif norm_cient and _normalizar(a.nome_cientifico) == norm_cient:
                resultado.append(a)
        return resultado

    def listar(
        self,
        classe: Optional[Classe] = None,
        sexo: Optional[Sexo] = None,
        regime_vida: Optional[RegimeVida] = None,
        status_vital: Optional[StatusVital] = None,
        termo_busca: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Animal]:
        resultado = list(self._por_animal_id.values())

        if classe:
            resultado = [a for a in resultado if a.classe == classe]
        if sexo:
            resultado = [a for a in resultado if a.sexo == sexo]
        if regime_vida:
            resultado = [a for a in resultado if a.regime_vida == regime_vida]
        if status_vital:
            resultado = [a for a in resultado if a.status_vital == status_vital]
        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado = [
                a for a in resultado
                if termo in _normalizar(a.animal_id)
                or termo in _normalizar(a.nome_comum)
                or termo in _normalizar(a.nome_cientifico)
                or termo in _normalizar(a.local_origem)
                or (a.animal_id_projeto and termo in _normalizar(a.animal_id_projeto))
                or (a.microchip and termo in _normalizar(a.microchip))
            ]

        resultado.sort(key=lambda a: (a.id or 0, a.animal_id))

        if skip > 0:
            resultado = resultado[skip:]
        if limit is not None and limit > 0:
            resultado = resultado[:limit]

        return resultado

    def count(self) -> int:
        return len(self._por_animal_id)

    def exists(self, animal_id: str) -> bool:
        if not animal_id:
            return False
        return animal_id.strip() in self._por_animal_id

    def clear(self) -> None:
        self._por_id.clear()
        self._por_animal_id.clear()
        self._por_projeto_id.clear()
        self._por_microchip.clear()
        self._por_nome_comum.clear()
        self._por_nome_cientifico.clear()
        self._por_classe.clear()
        self._por_sexo.clear()
        self._por_faixa_etaria.clear()
        self._por_orgao_origem.clear()
        self._por_regime_vida.clear()
        self._por_status_vital.clear()
        self._por_funcao.clear()
        self._proximo_id = 1

animal_repository = AnimalRepository()