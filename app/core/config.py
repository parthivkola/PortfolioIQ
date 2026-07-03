from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    database_url: str = (
        "postgresql+asyncpg://pip_user:pip_password@localhost:5433/portfolio_intelligence"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-to-a-random-64-char-string-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Market data
    market_data_provider: str = "yahoo"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Cache TTLs (seconds)
    cache_ttl_quote: int = 60
    cache_ttl_dashboard: int = 30
    cache_ttl_analytics: int = 300

    # Analytics
    tax_loss_materiality_threshold: float = 1000.0

    @property
    def async_database_url(self) -> str:
        """Normalize the DATABASE_URL for asyncpg.

        Render/Heroku provide postgres:// but SQLAlchemy asyncpg
        needs postgresql+asyncpg://.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
