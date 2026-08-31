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

    # --- documents and consent (DPDP Act 2023) ---
    # Redacted document bytes only. Compose mounts a named volume here.
    STORAGE_DIR: str = "./var/uploads"
    # Salt for the government-ID hash. Rotating this deliberately breaks de-duplication
    # of existing rows, which is the correct behaviour: the old hashes are no longer
    # meaningful. Falls back to SECRET_KEY so a dev clone works without extra setup.
    ID_HASH_SALT: str = ""
    CONSENT_POLICY_VERSION: str = "2026-08-01"

    # --- notifications and reach ---
    # database | console | sms | whatsapp. The demo runs on `database`: the message is
    # stored and read on the citizen's tracking page, needing no contact address at all.
    NOTIFICATION_DRIVER: str = "database"
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    # Used to build the tracking link inside a message.
    PUBLIC_WEB_URL: str = "http://localhost:3000"

    # --- hardening ---
    # Requests per window, per client, per route group. Generous by design: the point is
    # to stop a runaway script, not to ration a citizen who taps twice on 2G.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_DEFAULT: int = 120
    # The conversational endpoint costs a model call, so it is metered harder.
    RATE_LIMIT_CONVERSATION: int = 30
    RATE_LIMIT_LOGIN: int = 10
    # JSON lines rather than prose, so logs are greppable in a container.
    LOG_JSON: bool = True

    # --- language model (optional) ---
    # The LLM never decides eligibility. It proposes facts before the rule engine and
    # restates its reasons afterwards, so the provider is swappable and "none" is a
    # fully supported configuration, not a degraded one.
    LLM_PROVIDER: str = "auto"  # auto | anthropic | xai | groq | none
    ANTHROPIC_API_KEY: str = ""
    # xAI (Grok models) and Groq (open models on custom hardware) are different
    # companies with near-identical names. Both are OpenAI wire-compatible.
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    # Leave blank to use the provider default in app/services/llm.py.
    LLM_MODEL: str = ""
    LLM_TIMEOUT_SECONDS: float = 20.0
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def id_hash_salt(self) -> str:
        """Never empty. An unsalted ID hash is a rainbow table waiting to happen."""
        return self.ID_HASH_SALT or self.SECRET_KEY


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
