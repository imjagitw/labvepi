from typing import Optional, List, Dict, Union
from src.models.EstoqueReagente import EstoqueReagente
from src.models.Reagente import Reagente

def _normalizar(texto: Optional[str]) -> str:
    """Normaliza para chave indexada interna de busca em memória."""
    if not texto:
        return ""
    return " ".join(texto.strip().split()).casefold()

class EstoqueReagenteRepository:
    """
    Repositório de persistência e acesso a dados do modelo agregado EstoqueReagente.
    Responsabilidade exclusiva:
    - Armazenar, consultar, atualizar e remover agregações consolidadas de estoque por reagente.
    - Atuar como camada de acesso a dados (DAO/Persistência) para visões de inventário unificado.
    - Suporta indexação O(1) por ID numérico e por nome normalizado do reagente.
    - NÃO contém fórmulas de conversão dimensional ou cálculos temporais (delegados ao ReagenteService).
    """

    def __init__(self, estoques: Optional[List[EstoqueReagente]] = None):
        self._por_id: Dict[int, EstoqueReagente] = {}
        # O nome do reagente atua como a chave de agrupamento canônica do estoque
        self._por_nome: Dict[str, EstoqueReagente] = {}
        self._por_codigo: Dict[str, List[EstoqueReagente]] = {}
        self._proximo_id: int = 1

        for estoque in estoques or []:
            self.create(estoque)

    # -------------------------------------------------------------------------
    # GESTÃO INTERNA DE ÍNDICES:
    # -------------------------------------------------------------------------
    def _indexar(self, estoque: EstoqueReagente) -> None:
        if estoque.id is not None:
            self._por_id[int(estoque.id)] = estoque

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome:
            self._por_nome[chave_nome] = estoque

        if estoque.reagente_codigo:
            chave_cod = _normalizar(estoque.reagente_codigo)
            if chave_cod:
                self._por_codigo.setdefault(chave_cod, []).append(estoque)

    def _desindexar(self, estoque: EstoqueReagente) -> None:
        if estoque.id is not None:
            self._por_id.pop(int(estoque.id), None)

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome:
            self._por_nome.pop(chave_nome, None)

        if estoque.reagente_codigo:
            chave_cod = _normalizar(estoque.reagente_codigo)
            if chave_cod in self._por_codigo and estoque in self._por_codigo[chave_cod]:
                self._por_codigo[chave_cod].remove(estoque)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def create(self, estoque: EstoqueReagente) -> EstoqueReagente:
        """Persiste um novo registro consolidado de estoque de reagente."""
        if not estoque.reagente_nome:
            raise ValueError("O nome do reagente (reagente_nome) é obrigatório para o estoque.")

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome in self._por_nome:
            raise ValueError(f"Estoque para o reagente '{estoque.reagente_nome}' já está cadastrado.")

        if estoque.id is None:
            estoque.id = self._proximo_id
            self._proximo_id += 1
        else:
            chave_id = int(estoque.id)
            if chave_id in self._por_id:
                raise ValueError(f"Estoque com ID {chave_id} já existe no banco de dados.")
            if chave_id >= self._proximo_id:
                self._proximo_id = chave_id + 1

        self._indexar(estoque)
        return estoque

    def save(self, estoque: EstoqueReagente) -> EstoqueReagente:
        """Persiste ou atualiza o estoque se já possuir ID ou nome registrado."""
        if estoque.id is not None and int(estoque.id) in self._por_id:
            return self.update(estoque.id, estoque)

        chave_nome = _normalizar(estoque.reagente_nome)
        if chave_nome in self._por_nome:
            return self.update(chave_nome, estoque)

        return self.create(estoque)

    def update(self, identificador: Union[int, str], estoque_atualizado: EstoqueReagente) -> EstoqueReagente:
        """Atualiza a visão consolidada de estoque de um reagente existente."""
        antigo = self.buscar_por_id(identificador) or self.buscar_por_nome(str(identificador))
        if not antigo:
            raise KeyError(f"Estoque para '{identificador}' não encontrado para atualização.")

        self._desindexar(antigo)

        # Preserva ID numérico consistente
        if estoque_atualizado.id is None:
            estoque_atualizado.id = antigo.id
        elif int(estoque_atualizado.id) != int(antigo.id):
            chave_nova = int(estoque_atualizado.id)
            if chave_nova in self._por_id:
                raise ValueError(f"Já existe outro estoque com ID {chave_nova}.")
            if chave_nova >= self._proximo_id:
                self._proximo_id = chave_nova + 1

        # Valida se o novo nome colide com outro registro
        chave_nome_nova = _normalizar(estoque_atualizado.reagente_nome)
        chave_nome_antiga = _normalizar(antigo.reagente_nome)
        if chave_nome_nova != chave_nome_antiga and chave_nome_nova in self._por_nome:
            raise ValueError(f"Já existe outro estoque com o nome '{estoque_atualizado.reagente_nome}'.")

        self._indexar(estoque_atualizado)
        return estoque_atualizado

    def delete(self, identificador: Union[int, str]) -> bool:
        """Exclui a visão de estoque consolidado pelo ID numérico ou pelo nome do reagente."""
        estoque = self.buscar_por_id(identificador) or self.buscar_por_nome(str(identificador))
        if not estoque:
            return False

        self._desindexar(estoque)
        return True

    # -------------------------------------------------------------------------
    # CONSULTAS DIRETAS INDEXADAS:
    # -------------------------------------------------------------------------
    def buscar_por_id(self, id_numerico: Union[int, str]) -> Optional[EstoqueReagente]:
        try:
            return self._por_id.get(int(id_numerico))
        except (ValueError, TypeError):
            return None

    def buscar_por_nome(self, nome: str) -> Optional[EstoqueReagente]:
        """Consulta estoque consolidado pela chave canônica do nome do reagente."""
        chave = _normalizar(nome)
        if not chave:
            return None
        return self._por_nome.get(chave)

    def buscar_por_codigo(self, codigo: str) -> List[EstoqueReagente]:
        """Consulta registros de estoque que possuam o código de referência fornecido."""
        chave = _normalizar(codigo)
        if not chave:
            return []
        return list(self._por_codigo.get(chave, []))

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CONSULTA (LISTAGEM DINÂMICA):
    # -------------------------------------------------------------------------
    def listar(
        self,
        termo_busca: Optional[str] = None,
        apenas_com_lotes: Optional[bool] = None,
        ordenar_por: str = "nome",
        skip: int = 0,
        limit: int = 100,
    ) -> List[EstoqueReagente]:
        """Retorna lista de estoques aplicando busca textual, ordenação e paginação."""
        resultado_lista = list(self._por_nome.values())

        if apenas_com_lotes is not None:
            if apenas_com_lotes:
                resultado_lista = [e for e in resultado_lista if len(e.lotes) > 0]
            else:
                resultado_lista = [e for e in resultado_lista if len(e.lotes) == 0]

        if termo_busca:
            termo = _normalizar(termo_busca)
            resultado_lista = [
                e for e in resultado_lista
                if (
                    termo in _normalizar(e.reagente_nome)
                    or (e.reagente_codigo and termo in _normalizar(e.reagente_codigo))
                    or any(termo in _normalizar(l.numero_lote) or termo in _normalizar(l.marca) for l in e.lotes)
                )
            ]

        # Ordenação
        if ordenar_por == "id":
            resultado_lista.sort(key=lambda e: (int(e.id) if e.id is not None else 0))
        elif ordenar_por == "quantidade":
            resultado_lista.sort(key=lambda e: e.quantidade_total_unidades, reverse=True)
        else:
            resultado_lista.sort(key=lambda e: e.reagente_nome.lower())

        # Paginação
        if skip > 0:
            resultado_lista = resultado_lista[skip:]
        if limit is not None and limit > 0:
            resultado_lista = resultado_lista[:limit]

        return resultado_lista

    # -------------------------------------------------------------------------
    # MÉTODOS DE CONTROLE (COUNT, CONTAR, EXISTS, CLEAR):
    # -------------------------------------------------------------------------
    def count(self) -> int:
        """Retorna a quantidade total de tipos de reagentes com estoque registrado."""
        return len(self._por_nome)

    def exists(self, identificador: Union[int, str]) -> bool:
        """Verifica se existe um estoque registrado com o ID ou nome fornecido."""
        return self.buscar_por_id(identificador) is not None or self.buscar_por_nome(str(identificador)) is not None

    def clear(self) -> None:
        """Limpa todo o acervo de estoques agregados em memória."""
        self._por_id.clear()
        self._por_nome.clear()
        self._por_codigo.clear()
        self._proximo_id = 1

estoque_reagente_repository = EstoqueReagenteRepository()