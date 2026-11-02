import unittest
import sys
from pathlib import Path
# Garante import do backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.models.Especie import Especie, EspecieCreate, Classe
from src.repositories.especie_repository import EspecieRepository
from src.services.especie_service import EspecieService

class TestEspecieService(unittest.TestCase):
    def setUp(self):
        self.repo = EspecieRepository()
        self.service = EspecieService(repo=self.repo, carregar_catalogo_padrao=False)

    def test_cadastrar_especie_normalizacao_e_formatacao(self):
        esp = self.service.cadastrar_especie(
            {
                "nome_comum": "Onça-pintada",
                "nome_cientifico": "panthera onca",
                "classe": "mamíferos",
            }
        )
        self.assertEqual(esp.nome_comum, "Onça-pintada")
        self.assertEqual(esp.nome_cientifico, "Panthera onca")
        self.assertEqual(esp.classe, Classe.MAMIFERO)

    def test_buscar_por_nome_comum_e_cientifico(self):
        self.service.cadastrar_especie(
            {"nome_comum": "Mico-leão-dourado", "nome_cientifico": "Leontopithecus rosalia", "classe": "Mamífero"}
        )
        esp1 = self.service.buscar_por_nome_comum("mico-leão-dourado")
        self.assertIsNotNone(esp1)
        self.assertEqual(esp1.nome_cientifico, "Leontopithecus rosalia")

        esp2 = self.service.buscar_por_nome_cientifico("LEONTOPITHECUS ROSALIA")
        self.assertIsNotNone(esp2)
        self.assertEqual(esp2.nome_comum, "Mico-leão-dourado")

    def test_resolver_especie_com_apenas_nome_comum(self):
        self.service.cadastrar_especie(
            {"nome_comum": "Arara-canindé", "nome_cientifico": "Ara ararauna", "classe": Classe.AVES}
        )
        comum, cient, classe = self.service.resolver_especie(nome_comum="Arara-canindé")
        self.assertEqual(comum, "Arara-canindé")
        self.assertEqual(cient, "Ara ararauna")
        self.assertEqual(classe, Classe.AVES)

    def test_resolver_especie_com_apenas_nome_cientifico(self):
        self.service.cadastrar_especie(
            {"nome_comum": "Arara-canindé", "nome_cientifico": "Ara ararauna", "classe": Classe.AVES}
        )
        comum, cient, classe = self.service.resolver_especie(nome_cientifico="Ara ararauna")
        self.assertEqual(comum, "Arara-canindé")
        self.assertEqual(cient, "Ara ararauna")
        self.assertEqual(classe, Classe.AVES)

    def test_resolver_especie_inconsistente_falha(self):
        self.service.cadastrar_especie(
            {"nome_comum": "Gato", "nome_cientifico": "Felis catus", "classe": Classe.MAMIFERO}
        )
        self.service.cadastrar_especie(
            {"nome_comum": "Cachorro", "nome_cientifico": "Canis lupus familiaris", "classe": Classe.MAMIFERO}
        )
        with self.assertRaises(ValueError):
            self.service.resolver_especie(nome_comum="Gato", nome_cientifico="Canis lupus familiaris")

    def test_id_gerado_automaticamente_e_descarte_de_id_fornecido(self):
        """Testa que id/_id fornecido pelo usuário é ignorado e gerado automaticamente pelo banco."""
        # Usuário tenta forçar id customizado
        esp1 = self.service.cadastrar_especie(
            {
                "id": 9999,
                "_id": "custom_fake_id",
                "nome_comum": "Lobo-guará",
                "nome_cientifico": "Chrysocyon brachyurus",
                "classe": Classe.MAMIFERO,
            }
        )
        self.assertNotEqual(esp1.id, 9999)
        self.assertNotEqual(esp1.id, "custom_fake_id")
        self.assertEqual(esp1.id, 1)

        # Segundo cadastro autoincrementa
        esp2 = self.service.cadastrar_especie(
            {
                "nome_comum": "Tamanduá-bandeira",
                "nome_cientifico": "Myrmecophaga tridactyla",
                "classe": Classe.MAMIFERO,
            }
        )
        self.assertEqual(esp2.id, 2)

    def test_atualizar_especie_ignora_id_no_corpo(self):
        """Testa que id/_id fornecido no corpo do update é descartado e o id da rota prevalece."""
        esp = self.service.cadastrar_especie(
            {"nome_comum": "Tatu-bola", "nome_cientifico": "Tolypeutes tricinctus", "classe": Classe.MAMIFERO}
        )
        orig_id = esp.id

        atualizado = self.service.atualizar_especie(
            orig_id,
            {
                "id": 8888,
                "_id": 7777,
                "nome_comum": "Tatu-bola-do-nordeste",
            },
        )
        self.assertEqual(atualizado.id, orig_id)
        self.assertEqual(atualizado.nome_comum, "Tatu-bola-do-nordeste")


if __name__ == "__main__":
    unittest.main()