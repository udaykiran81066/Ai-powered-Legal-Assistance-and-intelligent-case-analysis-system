from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Legal RAG"
    database_url: str = "sqlite:///./legal_rag.db"
    chroma_dir: str = "./chroma_db"
    anthropic_api_key: str = ""
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    llm_model: str = "claude-sonnet-5-5"
    top_k: int = 5
    # Max cosine similarity below which the answer is flagged low-confidence. NOT yet
    # tuned for bge-base: calibrate on scripts/eval_retrieval.py scores before trusting.
    similarity_threshold: float = 0.5


settings = Settings()
