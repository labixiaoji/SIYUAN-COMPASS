from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PlanId = Literal["A", "B", "C"]
ListItemText = Annotated[str, Field(min_length=1, max_length=300)]
QuestionText = Annotated[str, Field(min_length=10, max_length=250)]


class _ReportDraftModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class ReportPortrait(_ReportDraftModel):
    fiveYearPortrait: str = Field(min_length=250, max_length=700)
    tenYearPortrait: str = Field(min_length=250, max_length=700)


class ReportAnalysisItem(_ReportDraftModel):
    title: str = Field(min_length=1, max_length=40)
    evidenceStatus: Literal["verified", "potential", "risk"]
    studentNarrative: str = Field(min_length=30, max_length=450)
    evidence: list[ListItemText] = Field(min_length=1, max_length=3)
    futureRelevance: str = Field(min_length=20, max_length=350)
    validation: str = Field(default="", max_length=300)


class ReportStrengthsAndRisks(_ReportDraftModel):
    strengths: list[ReportAnalysisItem] = Field(min_length=2, max_length=2)
    risks: list[ReportAnalysisItem] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def require_risk_validation(self):
        if any(item.evidenceStatus == "risk" for item in self.strengths):
            raise ValueError("优势的 evidenceStatus 只能是 verified 或 potential")
        if any(item.evidenceStatus != "risk" for item in self.risks):
            raise ValueError("风险的 evidenceStatus 必须是 risk")
        if any(not item.validation.strip() for item in self.risks):
            raise ValueError("每项风险必须包含验证或改善行动")
        return self


class ReportPlan(_ReportDraftModel):
    id: PlanId
    title: str = Field(min_length=4, max_length=80)
    futureScene: str = Field(min_length=30, max_length=500)
    whyItFitsYou: str = Field(min_length=30, max_length=450)
    currentGap: str = Field(min_length=20, max_length=300)
    firstExperiment: str = Field(min_length=20, max_length=350)
    decisionSignal: str = Field(min_length=20, max_length=300)

    @field_validator("id", mode="before")
    @classmethod
    def normalize_plan_id(cls, value):
        normalized = str(value).strip().upper().replace("PLAN", "").strip()
        return normalized


class ReportDiagnosis(_ReportDraftModel):
    currentConfusion: str = Field(min_length=20, max_length=600)
    underlyingProblem: str = Field(min_length=30, max_length=900)
    pathRelationship: str = Field(min_length=50, max_length=500)
    plans: list[ReportPlan] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def require_all_plan_ids(self):
        if {plan.id for plan in self.plans} != {"A", "B", "C"}:
            raise ValueError("plans 必须分别包含 Plan A、Plan B 和 Plan C")
        return self


class ReportAction(_ReportDraftModel):
    title: str = Field(min_length=1, max_length=80)
    purpose: str = Field(min_length=1, max_length=300)
    steps: list[ListItemText] = Field(min_length=1, max_length=4)
    completionCriteria: str = Field(min_length=1, max_length=300)
    deadline: str = Field(min_length=1, max_length=80)
    validatesPlans: list[PlanId] = Field(min_length=1, max_length=3)
    pathConnection: str = Field(min_length=30, max_length=400)
    reflectionSignal: str = Field(min_length=20, max_length=300)

    @field_validator("validatesPlans", mode="before")
    @classmethod
    def normalize_plan_ids(cls, value):
        if not isinstance(value, list):
            return value
        return [str(item).strip().upper().replace("PLAN", "").strip() for item in value]

    @model_validator(mode="after")
    def require_distinct_plan_ids(self):
        if len(set(self.validatesPlans)) != len(self.validatesPlans):
            raise ValueError("validatesPlans 不能包含重复路径")
        missing = [
            plan_id
            for plan_id in self.validatesPlans
            if f"Plan {plan_id}" not in self.pathConnection
        ]
        if missing:
            raise ValueError(f"pathConnection 必须说明这些路径的关系：{', '.join(missing)}")
        return self


class ReportLongTermQuestion(_ReportDraftModel):
    context: str = Field(min_length=30, max_length=500)
    question: str = Field(min_length=10, max_length=250)


class CareerBlueprintDraft(_ReportDraftModel):
    portrait: ReportPortrait
    strengthsAndRisks: ReportStrengthsAndRisks
    diagnosis: ReportDiagnosis
    sixMonthActions: list[ReportAction] = Field(min_length=3, max_length=5)
    reviewQuestions: list[QuestionText] = Field(min_length=5, max_length=7)
    longTermQuestion: ReportLongTermQuestion

    @model_validator(mode="after")
    def require_distinct_review_questions(self):
        normalized = {"".join(question.split()) for question in self.reviewQuestions}
        if len(normalized) != len(self.reviewQuestions):
            raise ValueError("reviewQuestions 不能包含重复问题")
        return self

    @model_validator(mode="after")
    def require_action_coverage_for_all_plans(self):
        covered_plans = {
            plan_id
            for action in self.sixMonthActions
            for plan_id in action.validatesPlans
        }
        if covered_plans != {"A", "B", "C"}:
            missing = sorted({"A", "B", "C"} - covered_plans)
            raise ValueError(f"六个月行动必须覆盖所有路径，缺少：{', '.join(missing)}")
        return self


class CareerBlueprintReport(BaseModel):
    id: str
    userId: str
    responseId: str
    profileId: str
    title: str
    content: str
    wordCount: int
    generationStatus: Literal["pending", "success", "failed"]
    qualityStatus: Literal["unchecked", "passed", "warning", "failed"]
    errorMessage: Optional[str] = None
    modelName: str
    promptVersion: str
    qualityRuleVersion: str = "legacy-rule-v1.0.0"
    inputSnapshot: dict[str, Any]
    retryCount: int
    createdAt: str
    updatedAt: str
    editedAt: Optional[str] = None
    editedBy: Optional[str] = None
    accountDisplayName: Optional[str] = None


class AdminReportUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)


class ReportFeedbackInput(BaseModel):
    understandingScore: int
    insightScore: int
    actionScore: int
    recommendScore: int
    comment: Optional[str] = None


class ReportFeedback(BaseModel):
    id: str
    reportId: str
    userId: str
    understandingScore: int
    insightScore: int
    actionScore: int
    recommendScore: int
    comment: Optional[str] = None
    createdAt: str
