import unittest
from datetime import date, datetime
from pydantic import ValidationError

from src.models.Usuario import Usuario, Perfil
from src.models.Exame import Exame, ExameCreate, ExameUpdate, ExameDetails, TipoExame, ResultadoExame, TesteLaboratorial
from src.models.Animal import Animal, AnimalCreate, AnimalUpdate, AnimalDetails, Sexo, StatusVital, Orgao, RegimeVida, FaixaEtaria, UnidadePeso, UnidadeIdade
from src.models.Especie.enums.Classe import Classe
from src.models.Amostra import Amostra, AmostraCreate, AmostraUpdate, AmostraDetails, MaterialBiologico, StatusAmostra, CondicaoArmazenamento, FaseAmostra, DestinoAmostra


class TestModelCorrections(unittest.TestCase):
    """
    Testes unitários para validar as correções de tipagem estrita nos modelos (models/),
    garantindo que campos antes heterogêneos (Union) ou ambíguos foram estritamente tipados.
    """

    # -------------------------------------------------------------------------
    # USUARIO: matricula (Optional[str]) e last_login (Optional[datetime])
    # -------------------------------------------------------------------------
    def test_usuario_matricula_e_last_login_tipagem(self):
        # Usuário válido com string e datetime
        u = Usuario(
            usuario="pesquisador1",
            nome="Dr. Pesquisador",
            email="pesquisador@ufpi.edu.br",
            senha="hash",
            perfil=Perfil.DOCENTE,
            matricula="SIAPE-123456",
            last_login=datetime(2026, 10, 17, 10, 30, 0),
        )
        self.assertIsInstance(u.matricula, str)
        self.assertEqual(u.matricula, "SIAPE-123456")
        self.assertIsInstance(u.last_login, datetime)
        self.assertEqual(u.last_login.year, 2026)

        # Matrícula numérica pode ser fornecida como string
        u2 = Usuario(
            usuario="aluno1",
            email="aluno@ufpi.edu.br",
            senha="hash",
            perfil=Perfil.BOLSISTA_PIBITI,
            matricula="0012345",
            last_login=None,
        )
        self.assertEqual(u2.matricula, "0012345")
        self.assertIsNone(u2.last_login)

    # -------------------------------------------------------------------------
    # ANIMAL: local_origem, municipio, uf, localidade_detalhe
    # -------------------------------------------------------------------------
    def test_animal_campos_localidade_estruturada(self):
        # Criação de Animal com campos de localidade estruturados
        an = Animal(
            animal_id="ANM01",
            classe=Classe.MAMIFERO,
            nome_comum="Morcego",
            nome_cientifico="Artibeus lituratus",
            sexo=Sexo.MACHO,
            peso="Não aferido",
            orgao=Orgao.UFPI,
            local_origem="Teresina/PI",
            municipio="Teresina",
            uf="PI",
            localidade_detalhe="Campus Petrônio Portella",
            status=RegimeVida.VIDA_LIVRE,
            status_vital=StatusVital.VIVO,
        )
        self.assertEqual(an.municipio, "Teresina")
        self.assertEqual(an.uf, "PI")
        self.assertEqual(an.localidade_detalhe, "Campus Petrônio Portella")
        self.assertEqual(an.local_origem, "Teresina/PI")

        # AnimalCreate com campos estruturados
        anc = AnimalCreate(
            animal_id="ANM02",
            classe=Classe.AVES,
            nome_comum="Gavião",
            nome_cientifico="Rupornis magnirostris",
            sexo=Sexo.FEMEA,
            peso=0.25,
            orgao=Orgao.UFPI,
            municipio="Parnaíba",
            uf="PI",
            localidade_detalhe="Praia da Pedra do Sal",
            status=RegimeVida.VIDA_LIVRE,
            status_vital=StatusVital.VIVO,
            faixa_etaria=FaixaEtaria.ADULTO,
        )
        self.assertEqual(anc.municipio, "Parnaíba")
        self.assertEqual(anc.uf, "PI")

    # -------------------------------------------------------------------------
    # AMOSTRA: data_coleta_amostra, data_entrega, latitude, longitude, enums
    # -------------------------------------------------------------------------
    def test_amostra_tipagem_estrita(self):
        # Amostra com datas estritas date e coordenadas float
        ams = Amostra(
            amostra_id="AMS01",
            animal_id="ANM01",
            data_coleta=date(2026, 10, 10),
            data_recebimento=date(2026, 10, 11),
            material_biologico=MaterialBiologico.SORO,
            status_amostra=StatusAmostra.DISPONIVEL,
            condicao_armazenamento=CondicaoArmazenamento.CONGELADA,
            fase_amostra=FaseAmostra.EXTRACAO,
            destino_amostra=DestinoAmostra.BIOBANCO_UFPI,
            latitude=-5.089,
            longitude=-42.801,
        )
        self.assertIsInstance(ams.data_coleta_amostra, date)
        self.assertIsInstance(ams.data_entrega, date)
        self.assertIsInstance(ams.latitude, float)
        self.assertIsInstance(ams.longitude, float)
        self.assertEqual(ams.material_biologico, MaterialBiologico.SORO)

        # AmostraCreate exige Enum estrito
        amsc = AmostraCreate(
            amostra_id="AMS02",
            animal="ANM01",
            data_coleta=date(2026, 10, 10),
            metodo_coleta=MaterialBiologico.SWAB_CLOACAL,
            status_amostra=StatusAmostra.DISPONIVEL,
            laudo_liberado=False,
            local_coleta="Teresina",
            nome_coletor="Bolsista LABVEPI",
            condicao_armazenamento=CondicaoArmazenamento.REFRIGERADA,
            fase_amostra=FaseAmostra.EXTRACAO,
            destino_amostra=DestinoAmostra.BIOBANCO_UFPI,
            kit_utilizado="Kit Extração",
            caixa="Caixa 01",
            dna_disponivel=True,
            rna_disponivel=False,
            sequenciamento=False,
            latitude=-5.09,
            longitude=-42.80,
        )
        self.assertEqual(amsc.material_biologico, MaterialBiologico.SWAB_CLOACAL)
        self.assertEqual(amsc.latitude, -5.09)


if __name__ == "__main__":
    unittest.main()
