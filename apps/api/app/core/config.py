from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration with safe defaults and environment validation."""

    app_name: str = "InsightFlow AI"
    app_env: Literal["development", "testing", "production"] = "development"
    app_debug: bool = False
    api_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://insightflow:insightflow@localhost:5432/insightflow"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security & Auth
    jwt_secret: str = "insightflow-insecure-dev-secret-key-replace-for-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # AI Provider Abstraction
    llm_provider: str = "gemini"
    llm_model: str = "gemini-1.5-pro"
    llm_api_key: str = ""
    llm_timeout_seconds: int = 45
    llm_max_tokens: int = 4000
    llm_temperature: float = 0.1

    # Object Storage & Uploads
    storage_backend: str = "local"
    data_dir: str = "./data/runtime"
    max_upload_size_mb: int = 50
    object_storage_endpoint: str | None = None
    object_storage_bucket: str = "insightflow"
    object_storage_access_key: str | None = None
    object_storage_secret_key: str | None = None

    # Logging & Observability
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "text"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("jwt_secret")
    @classmethod
    def validate_production_secret(cls, v: str, info) -> str:
        env = info.data.get("app_env", "development")
        if env == "production" and ("insecure" in v.lower() or "replace" in v.lower() or len(v) < 32):
            raise ValueError(
                "In production, JWT_SECRET must be at least 32 characters and cannot use default dev secret."
            )
        return v


settings = Settings()
