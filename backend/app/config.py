from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    database_url: str = Field(..., env='DATABASE_URL')
    db_host: str = Field(..., env='DB_HOST')
    db_port: int = Field(..., env='DB_PORT')
    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_PASSWORD')
    postgres_db: str = Field(..., env='POSTGRES_DB')

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8'
    }

settings = Settings()