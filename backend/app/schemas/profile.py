from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ConfidenceLevel = Literal["low", "medium", "high"]
FitLevel = Literal["low", "medium", "high", "uncertain"]


class ProfileFinding(BaseModel):
    title: str = ""
    conclusion: str = ""
    confidence: ConfidenceLevel = "low"
    evidence: list[str] = Field(default_factory=list)
    counterEvidence: list[str] = Field(default_factory=list)
    implications: list[str] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value):
        return value if value in {"low", "medium", "high"} else "low"


class ProfileContradiction(BaseModel):
    type: str = ""
    severity: Literal["low", "medium", "high"] = "low"
    description: str = ""
    evidence: list[str] = Field(default_factory=list)
    meaning: str = ""
    verificationAction: str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value):
        return value if value in {"low", "medium", "high"} else "low"


class EducationPathAssessment(BaseModel):
    path: str = ""
    fitLevel: FitLevel = "uncertain"
    rationale: str = ""
    evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    verificationActions: list[str] = Field(default_factory=list)

    @field_validator("fitLevel", mode="before")
    @classmethod
    def normalize_fit_level(cls, value):
        return value if value in {"low", "medium", "high", "uncertain"} else "uncertain"


class PlanOption(BaseModel):
    name: str = ""
    objective: str = ""
    rationale: str = ""
    advantages: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    nextSteps: list[str] = Field(default_factory=list)
    switchConditions: list[str] = Field(default_factory=list)


class ProfileAnalysisResult(BaseModel):
    summary: str = ""
    coreMotivations: list[ProfileFinding] = Field(default_factory=list)
    verifiedStrengths: list[ProfileFinding] = Field(default_factory=list)
    potentialStrengths: list[ProfileFinding] = Field(default_factory=list)
    keyRisks: list[ProfileFinding] = Field(default_factory=list)
    visionConsistency: ProfileFinding | None = None
    contradictions: list[ProfileContradiction] = Field(default_factory=list)
    informationGaps: list[str] = Field(default_factory=list)
    educationPathAssessments: list[EducationPathAssessment] = Field(default_factory=list)
    planA: PlanOption | None = None
    planB: PlanOption | None = None
    reportEvidenceMap: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("reportEvidenceMap", mode="before")
    @classmethod
    def normalize_report_evidence_map(cls, value):
        if not isinstance(value, dict):
            return value

        canonical_titles = {
            "一": "一、你5—10年后的人生画像",
            "二": "二、你的核心优势与风险短板",
            "三": "三、人生愿景与当前路径的匹配度诊断",
            "四": "四、接下来6个月，你可以做的3—5件事",
            "五": "五、半年后我会问你这些问题",
            "六": "六、一个值得你长期思考的问题",
        }
        normalized: dict[str, object] = {}
        for raw_key, evidence in value.items():
            key = str(raw_key).strip().lstrip("#").strip()
            module_number = key[:1]
            normalized[canonical_titles.get(module_number, key)] = evidence
        return normalized

class CareerProfile(BaseModel):
    id: str
    userId: str
    responseId: str
    modelName: str = "legacy-rule"
    promptVersion: str = "legacy-rule-v1.0.0"
    createdAt: str
    rawModelOutput: str | None = None
    qualityWarnings: list[str] = Field(default_factory=list)

    summary: str = ""
    coreMotivations: list[ProfileFinding] = Field(default_factory=list)
    verifiedStrengths: list[ProfileFinding] = Field(default_factory=list)
    potentialStrengths: list[ProfileFinding] = Field(default_factory=list)
    keyRisks: list[ProfileFinding] = Field(default_factory=list)
    visionConsistency: ProfileFinding | None = None
    contradictions: list[ProfileContradiction] = Field(default_factory=list)
    informationGaps: list[str] = Field(default_factory=list)
    educationPathAssessments: list[EducationPathAssessment] = Field(default_factory=list)
    planA: PlanOption | None = None
    planB: PlanOption | None = None
    reportEvidenceMap: dict[str, list[str]] = Field(default_factory=dict)

    # Legacy fields remain optional so existing JSON records can still be read.
    careerStateType: str = ""
    matchedStateTypes: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    strengthTags: list[str] = Field(default_factory=list)
    riskTags: list[str] = Field(default_factory=list)
    valueTags: list[str] = Field(default_factory=list)
    interestTags: list[str] = Field(default_factory=list)
    actionReadinessScore: int = 0
    ruleVersion: str = ""
