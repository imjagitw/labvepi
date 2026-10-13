from typing import Optional, List, Dict
from src.models.especie import Especie

def _normalizar(texto: str) -> str:
    """Normaliza para busca indexada: sem espaços redundantes e em minúsculas."""
    return " ".join(texto.strip().split()).casefold()

class EspecieRepository:
    """
    Repositório de persistência e consulta da entidade Especie.
    Responsabilidade:
    - Armazenar e consultar espécies (em memória ou no banco de dados).
    - Abstrair a persistência para que os serviços não dependam de detalhes de armazenamento.
    NÃO deve conter: regras de validação taxonômica, parsing de arquivos ou regras de negócio.
    """

    def __init__(self, especies: Optional[List[Especie]] = None):
        self._por_comum: Dict[str, Especie] = {}
        self._por_cientifico: Dict[str, Especie] = {}
        for especie in especies or []:
            self.salvar(especie)

    def salvar(self, especie: Especie) -> Especie:
        """Salva ou atualiza uma instância de Especie nos índices."""
        chave_comum = _normalizar(especie.nome_comum)
        chave_cient = _normalizar(especie.nome_cientifico)

        self._por_comum[chave_comum] = especie
        self._por_cientifico[chave_cient] = especie
        return especie

    def buscar_por_nome_comum(self, nome_comum: str) -> Optional[Especie]:
        """Recupera espécie pelo nome comum normalizado."""
        if not nome_comum:
            return None
        return self._por_comum.get(_normalizar(nome_comum))

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> Optional[Especie]:
        """Recupera espécie pelo binômio científico normalizado."""
        if not nome_cientifico:
            return None
        return self._por_cientifico.get(_normalizar(nome_cientifico))

    def buscar_por_id(self, id_especie: str) -> Optional[Especie]:
        """Recupera espécie pelo seu identificador primário se atribuído."""
        for esp in self._por_comum.values():
            if str(esp.id) == str(id_especie):
                return esp
        return None

    def listar(self) -> List[Especie]:
        """Retorna lista ordenada de todas as espécies salvas."""
        return sorted(self._por_comum.values(), key=lambda e: e.nome_comum)

    def remover(self, nome_comum: str) -> bool:
        """Remove espécie pelo nome comum."""
        chave_comum = _normalizar(nome_comum)
        if chave_comum not in self._por_comum:
            return False
        esp = self._por_comum.pop(chave_comum)
        chave_cient = _normalizar(esp.nome_cientifico)
        self._por_cientifico.pop(chave_cient, None)
        return True

    def existe(self, nome_comum: str) -> bool:
        """Verifica se um nome comum já existe no repositório."""
        return _normalizar(nome_comum) in self._por_comum

    def contar(self) -> int:
        """Retorna a contagem de espécies armazenadas."""
        return len(self._por_comum)

    def limpar(self) -> None:
        """Limpa o repositório."""
        self._por_comum.clear()
        self._por_cientifico.clear()


especie_repository = EspecieRepository()
