from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "http://127.0.0.1:8080"
    database_auth_token: str = ""
    environment: str = "development"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
