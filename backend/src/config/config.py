from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../streamlit/.streamlit/atlas.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    mongo_uri: str = Field(
        default="mongodb://localhost:27017/",
        validation_alias="MONGO_URI"
    )
    mongo_db: str = Field(
        default="pibit_app_dev",
        validation_alias="MONGO_DB"
    )
    ambiente: str = Field(
        default="dev",
        validation_alias="AMBIENTE"
    )

settings = Settings()