from __future__ import annotations

from typing import Literal

REQUIRED_SECTIONS = [
    "一、你5—10年后想成为的人",
    "二、你的当前生涯状态判断",
    "三、你的核心优势与主要风险",
    "四、愿景、教育路径与当前行动的匹配度诊断",
    "五、接下来6个月建议做的3—5件事",
    "六、半年后我会问你的问题",
    "七、一个值得长期思考的问题",
    "安全提醒",
]

DISCOURAGED_PHRASES = ["你必须", "你一定适合", "你不适合", "你肯定", "绝对", "唯一选择", "严重不足", "竞争力很弱"]


def count_chineseish_words(content: str) -> int:
    return len("".join(content.split()))


def check_report_quality(content: str) -> dict[str, Literal["passed", "warning", "failed"] | list[str]]:
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in content:
            warnings.append(f"缺少模块：{section}")

    for phrase in DISCOURAGED_PHRASES:
        if phrase in content:
            warnings.append(f"出现不建议表达：{phrase}")

    count = count_chineseish_words(content)
    if count > 1800:
        warnings.append(f"报告长度超过 1800 字符：{count}")
    if "心理咨询中心" not in content or "就业指导中心" not in content:
        warnings.append("缺少固定安全提醒")

    status: Literal["passed", "warning", "failed"] = "passed"
    if warnings:
        status = "failed" if any("缺少模块" in item for item in warnings) else "warning"
    return {"status": status, "warnings": warnings}
