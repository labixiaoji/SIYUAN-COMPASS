from __future__ import annotations

from collections.abc import Sequence
from difflib import SequenceMatcher
import re
from typing import Literal

from app.core.data_privacy import contains_obvious_contact_details

REPORT_QUALITY_VERSION = "report-quality-v2.6.0"

REQUIRED_SECTIONS = [
    "一、你5—10年后的人生画像",
    "二、你的优势，以及还可以继续积累的地方",
    "三、从现在走向未来，可以怎样选择",
    "四、接下来6个月，你可以做的3—5件事",
    "五、半年后我会问你这些问题",
    "六、一个值得你长期思考的问题",
    "安全提醒",
]

REQUIRED_CONTENT = [
    "Plan A",
    "Plan B",
    "Plan C",
    "你现在最想解决的困惑",
    "这份困惑背后，还缺少什么",
    "接下来，看看三种可能的方向",
    "心理咨询中心",
    "就业指导中心",
]
DISCOURAGED_PHRASES = ["你必须", "你一定适合", "你不适合", "你肯定", "绝对", "唯一选择", "严重不足", "竞争力很弱"]
TEMPLATE_PHRASES = [
    "基于以上分析",
    "综合来看",
    "总体而言",
    "值得注意的是",
    "可以看出",
    "有利于提升",
    "进一步提升",
    "增强竞争力",
    "实现个人价值",
    "在未来发展中",
]
STUDENT_FACING_TERM_LIMITS = {"验证": 4}
PORTRAIT_ANALYSIS_PHRASES = (
    "你现在需要",
    "你需要做",
    "你可以先",
    "建议你",
    "从现在到",
    "接下来半年",
    "第一，",
    "第二，",
    "第三，",
    "GPA",
    "专业排名",
    "还没有正式实习",
    "家庭期待",
    "核心取舍",
)
SECTION_MAX_LENGTHS = {
    "一、你5—10年后的人生画像": 1200,
    "二、你的优势，以及还可以继续积累的地方": 2000,
    "三、从现在走向未来，可以怎样选择": 3400,
    "四、接下来6个月，你可以做的3—5件事": 2200,
    "五、半年后我会问你这些问题": 900,
    "六、一个值得你长期思考的问题": 700,
}
SECTION_MIN_LENGTHS = {
    "一、你5—10年后的人生画像": 500,
    "二、你的优势，以及还可以继续积累的地方": 350,
    "三、从现在走向未来，可以怎样选择": 750,
    "四、接下来6个月，你可以做的3—5件事": 260,
    "五、半年后我会问你这些问题": 100,
    "六、一个值得你长期思考的问题": 80,
}
MIN_REPORT_LENGTH = 2500
RECOMMENDED_REPORT_MIN_LENGTH = 3500
RECOMMENDED_REPORT_MAX_LENGTH = 7000
PLAN_TITLES = ("Plan A", "Plan B", "Plan C")
STRUCTURED_SUBHEADINGS = (
    *PLAN_TITLES,
    "你现在最想解决的困惑",
    "你现在最大的困惑是什么",
    "这份困惑背后，还缺少什么",
    "这个困惑背后的真正问题是什么",
    "接下来，看看三种可能的方向",
    "把三条方向放在一起，可以怎么安排",
    "这三条方向应该怎么理解",
    "接下来可以怎么试一试",
    "接下来可以如何验证",
)
SECTION_ALIASES = {
    "二、你的优势，以及还可以继续积累的地方": (
        "二、你的优势，以及还可以继续积累的地方",
        "二、你的核心优势与风险短板",
    ),
    "三、从现在走向未来，可以怎样选择": (
        "三、从现在走向未来，可以怎样选择",
        "三、人生愿景与当前路径的匹配度诊断",
    ),
}
SUBHEADING_ALIASES = {
    "你现在最想解决的困惑": ("你现在最想解决的困惑", "你现在最大的困惑是什么"),
    "这份困惑背后，还缺少什么": ("这份困惑背后，还缺少什么", "这个困惑背后的真正问题是什么"),
    "接下来，看看三种可能的方向": (
        "接下来，看看三种可能的方向",
        "这三条方向应该怎么理解",
        "接下来可以怎么试一试",
        "接下来可以如何验证",
    ),
    "把三条方向放在一起，可以怎么安排": (
        "把三条方向放在一起，可以怎么安排",
        "现在更适合怎样安排",
    ),
    "接下来可以怎么试一试": ("接下来可以怎么试一试", "接下来可以如何验证"),
}
_ACTION_ITEM_PATTERNS = (
    re.compile(r"^\s*(?:\*\*)?\s*\d+\s*[.、](?:\*\*)?\s*"),
    re.compile(r"^\s*(?:\*\*)?\s*[（(]\s*\d+\s*[）)](?:\*\*)?\s*"),
    re.compile(r"^\s*行动[一二三四五六七八九十百千万]+(?:\s*[：:、.]\s*|\s+|$)"),
)


def count_chineseish_words(content: str) -> int:
    visible = re.sub(
        r"(?m)^\s{0,3}(?:#{1,6}\s*|[-+*]\s+|\d+[.、]\s*)",
        "",
        content,
    )
    visible = visible.replace("**", "").replace("__", "").replace("`", "")
    return len("".join(visible.split()))


def extract_action_items(content: str) -> list[str]:
    """Recognize common list formats without making formatting a hard failure."""

    return [
        line.strip()
        for line in content.splitlines()
        if line == line.lstrip() and any(pattern.match(line) for pattern in _ACTION_ITEM_PATTERNS)
    ]


def _section_lengths(content: str) -> dict[str, int]:
    lengths: dict[str, int] = {}
    positions: list[tuple[int, str, int]] = []
    for title in [*SECTION_MAX_LENGTHS, "安全提醒"]:
        aliases = SECTION_ALIASES.get(title, (title,))
        for alias in aliases:
            match = re.search(rf"(?m)^##\s+{re.escape(alias)}\s*$", content)
            if match:
                positions.append((match.start(), title, match.end()))
                break
    positions.sort()

    for index, (start, title, heading_end) in enumerate(positions):
        if title not in SECTION_MAX_LENGTHS:
            continue
        body_start = heading_end
        if index + 1 < len(positions):
            next_title_start = positions[index + 1][0]
            body_end = next_title_start
        else:
            body_end = len(content)
        lengths[title] = count_chineseish_words(content[body_start:body_end])
    return lengths


def _compact(value: str) -> str:
    return "".join(value.split())


def _has_heading(content: str, title: str) -> bool:
    return bool(re.search(rf"(?m)^##\s+{re.escape(title)}\s*$", content))


def _extract_section(content: str, title: str) -> str:
    aliases = SECTION_ALIASES.get(title, (title,))
    match = next(
        (
            found
            for alias in aliases
            if (found := re.search(rf"(?m)^##\s+{re.escape(alias)}\s*$", content))
        ),
        None,
    )
    if not match:
        return ""
    next_heading = re.search(r"(?m)^##\s+", content[match.end() :])
    end = match.end() + next_heading.start() if next_heading else len(content)
    return content[match.end() : end].strip()


def _has_subheading(content: str, title: str) -> bool:
    return _find_subheading(content, title) is not None


def _find_subheading(content: str, title: str) -> re.Match[str] | None:
    markdown = re.search(
        rf"(?m)^#{{3,6}}\s+{re.escape(title)}(?:[：:？?].*)?$",
        content,
    )
    if markdown:
        return markdown
    return re.search(
        rf"(?m)^\s*\*\*\s*{re.escape(title)}(?:[：:？?].*?)?\s*\*\*\s*$",
        content,
    )


def _extract_subsection(content: str, title: str) -> str:
    match = _find_subheading(content, title)
    if not match:
        return ""
    structured_titles = "|".join(re.escape(item) for item in STRUCTURED_SUBHEADINGS)
    next_heading = re.search(
        rf"(?m)^(?:#{{2,6}}\s+|\s*\*\*\s*(?:{structured_titles})(?:[：:？?].*?)?\s*\*\*\s*$)",
        content[match.end() :],
    )
    end = match.end() + next_heading.start() if next_heading else len(content)
    return content[match.end() : end].strip()


def _plan_warnings(content: str) -> list[str]:
    warnings: list[str] = []
    bodies = {title: _extract_subsection(content, title) for title in PLAN_TITLES}
    for title, body in bodies.items():
        if not _has_subheading(content, title):
            continue
        if count_chineseish_words(body) < 80:
            warnings.append(f"路径内容过少：{title}")
        if body and not any(keyword in body for keyword in ("下一步", "验证", "行动", "条件", "开始", "试一试", "重新想")):
            warnings.append(f"路径缺少验证行动或切换条件：{title}")

    compact_bodies = {title: _compact(body) for title, body in bodies.items() if body}
    for index, left in enumerate(PLAN_TITLES):
        for right in PLAN_TITLES[index + 1 :]:
            if left not in compact_bodies or right not in compact_bodies:
                continue
            similarity = SequenceMatcher(None, compact_bodies[left], compact_bodies[right]).ratio()
            if similarity >= 0.9:
                warnings.append(f"路径内容高度重复：{left} 与 {right}")
    return warnings


def _contains_meaningful_snippet(content: str, value: str, min_length: int = 6) -> bool:
    normalized = _compact(value)
    if not normalized or normalized == "未填写":
        return True

    content_normalized = _compact(content)
    if normalized in content_normalized:
        return True

    separators = "，,。.;；:：、!?！？\n"
    chunks = [normalized]
    for separator in separators:
        chunks = [part for chunk in chunks for part in chunk.split(separator)]
    return any(len(chunk) >= min_length and chunk in content_normalized for chunk in chunks)


def _contains_unqualified_phrase(content: str, phrase: str) -> bool:
    negated_prefixes = ("不是", "并非", "绝非", "没有", "不代表", "不意味着", "不等于", "并不")
    for match in re.finditer(re.escape(phrase), content):
        prefix = content[max(0, match.start() - 8) : match.start()]
        if any(prefix.endswith(item) for item in negated_prefixes):
            continue
        return True
    return False


def check_report_quality(
    content: str,
    expected_confusions: Sequence[str] | None = None,
    main_confusion_text: str | None = None,
    prohibited_personal_values: Sequence[str] | None = None,
    finish_reason: str | None = None,
) -> dict[str, Literal["passed", "warning", "failed"] | list[str]]:
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        aliases = SECTION_ALIASES.get(section, (section,))
        if not any(_has_heading(content, alias) for alias in aliases):
            warnings.append(f"缺少模块：{section}")

    for required in REQUIRED_CONTENT:
        is_subheading = required in {
            *PLAN_TITLES,
            "你现在最想解决的困惑",
            "这份困惑背后，还缺少什么",
            "接下来，看看三种可能的方向",
        }
        aliases = SUBHEADING_ALIASES.get(required, (required,))
        if (is_subheading and not any(_has_subheading(content, alias) for alias in aliases)) or (not is_subheading and required not in content):
            warnings.append(f"缺少关键内容：{required}")

    if finish_reason == "length":
        warnings.append("模型输出因长度限制被截断")

    if expected_confusions:
        missing_confusions = [item for item in expected_confusions if item and item not in content]
        if len(missing_confusions) == len([item for item in expected_confusions if item]):
            warnings.append("缺少当前困惑选项引用")

    if main_confusion_text and not _contains_meaningful_snippet(content, main_confusion_text):
        warnings.append("未明显回应主要困惑描述")

    for phrase in DISCOURAGED_PHRASES:
        if _contains_unqualified_phrase(content, phrase):
            warnings.append(f"出现不建议表达：{phrase}")

    for phrase in TEMPLATE_PHRASES:
        if phrase in content:
            warnings.append(f"出现模板化表达：{phrase}")

    for term, limit in STUDENT_FACING_TERM_LIMITS.items():
        occurrences = content.count(term)
        if occurrences > limit:
            warnings.append(f"学生可见文字反复使用生硬术语：{term}（{occurrences}次）")

    portrait = _extract_section(content, "一、你5—10年后的人生画像")
    portrait_analysis = [phrase for phrase in PORTRAIT_ANALYSIS_PHRASES if phrase in portrait]
    if portrait_analysis:
        warnings.append(f"人生画像混入当前分析或行动建议：{'、'.join(portrait_analysis)}")
    if portrait and not re.search(r"(?:五|5)年", portrait):
        warnings.append("人生画像没有明确展开五年后的生活")
    if portrait and not re.search(r"(?:十|10)年", portrait):
        warnings.append("人生画像没有明确展开十年后的生活")

    for section, length in _section_lengths(content).items():
        limit = SECTION_MAX_LENGTHS[section]
        minimum = SECTION_MIN_LENGTHS[section]
        if length < minimum:
            warnings.append(f"模块内容过少：{section} {length}/{minimum} 字符")
        if length > limit:
            warnings.append(f"模块超过建议上限：{section} {length}/{limit} 字符")

    count = count_chineseish_words(content)
    if count < MIN_REPORT_LENGTH:
        warnings.append(f"报告内容严重不足：{count}/{MIN_REPORT_LENGTH} 字符")
    if count < RECOMMENDED_REPORT_MIN_LENGTH:
        warnings.append(f"报告长度不足 {RECOMMENDED_REPORT_MIN_LENGTH} 字符建议下限：{count}")
    if count > RECOMMENDED_REPORT_MAX_LENGTH:
        warnings.append(f"报告长度超过 {RECOMMENDED_REPORT_MAX_LENGTH} 字符建议上限：{count}")

    warnings.extend(_plan_warnings(content))

    action_section_match = re.search(
        r"(?m)^##\s+四、接下来6个月，你可以做的3—5件事\s*$",
        content,
    )
    next_section_match = re.search(
        r"(?m)^##\s+五、半年后我会问你这些问题\s*$",
        content,
    )
    if action_section_match and next_section_match and next_section_match.start() > action_section_match.end():
        action_section = content[action_section_match.end() : next_section_match.start()]
        action_count = len(extract_action_items(action_section))
        if not 3 <= action_count <= 5:
            warnings.append(f"行动项格式或数量异常（建议3—5项）：{action_count}")

    if prohibited_personal_values:
        leaked = [
            value.strip()
            for value in prohibited_personal_values
            if isinstance(value, str) and len(value.strip()) >= 3 and value.strip() in content
        ]
        if leaked:
            warnings.append("报告包含不应展示的个人身份信息")
    if contains_obvious_contact_details(content):
        warnings.append("报告包含疑似联系方式或长数字标识")

    status: Literal["passed", "warning", "failed"] = "passed"
    fatal_warnings: list[str] = []
    if warnings:
        failed_markers = [
            "缺少模块",
            "缺少关键内容",
            "模型输出因长度限制被截断",
            "模块内容过少",
            "报告内容严重不足",
            "路径内容过少",
            "路径缺少验证行动或切换条件",
            "路径内容高度重复",
            "报告包含不应展示的个人身份信息",
            "报告包含疑似联系方式或长数字标识",
        ]
        fatal_warnings = [
            item
            for item in warnings
            if any(marker in item for marker in failed_markers)
        ]
        status = "failed" if fatal_warnings else "warning"
    return {"status": status, "warnings": warnings, "fatalWarnings": fatal_warnings}
