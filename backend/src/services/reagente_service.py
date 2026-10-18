from datetime import date
from typing import List, Dict, Optional
from collections import defaultdict
from src.models.Reagente import Reagente
from src.models.EstoqueReagente import EstoqueReagente

# Fatores para conversão dimensional para unidades base:
# Volume -> base 'ml'
# Massa -> base 'g'
FATORES_CONVERSAO = {
    # Volume (base: ml)
    "ml": ("volume", 1.0, "ml"),
    "l": ("volume", 1000.0, "ml"),
    "µl": ("volume", 0.001, "ml"),
    "ul": ("volume", 0.001, "ml"),
    # Massa (base: g)
    "g": ("massa", 1.0, "g"),
    "mg": ("massa", 0.001, "g"),
    "kg": ("massa", 1000.0, "g"),
}

class ReagenteService:
    """
    Serviço responsável pelas regras de negócio associadas aos Reagentes,
    como agrupamento por nome de reagente, consolidação de estoque com conversão
    dimensional e cálculo de indicadores de vencimento.
    """

    @staticmethod
    def validar_lotes_unicos(lotes: List[Reagente]) -> None:
        """Valida se não há números de lote duplicados para o mesmo reagente."""
        numeros_lotes = [lote.numero_lote for lote in lotes]
        if len(numeros_lotes) != len(set(numeros_lotes)):
            raise ValueError("Não pode haver números de lote repetidos para o mesmo reagente.")

    @staticmethod
    def calcular_vencimento(lote: Reagente) -> tuple[bool, int]:
        """
        Calcula os indicadores de vencimento para um lote de reagente:
        Retorna (esta_vencido: bool, dias_para_vencer: int).
        """
        hoje = date.today()
        esta_vencido = lote.data_validade < hoje
        dias_para_vencer = (lote.data_validade - hoje).days
        return esta_vencido, dias_para_vencer

    @classmethod
    def consolidar_estoque(cls, nome: str, codigo: Optional[str], lotes: List[Reagente]) -> EstoqueReagente:
        """
        Consolida uma lista de lotes em uma instância da entidade EstoqueReagente,
        calculando totais segregados, conversões dimensionais seguras e resumo textual.
        """
        cls.validar_lotes_unicos(lotes)

        qtd_unidades = sum(lote.quantidade_unidade for lote in lotes)
        totais_unidade: Dict[str, float] = {}
        totais_base: Dict[str, float] = {}

        for lote in lotes:
            # Enriquecimento com indicadores de vencimento
            vencido, dias = cls.calcular_vencimento(lote)
            lote.esta_vencido = vencido
            lote.dias_para_vencer = dias

            unidade_raw = (lote.unidade_medida or "ml").strip()
            qtd = lote.quantidade_volume if lote.quantidade_volume is not None else float(lote.quantidade_unidade)
            totais_unidade[unidade_raw] = round(totais_unidade.get(unidade_raw, 0.0) + qtd, 4)

            if lote.quantidade_volume is not None:
                unidade_lower = unidade_raw.lower()
                if unidade_lower in FATORES_CONVERSAO:
                    _, fator, base = FATORES_CONVERSAO[unidade_lower]
                    convertido = lote.quantidade_volume * fator
                    totais_base[base] = round(totais_base.get(base, 0.0) + convertido, 4)
                else:
                    totais_base[unidade_raw] = round(totais_base.get(unidade_raw, 0.0) + lote.quantidade_volume, 4)

        # Determina o volume consolidado principal
        if not totais_base:
            qtd_volume = float(sum((lote.quantidade_volume or 0.0) for lote in lotes))
        elif "ml" in totais_base:
            qtd_volume = totais_base["ml"]
        elif "g" in totais_base:
            qtd_volume = totais_base["g"]
        elif len(totais_base) == 1:
            qtd_volume = next(iter(totais_base.values()))
        else:
            qtd_volume = sum(totais_base.values())

        # Formata resumo legível
        partes_resumo = [f"{valor:g} {base}" for base, valor in totais_base.items()]
        resumo = ", ".join(partes_resumo) if partes_resumo else f"{qtd_unidades} un"

        return EstoqueReagente(
            nome=nome,
            codigo=codigo,
            lotes=lotes,
            quantidade_total_unidades=qtd_unidades,
            quantidade_total_volume=qtd_volume,
            totais_por_unidade=totais_unidade,
            totais_convertidos_base=totais_base,
            resumo_estoque=resumo,
        )

    @classmethod
    def agrupar_por_nome(cls, reagentes: List[Reagente]) -> Dict[str, EstoqueReagente]:
        """
        Recebe uma lista de instâncias de Reagente (lotes) e agrupa por nome.
        Retorna um dicionário mapeando o nome do reagente para EstoqueReagente consolidado.
        """
        grupos: Dict[str, List[Reagente]] = defaultdict(list)
        for r in reagentes:
            grupos[r.reagente_nome].append(r)

        estoque: Dict[str, EstoqueReagente] = {}
        for nome, lotes in grupos.items():
            codigo = lotes[0].reagente_codigo if lotes else None
            estoque[nome] = cls.consolidar_estoque(nome=nome, codigo=codigo, lotes=lotes)
        return estoque


reagente_service = ReagenteService()
