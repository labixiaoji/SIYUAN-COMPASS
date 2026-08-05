from fastapi import APIRouter, Depends, HTTPException

from app.schemas.assessment import AssessmentResponseInput, AssessmentSubmitResult
from app.schemas.generation_job import GenerationJobCreated, GenerationJobStatus
from app.services.assessment_validator import validate_assessment_fields
from app.services.auth import require_user
from app.services.generation_jobs import (
    ActiveGenerationJobError,
    GenerationQuotaExceededError,
    cancel_generation_job,
    create_generation_job,
    get_generation_job,
    run_generation_job,
    start_generation_job,
)

router = APIRouter(tags=["assessments"])


def _reserve_job(user_id: str, input_data: AssessmentResponseInput) -> GenerationJobStatus:
    try:
        return create_generation_job(user_id, input_data)
    except ActiveGenerationJobError as error:
        # Polling/new submissions also wake a task whose former worker lost its
        # lease without requiring a full application restart.
        start_generation_job(error.active_job.jobId)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "该账号已有报告正在生成中，请等待当前任务完成后再提交。",
                "jobId": error.active_job.jobId,
                "status": error.active_job.status,
                "stage": error.active_job.stage,
            },
        ) from error
    except GenerationQuotaExceededError as error:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "今日报告生成次数已用完，请明日再试。",
                "limit": error.limit,
                "used": error.used,
            },
        ) from error


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
    job = _reserve_job(user["id"], authenticated_input)
    start_generation_job(job.jobId)
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

    authenticated_input = input_data.model_copy(update={"userId": user["id"]})
    job = _reserve_job(user["id"], authenticated_input)
    await run_generation_job(job.jobId)
    completed = get_generation_job(job.jobId)
    if not completed:
        raise HTTPException(status_code=500, detail={"error": "生成任务状态丢失"})
    if completed.status != "success":
        status_code = 409 if completed.status == "cancelled" else 502
        raise HTTPException(
            status_code=status_code,
            detail={
                "stage": completed.stage,
                "error": completed.error or completed.message,
                "jobId": completed.jobId,
            },
        )
    if not completed.responseId or not completed.profileId or not completed.reportId:
        raise HTTPException(status_code=500, detail={"error": "生成任务结果不完整"})

    return AssessmentSubmitResult(
        userId=user["id"],
        responseId=completed.responseId,
        profileId=completed.profileId,
        reportId=completed.reportId,
        generationStatus=completed.generationStatus or "success",
    )
