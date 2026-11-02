from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "indexbeef"
    postgres_password: str = "indexbeef"
    postgres_db: str = "indexbeef"
    postgres_host: str = "db"
    postgres_port: int = 5432

    redis_host: str = "redis"
    redis_port: int = 6379

    minio_endpoint: str = "minio:9000"
    minio_root_user: str = "indexbeef"
    minio_root_password: str = "indexbeef-dev"
    minio_bucket: str = "indexbeef"

    api_log_level: str = "info"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
