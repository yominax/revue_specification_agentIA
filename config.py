"""Configuration de l'application."""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Configuration de l'application"""
    
    # API Keys
    openai_api_key: str = ""
    
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-large"
    
    # Configuration RAG
    chunk_size: int = 1000
    chunk_overlap: int = 200
    vector_store_type: Literal["chroma", "faiss"] = "chroma"
    
    # Configuration Agent
    temperature: float = 0.1
    max_tokens: int = 2000
    
    # Chemins
    base_dir: Path = Path(__file__).resolve().parent
    documents_path: Path = base_dir / "documents"
    vector_store_path: Path = base_dir / "vector_store"
    output_path: Path = base_dir / "reports"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

settings.documents_path.mkdir(exist_ok=True)
settings.vector_store_path.mkdir(exist_ok=True)
settings.output_path.mkdir(exist_ok=True)
