from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.assessment import AssessmentResponse, AssessmentResponseInput, AssessmentSubmitResult
from app.schemas.generation_job import GenerationJobCreated, GenerationJobStatus
from app.services.assessment_validator import validate_assessment_fields
from app.services.auth import require_user
from app.services.generation_jobs import (
    ActiveGenerationJobError,
    cancel_generation_job,
    create_generation_job,
    get_generation_job,
    start_generation_job,
)
from app.services.profile_analyzer import ProfileAnalysisError, analyze_career_profile
from app.services.report_generator import ReportGenerationError, generate_report
from app.storage.json_db import save_assessment_progress, save_report

router = APIRouter(tags=["assessments"])


@router.post("/assessment-jobs", response_model=GenerationJobCreated)
async def create_assessment_job(
    input_data: AssessmentResponseInput,
    user=Depends(require_user),
) -> GenerationJobCreated:
    field_errors = validate_assessment_fields(input_data)
    if field_errors:
        raise HTTPException(
            status_code=400,
            detail={"errors": list(field_errors.values()), "fieldErrors": field_errors},
        )

    authenticated_input = input_data.model_copy(update={"userId": user["id"]})
    try:
        job = create_generation_job(user["id"])
    except ActiveGenerationJobError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "该账号已有报告正在生成中，请等待当前任务完成后再提交。",
                "jobId": error.active_job.jobId,
                "status": error.active_job.status,
                "stage": error.active_job.stage,
            },
        ) from error
    start_generation_job(job.jobId, authenticated_input)
    return GenerationJobCreated(jobId=job.jobId, status="queued")


@router.get("/assessment-jobs/{job_id}", response_model=GenerationJobStatus)
def get_assessment_job(job_id: str, user=Depends(require_user)) -> GenerationJobStatus:
    job = get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "生成任务不存在或已过期"})
    if user["role"] != "admin" and job.userId != user["id"]:
        raise HTTPException(status_code=403, detail={"error": "无权查看该生成任务"})
    return job


@router.post("/assessment-jobs/{job_id}/cancel", response_model=GenerationJobStatus)
def cancel_assessment_job(job_id: str, user=Depends(require_user)) -> GenerationJobStatus:
    job = get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": "生成任务不存在或已过期"})
    if user["role"] != "admin" and job.userId != user["id"]:
        raise HTTPException(status_code=403, detail={"error": "无权取消该生成任务"})
    if job.status not in {"queued", "running"}:
        return job

    cancelled_job = cancel_generation_job(job_id)
    if not cancelled_job:
        raise HTTPException(status_code=404, detail={"error": "生成任务不存在或已过期"})
    return cancelled_job


@router.post("/assessments", response_model=AssessmentSubmitResult)
async def submit_assessment(
    input_data: AssessmentResponseInput,
    user=Depends(require_user),
) -> AssessmentSubmitResult:
    field_errors = validate_assessment_fields(input_data)
    if field_errors:
        raise HTTPException(
            status_code=400,
            detail={"errors": list(field_errors.values()), "fieldErrors": field_errors},
        )

    now = datetime.now(timezone.utc).isoformat()
    payload = input_data.model_dump()
    payload.pop("userId", None)
    response = AssessmentResponse(
        **payload,
        id=str(uuid4()),
        userId=user["id"],
        submittedAt=now,
        createdAt=now,
    )

    try:
        profile = await analyze_career_profile(response)
    except ProfileAnalysisError as error:
        raise HTTPException(
            status_code=502,
            detail={"stage": "用户画像生成失败", "error": str(error)},
        ) from error
    save_assessment_progress(response, profile)

    try:
        report = await generate_report(response, profile)
    except ReportGenerationError as error:
        raise HTTPException(
            status_code=502,
            detail={"stage": "生涯报告生成失败", "error": str(error)},
        ) from error
    save_report(report)

    return AssessmentSubmitResult(
        userId=user["id"],
        responseId=response.id,
        profileId=profile.id,
        reportId=report.id,
        generationStatus=report.generationStatus,
    )
