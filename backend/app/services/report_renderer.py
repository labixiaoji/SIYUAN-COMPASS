from __future__ import annotations

import re

from app.schemas.report import CareerBlueprintDraft, ReportAnalysisItem, ReportPlan


SAFETY_REMINDER = (
    "本报告是生涯探索参考，不是医学、心理诊断或人生定论；如持续感到焦虑、低落或无力，"
    "应联系学校心理咨询中心；升学就业的具体政策与机会应向学校就业指导中心、教务部门或官方渠道核实。"
)

PLAN_KINDS = {
    "A": "主攻路径",
    "B": "备选路径",
    "C": "探索路径",
}


def _inline(value: str) -> str:
    """Keep model text inside the renderer-controlled Markdown structure."""

    compact = " ".join(value.split()).replace("**", "").replace("__", "")
    return re.sub(r"^(?:#{1,6}|[-+*]|\d+[.、])\s+", "", compact).strip()


def _joined(values: list[str]) -> str:
    return "；".join(_inline(value) for value in values if _inline(value))


def _analysis_item(index: int, item: ReportAnalysisItem, *, include_validation: bool) -> list[str]:
    evidence_label = {
        "verified": "你已经做过的事",
        "potential": "目前能看到的线索",
        "risk": "目前需要留意的是",
    }[item.evidenceStatus]
    lines = [
        f"{index}. **{_inline(item.title)}**",
        f"  - {_inline(item.studentNarrative)}",
        f"  - {evidence_label}：{_joined(item.evidence)}",
    ]
    if include_validation:
        lines.append(f"  - 如果暂时不处理：{_inline(item.futureRelevance)}")
        lines.append(f"  - 可以先做：{_inline(item.validation)}")
    else:
        lines.append(f"  - 以后可能会用在：{_inline(item.futureRelevance)}")
    return lines


def _plan_lines(plan: ReportPlan) -> list[str]:
    return [
        f"### Plan {plan.id}：{_inline(plan.title)}（{PLAN_KINDS[plan.id]}）",
        _inline(plan.futureScene),
        "",
        _inline(plan.whyItFitsYou),
        "",
        f"- 眼下可以补上的：{_inline(plan.currentGap)}",
        f"- 可以先从哪一步开始：{_inline(plan.firstExperiment)}",
        f"- 什么时候值得重新想一想：{_inline(plan.decisionSignal)}",
    ]


def render_report_markdown(draft: CareerBlueprintDraft) -> str:
    plans = {plan.id: plan for plan in draft.diagnosis.plans}
    lines = [
        "# 我的生涯蓝图",
        "",
        "## 一、你5—10年后的人生画像",
        _inline(draft.portrait.fiveYearPortrait),
        "",
        _inline(draft.portrait.tenYearPortrait),
    ]

    lines.extend(["", "## 二、你的优势，以及还可以继续积累的地方", "", "### 你已经具备的优势"])
    for index, item in enumerate(draft.strengthsAndRisks.strengths, 1):
        lines.extend(_analysis_item(index, item, include_validation=False))
    lines.extend(["", "### 还可以继续积累的地方"])
    for index, item in enumerate(draft.strengthsAndRisks.risks, 1):
        lines.extend(_analysis_item(index, item, include_validation=True))

    lines.extend(
        [
            "",
            "## 三、从现在走向未来，可以怎样选择",
            "",
            "### 你现在最想解决的困惑",
            _inline(draft.diagnosis.currentConfusion),
            "",
            "### 这份困惑背后，还缺少什么？",
            _inline(draft.diagnosis.underlyingProblem),
            "",
            "### 接下来，看看三种可能的方向",
            "下面三条方向不是三个必须同时完成的任务，而是三种可以放在一起比较的未来走法。",
        ]
    )
    for plan_id in ("A", "B", "C"):
        lines.extend(["", *_plan_lines(plans[plan_id])])
    lines.extend(
        [
            "",
            "### 把三条方向放在一起，可以怎么安排？",
            _inline(draft.diagnosis.pathRelationship),
        ]
    )

    lines.extend(["", "## 四、接下来6个月，你可以做的3—5件事"])
    for index, action in enumerate(draft.sixMonthActions, 1):
        lines.extend(
            [
                "",
                f"{index}. **{_inline(action.title)}**",
                f"  - 可以从这些步骤开始：{_joined(action.steps)}",
                f"  - 这一步为什么重要：{_inline(action.purpose)}",
                f"  - 做到什么算完成：{_inline(action.completionCriteria)}",
                f"  - 适合什么时候做：{_inline(action.deadline)}",
                f"  - 它和未来方向的关系：{_inline(action.pathConnection)}",
                f"  - 做完后重点看看：{_inline(action.reflectionSignal)}",
            ]
        )

    lines.extend(["", "## 五、半年后我会问你这些问题", ""])
    lines.extend(
        f"{index}. {_inline(question)}"
        for index, question in enumerate(draft.reviewQuestions, 1)
    )
    lines.extend(
        [
            "",
            "## 六、一个值得你长期思考的问题",
            _inline(draft.longTermQuestion.context),
            "",
            f"**留给你的问题：**{_inline(draft.longTermQuestion.question)}",
            "",
            "## 安全提醒",
            SAFETY_REMINDER,
        ]
    )
    return "\n".join(lines).strip()
