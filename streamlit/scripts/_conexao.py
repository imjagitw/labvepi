"""
Resolução única de URI e nome do banco para os scripts (auditar_banco.py, setup_banco.py).

Ordem de precedência:
    1. Variáveis de ambiente MONGO_URI e MONGO_DB
    2. .streamlit/secrets.toml  ->  [mongo] uri = "...", db = "..."
    3. Banco padrão: pibit_app_dev  (NUNCA produção por omissão)

Requer Python 3.11+ (usa tomllib da biblioteca padrão).
"""
import os
import sys
from pathlib import Path

import certifi
from pymongo import MongoClient

PROD_DB = "pibit_app"
DEFAULT_DB = "pibit_app_dev"


def _ler_secrets() -> dict:
    caminho = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if not caminho.exists():
        return {}
    import tomllib  # Python 3.11+
    with open(caminho, "rb") as f:
        return tomllib.load(f).get("mongo", {})


def conectar():
    """Retorna (database, nome_do_banco)."""
    secrets = _ler_secrets()
    uri = os.environ.get("MONGO_URI") or secrets.get("uri")
    nome_db = os.environ.get("MONGO_DB") or secrets.get("db") or DEFAULT_DB
    if not uri:
        sys.exit("Defina MONGO_URI (variável de ambiente) ou [mongo].uri em .streamlit/secrets.toml.")
    client = MongoClient(uri, tls=True, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)
    return client[nome_db], nome_db
