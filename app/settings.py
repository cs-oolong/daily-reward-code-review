from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    ANALYTICS_URL: str = "http://localhost:8081/events"


settings = Settings()
