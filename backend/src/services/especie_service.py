from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from src.models.Especie import Especie, EspecieCreate, EspecieUpdate, Classe
from src.repositories.especie_repository import EspecieRepository, especie_repository
from etl.catalogo import normalizar_classe_taxonomica, formatar_nome_cientifico, importar_catalogo_csv

class EspecieService:
    """
    Serviço responsável pelas ações de negócio e ciclo de vida da entidade Espécie:
    - [CREATE] Validação, formatação taxonômica e cadastro de espécies.
    - [READ] Consultas, buscas indexadas, listagem, contagem e filtros cruzados.
    - [UPDATE] Atualização com checagem de consistência e regras taxonômicas.
    - [DELETE] Exclusão com validação de existência.
    - Resolução taxonômica automatizada a partir do catálogo.
    """

    def __init__(
        self,
        repo: Optional[EspecieRepository] = None,
        carregar_catalogo_padrao: bool = True,
    ):
        self.repo = repo or especie_repository
        if carregar_catalogo_padrao and self.repo.count() == 0:
            caminho_csv = Path(__file__).resolve().parent.parent / "data" / "especies_catalogo.csv"
            if caminho_csv.exists():
                importar_catalogo_csv(caminho_csv, repo=self.repo, ignorar_duplicados=True)

    @staticmethod
    def normalizar_classe(val: Union[str, Classe]) -> Classe:
        """Normaliza variações textuais para o Enum canônico Classe."""
        return normalizar_classe_taxonomica(val)

    @staticmethod
    def formatar_nome_cientifico(nome: str) -> str:
        """Aplica formatação taxonômica padrão (Gênero capitalizado, epíteto em minúsculo)."""
        return formatar_nome_cientifico(nome)

    # -------------------------------------------------------------------------
    # OPERAÇÕES DE CRUD:
    # -------------------------------------------------------------------------
    def cadastrar_especie(
        self,
        dados: Union[Dict[str, Any], EspecieCreate],
        ignorar_duplicados: bool = False,
    ) -> Especie:
        """[CREATE] Validações taxonômicas e cadastro de uma nova espécie."""
        if isinstance(dados, EspecieCreate):
            nome_comum = dados.nome_comum
            nome_cient = dados.nome_cientifico
            classe_val = dados.classe
        else:
            nome_comum = dados.get("nome_comum") or dados.get("nome")
            nome_cient = dados.get("nome_cientifico")
            classe_val = dados.get("classe")

        if not nome_comum or not str(nome_comum).strip():
            raise ValueError("O nome comum da espécie é obrigatório.")

        nome_comum_limpo = str(nome_comum).strip()
        nome_cient_formatado = self.formatar_nome_cientifico(str(nome_cient))
        classe_canon = self.normalizar_classe(classe_val)

        existente = self.repo.buscar_por_nome_comum(nome_comum_limpo)
        if existente:
            if ignorar_duplicados:
                return existente
            raise ValueError(f"Espécie com nome comum '{nome_comum_limpo}' já cadastrada.")

        especie = Especie(
            nome_comum=nome_comum_limpo,
            nome_cientifico=nome_cient_formatado,
            classe=classe_canon,
        )
        return self.repo.save(especie)

    def obter_especie(self, id_especie: Union[int, str]) -> Especie:
        """[READ] Recupera uma espécie cadastrada pelo seu identificador primário."""
        especie = self.repo.buscar_por_id(id_especie)
        if not especie:
            raise KeyError(f"Espécie com ID '{id_especie}' não encontrada.")
        return especie

    def obter_especie_detalhes(self, id_especie: Union[int, str]):
        """[READ] Recupera informações completas da espécie incluindo contagem e listagem de animais."""
        from src.repositories.animal_repository import animal_repository
        from src.models.Especie.especie_details import EspecieDetails

        especie = self.obter_especie(id_especie)
        animais = animal_repository.buscar_por_especie(
            nome_comum=especie.nome_comum,
            nome_cientifico=especie.nome_cientifico,
        )
        return EspecieDetails(
            id=especie.id,
            nome_comum=especie.nome_comum,
            nome_cientifico=especie.nome_cientifico,
            classe=especie.classe,
            quantidade_animais=len(animais),
            animais=animais,
        )

    def buscar_por_id(self, id_especie: Union[int, str]) -> Optional[Especie]:
        """[READ] Consulta espécie por ID (retorna None se não encontrada)."""
        return self.repo.buscar_por_id(id_especie)

    def buscar_por_nome_comum(self, nome_comum: str) -> Optional[Especie]:
        """[READ] Consulta espécie pelo nome comum indexado."""
        return self.repo.buscar_por_nome_comum(nome_comum)

    def buscar_por_nome_cientifico(self, nome_cientifico: str) -> Optional[Especie]:
        """[READ] Consulta espécie pelo nome científico indexado."""
        return self.repo.buscar_por_nome_cientifico(nome_cientifico)

    def buscar_por_classe(self, classe: Union[Classe, str]) -> List[Especie]:
        """[READ] Consulta espécies pela classe taxonômica."""
        classe_canon = self.normalizar_classe(classe)
        return self.repo.buscar_por_classe(classe_canon)

    def filtrar_especies(
        self, 
        nome_comum: Optional[str] = None, 
        nome_cientifico: Optional[str] = None, 
        classe: Optional[str] = None
    ) -> List[Especie]:
        """[READ] Filtros dinâmicos cruzados com condição 'AND'."""
        if nome_cientifico:
            especie = self.buscar_por_nome_cientifico(nome_cientifico)
            if not especie:
                return []
            if nome_comum and especie.nome_comum.casefold() != nome_comum.casefold():
                return []
            if classe and especie.classe != self.normalizar_classe(classe):
                return []
            return [especie]

        if nome_comum:
            especie = self.buscar_por_nome_comum(nome_comum)
            if not especie:
                return []
            if classe and especie.classe != self.normalizar_classe(classe):
                return []
            return [especie]

        if classe:
            try:
                return self.buscar_por_classe(classe)
            except ValueError:
                return [] 

        return self.listar_especies()

    def listar_especies(self) -> List[Especie]:
        """[READ] Lista todas as espécies cadastradas no acervo."""
        return self.repo.listar()

    def contar_especies(self) -> int:
        """[READ] Retorna a quantidade total de espécies cadastradas."""
        return self.repo.count()

    def atualizar_especie(
        self,
        id_especie: Union[int, str],
        dados_atualizacao: Union[Dict[str, Any], EspecieUpdate],
    ) -> Especie:
        """[UPDATE] Atualiza uma espécie existente com validação taxonômica."""
        especie_atual = self.obter_especie(id_especie)

        if isinstance(dados_atualizacao, EspecieUpdate):
            dados_novos = dados_atualizacao.model_dump(by_alias=True, exclude_unset=True)
        else:
            dados_novos = {k: v for k, v in dados_atualizacao.items() if v is not None}

        nome_comum = dados_novos.get("nome_comum") or dados_novos.get("nome") or especie_atual.nome_comum
        nome_cient = dados_novos.get("nome_cientifico") or especie_atual.nome_cientifico
        classe_val = dados_novos.get("classe") or especie_atual.classe

        nome_comum_limpo = str(nome_comum).strip()
        nome_cient_formatado = self.formatar_nome_cientifico(str(nome_cient))
        classe_canon = self.normalizar_classe(classe_val)

        if nome_comum_limpo.casefold() != especie_atual.nome_comum.casefold():
            existente = self.repo.buscar_por_nome_comum(nome_comum_limpo)
            if existente and str(existente.id) != str(especie_atual.id):
                raise ValueError(f"Espécie com nome comum '{nome_comum_limpo}' já cadastrada.")

        especie_modificada = Especie(
            id=especie_atual.id,
            nome_comum=nome_comum_limpo,
            nome_cientifico=nome_cient_formatado,
            classe=classe_canon,
        )
        return self.repo.update(id_especie, especie_modificada)

    def deletar_especie(self, id_especie: Union[int, str]) -> bool:
        self.obter_especie(id_especie)
        return self.repo.delete(id_especie)

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
        """
        Resolve dados taxonômicos consultando o catálogo:
        - Se informado apenas nome científico, completa nome comum e classe.
        - Se informado apenas nome comum, completa nome científico e classe.
        - Se informados ambos, valida coerência.
        - Se for espécie inédita, exige confirmação explícita e dados completos.
        """
        especie = None
        if nome_cientifico:
            especie = self.buscar_por_nome_cientifico(nome_cientifico)

        if especie is None and nome_comum:
            especie = self.buscar_por_nome_comum(nome_comum)

        if especie is not None:
            if nome_comum and self.buscar_por_nome_comum(nome_comum) not in (None, especie):
                raise ValueError(
                    f"O nome comum '{nome_comum}' e o científico '{nome_cientifico}' "
                    "não correspondem à mesma espécie cadastrada no catálogo."
                )
            return especie.nome_comum, especie.nome_cientifico, especie.classe

        # Espécie não encontrada
        classe_canon = self.normalizar_classe(classe) if classe else None
        if not (nome_comum and nome_cientifico and classe_canon):
            raise ValueError(
                "Espécie não encontrada no catálogo de referência. "
                "Para cadastrar uma nova espécie, informe obrigatoriamente: "
                "nome comum, nome científico e classe."
            )

        if not confirmar_nova_especie:
            raise ValueError(
                f"A espécie '{nome_comum}' ({nome_cientifico}) não está no catálogo. "
                "Confirme o cadastro da nova espécie ('confirmar_nova_especie=True') para prosseguir."
            )

        nova = self.cadastrar_especie(
            {"nome_comum": nome_comum, "nome_cientifico": nome_cientifico, "classe": classe_canon}
        )
        return nova.nome_comum, nova.nome_cientifico, nova.classe

    def importar_tabela_csv(
        self,
        caminho_arquivo: Union[str, Path],
        delimitador: Optional[str] = None,
        ignorar_duplicados: bool = True,
    ) -> int:
        return importar_catalogo_csv(
            caminho_arquivo=caminho_arquivo,
            repo=self.repo,
            delimitador=delimitador,
            ignorar_duplicados=ignorar_duplicados,
        )

especie_service = EspecieService()