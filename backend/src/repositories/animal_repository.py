from typing import Optional, List, Dict
from src.models.animal import Animal, Sexo, RegimeVida, StatusVital
from src.models.especie import Classe

class AnimalRepository:
    """
    Repositório para persistência e consulta da entidade Animal.
    Mantém índice em memória por identificador de laboratório (animal_id).
    """

    def __init__(self, animais: Optional[List[Animal]] = None):
        self._por_animal_id: Dict[str, Animal] = {}
        for animal in animais or []:
            self.salvar(animal)

    def salvar(self, animal: Animal) -> Animal:
        """Salva um novo animal. Lança ValueError se o animal_id já existir."""
        chave = animal.animal_id.strip()
        if chave in self._por_animal_id:
            raise ValueError(f"Animal com ID '{chave}' já está cadastrado.")
        self._por_animal_id[chave] = animal
        return animal

    def buscar_por_animal_id(self, animal_id: str) -> Optional[Animal]:
        """Busca animal pelo identificador único do laboratório."""
        if not animal_id:
            return None
        return self._por_animal_id.get(animal_id.strip())

    def buscar_por_id(self, id_numerico: int) -> Optional[Animal]:
        """Busca animal pelo identificador sequencial numérico (se atribuído)."""
        for animal in self._por_animal_id.values():
            if animal.id == id_numerico:
                return animal
        return None

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
        """Lista animais cadastrados aplicando filtros opcionais e paginação."""
        resultado = list(self._por_animal_id.values())

        if classe is not None:
            resultado = [a for a in resultado if a.classe == classe]
        if sexo is not None:
            resultado = [a for a in resultado if a.sexo == sexo]
        if regime_vida is not None:
            resultado = [a for a in resultado if a.regime_vida == regime_vida]
        if status_vital is not None:
            resultado = [a for a in resultado if a.status_vital == status_vital]
        if termo_busca:
            termo = termo_busca.strip().lower()
            resultado = [
                a for a in resultado
                if termo in a.animal_id.lower()
                or termo in a.nome_comum.lower()
                or termo in a.nome_cientifico.lower()
                or (a.local_origem and termo in a.local_origem.lower())
                or (a.animal_id_projeto and termo in a.animal_id_projeto.lower())
                or (a.microchip and termo in a.microchip.lower())
            ]

        # Ordenação consistente por animal_id
        resultado.sort(key=lambda a: a.animal_id)
        return resultado[skip : skip + limit]

    def atualizar(self, animal_id: str, animal_atualizado: Animal) -> Animal:
        """Atualiza os dados de um animal existente."""
        chave = animal_id.strip()
        if chave not in self._por_animal_id:
            raise KeyError(f"Animal com ID '{chave}' não encontrado para atualização.")
        self._por_animal_id[chave] = animal_atualizado
        return animal_atualizado

    def remover(self, animal_id: str) -> bool:
        """Remove um animal cadastrado pelo seu animal_id."""
        chave = animal_id.strip()
        if chave not in self._por_animal_id:
            raise KeyError(f"Animal com ID '{chave}' não encontrado para exclusão.")
        del self._por_animal_id[chave]
        return True

    def contar(self) -> int:
        """Retorna o total de animais cadastrados."""
        return len(self._por_animal_id)

    def existe(self, animal_id: str) -> bool:
        """Verifica se um animal com o determinado ID existe."""
        return animal_id.strip() in self._por_animal_id

    def limpar(self) -> None:
        """Limpa todos os registros do repositório."""
        self._por_animal_id.clear()


animal_repository = AnimalRepository()
