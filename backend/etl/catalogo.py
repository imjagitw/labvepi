"""
Carga e Ingestão do Catálogo de Espécies (LABVEPI / UFPI)
Lê planilhas/tabelas CSV de referência taxonômica recomendadas pelo laboratório,
normaliza classes e nomes científicos e popula o acervo de espécies.

Uso:
    python -m etl.catalogo [caminho_csv]
"""

import argparse
import csv
from pathlib import Path
from typing import Optional, Union

from src.models.Especie import Especie, Classe
from src.repositories.especie_repository import EspecieRepository, especie_repository
from src.utils.normalizacao import normalizar_enum

MAPA_CLASSES = {
    "ave": Classe.AVES,
    "aves": Classe.AVES,
    "mamifero": Classe.MAMIFERO,
    "mamífero": Classe.MAMIFERO,
    "mamiferos": Classe.MAMIFERO,
    "mamíferos": Classe.MAMIFERO,
    "reptil": Classe.REPTIL,
    "réptil": Classe.REPTIL,
    "repteis": Classe.REPTIL,
    "répteis": Classe.REPTIL,
    "anfibio": Classe.ANFIBIO,
    "anfíbio": Classe.ANFIBIO,
    "anfibios": Classe.ANFIBIO,
    "anfíbios": Classe.ANFIBIO,
    "peixe": Classe.PEIXE,
    "peixes": Classe.PEIXE,
}


def normalizar_classe_taxonomica(val: Union[str, Classe]) -> Classe:
    """Converte variações textuais de classe taxonômica para o Enum canônico Classe."""
    if isinstance(val, Classe):
        return val
    if not val or not isinstance(val, str):
        raise ValueError(f"Classe inválida: '{val}'.")
    chave = val.strip().lower()
    if chave in MAPA_CLASSES:
        return MAPA_CLASSES[chave]
    canon = normalizar_enum(Classe, val)
    if isinstance(canon, Classe):
        return canon
    raise ValueError(f"Classe inválida: '{val}'. Classes aceitas: {[c.value for c in Classe]}")


def formatar_nome_cientifico(nome: str) -> str:
    """Aplica formatação taxonômica padrão (Gênero capitalizado, epíteto em minúsculo)."""
    if not nome or not nome.strip():
        raise ValueError("O nome científico é obrigatório e não pode ser vazio.")
    partes = nome.strip().split()
    if not partes:
        raise ValueError("O nome científico é inválido.")
    return " ".join([partes[0].capitalize()] + [p.lower() for p in partes[1:]])


def importar_catalogo_csv(
    caminho_arquivo: Union[str, Path],
    repo: Optional[EspecieRepository] = None,
    delimitador: Optional[str] = None,
    ignorar_duplicados: bool = True,
) -> int:
    """
    Importa um catálogo de espécies a partir de um arquivo CSV.
    Retorna o total de novas espécies inseridas.
    """
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {caminho}")

    repositorio = repo or especie_repository
    total_importados = 0

    with open(caminho, mode="r", encoding="utf-8") as f:
        primeira_linha = f.readline()
        f.seek(0)
        sep = delimitador or (";" if ";" in primeira_linha and "," not in primeira_linha else ",")

        reader = csv.DictReader(f, delimiter=sep)
        for linha in reader:
            linha_norm = {k.strip().lower(): v.strip() for k, v in linha.items() if k and v}
            nome_comum = (
                linha_norm.get("nome_comum")
                or linha_norm.get("nome")
                or linha_norm.get("nome comum")
            )
            nome_cient = (
                linha_norm.get("nome_cientifico")
                or linha_norm.get("nome científico")
                or linha_norm.get("especie")
                or linha_norm.get("espécie")
            )
            classe_str = (
                linha_norm.get("classe")
                or linha_norm.get("classe_taxonomica")
                or linha_norm.get("grupo")
            )

            if nome_comum and nome_cient and classe_str:
                nome_comum_limpo = str(nome_comum).strip()
                existente = repositorio.buscar_por_nome_comum(nome_comum_limpo)
                if existente:
                    if ignorar_duplicados:
                        continue
                    raise ValueError(f"Espécie '{nome_comum_limpo}' já cadastrada.")

                nova_esp = Especie(
                    nome_comum=nome_comum_limpo,
                    nome_cientifico=formatar_nome_cientifico(str(nome_cient)),
                    classe=normalizar_classe_taxonomica(classe_str),
                )
                repositorio.save(nova_esp)
                total_importados += 1

    return total_importados


def main():
    parser = argparse.ArgumentParser(description="ETL - Carga de Catálogo de Espécies (LABVEPI)")
    parser.add_argument(
        "arquivo",
        nargs="?",
        default="src/data/especies_catalogo.csv",
        help="Caminho do arquivo CSV de espécies",
    )
    args = parser.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists() and (Path("backend") / args.arquivo).exists():
        caminho = Path("backend") / args.arquivo

    print(f"📖 Carregando catálogo taxonômico de espécies: {caminho}")
    total = importar_catalogo_csv(caminho, ignorar_duplicados=True)
    print(f"✅ Carga concluída: {total} novas espécies adicionadas ao catálogo.")


if __name__ == "__main__":
    main()
