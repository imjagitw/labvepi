# backend/src/database/connection.py
from typing import Optional
import certifi
from pymongo import MongoClient
from pymongo.database import Database
from src.config import settings

class DatabaseManager:
    _client: Optional[MongoClient] = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            cls._client = MongoClient(
                settings.mongo_uri,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=8000
            )
            # Testa conectividade
            cls._client.admin.command("ping")
        return cls._client

    @classmethod
    def get_database(cls) -> Database:
        client = cls.get_client()
        return client[settings.mongo_db]

    @classmethod
    def close_connection(cls):
        if cls._client:
            cls._client.close()
            cls._client = None

def get_db() -> Database:
    """Injeção de dependência FastAPI ou chamada direta nos repositórios."""
    return DatabaseManager.get_database()