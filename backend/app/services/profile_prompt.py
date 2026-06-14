from __future__ import annotations

import json

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import ProfileAnalysisResult
from app.services.question_rules import render_question_rules

PROFILE_PROMPT_VERSION = "profile-analysis-v1.4.0"


def build_profile_messages(response: AssessmentResponse, retry_reason: str | None = None) -> list[dict[str, str]]:
    response_payload = response.model_dump(mode="json")
    response_payload.pop("fiveYearIncome", None)
    response_payload.pop("tenYearIncome", None)
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

    retry_instruction = ""
    if retry_reason:
        retry_instruction = (
            f"\n上一次输出未通过校验，原因是：{retry_reason}。"
            "请只修复上述问题，并确保输出满足JSON Schema。"
            "仅当finish_reason为length或错误说明JSON无法解析时才压缩文字；字段校验失败时不要无谓删减必填字段。"
        )

    return [
        {
            "role": "system",
            "content": (
                "你是一名负责高校生涯规划评估的结构化分析专家。"
                "你的任务不是撰写报告，而是依据问卷设计规则完成证据推理，并只输出合法JSON。"
                "每个结论必须引用具体回答；必须区分事实、行为、规划、信息、意愿、自评和愿景。"
                "不得把自评直接写成已验证能力，不得把意愿直接写成适配结论，不得进行医学、心理或人格诊断。"
            ),
        },
        {
            "role": "user",
            "content": f"""
请根据“问题解释规则”和“学生回答”生成结构化用户画像JSON。问题解释规则来自问卷设计文档，是判断每道题用途的最高优先级依据。{retry_instruction}

分析流程必须按以下顺序执行：
1. 先识别客观事实和已经发生的行为证据。
2. 再识别动机、价值排序、教育意愿和5—10年愿景。
3. 对每项自评能力或兴趣，查找行为证据；有佐证才可进入verifiedStrengths，否则只能进入potentialStrengths。
4. 交叉检查教育意向、具体规划、确定度、目标岗位学历要求和科研兴趣，分别评估硕士、博士、直接就业，必要时增加出国路径。
5. 检查目标城市、行业、岗位、家庭、生活安排、技能和健康精力之间是否一致。
6. 主动查找意愿与行动、目标与资源、5年与10年、价值偏好之间的矛盾。矛盾不是错误，需说明含义和验证行动。
7. 根据证据强度生成Plan A与Plan B。两条路径必须可切换，写清下一步和切换条件。
8. 尽量建立reportEvidenceMap，为六个报告模块列出可使用的关键证据。
9. 对学生实际选择的每一个careerConfusions选项，必须使用selectedCareerConfusionRules中的专属用途和建议，不能合并成泛化结论。

约束：
- 所有evidence和counterEvidence必须写成“字段名：回答内容或可核对事实”的形式，字段名必须使用学生回答JSON中的英文键名。
- 优先保证summary、优势、风险、教育路径判断和Plan A / Plan B有实质内容；辅助字段缺失时可使用空数组或null。
- reportEvidenceMap建议使用JSON Schema中的六个中文模块标题；标题有轻微差异不会导致画像失败。
- verifiedStrengths至少需要一条behavior证据；没有满足条件的优势时允许为空。
- potentialStrengths用于表达尚待行为验证的能力或兴趣。
- 结论信心只能为low、medium或high；路径适配只能为low、medium、high或uncertain。
- Plan A不一定是升学，应由目标匹配、真实行动和时间窗口共同决定。
- 不分析、不预测也不评价薪资、收入区间、收入目标是否现实或住房购买能力；不得在画像任何字段中出现具体薪资结论。
- 不得编造院校、岗位待遇、家庭意见或学生未提供的经历。
- 输出应紧凑，总长度控制在约3500—5000个中文字符；同一证据不要在多个字段中反复解释。
- summary不超过200字；单项conclusion、rationale或meaning不超过120字；列表只保留最关键的2—3项。
- 只输出JSON对象，不要Markdown代码块、解释文字或前后缀。

问题解释规则：
{render_question_rules(response.careerConfusions)}

学生回答：
{response_json}

输出必须符合以下JSON Schema：
{schema_json}
""".strip(),
        },
    ]
