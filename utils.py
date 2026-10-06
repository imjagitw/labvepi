import streamlit as st
import certifi
import requests
import bcrypt
import regex as re
from pymongo import MongoClient
import bcrypt
import re
import requests

@st.cache_resource
def get_mongo_client():
    try:
        uri = st.secrets["mongo"]["uri"]
    except (KeyError, FileNotFoundError):
        raise RuntimeError(
            "MongoDB não configurado. "
            "Adicione [mongo].uri aos Secrets do Streamlit."
        )

    if not uri:
        raise RuntimeError(
            "O Secret [mongo].uri está vazio."
        )

    client = MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    return client

def connect_to_mongo():
    try:
        client = get_mongo_client()
        # Checa se existe uma flag de ambiente de desenvolvimento nos secrets
        is_dev = st.secrets.get("ambiente") == "dev"
        
        if is_dev:
            nome_db = "pibit_app_dev"
            st.sidebar.warning("⚠️ Rodando em ambiente de TESTE (DEV)")
        else:
            nome_db = "pibit_app" # Força produção se não for expressamente dev
        return client[nome_db]

    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        st.stop()

FIELDS_NUMERICOS = {'peso', 'quantidade', 'quantidade_unidade', 'quantidade_volume', 'latitude', 'longitude'}

def get_reagente_quantidade(doc: dict) -> float:
    """
    Retorna a quantidade de unidades do reagente priorizando 'quantidade_unidade'
    e utilizando 'quantidade' como fallback para dados legados.
    """
    if not isinstance(doc, dict):
        return 0.0
    val = doc.get('quantidade_unidade')
    if val is None:
        val = doc.get('quantidade', 0)
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

def normalize_document_types(doc: dict) -> dict:
    """
    Garante que todos os campos identificadores, códigos e textos
    sejam gravados estritamente como string no MongoDB, evitando
    inconsistências de tipo (ex: int vs Int64 vs str vs float).
    Campos explicitamente numéricos (peso, quantidade, etc.) são preservados.
    """
    if not isinstance(doc, dict):
        return doc

    normalized = {}
    for k, v in doc.items():
        if v is None:
            continue
        if k in FIELDS_NUMERICOS or isinstance(v, (bool, dict, list)):
            normalized[k] = v
        elif isinstance(v, float):
            normalized[k] = str(int(v)) if v.is_integer() else str(v)
        elif isinstance(v, int):
            normalized[k] = str(v)
        elif isinstance(v, str):
            normalized[k] = v.strip()
        else:
            normalized[k] = str(v).strip()
    return normalized

def add_document(collection_name, doc_data):
    db = connect_to_mongo()
    collection = db[collection_name]

    doc_data = normalize_document_types(doc_data)

    # Verifica se o _id já existe antes de inserir
    if "_id" in doc_data and collection.find_one({"_id": doc_data["_id"]}):
        return False, f"Erro: Já existe um registro com o ID '{doc_data['_id']}' na coleção '{collection_name}'."

    try:
        collection.insert_one(doc_data)
        return True, f"Registro com ID '{doc_data.get('_id', 'N/A')}' adicionado com sucesso na coleção '{collection_name}'!"
    except Exception as e:
        return False, f"Erro ao adicionar registro na coleção '{collection_name}': {e}"

db = connect_to_mongo()
users_collection = db["usuarios"]

def check_usr_pass(username: str, password: str) -> bool:
    user = users_collection.find_one({"username": username})
    if user:
        stored_hash = user['password'].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False

def load_lottieurl(url: str) -> str:
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def check_valid_name(name_sign_up: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z_][A-Za-z0-9_]*', name_sign_up))

def check_valid_email(email_sign_up: str) -> bool:
    regex = re.compile(r'([A-Za-z0-9]+[._-])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email_sign_up))

def check_unique_email(email_sign_up: str) -> bool:
    return users_collection.find_one({"email": email_sign_up}) is None

def non_empty_str_check(username_sign_up: str) -> bool:
    if not username_sign_up or username_sign_up.strip() == "":
        return False
    return True

def check_unique_usr(username_sign_up: str):
    if users_collection.find_one({"username": username_sign_up}):
        return False
    return non_empty_str_check(username_sign_up)

def register_new_usr(email_sign_up, username_sign_up, password_sign_up, matricula, created_at):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_sign_up.encode('utf-8'), salt)

    new_usr_data = {
        'username': username_sign_up,
        'email': email_sign_up,
        'password': hashed_password.decode('utf-8'),
        'matricula': matricula,
        'created_at': created_at
    }
    users_collection.insert_one(new_usr_data)

def check_username_exists(user_name: str) -> bool:
    return users_collection.find_one({"username": user_name}) is not None

def check_email_exists(email_forgot_passwd: str):
    user = users_collection.find_one({"email": email_forgot_passwd})
    if user:
        return True, user["username"]
    return False, None

def change_password(user_name: str, new_password: str):
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    result = users_collection.update_one(
        {"username": user_name},
        {"$set": {"password": hashed_password}}
    )
    return result.modified_count > 0