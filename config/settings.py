from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # Application Configuration
    app_name: str = "FastAPI Redis Vector Search"
    app_version: str = "1.0.0"
    debug: bool = True

    # Vector Search Configuration
    vector_dimension: int = 1024  # 匹配实际的嵌入向量维度
    distance_metric: str = "COSINE"
    max_results: int = 10
    force_recreate_index: bool = False  # 是否强制重新创建索引
    
    # Embedding Model Configuration
    embedding_provider: str = "sentence_transformers"  # Options: sentence_transformers, tei
    embedding_model_name: str = "bge-m3"
    
    # TEI Configuration
    tei_api_url: Optional[str] = None
    tei_api_key: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()