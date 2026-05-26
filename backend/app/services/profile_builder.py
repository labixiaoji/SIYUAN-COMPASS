from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.services.profile_classifier import classify_career_state

CAREER_RULE_VERSION = "v1.0.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def pick_high_scores(scores: dict[str, int], labels: dict[str, str]) -> list[str]:
    return [labels[key] for key, score in scores.items() if score >= 4 and key in labels]


def build_career_profile(response: AssessmentResponse) -> CareerProfile:
    result = classify_career_state(response)
    action_readiness_score = 1 if "还没有明显准备" in response.currentPreparations else min(5, max(1, len(response.currentPreparations)))

    ability_tags = pick_high_scores(
        response.abilityScores.model_dump(),
        {
            "logic": "逻辑分析",
            "expression": "表达写作",
            "spatialDesign": "空间设计",
            "interpersonal": "人际理解",
        },
    )
    interest_tags = pick_high_scores(
        response.interestScores.model_dump(),
        {
            "handsOn": "动手实践",
            "research": "研究分析",
            "creation": "创作表达",
            "helping": "助人咨询",
            "leadership": "领导影响",
            "detail": "规则细节",
        },
    )
    risk_tags = [
        *response.missingResources,
        "岗位认知不足" if "不了解" in response.targetJobAwareness or "大概" in response.targetJobAwareness else "",
        "健康精力风险" if "较差" in response.healthEnergyStatus else "",
    ]

    return CareerProfile(
        id=str(uuid4()),
        userId=response.userId,
        responseId=response.id,
        careerStateType=result["primaryType"],
        matchedStateTypes=result["matchedTypes"],
        evidence=result["evidence"],
        strengthTags=[*ability_tags, *interest_tags, *[item for item in response.currentPreparations if item != "还没有明显准备"]][:8],
        riskTags=list(dict.fromkeys([item for item in risk_tags if item])),
        valueTags=response.topValuesRanked,
        interestTags=interest_tags,
        actionReadinessScore=action_readiness_score,
        ruleVersion=CAREER_RULE_VERSION,
        createdAt=now_iso(),
    )
