import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.llm import provider
from app.llm.errors import LLMProviderError, error_kind_for_status


def settings(
    selected_provider: str = "kimi",
    max_output_tokens: int = 10000,
    max_requests_per_minute: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        llm_provider=selected_provider,
        kimi_api_key="kimi-key",
        kimi_base_url="https://api.moonshot.cn/v1",
        kimi_model="kimi-k2.6",
        deepseek_api_key="deepseek-key",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        llm_max_concurrency=3,
        llm_max_requests_per_minute=max_requests_per_minute,
        llm_max_retries=2,
        llm_max_output_tokens=max_output_tokens,
    )


class LlmProviderTest(unittest.TestCase):
    def test_status_uses_selected_provider(self) -> None:
        with patch.object(provider, "get_settings", return_value=settings("deepseek")):
            self.assertEqual(
                provider.get_llm_status(),
                {
                    "provider": "deepseek",
                    "configured": True,
                    "model": "deepseek-chat",
                    "baseUrl": "https://api.deepseek.com",
                    "apiKeyVariable": "DEEPSEEK_API_KEY",
                },
            )

    def test_invalid_provider_is_rejected(self) -> None:
        with patch.object(provider, "get_settings", return_value=settings("unknown")):
            with self.assertRaisesRegex(RuntimeError, "LLM_PROVIDER=unknown"):
                provider.get_llm_provider()

    def test_chat_completion_dispatches_to_kimi(self) -> None:
        kimi_call = AsyncMock(return_value={"content": "ok"})
        deepseek_call = AsyncMock(return_value={"content": "wrong"})
        with (
            patch.object(provider, "get_settings", return_value=settings("kimi")),
            patch.object(provider, "create_kimi_chat_completion", kimi_call),
            patch.object(provider, "create_deepseek_chat_completion", deepseek_call),
        ):
            result = asyncio.run(
                provider.create_chat_completion(
                    [{"role": "user", "content": "hello"}],
                    json_mode=True,
                )
            )

        self.assertEqual(result, {"content": "ok"})
        kimi_call.assert_awaited_once_with(
            [{"role": "user", "content": "hello"}],
            max_tokens=10000,
            json_mode=True,
        )
        deepseek_call.assert_not_awaited()

    def test_chat_completion_dispatches_to_deepseek(self) -> None:
        deepseek_call = AsyncMock(return_value={"content": "ok"})
        with (
            patch.object(provider, "get_settings", return_value=settings("deepseek")),
            patch.object(provider, "create_deepseek_chat_completion", deepseek_call),
        ):
            result = asyncio.run(
                provider.create_chat_completion([{"role": "user", "content": "hello"}])
            )

        self.assertEqual(result, {"content": "ok"})
        deepseek_call.assert_awaited_once_with(
            [{"role": "user", "content": "hello"}],
            temperature=0.4,
            max_tokens=10000,
            json_mode=False,
        )

    def test_output_token_limit_defaults_to_environment_setting(self) -> None:
        deepseek_call = AsyncMock(return_value={"content": "ok"})
        with (
            patch.object(provider, "get_settings", return_value=settings("deepseek", 2048)),
            patch.object(provider, "create_deepseek_chat_completion", deepseek_call),
        ):
            result = asyncio.run(provider.create_chat_completion([{"role": "user", "content": "hello"}]))

        self.assertEqual(result, {"content": "ok"})
        deepseek_call.assert_awaited_once_with(
            [{"role": "user", "content": "hello"}],
            temperature=0.4,
            max_tokens=2048,
            json_mode=False,
        )

    def test_concurrency_limit_applies_to_all_provider_calls(self) -> None:
        async def exercise() -> int:
            active = 0
            maximum = 0

            async def fake_call(*_args, **_kwargs):
                nonlocal active, maximum
                active += 1
                maximum = max(maximum, active)
                await asyncio.sleep(0.01)
                active -= 1
                return {"content": "ok"}

            with (
                patch.object(provider, "get_settings", return_value=settings("kimi")),
                patch.object(provider, "create_kimi_chat_completion", side_effect=fake_call),
            ):
                await asyncio.gather(*[
                    provider.create_chat_completion([{"role": "user", "content": "hello"}])
                    for _ in range(9)
                ])
            return maximum

        provider.reset_llm_runtime()
        self.assertEqual(asyncio.run(exercise()), 3)

    def test_transient_errors_retry_and_release_the_slot(self) -> None:
        stats = provider.LLMCallStats()
        call_results = [
            LLMProviderError("限流", kind="rate_limit", status_code=429),
            LLMProviderError("服务暂时不可用", kind="server", status_code=503),
            {"content": "ok"},
        ]
        call = AsyncMock(side_effect=call_results)
        sleep = AsyncMock()
        rate_limiter = Mock()
        rate_limiter.acquire = AsyncMock()

        async def exercise():
            with (
                patch.object(provider, "get_settings", return_value=settings("kimi")),
                patch.object(provider, "create_kimi_chat_completion", call),
                patch.object(provider, "_get_llm_rate_limiter", return_value=rate_limiter),
                patch.object(provider.asyncio, "sleep", sleep),
            ):
                return await provider.create_chat_completion(
                    [{"role": "user", "content": "hello"}],
                    stats=stats,
                )

        result = asyncio.run(exercise())

        self.assertEqual(result, {"content": "ok"})
        self.assertEqual(stats.request_attempts, 3)
        self.assertEqual(stats.retry_count, 2)
        self.assertEqual([item.args[0] for item in sleep.await_args_list], [2.0, 5.0])
        self.assertEqual(rate_limiter.acquire.await_count, 3)

    def test_retry_after_defers_the_shared_rate_limiter(self) -> None:
        call = AsyncMock(
            side_effect=[
                LLMProviderError(
                    "限流",
                    kind="rate_limit",
                    status_code=429,
                    retry_after_seconds=7,
                ),
                {"content": "ok"},
            ]
        )
        sleep = AsyncMock()
        rate_limiter = Mock()
        rate_limiter.acquire = AsyncMock()
        rate_limiter.defer = AsyncMock()

        async def exercise():
            with (
                patch.object(provider, "get_settings", return_value=settings("kimi")),
                patch.object(provider, "create_kimi_chat_completion", call),
                patch.object(provider, "_get_llm_rate_limiter", return_value=rate_limiter),
                patch.object(provider.asyncio, "sleep", sleep),
            ):
                return await provider.create_chat_completion(
                    [{"role": "user", "content": "hello"}]
                )

        self.assertEqual(asyncio.run(exercise()), {"content": "ok"})
        rate_limiter.defer.assert_awaited_once_with(7)
        self.assertEqual([item.args[0] for item in sleep.await_args_list], [7])

    def test_authentication_errors_are_not_retried(self) -> None:
        stats = provider.LLMCallStats()
        call = AsyncMock(side_effect=LLMProviderError("没有权限", kind="permission", status_code=403))

        async def exercise():
            with (
                patch.object(provider, "get_settings", return_value=settings("kimi")),
                patch.object(provider, "create_kimi_chat_completion", call),
            ):
                with self.assertRaises(LLMProviderError):
                    await provider.create_chat_completion(
                        [{"role": "user", "content": "hello"}],
                        stats=stats,
                    )

        asyncio.run(exercise())
        call.assert_awaited_once()
        self.assertEqual(stats.request_attempts, 1)
        self.assertEqual(stats.retry_count, 0)

    def test_http_timeout_is_retryable(self) -> None:
        self.assertEqual(error_kind_for_status(408), "timeout")


class RequestRateLimiterTest(unittest.IsolatedAsyncioTestCase):
    async def test_requests_are_smoothed_across_the_minute(self):
        current_time = [0.0]
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)
            current_time[0] += delay

        limiter = provider._RequestRateLimiter(
            2,
            clock=lambda: current_time[0],
            sleeper=fake_sleep,
        )

        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        self.assertEqual(delays, [30.0, 30.0])

    async def test_zero_disables_rate_limiting(self):
        sleep = AsyncMock()
        limiter = provider._RequestRateLimiter(0, sleeper=sleep)

        await limiter.acquire()
        await limiter.acquire()

        sleep.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
