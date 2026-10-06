"""
Issue 1 - Auditoria SOMENTE LEITURA do MongoDB (pibit_app).
Não imprime dados pessoais: mostra apenas nomes de campos, tipos e contagens.

Uso:
    export MONGO_URI="mongodb+srv://..."      # conta somente leitura, de preferência
    export MONGO_DB="pibit_app"               # ou pibit_app_dev (restauração do backup)
    python files/auditar_banco.py
Saída: console + files/relatorio_auditoria.json
"""
import os, sys, json
from datetime import datetime
from collections import Counter
from pymongo import MongoClient
import certifi

uri = os.environ.get("MONGO_URI")
nome_db = os.environ.get("MONGO_DB")

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
    sys.exit("Defina a variável de ambiente MONGO_URI.")

db = MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)[nome_db]

tipo = lambda v: type(v).__name__
vazio = lambda v: v is None or v == "" or v == []
rel = {}

# Campos obrigatórios segundo os formulários atuais (forms/*.py)
OBRIG = {
    "animais": ["classe", "nome_comum", "nome_cientifico", "sexo", "peso", "orgao",
                "status", "funcao", "local_origem", "faixa_etaria"],
    "amostras": ["animal_id", "local_coleta_amostra", "data_coleta_amostra", "nome_coletor",
                 "metodo_coleta", "condicao_amostra", "fase_amostra", "destino_amostra",
                 "kit_utilizado", "caixa", "sangue_disponivel", "dna_disponivel",
                 "rna_disponivel", "sequenciamento"],
    "exames": ["amostra_id", "tipo_exame", "teste_laboratorial", "laboratorio_realizador",
               "data_realizacao", "kit_utilizado", "resultado_detalhado",
               "responsavel_exame", "protocolo_exame"],
    "reagentes": ["nome", "codigo", "numero_lote", "marca", "data_validade",
                  "quantidade_unidade", "local_armazenamento"],
}

# 1) Coleções, contagens, índices, estrutura
print("== 1. COLEÇÕES ==")
rel["colecoes"] = {}
for nome in sorted(db.list_collection_names()):
    col = db[nome]
    n = col.count_documents({})
    idx = [{"name": i["name"], "key": list(i["key"].items()), "unique": i.get("unique", False)}
           for i in col.list_indexes()]
    campos = Counter()
    tipos_id = Counter()
    for d in col.find().limit(1000):
        tipos_id[tipo(d["_id"])] += 1
        for k, v in d.items():
            campos[f"{k}:{tipo(v)}"] += 1
    if nome == "usuarios":      # nunca expor nada além da estrutura
        campos = Counter({k: v for k, v in campos.items() if not k.startswith("password")})
    rel["colecoes"][nome] = {"total": n, "indices": idx, "tipos_de_id": dict(tipos_id),
                             "campos_vistos(amostra de até 1000)": dict(campos.most_common())}
    print(f"- {nome}: {n} docs | tipos de _id: {dict(tipos_id)}")
    for i in idx:
        print(f"    índice {i['name']} {i['key']} unique={i['unique']}")

animais = list(db["animais"].find({}, {"_id": 1}))
amostras = list(db["amostras"].find())
exames = list(db["exames"].find())
reagentes = list(db["reagentes"].find())
ids_animais = {a["_id"] for a in animais}
ids_amostras = {a["_id"] for a in amostras}
str_animais = {str(i) for i in ids_animais}
str_amostras = {str(i) for i in ids_amostras}

# 2) Vínculos quebrados
def vinculos(docs, campo, ids_exatos, ids_str):
    r = {"sem_campo": 0, "quebrado": 0, "so_bate_como_texto(tipo diferente)": 0, "ok": 0}
    exemplos = []
    for d in docs:
        v = d.get(campo)
        if vazio(v):
            r["sem_campo"] += 1; exemplos.append(str(d["_id"]))
        elif v in ids_exatos:
            r["ok"] += 1
        elif str(v) in ids_str:
            r["so_bate_como_texto(tipo diferente)"] += 1; exemplos.append(str(d["_id"]))
        else:
            r["quebrado"] += 1; exemplos.append(str(d["_id"]))
    r["ids_para_corrigir(max 20)"] = exemplos[:20]
    return r

print("\n== 2. VÍNCULOS ==")
rel["vinculos"] = {
    "amostras.animal_id -> animais._id": vinculos(amostras, "animal_id", ids_animais, str_animais),
    "exames.amostra_id -> amostras._id": vinculos(exames, "amostra_id", ids_amostras, str_amostras),
}
for k, v in rel["vinculos"].items():
    print(f"- {k}: " + ", ".join(f"{a}={b}" for a, b in v.items() if a != "ids_para_corrigir(max 20)"))

# 3) Campos obrigatórios realmente preenchidos
print("\n== 3. OBRIGATÓRIOS AUSENTES/VAZIOS ==")
rel["obrigatorios_ausentes"] = {}
for nome, docs in [("animais", list(db["animais"].find())), ("amostras", amostras),
                   ("exames", exames), ("reagentes", reagentes)]:
    falta = Counter()
    for d in docs:
        for c in OBRIG[nome]:
            if vazio(d.get(c)):
                falta[c] += 1
    rel["obrigatorios_ausentes"][nome] = dict(falta)
    print(f"- {nome} (de {len(docs)}): {dict(falta) or 'ok'}")

# 4) Divergências de nomes de campos observadas no código
print("\n== 4. DIVERGÊNCIAS DE CAMPOS ==")
def tem(docs, c): return sum(1 for d in docs if c in d and not vazio(d[c]))
animais_full = list(db["animais"].find())
rel["divergencias"] = {
    "animais: hvu (cadastro) vs id_hvu (busca)": {"hvu": tem(animais_full, "hvu"), "id_hvu": tem(animais_full, "id_hvu")},
    "reagentes: quantidade_unidade (cadastro) vs quantidade (lista/alertas)":
        {"quantidade_unidade": tem(reagentes, "quantidade_unidade"), "quantidade": tem(reagentes, "quantidade"),
         "so_quantidade_unidade (nunca aparecem nos alertas)": sum(1 for r in reagentes if "quantidade" not in r and "quantidade_unidade" in r)},
    "amostras: status (Editar_Amostra) vs status_amostra (Registros)": {"status": tem(amostras, "status"), "status_amostra": tem(amostras, "status_amostra")},
    "amostras: sangue_disponivel (cadastro) vs disponivel (Registros)": {"sangue_disponivel": tem(amostras, "sangue_disponivel"), "disponivel": tem(amostras, "disponivel")},
    "amostras: campo 'exames' embutido (Editar_Amostra)": tem(amostras, "exames"),
    "exames: com campo 'nome' (criados via Editar_Amostra) sem amostra_id":
        sum(1 for e in exames if "nome" in e and "amostra_id" not in e),
    "reagentes com _id ObjectId (ID deixado em branco)": sum(1 for r in reagentes if tipo(r["_id"]) == "ObjectId"),
    "exames com _id ObjectId (ID deixado em branco)": sum(1 for e in exames if tipo(e["_id"]) == "ObjectId"),
    "registros com campos 'unnamed*' (sujeiras de importação)": sum(
        sum(1 for d in db[c].find() if any(str(k).lower().startswith("unnamed") for k in d.keys()))
        for c in ["amostras", "animais", "exames", "reagentes"]
    ),
    "reagentes: tipos de data_validade": dict(Counter(tipo(r.get("data_validade")) for r in reagentes)),
    "animais: tipos de microchip": dict(Counter(tipo(a.get("microchip")) for a in animais_full if "microchip" in a and not vazio(a["microchip"]))),
    "animais: tipos de hvu": dict(Counter(tipo(a.get("hvu")) for a in animais_full if "hvu" in a and not vazio(a["hvu"]))),
    "animais: tipos de id_hvu": dict(Counter(tipo(a.get("id_hvu")) for a in animais_full if "id_hvu" in a and not vazio(a["id_hvu"]))),
    "animais: tipos de observacoes": dict(Counter(tipo(a.get("observacoes")) for a in animais_full if "observacoes" in a and not vazio(a["observacoes"]))),
}
for k, v in rel["divergencias"].items():
    print(f"- {k}: {v}")

# 5) Duplicidade em usuários (necessário antes de criar índice único)
us = db["usuarios"]
rel["usuarios"] = {
    "total": us.count_documents({}),
    "usernames_duplicados": [d["_id"] for d in us.aggregate([{"$group": {"_id": "$username", "n": {"$sum": 1}}}, {"$match": {"n": {"$gt": 1}}}])],
    "emails_duplicados": [d["_id"] for d in us.aggregate([{"$group": {"_id": "$email", "n": {"$sum": 1}}}, {"$match": {"n": {"$gt": 1}}}])],
}
print(f"\n== 5. USUÁRIOS == total={rel['usuarios']['total']} dup_username={len(rel['usuarios']['usernames_duplicados'])} dup_email={len(rel['usuarios']['emails_duplicados'])}")

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"resultados/relatorio_auditoria_{data_hora}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(rel, f, ensure_ascii=False, indent=2, default=str)
print(f"\nRelatório salvo em {out}  (contém IDs de registros: não versionar se forem sensíveis)")
