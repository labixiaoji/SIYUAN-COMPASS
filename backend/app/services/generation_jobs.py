from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.assessment import AssessmentResponse, AssessmentResponseInput
from app.schemas.generation_job import GenerationJobStatus
from app.services.profile_analyzer import ProfileAnalysisError, analyze_career_profile
from app.services.report_generator import ReportGenerationError, generate_report
from app.storage.json_db import (
    find_generation_job,
    find_user,
    save_assessment_progress,
    save_generation_job,
    save_report,
)

ACTIVE_TASKS: set[asyncio.Task[None]] = set()


def _set_job(job_id: str, **updates: object) -> None:
    current = find_generation_job(job_id)
    if not current:
        raise RuntimeError("生成任务不存在")
    save_generation_job(current.model_copy(update=updates))


def create_generation_job(user_id: str) -> GenerationJobStatus:
    job_id = str(uuid4())
    job = GenerationJobStatus(
        jobId=job_id,
        status="queued",
        stage="queued",
        progress=5,
        message="问卷已接收，等待开始分析。",
        userId=user_id,
    )
    save_generation_job(job)
    return job


def get_generation_job(job_id: str) -> GenerationJobStatus | None:
    return find_generation_job(job_id)


def start_generation_job(job_id: str, input_data: AssessmentResponseInput) -> None:
    task = asyncio.create_task(run_generation_job(job_id, input_data))
    ACTIVE_TASKS.add(task)
    task.add_done_callback(ACTIVE_TASKS.discard)


async def run_generation_job(job_id: str, input_data: AssessmentResponseInput) -> None:
    try:
        _set_job(
            job_id,
            status="running",
            stage="preparing",
            progress=10,
            message="正在整理问卷答案和生成任务。",
        )

        user = find_user(input_data.userId or "")
        if not user:
            raise RuntimeError("登录用户不存在")
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
        _set_job(job_id, userId=user["id"], responseId=response.id)

        def profile_progress(stage: str, progress: int, message: str) -> None:
            _set_job(job_id, stage=stage, progress=progress, message=message)

        try:
            profile = await analyze_career_profile(response, progress_callback=profile_progress)
        except ProfileAnalysisError as error:
            _set_job(
                job_id,
                status="failed",
                stage="profile_failed",
                message="用户画像生成失败。",
                error=str(error),
            )
            return

        _set_job(
            job_id,
            profileId=profile.id,
            stage="profile_complete",
            progress=55,
            message="结构化用户画像已生成，正在准备生涯报告。",
        )
        save_assessment_progress(response, profile)

        def report_progress(stage: str, progress: int, message: str) -> None:
            _set_job(job_id, stage=stage, progress=progress, message=message)

        try:
            report = await generate_report(response, profile, progress_callback=report_progress)
        except ReportGenerationError as error:
            _set_job(
                job_id,
                status="failed",
                stage="report_failed",
                message="生涯报告生成失败。",
                error=str(error),
            )
            return

        _set_job(
            job_id,
            stage="saving",
            progress=95,
            message="报告已通过校验，正在保存结果。",
        )
        save_report(report)
        _set_job(
            job_id,
            status="success",
            stage="completed",
            progress=100,
            message="生涯报告生成完成。",
            reportId=report.id,
            generationStatus=report.generationStatus,
        )
    except Exception as error:
        _set_job(
            job_id,
            status="failed",
            stage="failed",
            message="生成流程发生异常。",
            error=str(error),
        )
