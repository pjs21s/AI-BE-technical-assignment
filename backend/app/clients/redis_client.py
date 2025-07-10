from redis import Redis
from pydantic_settings import BaseSettings, SettingsConfigDict

class RedisSettings(BaseSettings):
    host: str = "redis"
    port: int = 6379
    db:   int = 0
    password: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",        # REDIS_HOST / REDIS_PORT / …
        env_file=".env",
        extra="ignore",             # ← 다른 환경변수들은 무시
    )

    @property
    def url(self) -> str:
        cred = f":{self.password}@" if self.password else ""
        return f"redis://{cred}{self.host}:{self.port}/{self.db}"

redis_settings = RedisSettings()
rds: Redis = Redis.from_url(redis_settings.url, decode_responses=False)
