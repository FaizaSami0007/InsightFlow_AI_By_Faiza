import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_config() -> None:
    config = Settings(
        app_env="development",
        jwt_secret="development-secret-key-that-is-long-enough",
    )
    assert config.app_name == "InsightFlow AI"
    assert config.app_env == "development"
    assert config.api_prefix == "/api/v1"
    assert "http://localhost:3000" in config.cors_origins


def test_cors_string_parsing() -> None:
    config = Settings(
        cors_origins="https://app.insightflow.ai, https://admin.insightflow.ai",  # type: ignore
        jwt_secret="development-secret-key-that-is-long-enough",
    )
    assert len(config.cors_origins) == 2
    assert "https://app.insightflow.ai" in config.cors_origins
    assert "https://admin.insightflow.ai" in config.cors_origins


def test_production_rejects_insecure_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            jwt_secret="insightflow-insecure-dev-secret-key-replace-for-production",
        )


def test_production_accepts_secure_secret() -> None:
    secure_secret = "a" * 32
    config = Settings(
        app_env="production",
        jwt_secret=secure_secret,
    )
    assert config.app_env == "production"
    assert config.jwt_secret == secure_secret


def test_database_url_normalization_postgres() -> None:
    config = Settings(
        database_url="postgres://user:pass@host:5432/dbname?sslmode=require",
        jwt_secret="a" * 32,
    )
    assert config.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=require"


def test_database_url_normalization_postgresql() -> None:
    config = Settings(
        database_url="postgresql://user:pass@host:5432/dbname",
        jwt_secret="a" * 32,
    )
    assert config.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname"


def test_database_url_preserves_asyncpg() -> None:
    config = Settings(
        database_url="postgresql+asyncpg://user:pass@host:5432/dbname",
        jwt_secret="a" * 32,
    )
    assert config.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname"


def test_database_url_preserves_sqlite() -> None:
    config = Settings(
        database_url="sqlite+aiosqlite:///./test.db",
        jwt_secret="a" * 32,
    )
    assert config.database_url == "sqlite+aiosqlite:///./test.db"

