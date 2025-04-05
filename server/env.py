from typing import Optional
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_DEBUG: bool = False
    API_CORS_ALLOWED_ORIGINS: list = ["*"]
    LOG_LEVEL: str = "INFO"


class OpenAISettings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = "sk-.."


class GrokAISettings(BaseSettings):
    XAI_API_KEY: Optional[str] = "sk-..."


class DeepSeekSettings(BaseSettings):
    DEEPSEEK_API_KEY: Optional[str] = "sk-..."


class DatabaseSettings(BaseSettings):
    SQLALCHEMY_PGVECTOR_URI: str = "postgresql://postgres:thangcho@localhost:5431/test"

class FDCSettings(BaseSettings):
    USDA_API_KEY: Optional[str] = "00..."


class Settings(
    APISettings,
    DatabaseSettings,
    FDCSettings,
    OpenAISettings,
    GrokAISettings,
    DeepSeekSettings,
):
    model_config = {"extra": "allow"}


def get_settings() -> Settings:
    kwargs = {"_env_file": ".env"}
    return Settings(**kwargs)


env = get_settings()

__all__ = ["env"]
