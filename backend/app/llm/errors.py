from __future__ import annotations

from typing import Literal


LLMErrorKind = Literal[
    "authentication",
    "permission",
    "invalid_request",
    "rate_limit",
    "server",
    "timeout",
    "network",
    "empty_response",
    "unknown",
]


class LLMProviderError(RuntimeError):
    """Safe, classified provider error used by the shared retry layer."""

    def __init__(
        self,
        message: str,
        *,
        kind: LLMErrorKind = "unknown",
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds

    @property
    def retryable(self) -> bool:
        return self.kind in {"rate_limit", "server", "timeout", "network"}


def error_kind_for_status(status_code: int) -> LLMErrorKind:
    if status_code == 401:
        return "authentication"
    if status_code == 403:
        return "permission"
    if status_code == 408:
        return "timeout"
    if status_code == 429:
        return "rate_limit"
    if 400 <= status_code < 500:
        return "invalid_request"
    if status_code >= 500:
        return "server"
    return "unknown"


def provider_http_error(
    provider: str,
    status_code: int,
    message: str | None = None,
    *,
    retry_after_seconds: float | None = None,
) -> LLMProviderError:
    detail = (message or "").strip()
    if len(detail) > 400:
        detail = detail[:400]
    suffix = f"：{detail}" if detail else ""
    return LLMProviderError(
        f"{provider} API 请求失败（HTTP {status_code}）{suffix}",
        kind=error_kind_for_status(status_code),
        status_code=status_code,
        retry_after_seconds=retry_after_seconds,
    )
