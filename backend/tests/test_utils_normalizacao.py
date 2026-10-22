import unittest

from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_peso,
    validar_peso,
    deduzir_faixa_etaria,
    normalizar_sexo,
    normalizar_status_vital,
    normalizar_material_biologico,
)
from src.models.Animal.enums.Sexo import Sexo
from src.models.Animal.enums.StatusVital import StatusVital
from src.models.Animal.enums.FaixaEtaria import FaixaEtaria
from src.models.Amostra.enums.MaterialBiologico import MaterialBiologico


class TestUtilsNormalizacao(unittest.TestCase):
    def test_eh_nao_informado(self):
        self.assertTrue(eh_nao_informado(None))
        self.assertTrue(eh_nao_informado(""))
        self.assertTrue(eh_nao_informado("-"))
        self.assertTrue(eh_nao_informado("NI"))
        self.assertTrue(eh_nao_informado("Não informado"))
        self.assertTrue(eh_nao_informado("nao informado"))
        self.assertFalse(eh_nao_informado(False))
        self.assertFalse(eh_nao_informado(True))
        self.assertFalse(eh_nao_informado("Macho"))
        self.assertFalse(eh_nao_informado(12))

    def test_normalizar_peso(self):
        self.assertEqual(normalizar_peso("400g"), 0.4)
        self.assertEqual(normalizar_peso("15 g"), 0.015)
        self.assertEqual(normalizar_peso("2.5kg"), 2.5)
        self.assertEqual(normalizar_peso("12,5"), 12.5)
        self.assertEqual(normalizar_peso(10), 10.0)
        self.assertEqual(normalizar_peso("NI"), "Não aferido")
        self.assertEqual(normalizar_peso(""), "Não aferido")
        self.assertEqual(normalizar_peso("-"), "Não aferido")
        self.assertEqual(normalizar_peso("não aferido"), "Não aferido")
        self.assertEqual(normalizar_peso("texto invalido"), "Não aferido")

    def test_validar_peso(self):
        validar_peso(10.5)
        validar_peso("Não aferido")
        with self.assertRaises(ValueError):
            validar_peso(0)
        with self.assertRaises(ValueError):
            validar_peso(-1.5)

    def test_deduzir_faixa_etaria(self):
        self.assertEqual(deduzir_faixa_etaria("6 meses"), FaixaEtaria.FILHOTE)
        self.assertEqual(deduzir_faixa_etaria("1.5 anos"), FaixaEtaria.JUVENIL)
        self.assertEqual(deduzir_faixa_etaria("3 anos"), FaixaEtaria.SUB_ADULTO)
        self.assertEqual(deduzir_faixa_etaria("6 anos"), FaixaEtaria.ADULTO)
        self.assertEqual(deduzir_faixa_etaria("12 anos"), FaixaEtaria.SENIL)
        self.assertEqual(deduzir_faixa_etaria("filhote"), FaixaEtaria.FILHOTE)
        self.assertEqual(deduzir_faixa_etaria("ninhego"), FaixaEtaria.NINHEGO)
        self.assertEqual(deduzir_faixa_etaria("potro"), FaixaEtaria.POTRO)
        self.assertEqual(deduzir_faixa_etaria("idoso"), FaixaEtaria.IDOSO)
        self.assertIsNone(deduzir_faixa_etaria(None))
        self.assertIsNone(deduzir_faixa_etaria(""))

    def test_normalizar_sexo(self):
        self.assertEqual(normalizar_sexo("M"), Sexo.MACHO)
        self.assertEqual(normalizar_sexo("macho"), Sexo.MACHO)
        self.assertEqual(normalizar_sexo("male"), Sexo.MACHO)
        self.assertEqual(normalizar_sexo("F"), Sexo.FEMEA)
        self.assertEqual(normalizar_sexo("femea"), Sexo.FEMEA)
        self.assertEqual(normalizar_sexo("fêmea"), Sexo.FEMEA)
        self.assertEqual(normalizar_sexo("female"), Sexo.FEMEA)
        self.assertEqual(normalizar_sexo("indeterminado"), Sexo.INDETERMINADO)
        self.assertEqual(normalizar_sexo("?"), Sexo.INDETERMINADO)
        self.assertEqual(normalizar_sexo("NI"), Sexo.NAO_INFORMADO)
        self.assertEqual(normalizar_sexo("-"), Sexo.NAO_INFORMADO)
        self.assertEqual(normalizar_sexo(None), Sexo.NAO_INFORMADO)

    def test_normalizar_status_vital(self):
        self.assertEqual(normalizar_status_vital("vivo"), StatusVital.VIVO)
        self.assertEqual(normalizar_status_vital("v"), StatusVital.VIVO)
        self.assertEqual(normalizar_status_vital("morto"), StatusVital.MORTO)
        self.assertEqual(normalizar_status_vital("óbito"), StatusVital.MORTO)
        self.assertEqual(normalizar_status_vital("obito"), StatusVital.MORTO)
        self.assertEqual(normalizar_status_vital("eutanasiado"), StatusVital.EUTANASIADO)
        self.assertEqual(normalizar_status_vital("eutanásia"), StatusVital.EUTANASIADO)
        self.assertEqual(normalizar_status_vital("NI"), StatusVital.NAO_INFORMADO)
        self.assertEqual(normalizar_status_vital(None), StatusVital.NAO_INFORMADO)

    def test_normalizar_material_biologico(self):
        self.assertEqual(normalizar_material_biologico("swab oral e cloacal"), MaterialBiologico.SWAB_ORAL_CLOACAL)
        self.assertEqual(normalizar_material_biologico("swab oral"), MaterialBiologico.SWAB_ORAL)
        self.assertEqual(normalizar_material_biologico("soro"), MaterialBiologico.SORO)
        self.assertEqual(normalizar_material_biologico("sangue total"), MaterialBiologico.SANGUE_TOTAL)
        self.assertEqual(normalizar_material_biologico("sangue (edta)"), MaterialBiologico.SANGUE_EDTA)
        self.assertEqual(normalizar_material_biologico("fígado"), MaterialBiologico.FIGADO)
        self.assertEqual(normalizar_material_biologico("figado"), MaterialBiologico.FIGADO)
        self.assertEqual(normalizar_material_biologico(""), MaterialBiologico.OUTRO)
        self.assertEqual(normalizar_material_biologico("outro"), MaterialBiologico.OUTRO)


    def test_normalizar_unidades(self):
        from src.utils.normalizacao import normalizar_unidade_peso, normalizar_unidade_idade
        from src.models.Animal.enums.UnidadePeso import UnidadePeso
        from src.models.Animal.enums.UnidadeIdade import UnidadeIdade

        self.assertEqual(normalizar_unidade_peso("kg"), UnidadePeso.KG)
        self.assertEqual(normalizar_unidade_peso("quilos"), UnidadePeso.KG)
        self.assertEqual(normalizar_unidade_peso("kilo"), UnidadePeso.KG)
        self.assertEqual(normalizar_unidade_peso("kilos"), UnidadePeso.KG)
        self.assertEqual(normalizar_unidade_peso("g"), UnidadePeso.G)
        self.assertEqual(normalizar_unidade_peso("gramas"), UnidadePeso.G)
        self.assertEqual(normalizar_unidade_peso("grama"), UnidadePeso.G)
        self.assertEqual(normalizar_unidade_peso("milig"), UnidadePeso.MG)
        self.assertEqual(normalizar_unidade_peso("miligramas"), UnidadePeso.MG)
        self.assertEqual(normalizar_unidade_peso("miligrama"), UnidadePeso.MG)
        self.assertEqual(normalizar_unidade_peso("mg"), UnidadePeso.MG)
        self.assertIsNone(normalizar_unidade_peso(None))

        self.assertEqual(normalizar_unidade_idade("anos"), UnidadeIdade.ANOS)
        self.assertEqual(normalizar_unidade_idade("ano"), UnidadeIdade.ANOS)
        self.assertEqual(normalizar_unidade_idade("meses"), UnidadeIdade.MESES)
        self.assertEqual(normalizar_unidade_idade("mês"), UnidadeIdade.MESES)
        self.assertEqual(normalizar_unidade_idade("semanas"), UnidadeIdade.SEMANAS)
        self.assertEqual(normalizar_unidade_idade("semana"), UnidadeIdade.SEMANAS)
        self.assertEqual(normalizar_unidade_idade("dias"), UnidadeIdade.DIAS)
        self.assertEqual(normalizar_unidade_idade("dia"), UnidadeIdade.DIAS)
        self.assertIsNone(normalizar_unidade_idade(None))

    def test_decompor_peso(self):
        from src.utils.normalizacao import decompor_peso
        from src.models.Animal.enums.UnidadePeso import UnidadePeso

        # Explícito com valor e unidade
        self.assertEqual(decompor_peso(peso_valor=15.0, peso_unidade=UnidadePeso.G), (0.015, 15.0, UnidadePeso.G))
        self.assertEqual(decompor_peso(peso_valor=2.5, peso_unidade=UnidadePeso.KG), (2.5, 2.5, UnidadePeso.KG))
        self.assertEqual(decompor_peso(peso_valor=500.0, peso_unidade=UnidadePeso.MG), (0.0005, 500.0, UnidadePeso.MG))

        # String com unidade
        self.assertEqual(decompor_peso(peso_bruto="400g"), (0.4, 400.0, UnidadePeso.G))
        self.assertEqual(decompor_peso(peso_bruto="1.5kg"), (1.5, 1.5, UnidadePeso.KG))
        self.assertEqual(decompor_peso(peso_bruto="500mg"), (0.0005, 500.0, UnidadePeso.MG))
        self.assertEqual(decompor_peso(peso_bruto="250 mg"), (0.00025, 250.0, UnidadePeso.MG))

        # Sentinela
        self.assertEqual(decompor_peso(peso_bruto="Não aferido"), ("Não aferido", None, None))
        self.assertEqual(decompor_peso(peso_bruto=None), ("Não aferido", None, None))

    def test_decompor_idade_e_deducao(self):
        from src.utils.normalizacao import decompor_idade, deduzir_faixa_etaria
        from src.models.Animal.enums.UnidadeIdade import UnidadeIdade
        from src.models.Animal.enums.FaixaEtaria import FaixaEtaria

        # Explícito valor e unidade
        self.assertEqual(decompor_idade(idade_valor=6, idade_unidade=UnidadeIdade.MESES), ("6 meses", 6.0, UnidadeIdade.MESES))
        self.assertEqual(decompor_idade(idade_valor=1, idade_unidade=UnidadeIdade.ANOS), ("1 ano", 1.0, UnidadeIdade.ANOS))
        self.assertEqual(decompor_idade(idade_valor=3, idade_unidade=UnidadeIdade.SEMANAS), ("3 semanas", 3.0, UnidadeIdade.SEMANAS))
        self.assertEqual(decompor_idade(idade_valor=10, idade_unidade=UnidadeIdade.DIAS), ("10 dias", 10.0, UnidadeIdade.DIAS))

        # String composta
        self.assertEqual(decompor_idade(idade_str="8 meses"), ("8 meses", 8.0, UnidadeIdade.MESES))
        self.assertEqual(decompor_idade(idade_str="3 anos"), ("3 anos", 3.0, UnidadeIdade.ANOS))

        # Dedução de faixa etária a partir de valor e unidade
        self.assertEqual(deduzir_faixa_etaria(idade_valor=6, idade_unidade=UnidadeIdade.MESES), FaixaEtaria.FILHOTE)
        self.assertEqual(deduzir_faixa_etaria(idade_valor=1.5, idade_unidade=UnidadeIdade.ANOS), FaixaEtaria.JUVENIL)
        self.assertEqual(deduzir_faixa_etaria(idade_valor=3, idade_unidade=UnidadeIdade.ANOS), FaixaEtaria.SUB_ADULTO)
        self.assertEqual(deduzir_faixa_etaria(idade_valor=6, idade_unidade=UnidadeIdade.ANOS), FaixaEtaria.ADULTO)
        self.assertEqual(deduzir_faixa_etaria(idade_valor=12, idade_unidade=UnidadeIdade.ANOS), FaixaEtaria.SENIL)

    def test_normalizar_data(self):
        from datetime import date
        from src.utils.normalizacao import normalizar_data

        # Objetos date
        self.assertEqual(normalizar_data(date(2022, 1, 28)), date(2022, 1, 28))
        # Formato ISO
        self.assertEqual(normalizar_data("2022-01-28"), date(2022, 1, 28))
        # Formato brasileiro com barra
        self.assertEqual(normalizar_data("28/01/2022"), date(2022, 1, 28))
        # Formato brasileiro com traço
        self.assertEqual(normalizar_data("28-01-2022"), date(2022, 1, 28))
        # Sentinelas com permitir_none=True
        self.assertIsNone(normalizar_data("NI"))
        self.assertIsNone(normalizar_data("-"))
        self.assertIsNone(normalizar_data(""))
        self.assertIsNone(normalizar_data("Não informado"))
        self.assertIsNone(normalizar_data(None))

        # Rejeição de inválidos
        with self.assertRaises(ValueError):
            normalizar_data("data_invalida")
        with self.assertRaises(ValueError):
            normalizar_data(None, permitir_none=False)

    def test_normalizar_coordenada(self):
        from src.utils.normalizacao import normalizar_coordenada

        # Decimal direto
        self.assertEqual(normalizar_coordenada(-5.089, eh_latitude=True), -5.089)
        self.assertEqual(normalizar_coordenada(-42.801, eh_latitude=False), -42.801)
        # String com vírgula
        self.assertEqual(normalizar_coordenada("-5,089", eh_latitude=True), -5.089)
        # DMS (graus sexagesimais)
        lat_dms = normalizar_coordenada("05°05'21\"S", eh_latitude=True)
        self.assertAlmostEqual(lat_dms, -5.089167, places=5)
        lon_dms = normalizar_coordenada("42°48'35\"W", eh_latitude=False)
        self.assertAlmostEqual(lon_dms, -42.809722, places=5)
        # Sentinelas -> None
        self.assertIsNone(normalizar_coordenada("-"))
        self.assertIsNone(normalizar_coordenada("NI"))
        self.assertIsNone(normalizar_coordenada(None))
        self.assertIsNone(normalizar_coordenada("Não informado"))

        # Fora dos limites
        with self.assertRaises(ValueError):
            normalizar_coordenada(95.0, eh_latitude=True)
        with self.assertRaises(ValueError):
            normalizar_coordenada(-190.0, eh_latitude=False)

    def test_decompor_localidade(self):
        from src.utils.normalizacao import decompor_localidade

        # Composto com barra "Municipio/UF"
        mun, uf, det, comp = decompor_localidade(local_origem="Teresina/PI")
        self.assertEqual(mun, "Teresina")
        self.assertEqual(uf, "PI")
        self.assertIsNone(det)
        self.assertEqual(comp, "Teresina/PI")

        # Composto com traço "Municipio - UF"
        mun, uf, det, comp = decompor_localidade(local_origem="Teresina - PI")
        self.assertEqual(mun, "Teresina")
        self.assertEqual(uf, "PI")

        # Com detalhe "Fazenda Santa Luzia, Teresina/PI"
        mun, uf, det, comp = decompor_localidade(local_origem="Fazenda Santa Luzia, Teresina/PI")
        self.assertEqual(mun, "Teresina")
        self.assertEqual(uf, "PI")
        self.assertEqual(det, "Fazenda Santa Luzia")
        self.assertEqual(comp, "Fazenda Santa Luzia, Teresina/PI")

        # Informados separadamente
        mun, uf, det, comp = decompor_localidade(municipio="Parnaíba", uf="PI", localidade_detalhe="Praia da Pedra do Sal")
        self.assertEqual(mun, "Parnaíba")
        self.assertEqual(uf, "PI")
        self.assertEqual(det, "Praia da Pedra do Sal")
        self.assertEqual(comp, "Praia da Pedra do Sal, Parnaíba/PI")

        # Apenas município
        mun, uf, det, comp = decompor_localidade(local_origem="Floriano")
        self.assertEqual(mun, "Floriano")
        self.assertIsNone(uf)
        self.assertEqual(comp, "Floriano")


    def test_normalizar_booleano(self):
        from src.utils.normalizacao import normalizar_booleano

        self.assertTrue(normalizar_booleano(True))
        self.assertTrue(normalizar_booleano("Sim"))
        self.assertTrue(normalizar_booleano("s"))
        self.assertTrue(normalizar_booleano("true"))
        self.assertTrue(normalizar_booleano("1"))
        self.assertTrue(normalizar_booleano(1))

        self.assertFalse(normalizar_booleano(False))
        self.assertFalse(normalizar_booleano("Não"))
        self.assertFalse(normalizar_booleano("nao"))
        self.assertFalse(normalizar_booleano("n"))
        self.assertFalse(normalizar_booleano("false"))
        self.assertFalse(normalizar_booleano("0"))
        self.assertFalse(normalizar_booleano(0))

        self.assertIsNone(normalizar_booleano(None))
        self.assertIsNone(normalizar_booleano(""))
        self.assertIsNone(normalizar_booleano("desconhecido"))

    def test_normalizar_enum(self):
        from src.utils.normalizacao import normalizar_enum
        from src.models.Amostra import CondicaoArmazenamento, StatusAmostra

        self.assertEqual(normalizar_enum(StatusAmostra, StatusAmostra.DISPONIVEL), StatusAmostra.DISPONIVEL)
        self.assertEqual(normalizar_enum(StatusAmostra, "Disponível"), StatusAmostra.DISPONIVEL)
        self.assertEqual(normalizar_enum(StatusAmostra, "disponivel"), StatusAmostra.DISPONIVEL)
        self.assertEqual(normalizar_enum(StatusAmostra, "DISPONIVEL"), StatusAmostra.DISPONIVEL)
        self.assertEqual(normalizar_enum(StatusAmostra, "NI", default=StatusAmostra.DISPONIVEL), StatusAmostra.DISPONIVEL)
        self.assertIsNone(normalizar_enum(CondicaoArmazenamento, None, default=None))

    def test_normalizar_reagente(self):
        from src.utils.normalizacao.reagente import normalizar_unidade_medida, normalizar_etapa_reagente
        from src.models.Reagente import UnidadeMedida, EtapaReagente

        self.assertEqual(normalizar_unidade_medida("ml"), UnidadeMedida.ML)
        self.assertEqual(normalizar_unidade_medida("Litro"), UnidadeMedida.L)
        self.assertEqual(normalizar_unidade_medida("mg"), UnidadeMedida.MG)
        self.assertEqual(normalizar_unidade_medida("frascos"), UnidadeMedida.UNIDADE)
        self.assertEqual(normalizar_unidade_medida(None), UnidadeMedida.ML)

        self.assertEqual(normalizar_etapa_reagente("extração"), EtapaReagente.EXTRAÇÃO)
        self.assertEqual(normalizar_etapa_reagente("qpcr"), EtapaReagente.PCR)
        self.assertEqual(normalizar_etapa_reagente("gel de agarose"), EtapaReagente.ELETRO)
        self.assertIsNone(normalizar_etapa_reagente(None))

    def test_reagente_quantidades_e_chaves(self):
        from src.utils.normalizacao.reagente import (
            normalizar_quantidade_unidade,
            normalizar_quantidade_volume,
            normalizar_chaves_reagente,
            normalizar_chaves_estoque,
            validar_lotes_unicos,
            calcular_vencimento,
            calcular_metricas_estoque,
        )
        from datetime import date, timedelta

        # Quantidade de unidades
        self.assertEqual(normalizar_quantidade_unidade("5"), 5)
        self.assertEqual(normalizar_quantidade_unidade(None), 1)
        with self.assertRaises(ValueError):
            normalizar_quantidade_unidade(0)

        # Quantidade de volume
        self.assertEqual(normalizar_quantidade_volume("10.5"), 10.5)
        self.assertIsNone(normalizar_quantidade_volume(None))
        self.assertIsNone(normalizar_quantidade_volume("NI"))
        with self.assertRaises(ValueError):
            normalizar_quantidade_volume("-2")

        # Normalização de chaves
        p_reag = normalizar_chaves_reagente({"codigo": "C123", "validade": "2026-12-31", "_id": 10})
        self.assertEqual(p_reag["reagente_codigo"], "C123")
        self.assertEqual(p_reag["data_validade"], "2026-12-31")
        self.assertEqual(p_reag["id"], 10)

        p_est = normalizar_chaves_estoque({"nome": "Taq Polimerase", "_id": 5})
        self.assertEqual(p_est["reagente_nome"], "Taq Polimerase")
        self.assertEqual(p_est["id"], 5)

        # Lotes únicos
        validar_lotes_unicos([{"numero_lote": "L1"}, {"numero_lote": "L2"}])
        with self.assertRaises(ValueError):
            validar_lotes_unicos([{"numero_lote": "L1"}, {"numero_lote": "l1"}])

        # Vencimento
        vencido, dias = calcular_vencimento(date.today() - timedelta(days=5))
        self.assertTrue(vencido)
        self.assertLess(dias, 0)

        # Métricas de estoque consolidadas
        lotes = [
            {"numero_lote": "L1", "quantidade_unidade": 2, "quantidade_volume": 500, "unidade_medida": "µl", "data_validade": date.today() + timedelta(days=30)},
            {"numero_lote": "L2", "quantidade_unidade": 1, "quantidade_volume": 1, "unidade_medida": "ml", "data_validade": date.today() + timedelta(days=60)},
        ]
        qtd_un, qtd_vol, totais_un, totais_base, resumo = calcular_metricas_estoque(lotes)
        self.assertEqual(qtd_un, 3)
        self.assertEqual(totais_base["ml"], 2.0)
        self.assertIn("ml", resumo)

    def test_import_direto_submodulos(self):
        from src.utils.normalizacao.comum import eh_nao_informado, normalizar_booleano
        from src.utils.normalizacao.local import normalizar_coordenada
        from src.utils.normalizacao.animal import normalizar_peso
        from src.utils.normalizacao.amostra_exame import normalizar_material_biologico
        from src.utils.normalizacao.reagente import normalizar_unidade_medida

        self.assertTrue(eh_nao_informado(None))
        self.assertTrue(normalizar_booleano("sim"))
        self.assertIsNotNone(normalizar_coordenada("-5.089"))
        self.assertEqual(normalizar_peso("1kg"), 1.0)
        self.assertIsNotNone(normalizar_material_biologico("soro"))
        self.assertIsNotNone(normalizar_unidade_medida("ml"))


if __name__ == "__main__":
    unittest.main()