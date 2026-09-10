from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
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
    # 校内模型网关可能通过 course-ai.env 提供通用 AI_* 变量。
    # 保留项目专用的 DEEPSEEK_* 变量，生产环境两种配置方式都可用。
    ai_api_key: str | None = None
    ai_api_base: str | None = None
    ai_model: str | None = None
    # Model calls can contain long structured reports; keep the timeout explicit
    # and configurable rather than relying on the HTTP client's short default.
    llm_timeout_seconds: float = Field(default=600, gt=0)
    llm_max_concurrency: int = Field(default=3, ge=1)
    # 按请求启动时间平滑限制每分钟模型请求次数；0 表示关闭。
    llm_max_requests_per_minute: int = Field(default=8, ge=0)
    llm_max_retries: int = Field(default=2, ge=0)
    # Maximum number of output tokens requested from the selected provider.
    # This is not the provider model's total context-window size.
    llm_max_output_tokens: int = Field(default=10000, ge=1)
    frontend_origins: str = "http://localhost:5173"
    auth_secret: str = "change-this-secret-before-production"
    auth_token_hours: int = 72
    local_auth_enabled: bool = True
    portal_session_secret: str | None = None
    portal_session_cookie_name: str = "session"
    portal_session_max_age_seconds: int = 604800
    portal_login_url: str = "https://ai4edu.sjtu.edu.cn/auth/jaccount/login"
    portal_logout_url: str = "https://ai4edu.sjtu.edu.cn/auth/logout"
    public_app_url: str = "http://localhost:5173"
    app_base_path: str = "/"
    report_generation_daily_limit: int = 0
    report_generation_quota_timezone: str = "Asia/Shanghai"
    generation_job_lease_seconds: int = 300
    generation_job_heartbeat_seconds: int = 30
    generation_job_retention_days: int = 30
    assessment_draft_retention_days: int = 30
    admin_audit_retention_days: int = 180
    admin_username: str = "admin"
    admin_password: str = "admin12345"
    admin_display_name: str = "系统管理员"
    generation_worker_count: int = Field(default=3, ge=1)
    database_url: str = "postgresql://siyuan:siyuan_password@localhost:5432/siyuan_compass"

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def effective_deepseek_api_key(self) -> str | None:
        return self.deepseek_api_key or self.ai_api_key

    @property
    def effective_deepseek_base_url(self) -> str:
        return self.ai_api_base or self.deepseek_base_url

    @property
    def effective_deepseek_model(self) -> str:
        return self.ai_model or self.deepseek_model

    @property
    def jaccount_enabled(self) -> bool:
        return bool(self.portal_session_secret and self.portal_login_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
