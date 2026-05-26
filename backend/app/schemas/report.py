from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile


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
    inputSnapshot: dict[str, Union[AssessmentResponse, CareerProfile]]
    retryCount: int
    createdAt: str
    updatedAt: str


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
