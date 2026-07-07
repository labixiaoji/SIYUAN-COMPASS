from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 180
    frontend_origins: str = "http://localhost:5173"
    auth_secret: str = "change-this-secret-before-production"
    auth_token_hours: int = 72
    admin_username: str = "admin"
    admin_password: str = "admin12345"
    admin_display_name: str = "系统管理员"
    database_url: str = "postgresql://siyuan:siyuan_password@localhost:5432/siyuan_compass"

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
