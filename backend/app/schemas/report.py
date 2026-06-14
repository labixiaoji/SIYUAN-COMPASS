from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

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
    inputSnapshot: dict[str, Any]
    retryCount: int
    createdAt: str
    updatedAt: str
    editedAt: Optional[str] = None
    editedBy: Optional[str] = None


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
