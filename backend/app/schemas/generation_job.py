from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class GenerationJobCreated(BaseModel):
    jobId: str
    status: Literal["queued"]
    maxConcurrentReports: int = Field(default=3, ge=1)


class GenerationFailure(BaseModel):
    """Safe, structured failure information for administrators.

    Provider responses and tracebacks are deliberately not part of this model;
    the task runner stores only a redacted diagnostic summary and a correlation
    id that can be matched with server logs.
    """

    code: str
    stage: str
    message: str
    retryable: bool = False
    provider: Optional[str] = None
    providerStatus: Optional[int] = None
    traceId: Optional[str] = None
    occurredAt: Optional[str] = None
    missingFields: list[str] = Field(default_factory=list)


class GenerationJobStatus(BaseModel):
    jobId: str
    status: Literal["queued", "running", "success", "failed", "cancelled"]
    stage: str
    progress: int = Field(ge=0, le=100)
    message: str
    maxConcurrentReports: int = Field(default=3, ge=1)
    userId: Optional[str] = None
    responseId: Optional[str] = None
    profileId: Optional[str] = None
    reportId: Optional[str] = None
    generationStatus: Optional[str] = None
    error: Optional[str] = None
    attempts: int = Field(default=0, ge=0)
    workerAttempts: int = Field(default=0, ge=0)
    llmRequestAttempts: int = Field(default=0, ge=0)
    llmRetryCount: int = Field(default=0, ge=0)
    qualityRepairCount: int = Field(default=0, ge=0)
    lastAttemptKind: Optional[str] = None
    failure: Optional[GenerationFailure] = None
    missingFields: list[str] = Field(default_factory=list)
    draftAvailable: bool = False
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class GenerationJobDraft(BaseModel):
    jobId: str
    answers: dict[str, Any]
    currentStep: int = Field(default=0, ge=0, le=6)
    version: int = Field(default=0, ge=0)
    source: Literal["cloud_draft", "job_input"]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
