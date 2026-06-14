import httpx

from app.core.config import get_settings


def is_deepseek_configured() -> bool:
    return bool(get_settings().deepseek_api_key)


async def create_deepseek_chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.4,
    max_tokens: int = 10000,
    json_mode: bool = False,
) -> dict[str, str]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，已跳过 DeepSeek 调用。")

    base_url = settings.deepseek_base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
                **({"response_format": {"type": "json_object"}} if json_mode else {}),
            },
        )
        data = response.json()

    if response.status_code >= 400:
        message = data.get("error", {}).get("message") if isinstance(data, dict) else None
        raise RuntimeError(message or f"DeepSeek API 请求失败：{response.status_code}")

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not content:
        raise RuntimeError("DeepSeek API 未返回报告内容。")

    finish_reason = data.get("choices", [{}])[0].get("finish_reason", "")
    return {
        "content": content,
        "modelName": settings.deepseek_model,
        "finishReason": finish_reason,
    }
