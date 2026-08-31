from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.llm.deepseek import create_deepseek_chat_completion
from app.llm.errors import LLMProviderError
from app.llm.kimi import create_kimi_chat_completion

SUPPORTED_LLM_PROVIDERS = {"kimi", "deepseek"}


@dataclass
class LLMCallStats:
    """Counters for one durable generation task."""

    request_attempts: int = 0
    retry_count: int = 0
    quality_repair_count: int = 0
    last_attempt_kind: str | None = None


_LLM_SEMAPHORE: asyncio.Semaphore | None = None
_LLM_SEMAPHORE_LOOP: asyncio.AbstractEventLoop | None = None
_LLM_SEMAPHORE_LIMIT: int | None = None


def reset_llm_runtime() -> None:
    """Reset the process-local limiter (used by lifecycle tests)."""

    global _LLM_SEMAPHORE, _LLM_SEMAPHORE_LOOP, _LLM_SEMAPHORE_LIMIT
    _LLM_SEMAPHORE = None
    _LLM_SEMAPHORE_LOOP = None
    _LLM_SEMAPHORE_LIMIT = None


def _get_llm_semaphore() -> asyncio.Semaphore:
    global _LLM_SEMAPHORE, _LLM_SEMAPHORE_LOOP, _LLM_SEMAPHORE_LIMIT
    loop = asyncio.get_running_loop()
    limit = max(int(getattr(get_settings(), "llm_max_concurrency", 3)), 1)
    if (
        _LLM_SEMAPHORE is None
        or _LLM_SEMAPHORE_LOOP is not loop
        or _LLM_SEMAPHORE_LIMIT != limit
    ):
        _LLM_SEMAPHORE = asyncio.Semaphore(limit)
        _LLM_SEMAPHORE_LOOP = loop
        _LLM_SEMAPHORE_LIMIT = limit
    return _LLM_SEMAPHORE


def get_llm_provider() -> str:
    provider = get_settings().llm_provider.strip().lower()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        supported = "、".join(sorted(SUPPORTED_LLM_PROVIDERS))
        raise RuntimeError(f"LLM_PROVIDER={provider or '<empty>'} 不受支持，可选：{supported}。")
    return provider


def get_llm_status() -> dict[str, Any]:
    settings = get_settings()
    provider = get_llm_provider()
    if provider == "deepseek":
        return {
            "provider": provider,
            "configured": bool(settings.deepseek_api_key),
            "model": settings.deepseek_model,
            "baseUrl": settings.deepseek_base_url,
            "apiKeyVariable": "DEEPSEEK_API_KEY",
        }
    return {
        "provider": provider,
        "configured": bool(settings.kimi_api_key),
        "model": settings.kimi_model,
        "baseUrl": settings.kimi_base_url,
        "apiKeyVariable": "KIMI_API_KEY",
    }


def is_llm_configured() -> bool:
    return bool(get_llm_status()["configured"])


def get_llm_configuration_error() -> str:
    status = get_llm_status()
    return f"大模型未配置，请检查 {status['apiKeyVariable']}。"


async def create_chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 10000,
    json_mode: bool = False,
    stats: LLMCallStats | None = None,
) -> dict[str, Any]:
    """Call the selected provider under one process-wide limit and retry policy."""

    provider = get_llm_provider()
    settings = get_settings()
    max_retries = max(int(getattr(settings, "llm_max_retries", 2)), 0)

    for attempt in range(max_retries + 1):
        if stats is not None:
            stats.request_attempts += 1
            stats.last_attempt_kind = "model_request" if attempt == 0 else "network_retry"
        try:
            # The semaphore is held only while the provider request is active;
            # exponential/backoff sleep happens after release.
            async with _get_llm_semaphore():
                if provider == "deepseek":
                    return await create_deepseek_chat_completion(
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        json_mode=json_mode,
                    )
                return await create_kimi_chat_completion(
                    messages,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
        except LLMProviderError as error:
            normalized = error
        except httpx.TimeoutException as error:
            normalized = LLMProviderError("大模型请求超时。", kind="timeout")
            normalized.__cause__ = error
        except httpx.RequestError as error:
            normalized = LLMProviderError("大模型网络连接失败。", kind="network")
            normalized.__cause__ = error

        if not normalized.retryable or attempt >= max_retries:
            raise normalized
        if stats is not None:
            stats.retry_count += 1
            stats.last_attempt_kind = "network_retry"
        retry_after = normalized.retry_after_seconds
        delay = retry_after if retry_after is not None and retry_after > 0 else (2.0 if attempt == 0 else 5.0)
        await asyncio.sleep(delay)

    raise AssertionError("unreachable")
