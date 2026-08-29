from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "setu"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "postgresql+asyncpg://saarthi:saarthi@localhost:5432/saarthi"
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- language model (optional) ---
    # The LLM never decides eligibility. It proposes facts before the rule engine and
    # restates its reasons afterwards, so the provider is swappable and "none" is a
    # fully supported configuration, not a degraded one.
    LLM_PROVIDER: str = "auto"  # auto | anthropic | xai | none
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    # Leave blank to use the provider default in app/services/llm.py.
    LLM_MODEL: str = ""
    LLM_TIMEOUT_SECONDS: float = 20.0
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
