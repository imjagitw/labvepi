from typing import Optional, List, Dict, Union
from src.models.Especie import Especie, Classe

def _normalizar(texto: str) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class EspecieRepository:
    """
    Repositório de persistência e acesso a dados da entidade Especie.
    Responsabilidade exclusiva:
    - Armazenar, consultar, atualizar e remover espécies no banco de dados (ou memória).
    - Atuar como camada de acesso a dados (DAO/Persistência).
    - NÃO contém regras de negócio, validações taxonômicas ou parsing de arquivos.
    """

    def __init__(self, especies: Optional[List[Especie]] = None):
        self._por_id: Dict[int, Especie] = {}
        self._por_comum: Dict[str, Especie] = {}
        self._por_cientifico: Dict[str, Especie] = {}
        self._por_classe: Dict[Classe, List[Especie]] = {}
        self._proximo_id: int = 1
        for especie in especies or []:
            self.create(especie)

    def create(self, especie: Especie) -> Especie:
        """Persiste um novo registro de espécie no banco de dados."""
        if especie.id is None:
            especie.id = self._proximo_id
            self._proximo_id += 1

        chave_id = int(especie.id)
        if chave_id in self._por_id:
            raise ValueError(f"Registro com ID {chave_id} já existe no banco de dados.")

        chave_comum = _normalizar(especie.nome_comum)
        chave_cient = _normalizar(especie.nome_cientifico)
        chave_classe = especie.classe

        self._por_id[chave_id] = especie
        if chave_comum:
            self._por_comum[chave_comum] = especie
        if chave_cient:
            self._por_cientifico[chave_cient] = especie

        if chave_classe not in self._por_classe:
            self._por_classe[chave_classe] = []
        if especie not in self._por_classe[chave_classe]:
            self._por_classe[chave_classe].append(especie)

        if chave_id >= self._proximo_id:
            self._proximo_id = chave_id + 1

        return especie

    def save(self, especie: Especie) -> Especie:
        """Alias para persistir a espécie (create ou update se já possuir ID cadastrado)."""
        if especie.id is not None:
            try:
                chave_id = int(especie.id)
                if chave_id in self._por_id:
                    return self.update(chave_id, especie)
            except (ValueError, TypeError):
                pass
        return self.create(especie)

    def update(self, id_especie: Union[int, str], especie_atualizada: Especie) -> Especie:
        """Atualiza os dados de uma espécie persistida e sincroniza os índices."""
        chave_id = int(id_especie)
        if chave_id not in self._por_id:
            raise KeyError(f"Espécie com ID {chave_id} não encontrada no banco de dados.")

        antiga = self._por_id[chave_id]

        # Limpeza dos índices antigos
        chave_comum_antiga = _normalizar(antiga.nome_comum)
        chave_cient_antiga = _normalizar(antiga.nome_cientifico)
        self._por_comum.pop(chave_comum_antiga, None)
        self._por_cientifico.pop(chave_cient_antiga, None)

        if antiga.classe in self._por_classe and antiga in self._por_classe[antiga.classe]:
            self._por_classe[antiga.classe].remove(antiga)

        # Atualização do registro
        especie_atualizada.id = chave_id
        chave_comum_nova = _normalizar(especie_atualizada.nome_comum)
        chave_cient_nova = _normalizar(especie_atualizada.nome_cientifico)
        nova_classe = especie_atualizada.classe

        self._por_id[chave_id] = especie_atualizada
        if chave_comum_nova:
            self._por_comum[chave_comum_nova] = especie_atualizada
        if chave_cient_nova:
            self._por_cientifico[chave_cient_nova] = especie_atualizada

        if nova_classe not in self._por_classe:
            self._por_classe[nova_classe] = []
        if especie_atualizada not in self._por_classe[nova_classe]:
            self._por_classe[nova_classe].append(especie_atualizada)

        return especie_atualizada

    def buscar_por_id(self, id_especie: Union[int, str]) -> Optional[Especie]:
        """Recupera o registro pela chave primária ID."""
        try:
            chave_id = int(id_especie)
        except (ValueError, TypeError):
            return None
        return self._por_id.get(chave_id)

    def buscar_por_nome_comum(self, nome_comum: str) -> Optional[Especie]:
        """Consulta registro por índice de nome comum."""
        if not nome_comum:
            return None
        return self._por_comum.get(_normalizar(nome_comum))

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> Optional[Especie]:
        """Consulta registro por índice de nome científico."""
        if not nome_cientifico:
            return None
        return self._por_cientifico.get(_normalizar(nome_cientifico))

    def buscar_por_classe(self, classe: Union[Classe, str]) -> List[Especie]:
        """Consulta registros pelo índice de classe taxonômica."""
        if not classe:
            return []
        if isinstance(classe, Classe):
            return list(self._por_classe.get(classe, []))
        for c in self._por_classe:
            if c.value.lower() == str(classe).strip().lower():
                return list(self._por_classe.get(c, []))
        return []

    def listar(self) -> List[Especie]:
        """Retorna todos os registros armazenados ordenados por ID."""
        return sorted(self._por_id.values(), key=lambda e: (int(e.id) if e.id is not None else 0))

    def delete(self, id_especie: Union[int, str]) -> bool:
        """Exclui o registro do banco de dados pelo ID."""
        try:
            chave_id = int(id_especie)
        except (ValueError, TypeError):
            return False

        if chave_id not in self._por_id:
            return False

        esp = self._por_id.pop(chave_id)
        self._por_comum.pop(_normalizar(esp.nome_comum), None)
        self._por_cientifico.pop(_normalizar(esp.nome_cientifico), None)

        if esp.classe in self._por_classe and esp in self._por_classe[esp.classe]:
            self._por_classe[esp.classe].remove(esp)

        return True

    def count(self) -> int:
        """Retorna a contagem de registros armazenados."""
        return len(self._por_id)

    def exists(self, id_especie: Union[int, str]) -> bool:
        """Verifica se existe registro com o ID fornecido."""
        try:
            return int(id_especie) in self._por_id
        except (ValueError, TypeError):
            return False

    def clear(self) -> None:
        """Limpa todo o armazenamento do banco de dados."""
        self._por_comum.clear()
        self._por_cientifico.clear()
        self._por_id.clear()
        self._por_classe.clear()
        self._proximo_id = 1

especie_repository = EspecieRepository()