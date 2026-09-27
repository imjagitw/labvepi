import streamlit as st
import os
import requests
import bcrypt
import regex as re
from pymongo import MongoClient
import bcrypt
import re
import requests

def connect_to_mongo():
    uri = os.environ.get("MONGO_URI")

    if not uri:
        raise RuntimeError(
            "MONGO_URI não configurada. Configure a conexão com o MongoDB."
        )

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client["pibit_app"]

    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        st.stop()

def add_document(collection_name, doc_data):
    db = connect_to_mongo()
    collection = db[collection_name]

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