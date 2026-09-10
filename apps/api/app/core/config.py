from functools import lru_cache

from pydantic import field_validator
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

    @field_validator("DATABASE_URL")
    @classmethod
    def _use_asyncpg(cls, url: str) -> str:
        """Force the asyncpg driver onto whatever URL the platform handed us.

        Managed Postgres providers inject a plain libpq URL — Render's
        `fromDatabase: connectionString` gives `postgresql://…`, Heroku-descended ones
        still give the legacy `postgres://…`. Neither names a driver, so SQLAlchemy picks
        its default for the `postgresql` dialect, which is psycopg2. This image installs
        only `asyncpg`, so the first thing that touches the database dies with

            ModuleNotFoundError: No module named 'psycopg2'

        — during `alembic upgrade head` in the entrypoint, before the app ever starts.
        The whole application is async, so the driver is not a preference to be configured
        per environment; it is the only one that can work. Normalising here fixes every
        consumer at once: the app engine, Alembic online, and Alembic offline (which
        strips the suffix again to render plain SQL).

        `sslmode` is libpq's spelling; asyncpg calls the same thing `ssl`. SQLAlchemy hands
        query parameters to the driver as keyword arguments, so a URL carrying `sslmode`
        reaches `asyncpg.connect(sslmode=...)` and dies on an unexpected keyword.

        It is *renamed* rather than dropped. Every managed provider that appends it —
        Render's external URL, Neon, Supabase — also refuses connections without TLS, so
        deleting the parameter would trade an obvious error for a connection the server
        rejects. The value is carried across untouched: `require` stays `require`, and a
        deployment asking for `verify-full` keeps asking for it.
        """
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        if "sslmode=" in url:
            from urllib.parse import urlencode, urlsplit, urlunsplit

            parts = urlsplit(url)
            pairs = [
                (pair.split("=", 1) if "=" in pair else (pair, ""))
                for pair in parts.query.split("&")
                if pair
            ]
            # `ssl` wins if both are somehow present: it is the one the driver reads.
            has_ssl = any(k == "ssl" for k, _ in pairs)
            renamed = [
                ("ssl", v) if k == "sslmode" and not has_ssl else (k, v)
                for k, v in pairs
                if not (k == "sslmode" and has_ssl)
            ]
            url = urlunsplit(parts._replace(query=urlencode(renamed)))

        return url

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_origin_regex(self) -> str | None:
        """In development only, also admit the machine's own LAN address.

        This project's premise is a Rs 6,000 handset on a bad connection, and that
        cannot be checked from a laptop. Opening the app on a phone means the browser's
        origin is `http://192.168.1.9:3000`, which an exact allowlist rejects — so the
        one device the product is designed for was the one device it could not be tested
        on (OPEN_ITEMS OI-29).

        Scoped to RFC 1918 ranges and to development. In production `ALLOWED_ORIGINS`
        remains an exact list and this returns None, because a wildcard on a private
        range is still a wildcard to anything sharing that network.
        """
        if self.ENVIRONMENT != "development":
            return None
        return (
            r"http://(localhost|127\.0\.0\.1"
            r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            r"|192\.168\.\d{1,3}\.\d{1,3}"
            r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}):\d+"
        )

    @property
    def id_hash_salt(self) -> str:
        """Never empty. An unsalted ID hash is a rainbow table waiting to happen."""
        return self.ID_HASH_SALT or self.SECRET_KEY


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
