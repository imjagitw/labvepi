"""
Módulo Base de Testes HTTP e DAO em Memória — LABVEPI
=====================================================
Implementa a infraestrutura das Fases 2 e 3 do Roadmap de Testes:
- ControllerTestCase: Classe base abstrata baseada em unittest.TestCase.
- Isolamento total em setUpClass: Desativa I/O do MongoDB forçando os 7 repositórios para modo O(1) em memória.
- Limpeza sistemática em setUp/tearDown: Executa .clear() em todos os repositórios garantindo isolamento entre testes.
- Helpers semânticos Arrange: Criação rápida e sem dependência de chamadas HTTP para pré-requisitos de dados.
- Helpers de contrato RESTful Assert: Validação padronizada de códigos (201, 200, 204 b"", 404, 409, 422) e imutabilidade de PKs.
- Verificadores reutilizáveis de contrato: Facilita a geração automática de testes para cada entidade/controller.
"""

import unittest
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi.testclient import TestClient

from src.main import app

# Importação dos 7 repositórios unificados
from src.repositories.especie_repository import especie_repository, EspecieRepository
from src.repositories.animal_repository import animal_repository, AnimalRepository
from src.repositories.amostra_repository import amostra_repository, AmostraRepository
from src.repositories.exame_repository import exame_repository, ExameRepository
from src.repositories.reagente_repository import reagente_repository, ReagenteRepository
from src.repositories.estoque_reagente_repository import estoque_reagente_repository, EstoqueReagenteRepository
from src.repositories.usuario_repository import usuario_repository, UsuarioRepository

# Modelos e Enums para injeção de dados de pré-requisitos
from src.models.Especie import Especie, Classe
from src.models.Animal import (
    Animal,
    Sexo,
    FaixaEtaria,
    Orgao,
    RegimeVida,
    StatusVital,
    UnidadePeso,
    UnidadeIdade,
)
from src.models.Amostra import (
    Amostra,
    MaterialBiologico,
    StatusAmostra,
    CondicaoArmazenamento,
    FaseAmostra,
    DestinoAmostra,
)
from src.models.Exame import Exame, TipoExame, ResultadoExame, TesteLaboratorial
from src.models.Reagente import Reagente, EtapaReagente, UnidadeMedida, StatusReagente
from src.models.EstoqueReagente import EstoqueReagente
from src.models.Usuario import Usuario, Perfil, StatusUsuario
from src.services.usuario_service import hash_password


ALL_REPOSITORIES = [
    especie_repository,
    animal_repository,
    amostra_repository,
    exame_repository,
    reagente_repository,
    estoque_reagente_repository,
    usuario_repository,
]


class ControllerTestCase(unittest.TestCase):
    """
    Classe base para testes de controladores e integração HTTP com TestClient.
    Garante o isolamento do banco MongoDB e fornece asserções contratuais padronizadas.
    """
    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        """
        Fase 2: Força todos os repositórios para modo de acesso em memória (use_mongo=False),
        eliminando I/O de rede com o MongoDB real, e inicializa o TestClient(app).
        """
        super().setUpClass()
        for repo in ALL_REPOSITORIES:
            repo._use_mongo = False
            repo._collection = None
            if hasattr(repo, "_db"):
                repo._db = None

        cls.client = TestClient(app)

    def setUp(self) -> None:
        """
        Fase 2: Limpa os registros em memória de todos os 7 repositórios
        antes de cada método de teste para garantir um estado 100% limpo e isolado.
        """
        super().setUp()
        self.limpar_repositorios()

    def tearDown(self) -> None:
        """
        Garante que nenhuma mutação vaze para o teste subsequente.
        """
        self.limpar_repositorios()
        super().tearDown()

    @classmethod
    def limpar_repositorios(cls) -> None:
        """Executa .clear() nos 7 repositórios em memória."""
        for repo in ALL_REPOSITORIES:
            repo.clear()

    # =========================================================================
    # FASE 2: HELPERS SEMÂNTICOS DE PRÉ-REQUISITOS (ARRANGE)
    # =========================================================================

    def criar_especie_pre_requisito(self, **kwargs) -> Especie:
        """
        Injeta diretamente uma espécie no repositório em memória para satisfazer dependências
        taxonômicas sem gerar requisições HTTP redundantes.
        """
        dados = {
            "nome_comum": "Morcego-vampiro",
            "nome_cientifico": "Desmodus rotundus",
            "classe": Classe.MAMIFERO,
        }
        dados.update(kwargs)

        # Se já existe espécie com esse nome científico, retorna existente
        existente = especie_repository.buscar_por_nome_cientifico(dados["nome_cientifico"])
        if existente:
            return existente

        especie = Especie(**dados)
        return especie_repository.create(especie)

    def criar_animal_pre_requisito(self, **kwargs) -> Animal:
        """
        Injeta diretamente um animal no repositório em memória.
        Garante que a espécie associada exista previamente.
        """
        nome_comum = kwargs.get("nome_comum", "Morcego-vampiro")
        nome_cientifico = kwargs.get("nome_cientifico", "Desmodus rotundus")
        classe = kwargs.get("classe", Classe.MAMIFERO)

        self.criar_especie_pre_requisito(
            nome_comum=nome_comum,
            nome_cientifico=nome_cientifico,
            classe=classe,
        )

        dados = {
            "animal_id": "ANI_TEST_001",
            "nome_comum": nome_comum,
            "nome_cientifico": nome_cientifico,
            "classe": classe,
            "sexo": Sexo.MACHO,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina/PI",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
            "peso": 30.0,
        }
        dados.update(kwargs)
        animal = Animal(**dados)
        return animal_repository.create(animal)

    def criar_amostra_pre_requisito(self, **kwargs) -> Amostra:
        """
        Injeta diretamente uma amostra no repositório em memória.
        Garante que o animal associado exista previamente.
        """
        animal_id = kwargs.get("animal_id", "ANI_TEST_001")
        if not animal_repository.buscar_por_animal_id(animal_id):
            self.criar_animal_pre_requisito(animal_id=animal_id)

        dados = {
            "amostra_id": "AMO_TEST_001",
            "animal_id": animal_id,
            "data_coleta": date.today(),
            "data_recebimento": date.today(),
            "material_biologico": MaterialBiologico.SORO,
            "status_amostra": StatusAmostra.DISPONIVEL,
            "laudo_liberado": False,
            "local_coleta": "Teresina - Zoobotânico",
            "nome_coletor": "Pesquisador LABVEPI",
            "condicao_armazenamento": CondicaoArmazenamento.CONGELADA,
            "fase_amostra": FaseAmostra.EXTRACAO,
            "destino_amostra": DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI,
            "caixa": "Caixa 01",
            "dna_disponivel": True,
            "rna_disponivel": False,
            "sequenciamento": False,
        }
        dados.update(kwargs)
        amostra = Amostra(**dados)
        return amostra_repository.create(amostra)

    def criar_exame_pre_requisito(self, **kwargs) -> Exame:
        """
        Injeta diretamente um exame no repositório em memória.
        Garante que a amostra associada exista previamente.
        """
        amostra_id = kwargs.get("amostra_id", "AMO_TEST_001")
        if not amostra_repository.buscar_por_amostra_id(amostra_id):
            self.criar_amostra_pre_requisito(amostra_id=amostra_id)

        dados = {
            "amostra_id": amostra_id,
            "tipo_exame": TipoExame.RAIVA,
            "resultado": ResultadoExame.NEGATIVO,
            "data_realizacao": date.today(),
            "teste_laboratorial": TesteLaboratorial.PCR,
            "responsavel_exame": "Dr. Silva",
            "kit_utilizado": "Kit PCR Raiva",
            "protocolo_exame": "PRT-001",
        }
        dados.update(kwargs)
        exame = Exame(**dados)
        return exame_repository.create(exame)

    def criar_reagente_pre_requisito(self, **kwargs) -> Reagente:
        """
        Injeta diretamente um lote de reagente no repositório em memória.
        """
        dados = {
            "reagente_codigo": "REA_TEST_001",
            "reagente_nome": "Taq DNA Polimerase",
            "numero_lote": "LOTE_TAQ_2026",
            "marca": "ThermoFisher",
            "data_validade": date.today() + timedelta(days=365),
            "reagente_local_armazenamento": "Freezer -20 C",
            "status_reagente": StatusReagente.DISPONIVEL,
            "quantidade_unidade": 2,
            "quantidade_volume": 500.0,
            "unidade_medida": UnidadeMedida.UL,
            "reagente_etapa": EtapaReagente.PCR,
        }
        dados.update(kwargs)
        reagente = Reagente(**dados)
        return reagente_repository.create(reagente)

    def criar_estoque_pre_requisito(self, **kwargs) -> EstoqueReagente:
        """
        Injeta diretamente um registro de estoque consolidado no repositório em memória.
        """
        dados = {
            "reagente_nome": "Taq DNA Polimerase",
            "reagente_codigo": "REA_TEST_001",
            "lotes": [],
            "quantidade_total_unidades": 0,
        }
        dados.update(kwargs)
        estoque = EstoqueReagente(**dados)
        return estoque_reagente_repository.create(estoque)

    def criar_usuario_pre_requisito(self, **kwargs) -> Usuario:
        """
        Injeta diretamente um usuário no repositório em memória com senha pré-hasheada.
        """
        senha_plana = kwargs.pop("senha_plana", None)
        password = kwargs.get("password")
        if senha_plana:
            password = hash_password(senha_plana)
        elif not password:
            password = hash_password("senhaSegura123")

        dados = {
            "username": "usuario_teste",
            "name": "Usuário de Teste",
            "email": "usuario_teste@ufpi.edu.br",
            "password": password,
            "perfil": Perfil.DOCENTE,
            "status": StatusUsuario.ATIVO,
        }
        dados.update(kwargs)
        dados["password"] = password
        usuario = Usuario(**dados)
        return usuario_repository.create(usuario)

    # =========================================================================
    # FASE 3: HELPERS DE ASSERÇÃO DE CONTRATO RESTFUL
    # =========================================================================

    def assert_status(self, response, expected_status: int, msg: Optional[str] = None) -> None:
        """
        Valida que o código de status HTTP da resposta corresponde ao esperado,
        com mensagem enriquecida contendo o corpo da resposta em caso de falha.
        """
        if response.status_code != expected_status:
            detalhe = f"Esperado status {expected_status}, mas obteve {response.status_code}. Resposta: {response.text}"
            if msg:
                detalhe = f"{msg} | {detalhe}"
            self.fail(detalhe)

    def assert_created(self, response) -> dict:
        """
        Valida contrato POST 201 Created e retorna o JSON desserializado.
        """
        self.assert_status(response, 201)
        return response.json()

    def assert_ok(self, response) -> Any:
        """
        Valida contrato 200 OK e retorna o payload retornado.
        """
        self.assert_status(response, 200)
        return response.json()

    def assert_no_content(self, response) -> None:
        """
        Valida contrato DELETE 204 No Content estritamente sem corpo (content == b"").
        """
        self.assert_status(response, 204)
        self.assertEqual(
            response.content,
            b"",
            f"Resposta 204 No Content deve ter corpo estritamente vazio (b''), mas recebeu: {response.content!r}",
        )

    def assert_not_found(self, response, expected_detail_substr: Optional[str] = None) -> dict:
        """
        Valida contrato 404 Not Found e a presença de 'detail'.
        """
        self.assert_status(response, 404)
        data = response.json()
        self.assertIn("detail", data, "Resposta 404 deve conter o atributo 'detail'")
        if expected_detail_substr:
            self.assertIn(
                expected_detail_substr.lower(),
                str(data["detail"]).lower(),
                f"Mensagem de detalhe esperada '{expected_detail_substr}' não encontrada em: {data['detail']}",
            )
        return data

    def assert_conflict(self, response, expected_code: Optional[str] = None) -> dict:
        """
        Valida contrato 409 Conflict estruturado (ex: confirmação ou chave duplicada).
        """
        self.assert_status(response, 409)
        data = response.json()
        self.assertIn("detail", data, "Resposta 409 deve conter o atributo 'detail'")
        if expected_code:
            detail = data["detail"]
            if isinstance(detail, dict):
                self.assertEqual(detail.get("codigo"), expected_code)
            else:
                self.assertIn(expected_code, str(detail))
        return data

    def assert_validation_error(self, response) -> dict:
        """
        Valida contrato 422 Unprocessable Entity (erros de schema/validação do Pydantic).
        """
        self.assert_status(response, 422)
        return response.json()

    def assert_primary_key_blocked(
        self,
        response_data: dict,
        fake_pk_sent: Any = 999999,
        fake_str_id: str = "FAKE_MONGO_ID",
    ) -> None:
        """
        Valida que IDs ou chaves primárias enviadas pelo cliente no payload foram descartadas
        ou substituídas por valores gerados pelo banco/serviço.
        """
        pk_id = response_data.get("id") or response_data.get("_id")
        self.assertNotEqual(
            pk_id,
            fake_pk_sent,
            f"Chave primária numérica informada pelo cliente ({fake_pk_sent}) não foi bloqueada!",
        )
        for key in ("_id", "animal_id", "amostra_id", "reagente_id", "exame_id"):
            if key in response_data:
                self.assertNotEqual(
                    response_data[key],
                    fake_str_id,
                    f"Chave identificadora ({key}) aceitou valor arbitrário do cliente: {fake_str_id}!",
                )

    # =========================================================================
    # FASE 3: MÉTODOS DE CONTRATO PADRÃO PARA GERAÇÃO AUTOMATIZADA
    # =========================================================================

    def verificar_contrato_post_criacao(
        self,
        rota: str,
        payload_valido: dict,
        fake_pk_field: str = "id",
        fake_pk_value: Any = 999999,
        expected_status: int = 201,
    ) -> dict:
        """
        Executa o fluxo padrão de POST:
        1. Envia payload com fake PK injetada.
        2. Assegura código 201 Created (ou status configurado).
        3. Assegura bloqueio da PK injetada.
        """
        payload = dict(payload_valido)
        payload[fake_pk_field] = fake_pk_value
        payload["_id"] = "FAKE_MONGO_ID"

        res = self.client.post(rota, json=payload)
        self.assert_status(res, expected_status)
        data = res.json()
        self.assert_primary_key_blocked(data, fake_pk_sent=fake_pk_value)
        return data

    def verificar_contrato_get_detalhes_e_filtros(
        self,
        rota_item: str,
        rota_listagem: str,
        query_param_filtro: Optional[Dict[str, Any]] = None,
    ) -> Tuple[dict, list]:
        """
        Executa o fluxo padrão de GET:
        1. Consulta de detalhes do item (200 OK).
        2. Listagem geral e/ou filtrada (200 OK com array).
        """
        res_det = self.client.get(rota_item)
        detalhes = self.assert_ok(res_det)

        res_list = self.client.get(rota_listagem, params=query_param_filtro)
        lista = self.assert_ok(res_list)
        self.assertIsInstance(lista, list, "Listagem do contrato deve retornar uma lista.")
        return detalhes, lista

    def verificar_contrato_patch_put_atualizacao(
        self,
        rota: str,
        payload_parcial: dict,
        metodo: str = "patch",
    ) -> dict:
        """
        Executa o fluxo padrão de atualização parcial (PATCH ou PUT):
        1. Submete alteração de atributos selecionados.
        2. Assegura status 200 OK.
        3. Verifica se os campos especificados foram atualizados.
        """
        call_fn = self.client.patch if metodo.lower() == "patch" else self.client.put
        res = call_fn(rota, json=payload_parcial)
        data = self.assert_ok(res)
        for k, v in payload_parcial.items():
            if k in data and k not in ("id", "_id"):
                self.assertEqual(data[k], v, f"Campo {k} não foi atualizado como esperado.")
        return data

    def verificar_contrato_delete(self, rota: str) -> None:
        """
        Executa o fluxo padrão de exclusão:
        1. DELETE retorna 204 No Content com corpo estritamente vazio (b'').
        2. GET subsequente na rota retorna 404 Not Found.
        """
        res_del = self.client.delete(rota)
        self.assert_no_content(res_del)

        res_get = self.client.get(rota)
        self.assert_not_found(res_get)
