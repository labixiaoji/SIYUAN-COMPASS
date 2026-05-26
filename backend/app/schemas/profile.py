from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

CareerStateType = Literal[
    "方向模糊型",
    "教育路径摇摆型",
    "科研深造倾向型",
    "高目标高压力型",
    "目标清晰但行动不足型",
    "稳定安全导向型",
]


class CareerProfile(BaseModel):
    id: str
    userId: str
    responseId: str
    careerStateType: CareerStateType
    matchedStateTypes: list[CareerStateType]
    evidence: list[str]
    strengthTags: list[str]
    riskTags: list[str]
    valueTags: list[str]
    interestTags: list[str]
    actionReadinessScore: int
    ruleVersion: str
    createdAt: str
