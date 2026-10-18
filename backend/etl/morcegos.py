"""
Extrator ETL - Planilha dos Morcegos (LABVEPI / UFPI)
Processa a pasta de trabalho com 3 abas: Teresina, Parnaíba e Floriano.
Gera documentos canônicos para Animais, Amostras e Exames, com IDs estáveis e idempotentes.

Uso:
    python -m etl.morcegos [caminho_planilha]
"""

import argparse
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import openpyxl

from src.utils.normalizacao import (
    eh_nao_informado,
    normalizar_peso,
    normalizar_sexo,
    normalizar_status_vital,
    normalizar_material_biologico,
)
from src.models.Animal.enums.Sexo import Sexo
from src.models.Animal.enums.StatusVital import StatusVital
from src.models.Animal.enums.FaixaEtaria import FaixaEtaria
from src.models.Amostra.enums.MaterialBiologico import MaterialBiologico
from src.models.Amostra.enums.StatusAmostra import StatusAmostra
from src.models.Amostra.enums.FaseAmostra import FaseAmostra
from src.models.Amostra.enums.DestinoAmostra import DestinoAmostra
from src.models.Exame.enums.TipoExame import TipoExame
from src.models.Exame.enums.ResultadoExame import ResultadoExame
from src.models.Exame.enums.TesteLaboratorial import TesteLaboratorial
from etl.base import Resultado, id_estavel

# Resolução de taxonomia de morcegos para catálogo LABVEPI
MAPA_TAXONOMICO_MORCEGOS: Dict[str, Tuple[str, str]] = {
    "molossus": ("Molossus sp.", "Molossus sp."),
    "molossus sp.": ("Molossus sp.", "Molossus sp."),
    "molossus molosus": ("Morcego-insetívoro", "Molossus molossus"),
    "molossus molossus": ("Morcego-insetívoro", "Molossus molossus"),
    "molossídeo": ("Molossus sp.", "Molossus sp."),
    "molossideo": ("Molossus sp.", "Molossus sp."),
    "artibeus lineatus": ("Morcego-de-linha-branca", "Platyrrhinus lineatus"),
    "artibeus literatus": ("Morcego-fruteiro-grande", "Artibeus lituratus"),
    "artibeus lituratus": ("Morcego-fruteiro-grande", "Artibeus lituratus"),
    "artibeus sp.": ("Artibeus sp.", "Artibeus sp."),
    "artibeus": ("Artibeus sp.", "Artibeus sp."),
}

SIGLAS_MATERIAIS = {
    MaterialBiologico.SANGUE_TOTAL: "SGT",
    MaterialBiologico.SANGUE: "SG",
    MaterialBiologico.FEZES: "FEZ",
    MaterialBiologico.ENEMA: "ENE",
    MaterialBiologico.PAPEL_FILTRO: "PF",
    MaterialBiologico.ESFREGACO_SANGUINEO: "ESF",
    MaterialBiologico.PULMAO: "PUL",
    MaterialBiologico.CORACAO: "COR",
    MaterialBiologico.FIGADO: "FIG",
    MaterialBiologico.ENCEFALO: "ENC",
    MaterialBiologico.ECTOPARASITA: "ECT",
    MaterialBiologico.SWAB_ORAL: "SWO",
    MaterialBiologico.SWAB_RETAL: "SWR",
}

def eh_sim(valor: Any) -> bool:
    """Verifica se a célula indica realização/presença de coleta."""
    if not valor:
        return False
    v_clean = str(valor).strip().lower()
    return "sim" in v_clean or v_clean in {"+", "positivo", "coletado"}

def processar_linha_morcego(
    row_dict: Dict[str, Any],
    n_linha: int,
    sheet_name: str,
    data_coleta_padrao: Optional[str],
    res: Resultado,
) -> None:
    identificacao_raw = row_dict.get("identificação")
    if eh_nao_informado(identificacao_raw):
        return

    codigo_limpo = str(identificacao_raw).strip()
    # Identificadores:
    # animal_id é o código do laboratório (ex: "M01")
    # id / _id é o identificador inteiro autoincremental do banco
    animal_id = codigo_limpo
    id_animal = res.proximo_id_animal()

    # 1. Resolução Taxonômica
    especie_raw = row_dict.get("espécie")
    if eh_nao_informado(especie_raw):
        nome_comum = "Não informado"
        nome_cientifico = "Não informado"
        res.problema(linha=n_linha, coluna="Espécie", valor=especie_raw, motivo=f"Espécie não informada ({sheet_name})")
    else:
        esp_limpa = str(especie_raw).strip().lower()
        if esp_limpa in MAPA_TAXONOMICO_MORCEGOS:
            nome_comum, nome_cientifico = MAPA_TAXONOMICO_MORCEGOS[esp_limpa]
        else:
            nome_comum = str(especie_raw).strip()
            nome_cientifico = str(especie_raw).strip()
            res.problema(linha=n_linha, coluna="Espécie", valor=especie_raw, motivo="Espécie não mapeada no catálogo padrão")

    # 2. Biometria (Peso)
    peso_raw = row_dict.get("peso")
    peso = normalizar_peso(peso_raw)
    if peso == "Não aferido" and not eh_nao_informado(peso_raw):
        res.problema(linha=n_linha, coluna="Peso", valor=peso_raw, motivo="Formato de peso não interpretável")

    # 3. Sexo
    sexo_raw = row_dict.get("sexo")
    sexo = normalizar_sexo(sexo_raw)
    if sexo == Sexo.NAO_INFORMADO and not eh_nao_informado(sexo_raw):
        res.problema(linha=n_linha, coluna="Sexo", valor=sexo_raw, motivo=f"Sexo não reconhecido ({sexo_raw})")

    # 4. Observações e Status Vital
    obs_raw = row_dict.get("obs")
    obs = "" if obs_raw is None else str(obs_raw).strip()
    status_vital = StatusVital.VIVO
    if any(termo in obs.lower() for termo in ["óbito", "obito", "morto"]):
        status_vital = StatusVital.MORTO
    elif "eutanásia" in obs.lower() or "eutanasia" in obs.lower():
        status_vital = StatusVital.EUTANASIADO

    # Registro de Animal Canônico
    animal_doc = {
        "_id": id_animal,
        "animal_id": animal_id,
        "classe": "Mamífero",
        "nome_comum": nome_comum,
        "nome_cientifico": nome_cientifico,
        "sexo": sexo.value,
        "peso": peso,
        "faixa_etaria": FaixaEtaria.NAO_INFORMADO.value,
        "orgao_origem": "UFPI",
        "local_origem": f"{sheet_name}/PI",
        "regime_vida": "Vida livre",
        "status_vital": status_vital.value,
        "animal_id_projeto": f"Projeto Interface Urbano-Florestal ({sheet_name})",
        "animal_observacoes": obs or None,
        "origem_planilha": "Planilha dos morcegos (atualizada 2022)_outubro 2022.xlsx",
        "origem_aba": sheet_name,
        "origem_linha": n_linha,
    }
    res.animais.append(animal_doc)

    # 5. Amostras Biológicas Vinculadas
    amostras_animal: List[Tuple[MaterialBiologico, Optional[str]]] = []

    # Sangue
    sangue_val = row_dict.get("sangue")
    if eh_sim(sangue_val):
        str_val = str(sangue_val).lower()
        if "total" in str_val and "diluído" not in str_val:
            mat = MaterialBiologico.SANGUE_TOTAL
        elif "diluído" in str_val or "diluido" in str_val:
            mat = MaterialBiologico.SANGUE
        else:
            mat = MaterialBiologico.SANGUE
        amostras_animal.append((mat, str(sangue_val).strip()))

    # Fezes
    if eh_sim(row_dict.get("fezes")):
        amostras_animal.append((MaterialBiologico.FEZES, "Fezes coletadas"))

    # Enema
    if eh_sim(row_dict.get("enema")):
        amostras_animal.append((MaterialBiologico.ENEMA, "Enema retal"))

    # Papel filtro
    if eh_sim(row_dict.get("papel filtro")):
        amostras_animal.append((MaterialBiologico.PAPEL_FILTRO, "Amostra em papel filtro"))

    # Esfregaço
    if eh_sim(row_dict.get("esfregaço")):
        amostras_animal.append((MaterialBiologico.ESFREGACO_SANGUINEO, "Esfregaço sanguíneo em lâmina"))

    # Swab Oral (COVID O)
    if eh_sim(row_dict.get("covid o")):
        amostras_animal.append((MaterialBiologico.SWAB_ORAL, "Swab oral coletado para pesquisa viral"))

    # Swab Retal (COVID R)
    if eh_sim(row_dict.get("covid r")):
        amostras_animal.append((MaterialBiologico.SWAB_RETAL, "Swab retal coletado para pesquisa viral"))

    # Extração de órgãos e tecidos mencionados nas OBS
    obs_lower = obs.lower()
    if "pulmão" in obs_lower or "pulmao" in obs_lower:
        amostras_animal.append((MaterialBiologico.PULMAO, "Pulmão colhido em necropsia"))
    if "coração" in obs_lower or "coracao" in obs_lower:
        amostras_animal.append((MaterialBiologico.CORACAO, "Coração colhido em necropsia"))
    if "fígado" in obs_lower or "figado" in obs_lower:
        amostras_animal.append((MaterialBiologico.FIGADO, "Fígado colhido em necropsia"))
    if "cérebro" in obs_lower or "cerebro" in obs_lower or "encéfalo" in obs_lower or "encefalo" in obs_lower:
        amostras_animal.append((MaterialBiologico.ENCEFALO, "Encéfalo colhido em necropsia"))
    if "ectoparasita" in obs_lower or "ectoparasitas" in obs_lower:
        amostras_animal.append((MaterialBiologico.ECTOPARASITA, "Ectoparasitas coletados no animal"))

    amostra_principal_id = None
    for mat_bio, desc_obs in amostras_animal:
        sigla = SIGLAS_MATERIAIS.get(mat_bio, "OUT")
        id_amostra = res.proximo_id_amostra()
        amostra_id = f"{codigo_limpo}-{sigla}"

        amostra_doc = {
            "_id": id_amostra,
            "amostra_id": amostra_id,
            "animal_id": animal_id,
            "material_biologico": mat_bio.value,
            "status_amostra": StatusAmostra.DISPONIVEL.value,
            "data_coleta_amostra": data_coleta_padrao,
            "local_coleta_amostra": f"{sheet_name}/PI",
            "destino_amostra": DestinoAmostra.LAB_VIGILANCIA_EPIZOOTIAS_UFPI.value,
            "fase_amostra": FaseAmostra.EXTRACAO.value,
            "amostra_observacoes": desc_obs,
            "origem_planilha": "Planilha dos morcegos (atualizada 2022)_outubro 2022.xlsx",
            "origem_aba": sheet_name,
            "origem_linha": n_linha,
        }
        res.amostras.append(amostra_doc)
        if not amostra_principal_id:
            amostra_principal_id = amostra_id

    # 6. Exames / Patógenos Investigados
    ensaios = [
        ("herpes", TipoExame.HERPESVIRIDAE, TesteLaboratorial.PCR, "Herpesvírus", None),
        ("aimes", TipoExame.AIMES, TesteLaboratorial.PCR, "Painel AIMES", None),
        ("covid o", TipoExame.COVID_ORAL, TesteLaboratorial.PCR, "SARS-CoV-2 (Swab Oral)", MaterialBiologico.SWAB_ORAL),
        ("covid r", TipoExame.COVID_RETAL, TesteLaboratorial.PCR, "SARS-CoV-2 (Swab Retal)", MaterialBiologico.SWAB_RETAL),
    ]

    for col_key, tipo_exame, teste_lab, nome_ensaio, mat_especifico in ensaios:
        if eh_sim(row_dict.get(col_key)):
            if mat_especifico:
                sigla_mat = SIGLAS_MATERIAIS.get(mat_especifico, "OUT")
                ref_amostra_id = f"{codigo_limpo}-{sigla_mat}"
            else:
                ref_amostra_id = amostra_principal_id or f"{codigo_limpo}-SG"

            id_exame = res.proximo_id_exame()
            res.exames.append({
                "_id": id_exame,
                "amostra_id": ref_amostra_id,
                "exame_id": f"{codigo_limpo}-{col_key.replace(' ', '').upper()}",
                "tipo_exame": tipo_exame.value,
                "resultado": ResultadoExame.AGUARDANDO.value,
                "teste_laboratorial": teste_lab.value,
                "data_realizacao": data_coleta_padrao,
                "laboratorio_realizador": "Laboratório de Vigilância em Epizootias - UFPI",
                "exame_observacoes": f"Coletado/Triado para {nome_ensaio}",
                "origem_planilha": "Planilha dos morcegos (atualizada 2022)_outubro 2022.xlsx",
                "origem_aba": sheet_name,
                "origem_linha": n_linha,
            })

def extrair_morcegos(caminho_xlsx: Union[str, Path], diretorio_saida: Union[str, Path]) -> Dict[str, int]:
    """Lê todas as abas da planilha de morcegos e gera os artefatos canônicos do ETL."""
    caminho = Path(caminho_xlsx)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    wb = openpyxl.load_workbook(caminho, data_only=True)
    res = Resultado()

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        # Recupera data de referência do cabeçalho da aba (geralmente linha 4)
        data_referencia = None
        for r in range(1, 6):
            for cell in ws[r]:
                if isinstance(cell.value, (datetime, date)):
                    data_referencia = cell.value.strftime("%Y-%m-%d")
                    break
            if data_referencia:
                break
        if not data_referencia:
            data_referencia = "2022-01-01"

        # Linha 6 contém os cabeçalhos
        header_cells = [cell.value for cell in ws[6]]
        headers_normalizados = [
            str(h).strip().lower() if h is not None else f"col_{idx}"
            for idx, h in enumerate(header_cells)
        ]

        # Linhas de dados começam na linha 7
        for n_linha in range(7, ws.max_row + 1):
            row_cells = [cell.value for cell in ws[n_linha]]
            # Se a linha inteira estiver vazia, encerra
            if all(v is None for v in row_cells):
                continue

            row_dict = {
                headers_normalizados[idx]: val
                for idx, val in enumerate(row_cells)
                if idx < len(headers_normalizados)
            }

            processar_linha_morcego(
                row_dict=row_dict,
                n_linha=n_linha,
                sheet_name=sheet_name,
                data_coleta_padrao=data_referencia,
                res=res,
            )

    contagens = res.salvar(diretorio_saida)
    return contagens

def main():
    parser = argparse.ArgumentParser(description="ETL para Planilha de Morcegos (LABVEPI)")
    parser.add_argument(
        "planilha",
        nargs="?",
        default="../planilhas/Planilha dos morcegos (atualizada 2022)_outubro 2022.xlsx",
        help="Caminho do arquivo .xlsx de morcegos",
    )
    parser.add_argument(
        "--saida",
        default="etl/saida/morcegos",
        help="Diretório de saída para os arquivos .jsonl e problemas.csv",
    )
    args = parser.parse_args()

    caminho_planilha = Path(args.planilha)
    # Se o caminho relativo for executado a partir de backend/
    if not caminho_planilha.exists() and (Path("..") / args.planilha).exists():
        caminho_planilha = Path("..") / args.planilha

    print(f"🦇 Iniciando ETL da Planilha de Morcegos: {caminho_planilha}")
    contagens = extrair_morcegos(caminho_planilha, args.saida)
    print("=" * 60)
    print("✅ ETL Morcegos concluído com sucesso!")
    print(f" • Animais extraídos:  {contagens['animais']}")
    print(f" • Amostras geradas:   {contagens['amostras']}")
    print(f" • Exames mapeados:    {contagens['exames']}")
    print(f" • Problemas logados:  {contagens['problemas']} (ver {args.saida}/problemas.csv)")
    print(f"Arquivos gerados em: {args.saida}/")
    print("=" * 60)


if __name__ == "__main__":
    main()