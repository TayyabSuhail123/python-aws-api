from pydantic_settings import BaseSettings , SettingsConfigDict      
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field("development", env="APP_ENV")
    log_level: str = Field("INFO",        env="LOG_LEVEL")
    agent_timeout: int = Field(5,         env="AGENT_TIMEOUT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )      
settings = Settings()
