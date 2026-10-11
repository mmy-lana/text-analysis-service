from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "http://127.0.0.1:8080"
    database_auth_token: str = ""
    environment: str = "development"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
    ]
    # Cryptographic salt for HMAC-based key and session hashing. Required in
    # production; a development-only fallback is derived at import time.
    api_key_salt: str = ""

    # Rate limiting: authenticated keys (requests/minute) and anonymous
    # clients identified by salted IP hash (requests/hour).
    rate_limit_authenticated_per_minute: int = 60
    rate_limit_anonymous_per_hour: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def _development_salt() -> str:
    """Fixed development-only salt. Never used in production; stable across
    worker processes so multi-worker deployments hash identities consistently."""
    return "insecure-development-salt"


settings = Settings()

if not settings.api_key_salt:
    if settings.environment.lower() in {"production", "prod"}:
        raise RuntimeError(
            "API_KEY_SALT must be provided via environment variables when "
            "ENVIRONMENT=production. Refusing to start with an insecure salt."
        )
    settings.api_key_salt = _development_salt()
