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

uri, nome_db = os.environ.get("MONGO_URI"), os.environ.get("MONGO_DB")
if not uri:
    try:
        secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("uri"):
                        uri = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.strip().startswith("db") and not nome_db:
                        nome_db = line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass

if not nome_db:
    nome_db = "pibit_app_dev"

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
    ("animais", [("id_hvu", ASCENDING)], {"sparse": True}),
    ("reagentes", [("data_validade", ASCENDING)], {}),
    ("usuarios", [("username", ASCENDING)], {"unique": True}),
    ("usuarios", [("email", ASCENDING)], {"unique": True}),
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
    # 1) reagentes: sincronizar quantidade <-> quantidade_unidade
    q1 = {"quantidade": {"$exists": False}, "quantidade_unidade": {"$exists": True}}
    q2 = {"quantidade_unidade": {"$exists": False}, "quantidade": {"$exists": True}}
    print(f"- reagentes sem 'quantidade': {db['reagentes'].count_documents(q1)}")
    print(f"- reagentes sem 'quantidade_unidade': {db['reagentes'].count_documents(q2)}")
    if a.aplicar:
        db["reagentes"].update_many(q1, [{"$set": {"quantidade": "$quantidade_unidade"}}])
        db["reagentes"].update_many(q2, [{"$set": {"quantidade_unidade": "$quantidade"}}])
    # 2) animais: migrar hvu legado para id_hvu e remover chave hvu legada em animais
    q1 = {"hvu": {"$exists": True}, "id_hvu": {"$exists": False}}
    q_legacy_hvu = {"hvu": {"$exists": True}}
    print(f"- animais com hvu legado sem id_hvu: {db['animais'].count_documents(q1)}")
    if a.aplicar:
        db["animais"].update_many(q1, [{"$set": {"id_hvu": "$hvu"}}])
        db["animais"].update_many(q_legacy_hvu, {"$unset": {"hvu": ""}})
    # 3) amostras: migrar status legado para status_amostra e remover chave status legada em amostras
    q1 = {"status": {"$exists": True}, "status_amostra": {"$exists": False}}
    q_legacy = {"status": {"$exists": True}}
    print(f"- amostras com status legado sem status_amostra: {db['amostras'].count_documents(q1)}")
    if a.aplicar:
        db["amostras"].update_many(q1, [{"$set": {"status_amostra": "$status"}}])
        db["amostras"].update_many(q_legacy, {"$unset": {"status": ""}})
    # 4) remoção de campos 'unnamed*' (sujeiras de importação de planilhas)
    for col_name in ["amostras", "animais", "exames", "reagentes"]:
        docs = list(db[col_name].find())
        unnamed_docs = [d for d in docs if any(str(k).lower().startswith("unnamed") for k in d.keys())]
        print(f"- {col_name} com campos 'unnamed': {len(unnamed_docs)}")
        if a.aplicar:
            for doc in unnamed_docs:
                bad_keys = {k: "" for k in doc.keys() if str(k).lower().startswith("unnamed")}
                db[col_name].update_one({"_id": doc["_id"]}, {"$unset": bad_keys})
    # 5) padronização de tipos (converter int/float/Int64 para str em campos identificadores e texto)
    campos_texto_map = {
        "animais": ["microchip", "id_hvu", "observacoes", "animal_id_projeto", "local_origem", "classe", "nome_comum", "nome_cientifico", "sexo", "status", "funcao", "orgao", "faixa_etaria", "idade", "suspeita_clinica"],
        "amostras": ["animal_id", "caixa", "observacoes", "metodo_coleta", "local_coleta_amostra", "nome_coletor", "condicao_amostra", "fase_amostra", "destino_amostra", "kit_utilizado", "amostra_id_projeto", "status_amostra"],
        "exames": ["amostra_id", "protocolo_exame", "observacoes", "observacoes_exame", "tipo_exame", "teste_laboratorial", "laboratorio_realizador", "resultado_detalhado", "responsavel_exame", "kit_utilizado"],
        "reagentes": ["codigo", "numero_lote", "observacoes", "marca", "local_armazenamento", "etapa", "nome"]
    }
    from collections import Counter
    for col_name, campos in campos_texto_map.items():
        docs = list(db[col_name].find())
        corrigidos = 0
        detalhes_campos = Counter()
        for doc in docs:
            sets = {}
            for c in campos:
                if c in doc and doc[c] is not None:
                    val = doc[c]
                    if not isinstance(val, str):
                        if isinstance(val, float) and val.is_integer():
                            sets[c] = str(int(val))
                        else:
                            sets[c] = str(val).strip()
                        detalhes_campos[c] += 1
                    elif val != val.strip():
                        sets[c] = val.strip()
                        detalhes_campos[c] += 1
            if sets:
                corrigidos += 1
                if a.aplicar:
                    db[col_name].update_one({"_id": doc["_id"]}, {"$set": sets})
        print(f"- {col_name} com tipos não-string/espaços em identificadores/texto: {corrigidos} docs {dict(detalhes_campos) or 'ok'}")
    print("(vínculos quebrados NÃO são corrigidos automaticamente: decidir caso a caso com o laboratório)")

# ---- Dados de exemplo ----
if a.seed:
    if not (nome_db.endswith("_dev") or nome_db.endswith("_test")):
        sys.exit("Recusado: --seed só roda em bancos terminados em _dev ou _test.")
    db["animais"].update_one({"_id": "TESTE-ANM001"}, {"$set": {"nome_comum": "Sagui", "nome_cientifico": "Callithrix jacchus", "classe": "Mamífero", "sexo": "Macho", "peso": 0.3, "orgao": "UFPI", "status": "Cativeiro", "funcao": "Outros", "local_origem": "Teresina", "faixa_etaria": "Adulto", "id_hvu": "H-1"}}, upsert=True)
    db["amostras"].update_one({"_id": "TESTE-AMS001"}, {"$set": {"animal_id": "TESTE-ANM001", "metodo_coleta": "Sangue", "data_coleta_amostra": "2026-01-10", "status_amostra": "Disponível"}}, upsert=True)
    db["exames"].update_one({"_id": "TESTE-EXM001"}, {"$set": {"amostra_id": "TESTE-AMS001", "tipo_exame": "RAIVA", "teste_laboratorial": "PCR", "resultado_detalhado": "Negativo"}}, upsert=True)
    db["amostras"].update_one({"_id": "TESTE-AMS002"}, {"$set": {"animal_id": "NAO-EXISTE", "metodo_coleta": "Fezes"}}, upsert=True)  # vínculo quebrado proposital
    db["reagentes"].update_one({"_id": "TESTE-REG001"}, {"$set": {"nome": "Kit teste", "quantidade": 1, "quantidade_unidade": 1, "data_validade": "2026-10-20", "local_armazenamento": "Freezer 1"}}, upsert=True)
    print("\nDados de exemplo TESTE-* criados (inclui 1 amostra com vínculo quebrado para testar a auditoria).")