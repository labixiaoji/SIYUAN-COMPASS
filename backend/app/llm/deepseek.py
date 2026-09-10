import httpx

from app.core.config import get_settings
from app.llm.errors import LLMProviderError, provider_http_error


def is_deepseek_configured() -> bool:
    return bool(get_settings().effective_deepseek_api_key)


async def create_deepseek_chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 10000,
    json_mode: bool = False,
) -> dict[str, str]:
    settings = get_settings()
    if not settings.effective_deepseek_api_key:
        raise LLMProviderError(
            "缺少 AI_API_KEY 或 DEEPSEEK_API_KEY，无法调用校内 DeepSeek。",
            kind="authentication",
        )

    base_url = settings.effective_deepseek_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.effective_deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.effective_deepseek_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                    **({"response_format": {"type": "json_object"}} if json_mode else {}),
                },
            )
    except httpx.TimeoutException as error:
        raise LLMProviderError("DeepSeek API 请求超时。", kind="timeout") from error
    except httpx.RequestError as error:
        raise LLMProviderError("DeepSeek API 网络连接失败。", kind="network") from error

    retry_after = response.headers.get("Retry-After")
    try:
        retry_after_seconds = float(retry_after) if retry_after else None
    except ValueError:
        retry_after_seconds = None

    try:
        data = response.json()
    except ValueError as error:
        if response.status_code >= 400:
            raise provider_http_error(
                "DeepSeek",
                response.status_code,
                retry_after_seconds=retry_after_seconds,
            ) from error
        raise LLMProviderError(
            f"DeepSeek API 返回了无法解析的响应：{response.status_code}",
            kind="unknown",
            status_code=response.status_code,
        ) from error

    if response.status_code >= 400:
        message = data.get("error", {}).get("message") if isinstance(data, dict) else None
        raise provider_http_error(
            "DeepSeek",
            response.status_code,
            message,
            retry_after_seconds=retry_after_seconds,
        )

    choice = (data.get("choices") or [{}])[0]
    content = (choice.get("message") or {}).get("content", "").strip()
    if not content:
        raise LLMProviderError("DeepSeek API 未返回报告内容。", kind="empty_response")

    return {
        "content": content,
        "modelName": data.get("model") or settings.effective_deepseek_model,
        "finishReason": choice.get("finish_reason") or "",
    }
