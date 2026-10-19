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
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Session & Quota limits
    MAX_DATASETS_PER_SESSION: int = 5
    SESSION_EXPIRY_DAYS: int = 7
    MAX_SAMPLE_COUNT: int = 10
    DEFAULT_SAMPLE_COUNT: int = 3

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
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # For PostgreSQL/Neon URLs, asyncpg only accepts specific connect kwargs.
        # libpq parameters (sslmode, channel_binding, target_session_attrs, etc.) crash asyncpg.connect().
        if "postgresql+asyncpg://" in url and "?" in url:
            from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

            parts = urlsplit(url)
            query_dict = dict(parse_qsl(parts.query))

            # Translate libpq sslmode to asyncpg ssl
            if "sslmode" in query_dict:
                query_dict["ssl"] = query_dict.pop("sslmode")

            # Whitelist only parameters supported by asyncpg.connect()
            allowed_asyncpg_params = {
                "ssl",
                "timeout",
                "command_timeout",
                "statement_cache_size",
                "server_settings",
            }
            clean_query = {k: v for k, v in query_dict.items() if k in allowed_asyncpg_params}
            url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(clean_query), parts.fragment))

        return url


settings = Settings()
