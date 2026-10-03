"""
Issue 2 - Índices, rotina de correção e dados de exemplo.
Por padrão roda em MODO SIMULAÇÃO (não altera nada). Use --aplicar para gravar.

Uso:
    export MONGO_URI="..."  MONGO_DB="pibit_app_dev"
    python scripts/setup_banco.py                       # mostra o que faria
    python scripts/setup_banco.py --aplicar             # cria índices
    python scripts/setup_banco.py --aplicar --seed      # + dados de exemplo (só em *_dev / *_test)
    python scripts/setup_banco.py --aplicar --corrigir  # + correções de dados antigos
"""
import os, sys, argparse
from pymongo import MongoClient, ASCENDING
import certifi

p = argparse.ArgumentParser()
p.add_argument("--aplicar", action="store_true")
p.add_argument("--seed", action="store_true")
p.add_argument("--corrigir", action="store_true")
a = p.parse_args()

uri, nome_db = os.environ.get("MONGO_URI"), os.environ.get("MONGO_DB", "pibit_app_dev")
if not uri:
    sys.exit("Defina MONGO_URI.")
db = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)[nome_db]
print(f"Banco: {nome_db} | modo: {'APLICAR' if a.aplicar else 'SIMULAÇÃO'}")

# ---- Índices (create_index é idempotente) ----
INDICES = [
    ("amostras", [("animal_id", ASCENDING)], {}),
    ("exames", [("amostra_id", ASCENDING)], {}),
    ("animais", [("nome_comum", ASCENDING)], {}),
    ("animais", [("microchip", ASCENDING)], {"sparse": True}),
    ("animais", [("hvu", ASCENDING)], {"sparse": True}),
    ("reagentes", [("data_validade", ASCENDING)], {}),
    ("usuarios", [("username", ASCENDING)], {"unique": True}),
    ("usuarios", [("email", ASCENDING)], {}),
]
for col, chave, opt in INDICES:
    print(f"- índice {col} {chave} {opt}")
    if a.aplicar:
        try:
            db[col].create_index(chave, **opt)
        except Exception as e:
            print(f"  ! falhou: {e}  (se for 'unique', rode a auditoria e resolva duplicados)")

# ---- Correções de dados antigos (idempotentes) ----
if a.corrigir:
    print("\nCorreções:")
    # 1) reagentes: copiar quantidade_unidade -> quantidade quando faltar
    q = {"quantidade": {"$exists": False}, "quantidade_unidade": {"$exists": True}}
    print(f"- reagentes sem 'quantidade': {db['reagentes'].count_documents(q)}")
    if a.aplicar:
        db["reagentes"].update_many(q, [{"$set": {"quantidade": "$quantidade_unidade"}}])
    # 2) animais: id_hvu -> hvu
    q = {"id_hvu": {"$exists": True}, "hvu": {"$exists": False}}
    print(f"- animais com id_hvu sem hvu: {db['animais'].count_documents(q)}")
    if a.aplicar:
        db["animais"].update_many(q, [{"$set": {"hvu": "$id_hvu"}}])
    # 3) amostras: status -> status_amostra
    q = {"status": {"$exists": True}, "status_amostra": {"$exists": False}}
    print(f"- amostras com status sem status_amostra: {db['amostras'].count_documents(q)}")
    if a.aplicar:
        db["amostras"].update_many(q, [{"$set": {"status_amostra": "$status"}}])
    print("(vínculos quebrados NÃO são corrigidos automaticamente: decidir caso a caso com o laboratório)")

# ---- Dados de exemplo ----
if a.seed:
    if not (nome_db.endswith("_dev") or nome_db.endswith("_test")):
        sys.exit("Recusado: --seed só roda em bancos terminados em _dev ou _test.")
    db["animais"].update_one({"_id": "TESTE-ANM001"}, {"$set": {"nome_comum": "Sagui", "nome_cientifico": "Callithrix jacchus", "classe": "Mamífero", "sexo": "Macho", "peso": 0.3, "orgao": "UFPI", "status": "Cativeiro", "funcao": "Outros", "local_origem": "Teresina", "faixa_etaria": "Adulto", "hvu": "H-1"}}, upsert=True)
    db["amostras"].update_one({"_id": "TESTE-AMS001"}, {"$set": {"animal_id": "TESTE-ANM001", "metodo_coleta": "Sangue", "data_coleta_amostra": "2026-01-10", "status_amostra": "Disponível"}}, upsert=True)
    db["exames"].update_one({"_id": "TESTE-EXM001"}, {"$set": {"amostra_id": "TESTE-AMS001", "tipo_exame": "RAIVA", "teste_laboratorial": "PCR", "resultado_detalhado": "Negativo"}}, upsert=True)
    db["amostras"].update_one({"_id": "TESTE-AMS002"}, {"$set": {"animal_id": "NAO-EXISTE", "metodo_coleta": "Fezes"}}, upsert=True)  # vínculo quebrado proposital
    db["reagentes"].update_one({"_id": "TESTE-REG001"}, {"$set": {"nome": "Kit teste", "quantidade": 1, "quantidade_unidade": 1, "data_validade": "2026-10-20", "local_armazenamento": "Freezer 1"}}, upsert=True)
    print("\nDados de exemplo TESTE-* criados (inclui 1 amostra com vínculo quebrado para testar a auditoria).")