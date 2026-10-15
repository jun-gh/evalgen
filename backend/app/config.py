import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings with environment variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "EvalGen"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database: SQLite async by default for local dev; Neon Serverless Postgres for prod
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./.data/evalgen.db",
        description="Async database connection string",
    )

    # Google Gemini AI settings
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API Key for synthesis and evaluation",
    )
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://evalgen.pages.dev",
    ]

    # MCP servers configuration path
    MCP_SERVERS_CONFIG_PATH: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def normalized_database_url(self) -> str:
        """Converts postgres:// or postgresql:// to postgresql+asyncpg:// for async SQLAlchemy."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
