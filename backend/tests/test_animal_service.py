import unittest
import tempfile
import sys
from pathlib import Path

# Garante import do backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.Animal import (
    Animal,
    AnimalCreate,
    AnimalUpdate,
    Sexo,
    FaixaEtaria,
    Orgao,
    RegimeVida,
    StatusVital,
    UnidadePeso,
    UnidadeIdade,
)
from src.models.Especie import Classe
from src.repositories.especie_repository import EspecieRepository
from src.repositories.animal_repository import AnimalRepository
from src.services.especie_service import EspecieService
from src.services.animal_service import AnimalService


class TestAnimalService(unittest.TestCase):
    def setUp(self):
        """Cria instâncias isoladas de repositórios e serviços para cada teste."""
        self.especie_repo = EspecieRepository()
        self.especie_service = EspecieService(repo=self.especie_repo, carregar_catalogo_padrao=True)
        self.animal_repo = AnimalRepository()
        self.service = AnimalService(
            especie_serv=self.especie_service,
            animal_repo=self.animal_repo,
        )

    def test_criar_animal_com_especie_automatizada_por_nome_comum(self):
        """Testa se nome_cientifico e classe são preenchidos automaticamente pelo catálogo."""
        dados = {
            "animal_id": "TEST_001",
            "nome_comum": "Bugio-preto",
            "sexo": Sexo.MACHO,
            "peso": 4.5,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        }
        animal = self.service.criar_animal(dados)

        self.assertEqual(animal.animal_id, "TEST_001")
        self.assertEqual(animal.nome_comum, "Bugio-preto")
        self.assertEqual(animal.nome_cientifico, "Alouatta caraya")
        self.assertEqual(animal.classe, Classe.MAMIFERO)

    def test_criar_animal_com_especie_automatizada_por_nome_cientifico(self):
        """Testa se nome_comum e classe são preenchidos automaticamente pelo nome científico."""
        dados = {
            "animal_id": "TEST_002",
            "nome_cientifico": "Amazona aestiva",
            "sexo": Sexo.FEMEA,
            "peso": "400g",
            "orgao": Orgao.IBAMA_CETAS_PI,
            "local_origem": "Teresina",
            "status": RegimeVida.CATIVEIRO,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        }
        animal = self.service.criar_animal(dados)

        self.assertEqual(animal.nome_comum, "Papagaio-verdadeiro")
        self.assertEqual(animal.nome_cientifico, "Amazona aestiva")
        self.assertEqual(animal.classe, Classe.AVES)
        self.assertEqual(animal.peso, 0.4)  # 400g convertido para 0.4 kg

    def test_processamento_e_conversao_peso(self):
        """Testa tratamento de formatos de peso: gramas, kg, strings, vírgulas e não aferido."""
        self.assertEqual(self.service.processar_peso("500g"), 0.5)
        self.assertEqual(self.service.processar_peso("15g"), 0.015)
        self.assertEqual(self.service.processar_peso("2.5kg"), 2.5)
        self.assertEqual(self.service.processar_peso("12,5"), 12.5)
        self.assertEqual(self.service.processar_peso(10), 10.0)
        self.assertEqual(self.service.processar_peso("Não aferido"), "Não aferido")
        self.assertEqual(self.service.processar_peso("NI"), "Não aferido")
        self.assertEqual(self.service.processar_peso("-"), "Não aferido")
        self.assertEqual(self.service.processar_peso(""), "Não aferido")
        self.assertEqual(self.service.processar_peso(None), "Não aferido")

        with self.assertRaises(ValueError):
            self.service.validar_peso(0)

        with self.assertRaises(ValueError):
            self.service.validar_peso(-1.5)

    def test_deducao_automatica_faixa_etaria(self):
        """Testa dedução de faixa etária a partir da idade informada."""
        self.assertEqual(self.service.deduzir_faixa_etaria("6 meses"), FaixaEtaria.FILHOTE)
        self.assertEqual(self.service.deduzir_faixa_etaria("1.5 anos"), FaixaEtaria.JUVENIL)
        self.assertEqual(self.service.deduzir_faixa_etaria("3 anos"), FaixaEtaria.SUB_ADULTO)
        self.assertEqual(self.service.deduzir_faixa_etaria("6 anos"), FaixaEtaria.ADULTO)
        self.assertEqual(self.service.deduzir_faixa_etaria("12 anos"), FaixaEtaria.SENIL)
        self.assertEqual(self.service.deduzir_faixa_etaria("filhote de ninho"), FaixaEtaria.FILHOTE)

        dados = {
            "animal_id": "TEST_FAIXA",
            "nome_comum": "Gato",
            "sexo": Sexo.FEMEA,
            "peso": "Não aferido",
            "idade": "8 meses",
            "orgao": Orgao.HVU,
            "local_origem": "Teresina",
            "status": RegimeVida.DOMICILIADO,
            "status_vital": StatusVital.VIVO,
        }
        animal = self.service.criar_animal(dados)
        self.assertEqual(animal.faixa_etaria, FaixaEtaria.FILHOTE)

    def test_especie_inedita_exige_confirmacao_e_dados_completos(self):
        """Testa que espécie fora do catálogo é rejeitada sem confirmação explícita."""
        dados = {
            "animal_id": "TEST_NOVA_01",
            "nome_comum": "Animal Raro Silvestre",
            "nome_cientifico": "Silvestris rarissimus",
            "classe": Classe.MAMIFERO,
            "sexo": Sexo.MACHO,
            "peso": 12.0,
            "faixa_etaria": FaixaEtaria.ADULTO,
            "orgao": Orgao.UFPI,
            "local_origem": "Parque Nacional",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
        }
        # Sem confirmação deve falhar
        with self.assertRaises(ValueError):
            self.service.criar_animal(dados, confirmar_nova_especie=False)

        # Com confirmação deve cadastrar tanto no repositório de espécies quanto no animal
        animal = self.service.criar_animal(dados, confirmar_nova_especie=True)
        self.assertEqual(animal.animal_id, "TEST_NOVA_01")
        self.assertEqual(animal.nome_comum, "Animal Raro Silvestre")

        # Agora a nova espécie deve estar no serviço de espécies e ser reaproveitada
        esp = self.especie_service.buscar_por_nome_comum("Animal Raro Silvestre")
        self.assertIsNotNone(esp)
        self.assertEqual(esp.nome_cientifico, "Silvestris rarissimus")

    def test_recusar_animal_id_duplicado(self):
        """Garante que IDs de laboratório duplicados são rejeitados."""
        dados = {
            "animal_id": "DUP_001",
            "nome_comum": "Cachorro",
            "sexo": Sexo.MACHO,
            "peso": 10,
            "faixa_etaria": FaixaEtaria.ADULTO,
            "orgao": Orgao.HVU,
            "local_origem": "Teresina",
            "status": RegimeVida.DOMICILIADO,
            "status_vital": StatusVital.VIVO,
        }
        self.service.criar_animal(dados)

        with self.assertRaises(ValueError):
            self.service.criar_animal(dados)

    def test_crud_completo_obter_listar_atualizar_deletar(self):
        """Testa ciclo completo de CRUD: Create, Read, Update, Delete."""
        # 1. Create
        dados1 = {
            "animal_id": "ANM_A",
            "nome_comum": "Jiboia",
            "sexo": Sexo.INDETERMINADO,
            "peso": 3.2,
            "orgao": Orgao.ZOOLOGICO_PI,
            "local_origem": "Teresina",
            "status": RegimeVida.CATIVEIRO,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        }
        dados2 = {
            "animal_id": "ANM_B",
            "nome_comum": "Sapo-cururu",
            "sexo": Sexo.MACHO,
            "peso": "180g",
            "orgao": Orgao.UFPI,
            "local_origem": "Parnaíba",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "idade": "2 anos",
        }
        self.service.criar_animal(dados1)
        self.service.criar_animal(dados2)

        # 2. Read (obter por ID)
        a1 = self.service.obter_animal("ANM_A")
        self.assertEqual(a1.nome_comum, "Jiboia")
        self.assertEqual(a1.classe, Classe.REPTIL)

        with self.assertRaises(KeyError):
            self.service.obter_animal("ANM_INEXISTENTE")

        # 3. Read (listar com filtros)
        todos = self.service.listar_animais()
        self.assertEqual(len(todos), 2)

        apenas_repteis = self.service.listar_animais(classe=Classe.REPTIL)
        self.assertEqual(len(apenas_repteis), 1)
        self.assertEqual(apenas_repteis[0].animal_id, "ANM_A")

        por_busca = self.service.listar_animais(termo_busca="Parnaíba")
        self.assertEqual(len(por_busca), 1)
        self.assertEqual(por_busca[0].animal_id, "ANM_B")

        # 4. Update
        atualizado = self.service.atualizar_animal(
            "ANM_A",
            {"peso": "4.0kg", "local_origem": "Floriano"}
        )
        self.assertEqual(atualizado.peso, 4.0)
        self.assertEqual(atualizado.local_origem, "Floriano")

        # Update alterando espécie com resolução automática
        atualizado_esp = self.service.atualizar_animal("ANM_A", {"nome_comum": "Cavalo"})
        self.assertEqual(atualizado_esp.nome_comum, "Cavalo")
        self.assertEqual(atualizado_esp.nome_cientifico, "Equus caballus")
        self.assertEqual(atualizado_esp.classe, Classe.MAMIFERO)

        # 5. Delete
        removido = self.service.deletar_animal("ANM_A")
        self.assertTrue(removido)
        self.assertEqual(self.service.animal_repo.count(), 1)

        with self.assertRaises(KeyError):
            self.service.obter_animal("ANM_A")

    def test_importar_catalogo_externo_csv(self):
        """Testa importação de tabela CSV via EspecieService e resolução pelo AnimalService."""
        conteudo_csv = (
            "nome_comum,nome_cientifico,classe\n"
            "Lobo-guará,Chrysocyon brachyurus,Mamífero\n"
            "Tucano-toco,Ramphastos toco,Ave\n"
        )
        with tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False) as f:
            f.write(conteudo_csv)
            f.flush()
            caminho_csv = f.name

        try:
            novas = self.especie_service.importar_tabela_csv(caminho_csv)
            self.assertEqual(novas, 2)

            dados_lobo = {
                "animal_id": "LOBO_01",
                "nome_comum": "Lobo-guará",
                "sexo": Sexo.FEMEA,
                "peso": "23,5kg",
                "faixa_etaria": FaixaEtaria.ADULTO,
                "orgao": Orgao.IBAMA_CETAS_PI,
                "local_origem": "Picos",
                "status": RegimeVida.VIDA_LIVRE,
                "status_vital": StatusVital.VIVO,
            }
            animal = self.service.criar_animal(dados_lobo)
            self.assertEqual(animal.nome_cientifico, "Chrysocyon brachyurus")
            self.assertEqual(animal.classe, Classe.MAMIFERO)
        finally:
            Path(caminho_csv).unlink(missing_ok=True)

    # ---------------------------------------------------------------------
    # OBRIGATORIEDADE (NOVOS CADASTROS) x CARGA LEGADA
    # ---------------------------------------------------------------------
    def _dados_completos(self, **sobrescrever):
        dados = {
            "animal_id": "OBR_001",
            "nome_comum": "Bugio-preto",
            "sexo": Sexo.MACHO,
            "peso": 4.5,
            "faixa_etaria": FaixaEtaria.ADULTO,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
        }
        dados.update(sobrescrever)
        return {k: v for k, v in dados.items() if v is not ...}

    def test_cadastrar_animal_sem_sexo(self):
        """Novo cadastro sem sexo (ausente ou 'Não informado') deve ser rejeitado."""
        with self.assertRaises(ValueError):
            self.service.criar_animal(self._dados_completos(sexo=...))
        with self.assertRaises(ValueError):
            self.service.criar_animal(self._dados_completos(sexo=Sexo.NAO_INFORMADO))
        self.assertEqual(self.animal_repo.count(), 0)

    def test_rejeita_cada_campo_obrigatorio_ausente_ou_nao_informado(self):
        """Cada campo obrigatório ausente, vazio ou 'Não informado' gera ValueError."""
        casos = {
            "orgao": [..., None, Orgao.NAO_INFORMADO],
            "local_origem": [..., "", "   ", "Não informado"],
            "status": [..., None, RegimeVida.NAO_INFORMADO],
            "status_vital": [..., None, StatusVital.NAO_INFORMADO],
            "faixa_etaria": [..., None, FaixaEtaria.NAO_INFORMADO],
            "peso": [..., None, "", "NI", "abc", 0, -2],
        }
        for campo, valores in casos.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaises(ValueError):
                        self.service.criar_animal(self._dados_completos(**{campo: valor}))
        self.assertEqual(self.animal_repo.count(), 0)

    def test_peso_nao_aferido_explicito_e_aceito(self):
        animal = self.service.criar_animal(self._dados_completos(peso="Não aferido"))
        self.assertEqual(animal.peso, "Não aferido")

    def test_faixa_etaria_deduzida_da_idade_satisfaz_obrigatoriedade(self):
        animal = self.service.criar_animal(
            self._dados_completos(faixa_etaria=..., idade="3 anos")
        )
        self.assertEqual(animal.faixa_etaria, FaixaEtaria.SUB_ADULTO)

    def test_rejeicao_nao_cadastra_especie_nova(self):
        """Se o animal for rejeitado por obrigatoriedade, a espécie nova não é criada."""
        dados = self._dados_completos(
            nome_comum="Espécie Fantasma",
            nome_cientifico="Phantasma inexistens",
            classe=Classe.MAMIFERO,
            status_vital=...,
        )
        with self.assertRaises(ValueError):
            self.service.criar_animal(dados, confirmar_nova_especie=True)
        self.assertIsNone(self.especie_service.buscar_por_nome_comum("Espécie Fantasma"))

    def test_animal_create_exige_campos_obrigatorios(self):
        """O schema AnimalCreate (entrada da API) não aceita omissão dos obrigatórios."""
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            AnimalCreate(animal_id="X1", nome_comum="Bugio-preto")

        dto = AnimalCreate(**self._dados_completos(animal_id="DTO_001"))
        animal = self.service.criar_animal(dto)
        self.assertEqual(animal.animal_id, "DTO_001")

        dto_ni = AnimalCreate(**self._dados_completos(animal_id="DTO_002", sexo=Sexo.NAO_INFORMADO))
        with self.assertRaises(ValueError):
            self.service.criar_animal(dto_ni)

    def test_carga_legada_preenche_nao_informado(self):
        """Na carga de planilhas antigas, campos ausentes viram 'Não informado'/'Não aferido'."""
        animal = self.service.criar_animal(
            {"animal_id": "LEG_001", "nome_comum": "Bugio-preto", "peso": "NI", "sexo": "-"},
            carga_legada=True,
        )
        self.assertEqual(animal.sexo, Sexo.NAO_INFORMADO)
        self.assertEqual(animal.peso, "Não aferido")
        self.assertEqual(animal.faixa_etaria, FaixaEtaria.NAO_INFORMADO)
        self.assertEqual(animal.orgao_origem, Orgao.NAO_INFORMADO)
        self.assertEqual(animal.local_origem, "Não informado")
        self.assertEqual(animal.regime_vida, RegimeVida.NAO_INFORMADO)
        self.assertEqual(animal.status_vital, StatusVital.NAO_INFORMADO)
        self.assertEqual(animal.classe, Classe.MAMIFERO)

    def test_update_rejeita_obrigatorio_vazio_mas_permite_parcial_em_legado(self):
        """Update parcial: campos enviados são validados; legado incompleto pode ser editado aos poucos."""
        self.service.criar_animal(
            {"animal_id": "LEG_002", "nome_comum": "Bugio-preto"}, carga_legada=True
        )
        atualizado = self.service.atualizar_animal("LEG_002", {"sexo": Sexo.FEMEA})
        self.assertEqual(atualizado.sexo, Sexo.FEMEA)
        self.assertEqual(atualizado.status_vital, StatusVital.NAO_INFORMADO)

        with self.assertRaises(ValueError):
            self.service.atualizar_animal("LEG_002", {"sexo": Sexo.NAO_INFORMADO})
        with self.assertRaises(ValueError):
            self.service.atualizar_animal("LEG_002", {"peso": ""})
        with self.assertRaises(ValueError):
            self.service.atualizar_animal(
                "LEG_002", AnimalUpdate(animal_id="LEG_002", orgao=Orgao.NAO_INFORMADO)
            )

        atualizado = self.service.atualizar_animal(
            "LEG_002", AnimalUpdate(animal_id="LEG_002", orgao=Orgao.HVU, status=RegimeVida.CATIVEIRO)
        )
        self.assertEqual(atualizado.orgao_origem, Orgao.HVU)
        self.assertEqual(atualizado.regime_vida, RegimeVida.CATIVEIRO)

    def test_criar_animal_com_peso_valor_e_unidade(self):
        """Testa cadastro com valor numérico e unidade de peso (g e kg)."""
        # Morcego pequeno: 15 gramas
        dados_morcego = {
            "animal_id": "BAT_001",
            "nome_comum": "Morcego-de-linha-branca",
            "sexo": Sexo.MACHO,
            "peso_valor": 15.0,
            "peso_unidade": UnidadePeso.G,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        }
        bat = self.service.criar_animal(dados_morcego)
        self.assertEqual(bat.peso, 0.015)  # 15g convertido para 0.015 kg canônico
        self.assertEqual(bat.peso_valor, 15.0)
        self.assertEqual(bat.peso_unidade, UnidadePeso.G)

        # Bugio adulto: 4.8 kg
        dados_bugio = {
            "animal_id": "BUG_001",
            "nome_comum": "Bugio-preto",
            "sexo": Sexo.MACHO,
            "peso_valor": 4.8,
            "peso_unidade": UnidadePeso.KG,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        }
        bugio = self.service.criar_animal(dados_bugio)
        self.assertEqual(bugio.peso, 4.8)
        self.assertEqual(bugio.peso_valor, 4.8)
        self.assertEqual(bugio.peso_unidade, UnidadePeso.KG)

        # Espécime diminuto/filhote neonatal: 800 mg
        dados_tiny = {
            "animal_id": "TINY_001",
            "nome_comum": "Morcego-de-linha-branca",
            "sexo": Sexo.INDETERMINADO,
            "peso_valor": 800.0,
            "peso_unidade": UnidadePeso.MG,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.FILHOTE,
        }
        tiny = self.service.criar_animal(dados_tiny)
        self.assertEqual(tiny.peso, 0.0008)
        self.assertEqual(tiny.peso_valor, 800.0)
        self.assertEqual(tiny.peso_unidade, UnidadePeso.MG)

    def test_criar_animal_com_idade_estruturada(self):
        """Testa cadastro com valor numérico e unidade temporal de idade deduzindo faixa etária."""
        dados_filhote = {
            "animal_id": "CAT_001",
            "nome_comum": "Gato",
            "sexo": Sexo.FEMEA,
            "peso": 1.2,
            "idade_valor": 4,
            "idade_unidade": UnidadeIdade.MESES,
            "orgao": Orgao.HVU,
            "local_origem": "Teresina",
            "status": RegimeVida.DOMICILIADO,
            "status_vital": StatusVital.VIVO,
        }
        cat = self.service.criar_animal(dados_filhote)
        self.assertEqual(cat.idade, "4 meses")
        self.assertEqual(cat.idade_valor, 4.0)
        self.assertEqual(cat.idade_unidade, UnidadeIdade.MESES)
        self.assertEqual(cat.faixa_etaria, FaixaEtaria.FILHOTE)

        dados_adulto = {
            "animal_id": "DOG_001",
            "nome_comum": "Cachorro",
            "sexo": Sexo.MACHO,
            "peso": 12.0,
            "idade_valor": 5,
            "idade_unidade": UnidadeIdade.ANOS,
            "orgao": Orgao.HVU,
            "local_origem": "Teresina",
            "status": RegimeVida.DOMICILIADO,
            "status_vital": StatusVital.VIVO,
        }
        dog = self.service.criar_animal(dados_adulto)
        self.assertEqual(dog.idade, "5 anos")
        self.assertEqual(dog.idade_valor, 5.0)
        self.assertEqual(dog.idade_unidade, UnidadeIdade.ANOS)
        self.assertEqual(dog.faixa_etaria, FaixaEtaria.ADULTO)

    def test_atualizar_animal_com_peso_e_idade_estruturados(self):
        """Testa atualização de animal com novos valores e unidades de peso e idade."""
        dados = {
            "animal_id": "ANM_STRUCT",
            "nome_comum": "Gato",
            "sexo": Sexo.MACHO,
            "peso": 2.0,
            "idade": "1 ano",
            "orgao": Orgao.HVU,
            "local_origem": "Teresina",
            "status": RegimeVida.DOMICILIADO,
            "status_vital": StatusVital.VIVO,
        }
        animal = self.service.criar_animal(dados)
        self.assertEqual(animal.peso, 2.0)

        # Atualiza peso para 2500g e idade para 3 anos
        atualizacao = {
            "peso_valor": 2500.0,
            "peso_unidade": UnidadePeso.G,
            "idade_valor": 3,
            "idade_unidade": UnidadeIdade.ANOS,
        }
        atualizado = self.service.atualizar_animal("ANM_STRUCT", atualizacao)
        self.assertEqual(atualizado.peso, 2.5)  # 2500g = 2.5 kg
        self.assertEqual(atualizado.peso_valor, 2500.0)
        self.assertEqual(atualizado.peso_unidade, UnidadePeso.G)
        self.assertEqual(atualizado.idade, "3 anos")
        self.assertEqual(atualizado.idade_valor, 3.0)
        self.assertEqual(atualizado.idade_unidade, UnidadeIdade.ANOS)
        self.assertEqual(atualizado.faixa_etaria, FaixaEtaria.SUB_ADULTO)

    def test_obter_animal_detalhes_contem_campos_estruturados(self):
        """Testa se AnimalDetails expõe corretamente peso_valor, peso_unidade, idade_valor e idade_unidade."""
        dados = {
            "animal_id": "ANM_DET",
            "nome_comum": "Bugio-preto",
            "sexo": Sexo.FEMEA,
            "peso_valor": 3.8,
            "peso_unidade": UnidadePeso.KG,
            "idade_valor": 6,
            "idade_unidade": UnidadeIdade.ANOS,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
        }
        self.service.criar_animal(dados)
        detalhes = self.service.obter_animal_detalhes("ANM_DET")
        self.assertEqual(detalhes.peso, 3.8)
        self.assertEqual(detalhes.peso_valor, 3.8)
        self.assertEqual(detalhes.peso_unidade, UnidadePeso.KG)
        self.assertEqual(detalhes.idade, "6 anos")
        self.assertEqual(detalhes.idade_valor, 6.0)
        self.assertEqual(detalhes.idade_unidade, UnidadeIdade.ANOS)

    def test_repositorio_busca_por_unidade_peso_e_faixa(self):
        """Testa métodos de busca do repositório por unidade e faixa de peso."""
        self.service.criar_animal({
            "animal_id": "BAT_INDEX",
            "nome_comum": "Morcego-de-linha-branca",
            "sexo": Sexo.MACHO,
            "peso_valor": 20.0,
            "peso_unidade": UnidadePeso.G,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        })
        self.service.criar_animal({
            "animal_id": "BUG_INDEX",
            "nome_comum": "Bugio-preto",
            "sexo": Sexo.FEMEA,
            "peso_valor": 5.0,
            "peso_unidade": UnidadePeso.KG,
            "orgao": Orgao.UFPI,
            "local_origem": "Teresina",
            "status": RegimeVida.VIDA_LIVRE,
            "status_vital": StatusVital.VIVO,
            "faixa_etaria": FaixaEtaria.ADULTO,
        })

        em_gramas = self.animal_repo.buscar_por_unidade_peso(UnidadePeso.G)
        self.assertEqual(len(em_gramas), 1)
        self.assertEqual(em_gramas[0].animal_id, "BAT_INDEX")

        em_kg = self.animal_repo.buscar_por_unidade_peso(UnidadePeso.KG)
        self.assertTrue(any(a.animal_id == "BUG_INDEX" for a in em_kg))

        pesados = self.animal_repo.buscar_por_faixa_peso(min_kg=1.0)
        self.assertTrue(any(a.animal_id == "BUG_INDEX" for a in pesados))
        self.assertFalse(any(a.animal_id == "BAT_INDEX" for a in pesados))


if __name__ == "__main__":
    unittest.main()