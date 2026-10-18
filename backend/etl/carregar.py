"""
Carregador Genérico de Dados ETL (LABVEPI / UFPI)
Lê lotes canônicos gerados em .jsonl, valida schemas com carga_legada=True,
assegura integridade referencial de vínculos e grava de forma idempotente (upsert)
exclusivamente contra o banco de dados 'pibit_app_dev'.

Uso:
    python -m etl.carregar etl/saida/morcegos               # Modo dry-run (padrão)
    python -m etl.carregar etl/saida/morcegos --dry-run     # Validação sem gravação
    python -m etl.carregar etl/saida/morcegos --aplicar     # Gravação efetiva no banco
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from src.models.Animal.animal import Animal
from src.models.Amostra.amostra import Amostra
from src.models.Exame.exame import Exame
from src.services.animal_service import animal_service
from src.services.amostra_service import amostra_service

# Banco de dados estritamente autorizado para cargas do ETL
BANCO_AUTORIZADO = "pibit_app_dev"

@dataclass
class RelatorioCarga:
    animais_lidos: int = 0
    animais_validos: int = 0
    amostras_lidas: int = 0
    amostras_validas: int = 0
    exames_lidos: int = 0
    exames_validos: int = 0
    erros_validacao: List[Dict[str, Any]] = field(default_factory=list)
    erros_vinculo: List[Dict[str, Any]] = field(default_factory=list)
    animais_gravados: int = 0
    amostras_gravadas: int = 0
    exames_gravados: int = 0
    modo: str = "dry-run"

def obter_mongo_uri(uri_cli: Optional[str] = None) -> str:
    """Recupera URI do MongoDB priorizando CLI, variáveis de ambiente e arquivos locais."""
    if uri_cli:
        return uri_cli
    if os.getenv("MONGO_URI"):
        return os.getenv("MONGO_URI")  # type: ignore[return-value]
    if os.getenv("MONGODB_URI"):
        return os.getenv("MONGODB_URI")  # type: ignore[return-value]

    candidatos = [
        Path("../streamlit/.streamlit/atlas.env"),
        Path("streamlit/.streamlit/atlas.env"),
        Path(".env"),
        Path("../.env"),
    ]
    for p in candidatos:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("export "):
                        line = line[7:].strip()
                    if line.startswith("MONGODB_URI=") or line.startswith("MONGO_URI="):
                        val = line.split("=", 1)[1].strip("\"' ")
                        if val:
                            return val
            except Exception:
                pass

    return "mongodb://localhost:27017/"

def ler_arquivo_jsonl(caminho: Path) -> List[Dict[str, Any]]:
    """Lê todas as linhas de um arquivo .jsonl."""
    if not caminho.exists():
        return []
    docs: List[Dict[str, Any]] = []
    with open(caminho, mode="r", encoding="utf-8") as f:
        for idx, linha in enumerate(f, start=1):
            linha_str = linha.strip()
            if not linha_str:
                continue
            try:
                doc = json.loads(linha_str)
                docs.append(doc)
            except json.JSONDecodeError as e:
                print(f"⚠️ Erro ao decodificar JSON na linha {idx} de {caminho}: {e}")
    return docs

def validar_documentos(
    animais: List[Dict[str, Any]],
    amostras: List[Dict[str, Any]],
    exames: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Valida cada documento contra os schemas de domínio e regras de carga_legada=True.
    Retorna (animais_validos, amostras_validas, exames_validos, erros_validacao).
    """
    erros: List[Dict[str, Any]] = []

    # 1. Animais
    animais_validos: List[Dict[str, Any]] = []
    for doc in animais:
        doc_id = doc.get("animal_id") or doc.get("_id")
        try:
            # Aplica regras legadas do service
            payload_copy = dict(doc)
            animal_service.aplicar_obrigatoriedade(payload_copy, carga_legada=True)
            # Validação pelo model Pydantic
            Animal(**payload_copy)
            animais_validos.append(payload_copy)
        except Exception as e:
            erros.append({
                "entidade": "Animal",
                "id": doc_id,
                "motivo": f"Falha de validação: {e}",
            })

    # 2. Amostras
    amostras_validas: List[Dict[str, Any]] = []
    for doc in amostras:
        doc_id = doc.get("amostra_id") or doc.get("_id")
        try:
            payload_copy = dict(doc)
            amostra_service.aplicar_obrigatoriedade(payload_copy, carga_legada=True)
            Amostra(**payload_copy)
            amostras_validas.append(payload_copy)
        except Exception as e:
            erros.append({
                "entidade": "Amostra",
                "id": doc_id,
                "motivo": f"Falha de validação: {e}",
            })

    # 3. Exames
    exames_validos: List[Dict[str, Any]] = []
    for doc in exames:
        doc_id = doc.get("exame_id") or doc.get("_id")
        try:
            payload_copy = dict(doc)
            Exame(**payload_copy)
            exames_validos.append(payload_copy)
        except Exception as e:
            erros.append({
                "entidade": "Exame",
                "id": doc_id,
                "motivo": f"Falha de validação: {e}",
            })

    return animais_validos, amostras_validas, exames_validos, erros

def verificar_integridade_vinculos(
    animais_validos: List[Dict[str, Any]],
    amostras_validas: List[Dict[str, Any]],
    exames_validos: List[Dict[str, Any]],
    db=None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Garante integridade referencial:
    - Amostra só é aprovada se seu animal_id existir no lote de animais válidos ou já no banco.
    - Exame só é aprovado se seu amostra_id existir no lote de amostras válidas ou já no banco.
    """
    erros_vinculo: List[Dict[str, Any]] = []

    # Conjunto de IDs de animais conhecidos
    animais_conhecidos: Set[str] = {
        a["animal_id"] for a in animais_validos if a.get("animal_id")
    }
    if db is not None:
        try:
            animais_no_banco = db.animais.distinct("animal_id")
            animais_conhecidos.update(str(x) for x in animais_no_banco if x)
        except Exception as e:
            print(f"⚠️ Aviso ao consultar animais existentes no banco: {e}")

    # Validação de vínculos de Amostras
    amostras_aprovadas: List[Dict[str, Any]] = []
    amostras_conhecidas: Set[str] = set()

    for am in amostras_validas:
        amostra_id = am.get("amostra_id", "DESCONHECIDA")
        animal_vinculado = am.get("animal_id")

        if not animal_vinculado or animal_vinculado not in animais_conhecidos:
            erros_vinculo.append({
                "entidade": "Amostra",
                "id": amostra_id,
                "vinculo_esperado": "Animal",
                "chave_ausente": animal_vinculado,
                "motivo": f"Animal '{animal_vinculado}' não existe no lote nem no banco de dados.",
            })
        else:
            amostras_aprovadas.append(am)
            amostras_conhecidas.add(amostra_id)

    if db is not None:
        try:
            amostras_no_banco = db.amostras.distinct("amostra_id")
            amostras_conhecidas.update(str(x) for x in amostras_no_banco if x)
        except Exception as e:
            print(f"⚠️ Aviso ao consultar amostras existentes no banco: {e}")

    # Validação de vínculos de Exames
    exames_aprovados: List[Dict[str, Any]] = []
    for ex in exames_validos:
        exame_id = ex.get("exame_id", "DESCONHECIDO")
        amostra_vinculada = ex.get("amostra_id")

        if not amostra_vinculada or amostra_vinculada not in amostras_conhecidas:
            erros_vinculo.append({
                "entidade": "Exame",
                "id": exame_id,
                "vinculo_esperado": "Amostra",
                "chave_ausente": amostra_vinculada,
                "motivo": f"Amostra '{amostra_vinculada}' não existe no lote nem no banco de dados.",
            })
        else:
            exames_aprovados.append(ex)

    return animais_validos, amostras_aprovadas, exames_aprovados, erros_vinculo

def serializar_para_mongo(obj: Any) -> Any:
    """Converte recursivamente objetos como date, datetime e Enum para formatos aceitos pelo MongoDB."""
    if isinstance(obj, dict):
        return {k: serializar_para_mongo(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serializar_para_mongo(v) for v in obj]
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    return obj

def persistir_lote_mongodb(
    animais: List[Dict[str, Any]],
    amostras: List[Dict[str, Any]],
    exames: List[Dict[str, Any]],
    db,
) -> Tuple[int, int, int]:
    """
    Grava os documentos no MongoDB usando upsert idempotente:
    update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    """
    cont_animais = 0
    for doc in animais:
        if "_id" not in doc:
            continue
        doc_mongo = serializar_para_mongo(doc)
        db.animais.update_one({"_id": doc_mongo["_id"]}, {"$set": doc_mongo}, upsert=True)
        cont_animais += 1

    cont_amostras = 0
    for doc in amostras:
        if "_id" not in doc:
            continue
        doc_mongo = serializar_para_mongo(doc)
        db.amostras.update_one({"_id": doc_mongo["_id"]}, {"$set": doc_mongo}, upsert=True)
        cont_amostras += 1

    cont_exames = 0
    for doc in exames:
        if "_id" not in doc:
            continue
        doc_mongo = serializar_para_mongo(doc)
        db.exames.update_one({"_id": doc_mongo["_id"]}, {"$set": doc_mongo}, upsert=True)
        cont_exames += 1

    return cont_animais, cont_amostras, cont_exames

def executar_carga(
    diretorio: Union[str, Path],
    aplicar: bool = False,
    mongo_uri: Optional[str] = None,
    banco: str = BANCO_AUTORIZADO,
) -> RelatorioCarga:
    """Executa o pipeline completo de validação e carga de um lote ETL."""
    # Validação de segurança estrita: o banco DEVE ser pibit_app_dev
    if banco != BANCO_AUTORIZADO:
        raise ValueError(
            f"Operação abortada por segurança. A gravação do ETL é permitida "
            f"exclusivamente contra o banco '{BANCO_AUTORIZADO}', mas foi solicitado '{banco}'."
        )

    p_dir = Path(diretorio)
    if not p_dir.exists():
        raise FileNotFoundError(f"Diretório de lote não encontrado: {p_dir}")

    relatorio = RelatorioCarga(modo="aplicar" if aplicar else "dry-run")

    # 1. Leitura dos .jsonl
    animais_raw = ler_arquivo_jsonl(p_dir / "animais.jsonl")
    amostras_raw = ler_arquivo_jsonl(p_dir / "amostras.jsonl")
    exames_raw = ler_arquivo_jsonl(p_dir / "exames.jsonl")

    relatorio.animais_lidos = len(animais_raw)
    relatorio.amostras_lidas = len(amostras_raw)
    relatorio.exames_lidos = len(exames_raw)

    # 2. Conexão ao MongoDB (necessária se aplicar=True ou para checar vínculos pré-existentes)
    db = None
    if aplicar:
        import pymongo
        uri = obter_mongo_uri(mongo_uri)
        cliente = pymongo.MongoClient(uri, serverSelectionTimeoutMS=8000)
        # Teste de conectividade
        cliente.admin.command("ping")
        db = cliente[BANCO_AUTORIZADO]

    # 3. Validação dos schemas com carga_legada=True
    a_val, am_val, ex_val, erros_val = validar_documentos(animais_raw, amostras_raw, exames_raw)
    relatorio.erros_validacao = erros_val

    # 4. Verificação de integridade referencial de vínculos
    a_ok, am_ok, ex_ok, erros_vin = verificar_integridade_vinculos(a_val, am_val, ex_val, db=db)
    relatorio.erros_vinculo = erros_vin

    relatorio.animais_validos = len(a_ok)
    relatorio.amostras_validas = len(am_ok)
    relatorio.exames_validos = len(ex_ok)

    # 5. Gravação se aplicar=True
    if aplicar and db is not None:
        g_a, g_am, g_ex = persistir_lote_mongodb(a_ok, am_ok, ex_ok, db)
        relatorio.animais_gravados = g_a
        relatorio.amostras_gravadas = g_am
        relatorio.exames_gravados = g_ex

    return relatorio

def main():
    parser = argparse.ArgumentParser(
        description="Carregador Genérico de ETL para o MongoDB (LABVEPI / UFPI)"
    )
    parser.add_argument(
        "diretorio",
        nargs="?",
        default="etl/saida/morcegos",
        help="Diretório onde estão os arquivos .jsonl (padrão: etl/saida/morcegos)",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Executa a gravação idempotente (upsert) no banco 'pibit_app_dev'. Se omitido, roda em modo dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa apenas a validação sem gravar dados no banco.",
    )
    parser.add_argument(
        "--mongo-uri",
        default=None,
        help="URI de conexão ao MongoDB (opcional, busca automaticamente nas configurações)",
    )
    parser.add_argument(
        "--db",
        default=BANCO_AUTORIZADO,
        help=f"Nome do banco de dados (restrito estritamente a '{BANCO_AUTORIZADO}')",
    )
    args = parser.parse_args()

    diretorio = Path(args.diretorio)
    if not diretorio.exists() and (Path("..") / args.diretorio).exists():
        diretorio = Path("..") / args.diretorio

    aplicar = bool(args.aplicar and not args.dry_run)
    modo_texto = "🔥 APLICAÇÃO EFETIVA (UPSERT)" if aplicar else "🛡️ DRY-RUN (APENAS VALIDAÇÃO)"

    print("=" * 65)
    print(f"📦 Carregador de ETL - LABVEPI: {modo_texto}")
    print(f"📁 Diretório de entrada: {diretorio}")
    print(f"🗄️  Banco alvo:          {BANCO_AUTORIZADO}")
    print("=" * 65)

    try:
        relatorio = executar_carga(
            diretorio=diretorio,
            aplicar=aplicar,
            mongo_uri=args.mongo_uri,
            banco=args.db,
        )

        print("\n📊 RESULTADO DA OPERAÇÃO:")
        print(f" • Animais:  {relatorio.animais_validos}/{relatorio.animais_lidos} válidos"
              f"{f' | {relatorio.animais_gravados} gravados no MongoDB' if aplicar else ''}")
        print(f" • Amostras: {relatorio.amostras_validas}/{relatorio.amostras_lidas} válidas"
              f"{f' | {relatorio.amostras_gravadas} gravadas no MongoDB' if aplicar else ''}")
        print(f" • Exames:   {relatorio.exames_validos}/{relatorio.exames_lidos} válidos"
              f"{f' | {relatorio.exames_gravados} gravados no MongoDB' if aplicar else ''}")

        total_erros = len(relatorio.erros_validacao) + len(relatorio.erros_vinculo)
        if total_erros > 0:
            print(f"\n⚠️  Total de inconsistências detectadas: {total_erros}")
            for err in relatorio.erros_validacao[:10]:
                print(f"   [Validação] {err['entidade']} ID={err['id']}: {err['motivo']}")
            for err in relatorio.erros_vinculo[:10]:
                print(f"   [Vínculo]   {err['entidade']} ID={err['id']}: {err['motivo']}")
            if total_erros > 20:
                print(f"   ... e mais {total_erros - 20} inconsistências omitidas.")
        else:
            print("\n✨ 100% dos documentos passaram nas validações de schema e integridade referencial!")

        if not aplicar:
            print("\n💡 Dica: Para persistir os dados no banco 'pibit_app_dev', execute com a flag '--aplicar':")
            print(f"   python -m etl.carregar {diretorio} --aplicar")

        print("=" * 65)

    except Exception as e:
        print(f"\n❌ Erro durante a execução da carga: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()