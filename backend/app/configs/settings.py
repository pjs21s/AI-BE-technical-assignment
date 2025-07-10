from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    openai_timeout: float = 15.0          # 초
    openai_max_retries: int = 4
    openai_backoff_min: float = 0.5       # s
    openai_backoff_max: float = 4.0
    
    database_url: str = Field(..., env='DATABASE_URL')
    db_host: str = Field(..., env='DB_HOST')
    db_port: int = Field(..., env='DB_PORT')
    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_PASSWORD')
    postgres_db: str = Field(..., env='POSTGRES_DB')

    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: str = Field(..., env='REDIS_PORT')
    redis_db: str = Field(..., env='REDIS_DB')
    redis_password: str = Field(..., env='REDIS_PASSWORD')

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()