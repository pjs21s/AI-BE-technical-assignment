from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    database_url: str = Field(..., env='DATABASE_URL')

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8'
    }

settings = Settings()