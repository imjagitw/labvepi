from typing import Optional, List, Dict, Union
from src.models.Amostra import (
    Amostra,
    CondicaoArmazenamento,
    DestinoAmostra,
    FaseAmostra,
    MaterialBiologico,
    StatusAmostra,
)

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class AmostraRepository:
    """
    Repositório de persistência e acesso a dados da entidade Amostra.
    Responsabilidade exclusiva:
    - Armazenar, consultar, filtrar, atualizar e remover amostras.
    """

    def __init__(self, amostras: Optional[List[Amostra]] = None):
        self._por_id: Dict[int, Amostra] = {}
        self._por_amostra_id: Dict[str, Amostra] = {}
        # Correção: Um animal pode ter várias amostras (1:N)
        self._por_animal_id: Dict[str, List[Amostra]] = {}
        self._por_condicao_armazenamento: Dict[CondicaoArmazenamento, List[Amostra]] = {}
        self._por_destino_amostra: Dict[DestinoAmostra, List[Amostra]] = {}
        self._por_fase_amostra: Dict[FaseAmostra, List[Amostra]] = {}
        self._por_material_biologico: Dict[MaterialBiologico, List[Amostra]] = {}
        self._por_status_amostra: Dict[StatusAmostra, List[Amostra]] = {}
        self._proximo_id: int = 1

        for amostra in amostras or []:
            self.create(amostra)
    
    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, amostra: Amostra) -> None:
        chave_id = amostra.amostra_id.strip()
        self._por_amostra_id[chave_id] = amostra

        if amostra.id is not None:
            self._por_id[amostra.id] = amostra

        if amostra.animal_id:
            chave_animal = amostra.animal_id.strip()
            self._por_animal_id.setdefault(chave_animal, []).append(amostra)

        self._por_condicao_armazenamento.setdefault(amostra.condicao_armazenamento, []).append(amostra)
        self._por_destino_amostra.setdefault(amostra.destino_amostra, []).append(amostra)
        self._por_fase_amostra.setdefault(amostra.fase_amostra, []).append(amostra)
        self._por_material_biologico.setdefault(amostra.material_biologico, []).append(amostra)
        self._por_status_amostra.setdefault(amostra.status_amostra, []).append(amostra)
    
    def _desindexar(self, amostra: Amostra) -> None:
        chave_id = amostra.amostra_id.strip()
        self._por_amostra_id.pop(chave_id, None)

        if amostra.id is not None:
            self._por_id.pop(amostra.id, None)

        if amostra.animal_id:
            chave_animal = amostra.animal_id.strip()
            if amostra in self._por_animal_id.get(chave_animal, []):
                self._por_animal_id[chave_animal].remove(amostra)

        if amostra in self._por_condicao_armazenamento.get(amostra.condicao_armazenamento, []):
            self._por_condicao_armazenamento[amostra.condicao_armazenamento].remove(amostra)
            
        if amostra in self._por_destino_amostra.get(amostra.destino_amostra, []):
            self._por_destino_amostra[amostra.destino_amostra].remove(amostra)
            
        if amostra in self._por_fase_amostra.get(amostra.fase_amostra, []):
            self._por_fase_amostra[amostra.fase_amostra].remove(amostra)
            
        if amostra in self._por_material_biologico.get(amostra.material_biologico, []):
            self._por_material_biologico[amostra.material_biologico].remove(amostra)
            
        if amostra in self._por_status_amostra.get(amostra.status_amostra, []):
            self._por_status_amostra[amostra.status_amostra].remove(amostra)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, amostra: Amostra) -> Amostra:
        if not amostra.amostra_id:
            raise ValueError("O identificador único da amostra (amostra_id) é obrigatório.")

        chave_id = amostra.amostra_id.strip()
        if chave_id in self._por_amostra_id:
            raise ValueError(f"Amostra com ID '{chave_id}' já está cadastrada.")

        if amostra.id is None:
            amostra.id = self._proximo_id
            self._proximo_id += 1
        elif amostra.id >= self._proximo_id:
            self._proximo_id = amostra.id + 1

        self._indexar(amostra)
        return amostra
    
    def save(self, amostra: Amostra) -> Amostra:
        chave = amostra.amostra_id.strip()
        if chave in self._por_amostra_id:
            return self.update(chave, amostra)
        return self.create(amostra)
    
    def update(self, amostra_id: str, amostra_atualizada: Amostra) -> Amostra:
        chave = amostra_id.strip()
        if chave not in self._por_amostra_id:
            raise KeyError(f"Amostra com ID '{chave}' não encontrada.")

        amostra_antiga = self._por_amostra_id[chave]

        if amostra_antiga.amostra_id != amostra_atualizada.amostra_id:
            raise ValueError("Não é permitido alterar o identificador único da amostra.")

        self._desindexar(amostra_antiga)

        if amostra_atualizada.id is None:
            amostra_atualizada.id = amostra_antiga.id
        elif amostra_atualizada.id != amostra_antiga.id:
            if amostra_atualizada.id in self._por_id:
                raise ValueError(f"Já existe uma amostra com o ID '{amostra_atualizada.id}'.")
            if amostra_atualizada.id >= self._proximo_id:
                self._proximo_id = amostra_atualizada.id + 1

        self._indexar(amostra_atualizada)
        return amostra_atualizada
    
    def delete(self, amostra_id: str) -> bool:
        chave = amostra_id.strip()
        if chave in self._por_amostra_id:
            amostra = self._por_amostra_id[chave]
            self._desindexar(amostra)
            return True
        return False
    
    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        animal_id: Optional[str] = None,
        status_amostra: Optional[StatusAmostra] = None,
        fase_amostra: Optional[FaseAmostra] = None,
        condicao_armazenamento: Optional[CondicaoArmazenamento] = None,
        destino_amostra: Optional[DestinoAmostra] = None,
        material_biologico: Optional[MaterialBiologico] = None,
        ordenar_por: str = 'id',
        skip: int = 0,
        limit: int = 100,
    ) -> List[Amostra]:
        """
        Retorna lista de amostras armazenadas aplicando filtros, ordenação dinâmica e paginação.
        """
        resultado = list(self._por_amostra_id.values())

        # Aplicação de Filtros
        if animal_id:
            chave_animal = animal_id.strip()
            resultado = [a for a in resultado if a.animal_id and a.animal_id.strip() == chave_animal]
        if status_amostra:
            resultado = [a for a in resultado if a.status_amostra == status_amostra]
        if fase_amostra:
            resultado = [a for a in resultado if a.fase_amostra == fase_amostra]
        if condicao_armazenamento:
            resultado = [a for a in resultado if a.condicao_armazenamento == condicao_armazenamento]
        if destino_amostra:
            resultado = [a for a in resultado if a.destino_amostra == destino_amostra]
        if material_biologico:
            resultado = [a for a in resultado if a.material_biologico == material_biologico]

        # Paginação
        if skip > 0:
            resultado = resultado[skip:]
        if limit is not None and limit > 0:
            resultado = resultado[:limit]

        return resultado
    
    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[Amostra]:
        try:
            return self._por_id.get(int(id_numerico))
        except (ValueError, TypeError):
            return None
    
    def buscar_por_amostra_id(self, amostra_id: str) -> Optional[Amostra]:
        if not amostra_id:
            return None
        return self._por_amostra_id.get(amostra_id.strip())
    
    def buscar_por_animal_id(self, animal_id: str) -> List[Amostra]:
        """Retorna todas as amostras coletadas de um determinado animal."""
        if not animal_id:
            return []
        return list(self._por_animal_id.get(animal_id.strip(), []))
    
    def buscar_por_condicao_armazenamento(self, condicao_armazenamento: CondicaoArmazenamento) -> List[Amostra]:
        return list(self._por_condicao_armazenamento.get(condicao_armazenamento, []))
    
    def buscar_por_destino_amostra(self, destino_amostra: DestinoAmostra) -> List[Amostra]:
        return list(self._por_destino_amostra.get(destino_amostra, []))
    
    def buscar_por_fase_amostra(self, fase_amostra: FaseAmostra) -> List[Amostra]:
        return list(self._por_fase_amostra.get(fase_amostra, []))
    
    def buscar_por_material_biologico(self, material_biologico: MaterialBiologico) -> List[Amostra]:
        return list(self._por_material_biologico.get(material_biologico, []))
    
    def buscar_por_status_amostra(self, status_amostra: StatusAmostra) -> List[Amostra]:
        return list(self._por_status_amostra.get(status_amostra, []))

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONTROLE (COUNT, EXISTS, CLEAR):
    # -------------------------------------------------------------------------
    def count(self) -> int:
        """Retorna a quantidade total de amostras cadastradas."""
        return len(self._por_amostra_id)

    def exists(self, amostra_id: str) -> bool:
        """Verifica se existe uma amostra com o identificador fornecido."""
        if not amostra_id:
            return False
        return amostra_id.strip() in self._por_amostra_id

    def clear(self) -> None:
        """Limpa todo o armazenamento em memória do repositório."""
        self._por_id.clear()
        self._por_amostra_id.clear()
        self._por_animal_id.clear()
        self._por_condicao_armazenamento.clear()
        self._por_destino_amostra.clear()
        self._por_fase_amostra.clear()
        self._por_material_biologico.clear()
        self._por_status_amostra.clear()
        self._proximo_id = 1

amostra_repository = AmostraRepository()