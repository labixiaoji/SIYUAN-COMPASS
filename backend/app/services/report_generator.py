from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from app.llm.deepseek import create_deepseek_chat_completion, is_deepseek_configured
from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintReport
from app.services.report_prompt import build_report_messages
from app.services.report_quality_check import check_report_quality, count_chineseish_words

REPORT_PROMPT_VERSION = "deepseek-v4.0.0"


class ReportGenerationError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


ProgressCallback = Callable[[str, int, str], None]


async def generate_report(
    response: AssessmentResponse,
    profile: CareerProfile,
    progress_callback: ProgressCallback | None = None,
) -> CareerBlueprintReport:
    if not is_deepseek_configured():
        raise ReportGenerationError("大模型未配置，请检查 DEEPSEEK_API_KEY。")

    now = now_iso()
    if progress_callback:
        progress_callback("report_generating", 65, "正在基于原始问卷和结构化画像生成六模块三路径报告。")
    try:
        result = await create_deepseek_chat_completion(
            build_report_messages(response, profile),
            max_tokens=10000,
        )
    except Exception as error:
        raise ReportGenerationError(f"大模型调用失败：{error}") from error

    if progress_callback:
        progress_callback("report_validating", 88, "报告已返回，正在检查六个模块、Plan A / Plan B / Plan C、困惑回应和安全提醒。")
    quality = check_report_quality(
        result["content"],
        expected_confusions=response.careerConfusions,
        main_confusion_text=response.mainConfusionText,
    )
    if quality["status"] == "failed":
        fatal_warnings = quality.get("fatalWarnings") or quality["warnings"]
        nonfatal_warnings = [item for item in quality["warnings"] if item not in fatal_warnings]
        warning_suffix = f"；普通警告：{'；'.join(nonfatal_warnings)}" if nonfatal_warnings else ""
        raise ReportGenerationError(f"大模型返回的报告未通过结构校验：{'；'.join(fatal_warnings)}{warning_suffix}")

    return CareerBlueprintReport(
        id=str(uuid4()),
        userId=response.userId,
        responseId=response.id,
        profileId=profile.id,
        title="我的生涯蓝图",
        content=result["content"],
        wordCount=count_chineseish_words(result["content"]),
        generationStatus="success",
        qualityStatus=quality["status"],
        errorMessage="；".join(quality["warnings"]) or None,
        modelName=result["modelName"],
        promptVersion=REPORT_PROMPT_VERSION,
        inputSnapshot={"response": response, "profile": profile},
        retryCount=0,
        createdAt=now,
        updatedAt=now,
    )
