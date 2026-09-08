from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from pydantic import ValidationError

from app.llm.provider import (
    LLMCallStats,
    create_chat_completion,
    get_llm_configuration_error,
    is_llm_configured,
)
from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintDraft, CareerBlueprintReport
from app.services.report_prompt import build_report_messages
from app.services.profile_prompt import redact_model_forbidden_values
from app.services.report_quality_check import (
    REPORT_QUALITY_VERSION,
    check_report_quality,
    count_chineseish_words,
)
from app.services.report_renderer import render_report_markdown

REPORT_PROMPT_VERSION = "career-blueprint-v2.5.0"


class ReportGenerationError(RuntimeError):
    pass


def _parse_report_json(content: str) -> CareerBlueprintDraft:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    if not cleaned.startswith("{"):
        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        if object_start >= 0 and object_end > object_start:
            cleaned = cleaned[object_start : object_end + 1]

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise ReportGenerationError(
            f"报告模型返回的JSON无法解析：{error.msg}（第{error.lineno}行，第{error.colno}列）"
        ) from error

    if not isinstance(payload, dict):
        raise ReportGenerationError("报告模型返回的JSON必须是对象。")

    try:
        return CareerBlueprintDraft.model_validate(payload)
    except ValidationError as error:
        details = []
        for item in error.errors()[:6]:
            location = ".".join(str(part) for part in item["loc"]) or "root"
            details.append(f"{location} {item['msg']}")
        remaining = len(error.errors()) - len(details)
        suffix = f"；另有{remaining}项错误" if remaining > 0 else ""
        raise ReportGenerationError(f"报告JSON字段校验失败：{'；'.join(details)}{suffix}") from error


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


ProgressCallback = Callable[[str, int, str], None]


async def generate_report(
    response: AssessmentResponse,
    profile: CareerProfile,
    progress_callback: ProgressCallback | None = None,
    llm_stats: LLMCallStats | None = None,
) -> CareerBlueprintReport:
    if not is_llm_configured():
        raise ReportGenerationError(get_llm_configuration_error())

    now = now_iso()
    result: dict[str, str] | None = None
    content: str | None = None
    quality = None
    retry_count = 0
    retry_reason: str | None = None
    for attempt in range(2):
        if attempt > 0 and llm_stats is not None:
            llm_stats.quality_repair_count += 1
        if progress_callback:
            if attempt == 0:
                progress_callback("report_generating", 65, "正在生成结构化六模块三路径报告草稿。")
            else:
                progress_callback("report_retrying", 82, "结构化报告未通过校验，正在定向修复字段。")
        try:
            call_kwargs: dict[str, Any] = {
                "temperature": 0.2,
                "json_mode": True,
            }
            if llm_stats is not None:
                call_kwargs["stats"] = llm_stats
            result = await create_chat_completion(
                build_report_messages(response, profile, retry_reason),
                **call_kwargs,
            )
            if attempt > 0 and llm_stats is not None:
                llm_stats.last_attempt_kind = "quality_repair"
        except Exception as error:
            raise ReportGenerationError(f"大模型调用失败：{error}") from error

        try:
            if result.get("finishReason") == "length":
                raise ReportGenerationError("模型输出因长度限制被截断")
            draft = _parse_report_json(
                redact_model_forbidden_values(result["content"], response)
            )
            content = render_report_markdown(draft)
            if progress_callback:
                progress_callback("report_validating", 88, "报告草稿已返回，正在校验字段、证据、路径、行动和隐私信息。")
            quality = check_report_quality(
                content,
                expected_confusions=response.careerConfusions,
                main_confusion_text=response.mainConfusionText,
                prohibited_personal_values=(
                    response.studentName,
                    response.studentNumber,
                    response.contactInfo,
                ),
                finish_reason=result.get("finishReason"),
            )
            repair_warnings = [
                warning
                for warning in quality["warnings"]
                if warning.startswith(
                    (
                        "报告长度不足",
                        "报告长度超过",
                        "出现模板化表达",
                        "学生可见文字反复使用生硬术语",
                        "人生画像",
                    )
                )
            ]
            if quality["status"] == "failed" or (attempt == 0 and repair_warnings):
                if quality["status"] == "failed":
                    reasons = quality.get("fatalWarnings") or quality["warnings"]
                else:
                    reasons = repair_warnings
                raise ReportGenerationError(f"报告内容质量校验失败：{'；'.join(reasons)}")
            retry_count = attempt
            break
        except ReportGenerationError as error:
            retry_reason = f"{error}；finish_reason={result.get('finishReason') or 'unknown'}"
            if attempt == 1:
                raise ReportGenerationError(f"{retry_reason}；已自动重试1次仍失败") from error

    if not result or not content or quality is None:
        raise ReportGenerationError("大模型未返回可用的结构化报告。")

    return CareerBlueprintReport(
        id=str(uuid4()),
        userId=response.userId,
        responseId=response.id,
        profileId=profile.id,
        title="我的生涯蓝图",
        content=content,
        wordCount=count_chineseish_words(content),
        generationStatus="success",
        qualityStatus=quality["status"],
        errorMessage="；".join(quality["warnings"]) or None,
        modelName=result["modelName"],
        promptVersion=REPORT_PROMPT_VERSION,
        qualityRuleVersion=REPORT_QUALITY_VERSION,
        inputSnapshot={"response": response, "profile": profile},
        retryCount=retry_count,
        createdAt=now,
        updatedAt=now,
    )
