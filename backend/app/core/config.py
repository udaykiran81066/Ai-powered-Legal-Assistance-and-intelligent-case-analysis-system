from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Legal RAG"
    database_url: str = "sqlite:///./legal_rag.db"
    chroma_dir: str = "./chroma_db"
    anthropic_api_key: str = ""
    embedding_model: str = "BAAI/bge-base-en-v1.5"


settings = Settings()
