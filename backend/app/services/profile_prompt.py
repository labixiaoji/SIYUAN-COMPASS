from __future__ import annotations

import json

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import ProfileAnalysisResult
from app.core.data_privacy import redact_obvious_contact_details
from app.services.question_rules import render_question_rules

PROFILE_PROMPT_VERSION = "profile-analysis-v1.8.0"

# These values are either direct identifiers, internal linkage metadata, or
# questionnaire fields that are not needed to produce career guidance.  Keep
# the exclusion in one place so both LLM stages use the same data boundary.
DIRECT_IDENTIFIER_FIELDS = frozenset(
    {
        "studentName",
        "school",
        "studentNumber",
        "contactInfo",
    }
)
INTERNAL_METADATA_FIELDS = frozenset(
    {
        "id",
        "userId",
        "submittedAt",
        "createdAt",
    }
)
MODEL_UNUSED_RESPONSE_FIELDS = frozenset(
    {
        "fiveYearIncome",
        "tenYearIncome",
        "educationCertainty",
        "englishCertificates",
        "academicExperiences",
        "executionCase",
        "negativeFeedbackReaction",
    }
)
MODEL_EXCLUDED_RESPONSE_FIELDS = (
    DIRECT_IDENTIFIER_FIELDS | INTERNAL_METADATA_FIELDS | MODEL_UNUSED_RESPONSE_FIELDS
)


def build_model_safe_response_payload(response: AssessmentResponse) -> dict[str, object]:
    """Return only questionnaire fields approved for external model input."""

    response_payload = response.model_dump(
        mode="json",
        exclude=MODEL_EXCLUDED_RESPONSE_FIELDS,
    )
    if response.doctoralCareerDirection != "其他发展方向":
        response_payload.pop("doctoralCareerOther", None)
    if "其他" not in response.educationPathReasons:
        response_payload.pop("educationPathReasonOther", None)
    if "其他" not in response.currentPreparations:
        response_payload.pop("currentPreparationOther", None)
    if "其他" not in response.jobInfoChannels:
        response_payload.pop("jobInfoChannelOther", None)
    if "其他" not in response.careerConfusions:
        response_payload.pop("careerConfusionOther", None)
    return response_payload


def _has_model_value(value: object) -> bool:
    """Return whether a value carries information worth sending to the model."""

    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value) and any(_has_model_value(item) for item in value)
    return True


def compact_model_payload(payload: dict[str, object]) -> dict[str, object]:
    """Drop empty optional answers while keeping the approved data boundary."""

    return {
        field_name: value
        for field_name, value in payload.items()
        if _has_model_value(value)
    }


def redact_model_forbidden_values(text: str, response: AssessmentResponse) -> str:
    """Redact known identifiers if a user repeats them in another answer."""

    redacted = text
    forbidden_values: set[str] = set()
    for field_name in DIRECT_IDENTIFIER_FIELDS | INTERNAL_METADATA_FIELDS:
        value = getattr(response, field_name, None)
        if isinstance(value, str) and value.strip():
            normalized = value.strip()
            forbidden_values.add(normalized)
            # Structured profile values are JSON encoded before this final
            # safeguard, so also cover escaped newlines, quotes and slashes.
            forbidden_values.add(json.dumps(normalized, ensure_ascii=False)[1:-1])
    for forbidden_value in sorted(forbidden_values, key=len, reverse=True):
        redacted = redacted.replace(forbidden_value, "[已脱敏]")
    return redact_obvious_contact_details(redacted)


def _render_model_safe_question_rules(
    selected_confusions: list[str],
    available_fields: set[str] | None = None,
) -> str:
    rules_payload = json.loads(render_question_rules(selected_confusions))
    question_rules = rules_payload.get("questionRules")
    if isinstance(question_rules, dict):
        for field_name in list(question_rules):
            if field_name in MODEL_EXCLUDED_RESPONSE_FIELDS:
                question_rules.pop(field_name, None)
        if available_fields is not None:
            # Only retain rules for supplied answers.  Cross-field checks are
            # useful when their referenced answer is present, but sending the
            # entire questionnaire rulebook for every request is unnecessary.
            question_rules = {
                field_name: {
                    **rule,
                    "checks": [
                        check
                        for check in rule.get("checks", [])
                        if check in available_fields
                    ],
                }
                for field_name, rule in question_rules.items()
                if field_name in available_fields
            }
            rules_payload["questionRules"] = question_rules
    rules_payload.pop("source", None)
    return json.dumps(rules_payload, ensure_ascii=False, separators=(",", ":"))


def build_profile_messages(response: AssessmentResponse, retry_reason: str | None = None) -> list[dict[str, str]]:
    response_payload = compact_model_payload(build_model_safe_response_payload(response))
    response_json = json.dumps(
        response_payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    schema_json = json.dumps(
        ProfileAnalysisResult.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    question_rules_json = _render_model_safe_question_rules(
        response.careerConfusions,
        available_fields=set(response_payload),
    )

    retry_instruction = ""
    if retry_reason:
        retry_instruction = (
            f"\n上一次输出未通过校验，原因是：{retry_reason}。"
            "请只修复上述问题，并确保输出满足JSON Schema。"
            "仅当finish_reason为length或错误说明JSON无法解析时才压缩文字；字段校验失败时不要无谓删减必填字段。"
        )

    user_content = f"""
请根据“问题解释规则”和“学生回答”生成结构化用户画像 JSON。规则是判断题目用途的最高优先级依据；未出现在回答 JSON 中的字段视为未提供。{retry_instruction}

分析顺序：
1. 先区分事实、已发生行为、动机、价值、意愿、自评和愿景。
2. 按 educationStage 判断适用问题：博士生不分析读硕/读博，本科生不套用博士出口问题。
3. 自评能力、兴趣和他人称赞只有在成果、项目、竞赛、科研、实习或准备细节佐证时进入 verifiedStrengths，否则进入 potentialStrengths。
4. 结合学业、二专、转专业、准备、目标岗位、执行力、抗压、健康精力和风险偏好，交叉评估升学、就业、出国、体制内、企业研发等路径；缺失信息标为信息缺口，不得猜测。
5. 检查城市、行业、岗位、家庭生活、技能和风险偏好的一致性，并记录意愿与行动、目标与资源、5年与10年之间的矛盾及验证行动。
6. 生成有证据的 Plan A（主攻）、Plan B（可切换备选）和不重复前两者的 Plan C（系统建议或低成本验证方向），写清下一步与切换条件；尽量为六个报告模块建立 reportEvidenceMap。
7. 每个 careerConfusions 必须使用 selectedCareerConfusionRules 中对应的用途和建议。

硬约束：
- evidence、counterEvidence 使用“英文字段名：回答或可核对事实”；直接身份信息不得进入画像或 reportEvidenceMap。
- 优先保证 summary、优势、风险、教育路径和三条计划；无证据的 verifiedStrengths 允许为空，potentialStrengths 只表示待验证。
- confidence 只能是 low/medium/high，fitLevel 只能是 low/medium/high/uncertain。
- 不分析或评价薪资、收入、购房能力；不得编造经历、院校、待遇或家庭意见；不做医学、心理或人格诊断。
- summary 不超过200字，单项 conclusion/rationale/meaning 不超过120字，列表保留最关键的2—3项；同一证据不要重复解释。
- 只输出紧凑 JSON 对象，不要 Markdown、解释或前后缀。

问题解释规则（仅包含本次回答涉及的字段）：
{question_rules_json}

学生回答：
{response_json}

输出必须符合以下JSON Schema：
{schema_json}
""".strip()
    user_content = redact_model_forbidden_values(user_content, response)

    return [
        {
            "role": "system",
            "content": (
                "你是一名高校生涯规划结构化分析专家。"
                "依据问卷规则和回答完成证据推理，只输出符合 Schema 的 JSON；区分事实、行为、意愿和自评，"
                "不得把自评当作已验证能力或进行医学、心理、人格诊断。"
            ),
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]
