from __future__ import annotations

from typing import Literal

REQUIRED_SECTIONS = [
    "一、你5—10年后的人生画像",
    "二、你的核心优势与风险短板",
    "三、人生愿景与当前路径的匹配度诊断",
    "四、接下来6个月，你可以做的3—5件事",
    "五、半年后我会问你这些问题",
    "六、一个值得你长期思考的问题",
    "安全提醒",
]

REQUIRED_CONTENT = ["Plan A", "Plan B", "心理咨询中心", "就业指导中心"]
DISCOURAGED_PHRASES = ["你必须", "你一定适合", "你不适合", "你肯定", "绝对", "唯一选择", "严重不足", "竞争力很弱"]
SECTION_MAX_LENGTHS = {
    "一、你5—10年后的人生画像": 450,
    "二、你的核心优势与风险短板": 550,
    "三、人生愿景与当前路径的匹配度诊断": 1000,
    "四、接下来6个月，你可以做的3—5件事": 850,
    "五、半年后我会问你这些问题": 300,
    "六、一个值得你长期思考的问题": 180,
}


def count_chineseish_words(content: str) -> int:
    return len("".join(content.split()))


def _section_lengths(content: str) -> dict[str, int]:
    lengths: dict[str, int] = {}
    positions = [
        (content.find(title), title)
        for title in [*SECTION_MAX_LENGTHS, "安全提醒"]
        if content.find(title) >= 0
    ]
    positions.sort()

    for index, (start, title) in enumerate(positions):
        if title not in SECTION_MAX_LENGTHS:
            continue
        heading_end = content.find("\n", start + len(title))
        body_start = heading_end + 1 if heading_end >= 0 else start + len(title)
        if index + 1 < len(positions):
            next_title_start = positions[index + 1][0]
            next_heading_start = content.rfind("\n", 0, next_title_start)
            body_end = next_heading_start if next_heading_start >= 0 else next_title_start
        else:
            body_end = len(content)
        lengths[title] = count_chineseish_words(content[body_start:body_end])
    return lengths


def check_report_quality(content: str) -> dict[str, Literal["passed", "warning", "failed"] | list[str]]:
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in content:
            warnings.append(f"缺少模块：{section}")

    for required in REQUIRED_CONTENT:
        if required not in content:
            warnings.append(f"缺少关键内容：{required}")

    for phrase in DISCOURAGED_PHRASES:
        if phrase in content:
            warnings.append(f"出现不建议表达：{phrase}")

    for section, length in _section_lengths(content).items():
        limit = SECTION_MAX_LENGTHS[section]
        if length > limit:
            warnings.append(f"模块超过建议上限：{section} {length}/{limit} 字符")

    count = count_chineseish_words(content)
    if count < 2400:
        warnings.append(f"报告长度不足 2400 字符：{count}")
    if count > 4000:
        warnings.append(f"报告长度超过 4000 字符：{count}")

    status: Literal["passed", "warning", "failed"] = "passed"
    if warnings:
        status = "failed" if any("缺少模块" in item or "缺少关键内容" in item for item in warnings) else "warning"
    return {"status": status, "warnings": warnings}
