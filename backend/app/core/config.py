from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    llm_provider: str = "kimi"
    kimi_api_key: str | None = None
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "kimi-k2.6"
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 180
    speech_provider: str = "disabled"
    speech_xfyun_app_id: str | None = None
    speech_xfyun_api_key: str | None = None
    speech_xfyun_api_secret: str | None = None
    speech_xfyun_base_url: str = "https://office-api-ist-dx.iflyaisol.com"
    speech_xfyun_language: str = "autodialect"
    speech_xfyun_domain: str = "edu"
    speech_xfyun_poll_interval_seconds: float = 1.5
    speech_xfyun_poll_timeout_seconds: float = 120
    speech_timeout_seconds: float = 30
    speech_max_file_mb: int = 10
    speech_daily_limit: int = 20
    speech_quota_timezone: str = "Asia/Shanghai"
    frontend_origins: str = "http://localhost:5173"
    auth_secret: str = "change-this-secret-before-production"
    auth_token_hours: int = 72
    report_generation_daily_limit: int = 3
    report_generation_quota_timezone: str = "Asia/Shanghai"
    generation_job_lease_seconds: int = 300
    generation_job_heartbeat_seconds: int = 30
    generation_job_retention_days: int = 30
    admin_audit_retention_days: int = 180
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
