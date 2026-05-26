from __future__ import annotations

from dataclasses import dataclass

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerStateType

PRIORITY: list[CareerStateType] = [
    "方向模糊型",
    "教育路径摇摆型",
    "科研深造倾向型",
    "高目标高压力型",
    "目标清晰但行动不足型",
    "稳定安全导向型",
]


@dataclass
class CareerStateMatch:
    type: CareerStateType
    evidence: list[str]
    score: int


def includes(items: list[str], value: str) -> bool:
    return any(value in item or item in value for item in items)


def maybe_match(match_type: CareerStateType, evidence: list[str], minimum: int = 1) -> CareerStateMatch | None:
    if len(evidence) >= minimum:
        return CareerStateMatch(type=match_type, evidence=evidence, score=len(evidence))
    return None


def classify_career_state(input_data: AssessmentResponse) -> dict[str, object]:
    matches = [
        match_unclear_direction(input_data),
        match_education_swing(input_data),
        match_research_path(input_data),
        match_high_goal_high_pressure(input_data),
        match_clear_goal_low_action(input_data),
        match_stability_oriented(input_data),
    ]
    valid_matches = [match for match in matches if match is not None]
    primary_type = next((item for item in PRIORITY if any(match.type == item for match in valid_matches)), "方向模糊型")

    return {
        "primaryType": primary_type,
        "matchedTypes": [match.type for match in valid_matches],
        "evidence": [item for match in valid_matches for item in match.evidence],
    }


def match_unclear_direction(input_data: AssessmentResponse) -> CareerStateMatch | None:
    evidence: list[str] = []
    if input_data.educationPath == "暂不确定":
        evidence.append("毕业后路径暂不确定")
    if includes(input_data.targetIndustries, "暂不确定"):
        evidence.append("目标行业暂不确定")
    if input_data.futureRoleType == "还不确定":
        evidence.append("未来角色还不确定")
    if includes(input_data.careerConfusions, "不知道未来适合做什么"):
        evidence.append("当前困惑包含不知道未来适合做什么")
    if includes(input_data.missingResources, "不知道方向"):
        evidence.append("目前最缺的是方向")
    return maybe_match("方向模糊型", evidence, 2)


def match_education_swing(input_data: AssessmentResponse) -> CareerStateMatch | None:
    evidence: list[str] = []
    if input_data.educationCertainty <= 2:
        evidence.append("教育路径确定程度较低")
    if includes(input_data.careerConfusions, "纠结就业、读研、出国、读博"):
        evidence.append("当前困惑包含路径选择纠结")
    if includes(input_data.educationPathReasons, "想延缓就业压力"):
        evidence.append("路径动机包含延缓就业压力")
    if includes(input_data.educationPathReasons, "还没有想清楚"):
        evidence.append("路径动机包含暂时倾向")
    return maybe_match("教育路径摇摆型", evidence)


def match_research_path(input_data: AssessmentResponse) -> CareerStateMatch | None:
    evidence: list[str] = []
    if input_data.educationPath in ["国内读研", "读博 / 科研方向"]:
        evidence.append("教育路径偏向读研或科研")
    if input_data.phdIntention in ["明确考虑", "有一点兴趣"]:
        evidence.append("对读博有明确或初步兴趣")
    if input_data.interestScores.research >= 4:
        evidence.append("研究分析兴趣较高")
    if input_data.abilityScores.logic >= 4:
        evidence.append("逻辑能力自评分较高")
    if includes(input_data.educationPathReasons, "真正喜欢科研或学术探索"):
        evidence.append("路径动机包含科研兴趣")
    return maybe_match("科研深造倾向型", evidence, 2)


def match_high_goal_high_pressure(input_data: AssessmentResponse) -> CareerStateMatch | None:
    evidence: list[str] = []
    if includes(input_data.fiveYearPriorities, "高收入"):
        evidence.append("五年优先追求包含高收入")
    if includes(input_data.fiveYearPriorities, "快速成长"):
        evidence.append("五年优先追求包含快速成长")
    if input_data.lifePreference == "事业优先，愿意承受较高强度":
        evidence.append("生活偏好为事业优先和高强度")
    if "一般" in input_data.healthEnergyStatus or "较差" in input_data.healthEnergyStatus:
        evidence.append("健康精力状态需要关注")
    if includes(input_data.missingResources, "缺时间") or includes(input_data.missingResources, "缺信心"):
        evidence.append("当前资源缺口包含时间或信心")
    return maybe_match("高目标高压力型", evidence, 2)


def match_clear_goal_low_action(input_data: AssessmentResponse) -> CareerStateMatch | None:
    clear_goal = not includes(input_data.targetIndustries, "暂不确定") and input_data.futureRoleType != "还不确定"
    low_action = len(input_data.currentPreparations) < 2 or includes(input_data.currentPreparations, "还没有明显准备")
    if clear_goal and low_action:
        return maybe_match("目标清晰但行动不足型", ["目标行业和未来角色较清楚，但行动准备仍偏少"])
    return None


def match_stability_oriented(input_data: AssessmentResponse) -> CareerStateMatch | None:
    evidence: list[str] = []
    top_two_values = input_data.topValuesRanked[:2]
    if includes(top_two_values, "稳定"):
        evidence.append("核心价值观前两项包含稳定")
    if includes(top_two_values, "平衡"):
        evidence.append("核心价值观前两项包含平衡")
    if input_data.lifePreference == "稳定体面，风险可控":
        evidence.append("生活状态偏好为稳定体面")
    if input_data.educationPath in ["考公 / 选调 / 事业单位", "国企 / 央企 / 研究院"]:
        evidence.append("教育路径偏向稳定组织")
    return maybe_match("稳定安全导向型", evidence, 2)
