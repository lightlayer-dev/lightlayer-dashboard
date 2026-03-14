"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LightLayer Dashboard"
    database_url: str = "postgresql+asyncpg://localhost:5432/lightlayer"
    secret_key: str = "change-me-in-production"
    api_key_prefix: str = "ll_"

    model_config = {"env_prefix": "LIGHTLAYER_"}


settings = Settings()
