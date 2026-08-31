import json

import httpx

from app.core.config import get_settings
from app.llm.errors import LLMProviderError, provider_http_error


def is_kimi_configured() -> bool:
    return bool(get_settings().kimi_api_key)


async def create_kimi_chat_completion(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 10000,
    json_mode: bool = False,
) -> dict[str, str]:
    settings = get_settings()
    if not settings.kimi_api_key:
        raise LLMProviderError("缺少 KIMI_API_KEY，无法调用 Kimi。", kind="authentication")

    base_url = settings.kimi_base_url.rstrip("/")
    content_parts: list[str] = []
    finish_reason = ""
    model_name = settings.kimi_model
    reasoning_length = 0

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.kimi_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.kimi_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "stream": True,
                    "thinking": {"type": "disabled"},
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                },
            ) as response:
                retry_after = response.headers.get("Retry-After")
                try:
                    retry_after_seconds = float(retry_after) if retry_after else None
                except ValueError:
                    retry_after_seconds = None

                if response.status_code >= 400:
                    raw_error = await response.aread()
                    try:
                        error_data = json.loads(raw_error)
                    except (json.JSONDecodeError, TypeError):
                        error_data = None
                    message = error_data.get("error", {}).get("message") if isinstance(error_data, dict) else None
                    raise provider_http_error(
                        "Kimi",
                        response.status_code,
                        message,
                        retry_after_seconds=retry_after_seconds,
                    )

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    model_name = chunk.get("model") or model_name
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    reasoning_content = delta.get("reasoning_content") or ""
                    content_delta = delta.get("content") or ""
                    reasoning_length += len(reasoning_content)
                    if content_delta:
                        content_parts.append(content_delta)
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
    except LLMProviderError:
        raise
    except httpx.TimeoutException as error:
        raise LLMProviderError("Kimi API 请求超时。", kind="timeout") from error
    except httpx.RequestError as error:
        raise LLMProviderError("Kimi API 网络连接失败。", kind="network") from error

    content = "".join(content_parts).strip()
    if not content:
        detail = f"结束原因：{finish_reason or '未知'}，推理内容长度：{reasoning_length}"
        raise LLMProviderError(f"Kimi API 未返回报告正文（{detail}）。", kind="empty_response")

    return {
        "content": content,
        "modelName": model_name,
        "finishReason": finish_reason,
    }
