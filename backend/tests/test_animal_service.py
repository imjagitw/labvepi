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
        self.assertEqual(self.service.animal_repo.contar(), 1)

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


if __name__ == "__main__":
    unittest.main()
