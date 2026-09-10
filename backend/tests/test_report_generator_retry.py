import asyncio
import json
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from app.services.report_generator import ReportGenerationError, generate_report
from tests.test_structured_report_generation import make_draft_payload


def _response() -> SimpleNamespace:
    return SimpleNamespace(
        id="response-1",
        userId="user-1",
        careerConfusions=["不知道未来适合做什么"],
        mainConfusionText="我还没有找到能够验证方向的行动",
        studentName="张同学",
        studentNumber="520000000000",
        contactInfo="student@example.com",
    )


FAILED_QUALITY = {
    "status": "failed",
    "warnings": ["路径内容过少：Plan C"],
    "fatalWarnings": ["路径内容过少：Plan C"],
}
LENGTH_WARNING_QUALITY = {
    "status": "warning",
    "warnings": ["报告长度不足 3500 字符建议下限：3200"],
    "fatalWarnings": [],
}


class ReportGeneratorRetryTest(unittest.TestCase):
    def test_invalid_first_json_is_repaired_once(self) -> None:
        valid_json = json.dumps(make_draft_payload(), ensure_ascii=False)
        completion = AsyncMock(
            side_effect=[
                {"content": "first", "modelName": "test-model", "finishReason": "stop"},
                {"content": valid_json, "modelName": "test-model", "finishReason": "stop"},
            ]
        )
        with (
            patch("app.services.report_generator.is_llm_configured", return_value=True),
            patch(
                "app.services.report_generator.build_report_messages",
                side_effect=lambda response, profile, reason: [{"role": "user", "content": reason or "prompt"}],
            ) as build_messages,
            patch("app.services.report_generator.create_chat_completion", completion),
        ):
            report = asyncio.run(generate_report(_response(), SimpleNamespace(id="profile-1")))

        self.assertIn("### Plan A：连接技术与真实需求的产品方向（主攻路径）", report.content)
        self.assertEqual(report.retryCount, 1)
        self.assertEqual(report.qualityRuleVersion, "report-quality-v2.6.0")
        self.assertEqual(completion.await_count, 2)
        self.assertTrue(completion.await_args_list[1].kwargs["json_mode"])
        self.assertIn("JSON无法解析", build_messages.call_args_list[1].args[2])

    def test_nonfatal_quality_warning_does_not_regenerate_report(self) -> None:
        valid_json = json.dumps(make_draft_payload(), ensure_ascii=False)
        completion = AsyncMock(
            return_value={"content": valid_json, "modelName": "test-model", "finishReason": "stop"}
        )
        with (
            patch("app.services.report_generator.is_llm_configured", return_value=True),
            patch(
                "app.services.report_generator.build_report_messages",
                side_effect=lambda response, profile, reason: [{"role": "user", "content": reason or "prompt"}],
            ) as build_messages,
            patch("app.services.report_generator.create_chat_completion", completion),
            patch(
                "app.services.report_generator.check_report_quality",
                return_value=LENGTH_WARNING_QUALITY,
            ),
        ):
            report = asyncio.run(generate_report(_response(), SimpleNamespace(id="profile-1")))

        self.assertEqual(report.retryCount, 0)
        self.assertEqual(report.qualityStatus, "warning")
        self.assertEqual(completion.await_count, 1)
        self.assertEqual(build_messages.call_count, 1)

    def test_second_quality_failure_stops_without_saving_report(self) -> None:
        valid_json = json.dumps(make_draft_payload(), ensure_ascii=False)
        completion = AsyncMock(
            side_effect=[
                {"content": valid_json, "modelName": "test-model", "finishReason": "stop"},
                {"content": valid_json, "modelName": "test-model", "finishReason": "stop"},
            ]
        )
        with (
            patch("app.services.report_generator.is_llm_configured", return_value=True),
            patch("app.services.report_generator.build_report_messages", return_value=[]),
            patch("app.services.report_generator.create_chat_completion", completion),
            patch(
                "app.services.report_generator.check_report_quality",
                side_effect=[FAILED_QUALITY, FAILED_QUALITY],
            ),
        ):
            with self.assertRaisesRegex(ReportGenerationError, "已自动重试1次仍失败"):
                asyncio.run(generate_report(_response(), SimpleNamespace(id="profile-1")))

        self.assertEqual(completion.await_count, 2)


if __name__ == "__main__":
    unittest.main()
