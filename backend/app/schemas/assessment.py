from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AbilityScores(BaseModel):
    logic: int = Field(ge=1, le=5)
    expression: int = Field(ge=1, le=5)
    spatialDesign: int = Field(ge=1, le=5)
    interpersonal: int = Field(ge=1, le=5)


class InterestScores(BaseModel):
    handsOn: int = Field(ge=1, le=5)
    research: int = Field(ge=1, le=5)
    creation: int = Field(ge=1, le=5)
    helping: int = Field(ge=1, le=5)
    leadership: int = Field(ge=1, le=5)
    detail: int = Field(ge=1, le=5)


class AssessmentResponseInput(BaseModel):
    grade: str
    collegeMajor: str
    hometown: Optional[str] = None
    preferredCity: str
    careerConfusions: list[str]
    mainConfusionText: Optional[str] = None
    educationPath: str
    educationPathReasons: list[str]
    educationCertainty: int = Field(ge=1, le=5)
    phdIntention: str
    phdReasons: list[str] = Field(default_factory=list)
    fiveYearPriorities: list[str]
    targetIndustries: list[str]
    futureRoleType: str
    lifePreference: str
    tenYearSelfDescription: Optional[str] = None
    topValuesRanked: list[str]
    abilityScores: AbilityScores
    interestScores: InterestScores
    currentPreparations: list[str]
    missingResources: list[str]
    majorOutcomeAwareness: str
    targetJobAwareness: str
    healthEnergyStatus: str
    exerciseFrequency: Optional[str] = None
    userId: Optional[str] = None


class AssessmentResponse(AssessmentResponseInput):
    id: str
    userId: str
    submittedAt: str
    createdAt: str


class AssessmentSubmitResult(BaseModel):
    userId: str
    responseId: str
    profileId: str
    reportId: str
    generationStatus: str
