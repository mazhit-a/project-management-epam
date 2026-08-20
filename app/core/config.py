from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Project Management API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = []
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "app"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    S3_ENDPOINT_URL: str | None = None
    S3_PUBLIC_ENDPOINT_URL: str | None = None
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    S3_BUCKET: str = "documents"
    AWS_REGION: str = "us-east-1"

    @property
    def s3_public_endpoint_url(self) -> str | None:
        """Endpoint external clients can actually reach for presigned URLs.

        S3_ENDPOINT_URL is set to the container-internal address (e.g.
        http://ministack:4566) for the app's own calls to the storage backend.
        That hostname isn't resolvable outside the Docker network, so presigned
        URLs handed to real clients need a separate, publicly reachable address.
        """
        return self.S3_PUBLIC_ENDPOINT_URL or self.S3_ENDPOINT_URL

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _assemble_cors(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
