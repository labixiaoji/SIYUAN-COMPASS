from __future__ import annotations

import asyncio
import logging
import re
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from app.core.config import get_settings
from app.core.data_privacy import redact_obvious_contact_details
from app.llm.errors import LLMProviderError
from app.llm.provider import LLMCallStats
from app.schemas.assessment import AssessmentResponse, AssessmentResponseInput
from app.schemas.generation_job import GenerationFailure, GenerationJobStatus
from app.services.assessment_validator import validate_assessment_fields, validate_raw_assessment_fields
from app.services.profile_analyzer import ProfileAnalysisError, analyze_career_profile
from app.services.report_generator import ReportGenerationError, generate_report
from app.storage.json_db import (
    GenerationQuotaStorageError,
    cancel_generation_job_record,
    claim_next_generation_job,
    claim_generation_job,
    delete_expired_generation_jobs,
    find_generation_job,
    find_profile,
    find_report,
    find_response,
    find_response_owner,
    find_user,
    generation_job_retry_delay,
    load_generation_job_input,
    renew_generation_job_lease,
    requeue_generation_job_claim,
    save_assessment_progress,
    save_generation_job_if_user_idle,
    save_report,
    update_generation_job_conditionally,
)

ACTIVE_TASKS: dict[str, asyncio.Task[None]] = {}
ACTIVE_TASK_LOOPS: dict[str, asyncio.AbstractEventLoop] = {}
WORKER_TASKS: dict[str, asyncio.Task[None]] = {}
WORKER_CLAIMS: dict[str, str] = {}
WORKER_WAKE_EVENT: asyncio.Event | None = None
WORKER_STOP_EVENT: asyncio.Event | None = None
logger = logging.getLogger(__name__)


class ActiveGenerationJobError(RuntimeError):
    def __init__(self, active_job: GenerationJobStatus) -> None:
        self.active_job = active_job
        super().__init__("该账号已有报告正在生成中")


class GenerationQuotaExceededError(RuntimeError):
    def __init__(self, *, limit: int, used: int) -> None:
        self.limit = limit
        self.used = used
        super().__init__(f"今日报告生成次数已用完（{used}/{limit}）")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _failure_stage(stage: str) -> str:
    normalized = (stage or "").lower()
    if normalized.startswith("validation"):
        return "validation"
    if normalized.startswith("profile"):
        return "profile"
    if normalized.startswith("report"):
        return "report"
    if normalized in {"saving", "persistence"}:
        return "persistence"
    return "unknown"


def _failure_detail(error: BaseException) -> str:
    detail = str(error).strip() or "未提供具体错误信息"
    # Error strings can contain provider payload fragments or accidental
    # contact details. Keep the administrator diagnostic useful but bounded.
    detail = re.sub(
        r"(?i)(api[-_ ]?key|authorization|password|passwd|secret|token)(?:['\"]?\s*[:=]\s*['\"]?)[^,;\s'\"}]+",
        r"\1=[已隐藏]",
        detail,
    )
    detail = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [已隐藏]", detail)
    detail = redact_obvious_contact_details(detail)
    return detail[:600]


def _find_llm_error(error: BaseException) -> LLMProviderError | None:
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, LLMProviderError):
            return current
        current = current.__cause__ or current.__context__
    return None


def _failure_code(stage: str, error: BaseException) -> tuple[str, bool]:
    llm_error = _find_llm_error(error)
    normalized = f"{error} {error.__cause__ or ''}".lower()
    prefix = _failure_stage(stage).upper()
    if llm_error:
        if llm_error.kind == "timeout":
            return f"{prefix}_MODEL_TIMEOUT", True
        if llm_error.kind in {"authentication", "permission"}:
            return f"{prefix}_MODEL_AUTH", False
        if llm_error.kind == "rate_limit":
            return f"{prefix}_MODEL_QUOTA", True
        if llm_error.kind in {"server", "network"}:
            return f"{prefix}_MODEL_UNAVAILABLE", True
        if llm_error.kind == "invalid_request":
            return f"{prefix}_MODEL_REQUEST_INVALID", False
        if llm_error.kind == "empty_response":
            return f"{prefix}_MODEL_EMPTY_RESPONSE", False
    if prefix == "VALIDATION":
        return "ASSESSMENT_SCHEMA_INVALID", False
    if any(item in normalized for item in ("timeout", "timed out", "超时")):
        return f"{prefix}_MODEL_TIMEOUT", True
    # Quality-gate messages commonly contain “缺少关键内容”；classify the
    # explicit quality failure before falling back to authentication keywords.
    if "质量" in normalized:
        return f"{prefix}_QUALITY_FAILED", False
    if any(item in normalized for item in ("401", "403", "api_key", "api key", "未配置")):
        return f"{prefix}_MODEL_AUTH", False
    if any(item in normalized for item in ("429", "quota", "rate limit", "限流", "额度")):
        return f"{prefix}_MODEL_QUOTA", True
    if any(item in normalized for item in ("json", "schema", "校验", "结构")):
        return f"{prefix}_SCHEMA_INVALID", False
    if prefix == "PERSISTENCE":
        return "PERSISTENCE_ERROR", True
    return f"{prefix}_INTERNAL_ERROR", False


def build_generation_failure(job_id: str, stage: str, error: BaseException) -> GenerationFailure:
    code, retryable = _failure_code(stage, error)
    try:
        settings = get_settings()
        provider = (getattr(settings, "llm_provider", "") or "").strip().lower() or None
    except Exception:
        provider = None
    llm_error = _find_llm_error(error)
    status_match = re.search(r"\b([45]\d{2})\b", str(error))
    return GenerationFailure(
        code=code,
        stage=_failure_stage(stage),
        message=_failure_detail(error),
        retryable=retryable,
        provider=provider,
        providerStatus=(
            llm_error.status_code
            if llm_error and llm_error.status_code is not None
            else int(status_match.group(1)) if status_match else None
        ),
        traceId=job_id,
        occurredAt=now_iso(),
    )


def _failure_updates(job_id: str, stage: str, error: BaseException) -> dict[str, object]:
    failure = build_generation_failure(job_id, stage, error)
    logger.warning(
        "generation job failed job_id=%s stage=%s code=%s retryable=%s provider=%s provider_status=%s detail=%s",
        job_id,
        failure.stage,
        failure.code,
        failure.retryable,
        failure.provider or "unknown",
        failure.providerStatus or "unknown",
        failure.message,
    )
    return {
        "error": failure.message,
        "failure": failure.model_dump(mode="json"),
    }


def _validation_failure_updates(
    job_id: str,
    field_errors: dict[str, str],
) -> dict[str, object]:
    missing_fields = sorted(field_errors)
    message = "问卷信息不完整，请补充后重新提交。"
    failure = GenerationFailure(
        code="ASSESSMENT_INCOMPLETE",
        stage="validation",
        message=message,
        retryable=False,
        traceId=job_id,
        occurredAt=now_iso(),
        missingFields=missing_fields,
    )
    logger.info(
        "generation job rejected before model call job_id=%s code=%s missing_fields=%s",
        job_id,
        failure.code,
        ",".join(missing_fields),
    )
    return {
        "error": message,
        "failure": failure.model_dump(mode="json"),
        "missingFields": missing_fields,
    }


def _llm_stats_updates(stats: LLMCallStats) -> dict[str, object]:
    return {
        "llmRequestAttempts": stats.request_attempts,
        "llmRetryCount": stats.retry_count,
        "qualityRepairCount": stats.quality_repair_count,
        "lastAttemptKind": stats.last_attempt_kind,
    }


def create_generation_job(
    user_id: str,
    input_data: AssessmentResponseInput,
) -> GenerationJobStatus:
    job_id = str(uuid4())
    now = now_iso()
    settings = get_settings()
    worker_count = max(int(getattr(settings, "generation_worker_count", 3)), 1)
    job = GenerationJobStatus(
        jobId=job_id,
        status="queued",
        stage="queued",
        progress=5,
        message=f"问卷已接收，等待开始分析（系统最多同时生成{worker_count}份报告）。",
        maxConcurrentReports=worker_count,
        userId=user_id,
        createdAt=now,
        updatedAt=now,
    )
    quota_timezone = ZoneInfo(settings.report_generation_quota_timezone)
    quota_now = datetime.now(quota_timezone)
    quota_since = quota_now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ).astimezone(timezone.utc)
    # Keep omitted backwards-compatible defaults absent from the durable
    # snapshot.  The worker must be able to distinguish an explicit answer
    # from Pydantic having filled a missing field before the queue was written.
    input_snapshot = input_data.model_dump(mode="json")
    for field_name in ("preferredWorkStyle", "longTermPersistence"):
        if field_name not in input_data.model_fields_set:
            input_snapshot.pop(field_name, None)
    try:
        active_job = save_generation_job_if_user_idle(
            job,
            input_data=input_snapshot,
            daily_limit=max(settings.report_generation_daily_limit, 0),
            quota_day=quota_now.date(),
            quota_since=quota_since,
            retention_days=settings.generation_job_retention_days,
        )
    except GenerationQuotaStorageError as error:
        raise GenerationQuotaExceededError(limit=error.limit, used=error.used) from error
    if active_job:
        raise ActiveGenerationJobError(active_job)
    return job


def get_generation_job(job_id: str) -> GenerationJobStatus | None:
    return find_generation_job(job_id)


async def wait_for_generation_job(
    job_id: str,
    *,
    timeout_seconds: float | None = None,
) -> GenerationJobStatus | None:
    """Wait for a durable job transition without owning or cancelling its worker."""

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds if timeout_seconds is not None else None
    while True:
        job = find_generation_job(job_id)
        if not job or job.status in {"success", "failed", "cancelled"}:
            return job
        if deadline is not None:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return job
            await asyncio.sleep(min(0.25, remaining))
        else:
            await asyncio.sleep(0.25)


def _task_finished(job_id: str, task: asyncio.Task[None]) -> None:
    if ACTIVE_TASKS.get(job_id) is task:
        ACTIVE_TASKS.pop(job_id, None)
        ACTIVE_TASK_LOOPS.pop(job_id, None)


def _alive_worker_tasks() -> list[asyncio.Task[None]]:
    return [task for task in WORKER_TASKS.values() if not task.done()]


def wake_generation_workers() -> None:
    if WORKER_WAKE_EVENT is not None:
        WORKER_WAKE_EVENT.set()


def start_generation_job(_job_id: str) -> None:
    """Compatibility entry point: enqueueing only wakes the fixed workers."""

    if not _alive_worker_tasks():
        try:
            start_generation_workers()
        except RuntimeError:
            # Calls made outside an event loop are harmless; application
            # startup will create the workers once the loop is available.
            return
    wake_generation_workers()


def recover_generation_jobs() -> int:
    """Start a fixed worker pool; queued and expired jobs remain database-owned."""
    settings = get_settings()
    delete_expired_generation_jobs(settings.generation_job_retention_days)
    return start_generation_workers()


def start_generation_workers() -> int:
    global WORKER_WAKE_EVENT, WORKER_STOP_EVENT
    loop = asyncio.get_running_loop()
    worker_count = max(int(getattr(get_settings(), "generation_worker_count", 3)), 1)
    if WORKER_WAKE_EVENT is None or WORKER_STOP_EVENT is None or WORKER_STOP_EVENT.is_set():
        WORKER_WAKE_EVENT = asyncio.Event()
        WORKER_STOP_EVENT = asyncio.Event()
    for index in range(worker_count):
        worker_id = f"generation-worker-{index + 1}"
        existing = WORKER_TASKS.get(worker_id)
        if existing and not existing.done():
            continue
        task = loop.create_task(
            _generation_worker_loop(worker_id, WORKER_STOP_EVENT),
            name=worker_id,
        )
        WORKER_TASKS[worker_id] = task
    return worker_count


async def stop_generation_workers() -> None:
    global WORKER_WAKE_EVENT, WORKER_STOP_EVENT
    stop_event = WORKER_STOP_EVENT
    tasks = list(WORKER_TASKS.values())
    if stop_event is None and not tasks:
        return
    if stop_event is not None:
        stop_event.set()
    wake_generation_workers()
    for task in tasks:
        if not task.done():
            task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    for job_id, claim_token in list(WORKER_CLAIMS.items()):
        try:
            requeue_generation_job_claim(job_id, claim_token)
        except Exception:
            logger.exception("failed to release worker claim during shutdown job_id=%s", job_id)

    for job_id in list(ACTIVE_TASKS):
        ACTIVE_TASKS.pop(job_id, None)
        ACTIVE_TASK_LOOPS.pop(job_id, None)
    WORKER_CLAIMS.clear()
    WORKER_TASKS.clear()
    WORKER_WAKE_EVENT = None
    WORKER_STOP_EVENT = None


def cancel_generation_job(job_id: str) -> GenerationJobStatus | None:
    current = find_generation_job(job_id)
    if not current:
        return None
    if current.status not in {"queued", "running"}:
        return current

    cancelled = cancel_generation_job_record(job_id)
    if not cancelled:
        return find_generation_job(job_id)

    task = ACTIVE_TASKS.get(job_id)
    loop = ACTIVE_TASK_LOOPS.get(job_id)
    if task and loop and not task.done():
        loop.call_soon_threadsafe(task.cancel)
    return cancelled


async def _claim_when_available(job_id: str, claim_token: str) -> GenerationJobStatus | None:
    settings = get_settings()
    while True:
        claimed = claim_generation_job(
            job_id,
            claim_token=claim_token,
            lease_seconds=settings.generation_job_lease_seconds,
        )
        if claimed:
            return claimed
        retry_after = generation_job_retry_delay(
            job_id,
            settings.generation_job_lease_seconds,
        )
        if retry_after is None:
            return None
        await asyncio.sleep(
            min(
                retry_after + 0.05,
                max(settings.generation_job_heartbeat_seconds, 1),
            )
        )


async def _wait_for_generation_work() -> None:
    event = WORKER_WAKE_EVENT
    if event is None:
        await asyncio.sleep(1)
        return
    try:
        await asyncio.wait_for(event.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        return
    finally:
        if event.is_set():
            event.clear()


async def _heartbeat(job_id: str, claim_token: str) -> None:
    settings = get_settings()
    interval = max(
        1,
        min(settings.generation_job_heartbeat_seconds, settings.generation_job_lease_seconds // 2),
    )
    while True:
        await asyncio.sleep(interval)
        if not renew_generation_job_lease(
            job_id,
            claim_token,
            settings.generation_job_lease_seconds,
        ):
            return


def _update_running_job(
    job_id: str,
    claim_token: str,
    *,
    terminal: bool = False,
    **updates: Any,
) -> GenerationJobStatus | None:
    preserve_input = updates.get("status") in {"failed", "cancelled"}
    return update_generation_job_conditionally(
        job_id,
        dict(updates),
        expected_statuses=("running",),
        claim_token=claim_token,
        clear_private_state=terminal and not preserve_input,
        clear_input_data=terminal and not preserve_input,
        release_claim=terminal,
    )


def _require_job_update(
    job_id: str,
    claim_token: str,
    **updates: Any,
) -> GenerationJobStatus:
    updated = _update_running_job(job_id, claim_token, **updates)
    if not updated:
        raise asyncio.CancelledError
    return updated


def _response_matches(response: AssessmentResponse | None, user_id: str, response_id: str) -> bool:
    return bool(
        response
        and response.id == response_id
        and response.userId == user_id
    )


def _profile_matches(profile, user_id: str, response_id: str, profile_id: str) -> bool:
    return bool(
        profile
        and profile.id == profile_id
        and profile.userId == user_id
        and profile.responseId == response_id
    )


def _report_matches(report, user_id: str, response_id: str, profile_id: str) -> bool:
    return bool(
        report
        and report.id
        and report.generationStatus == "success"
        # Legacy test/storage adapters may omit relational fields; real report
        # rows always contain them and mismatches are never accepted.
        and (getattr(report, "userId", user_id) == user_id)
        and (getattr(report, "responseId", response_id) == response_id)
        and (getattr(report, "profileId", profile_id) == profile_id)
    )


async def _run_claimed_generation_job(
    claimed: GenerationJobStatus,
    claim_token: str,
) -> None:
    job_id = claimed.jobId
    heartbeat: asyncio.Task[None] | None = None
    stats = LLMCallStats(
        request_attempts=claimed.llmRequestAttempts,
        retry_count=claimed.llmRetryCount,
        quality_repair_count=claimed.qualityRepairCount,
        last_attempt_kind=claimed.lastAttemptKind,
    )
    try:
        heartbeat = asyncio.create_task(_heartbeat(job_id, claim_token))

        user_id = claimed.userId or ""

        # A crash can happen after the report transaction commits but before the
        # final job transition. Reuse that committed result instead of generating
        # a second report/version.
        if claimed.reportId:
            saved_report = find_report(claimed.reportId)
            if saved_report is not None and _report_matches(
                saved_report,
                user_id,
                claimed.responseId or getattr(saved_report, "responseId", "") or "",
                claimed.profileId or getattr(saved_report, "profileId", "") or "",
            ):
                _update_running_job(
                    job_id,
                    claim_token,
                    terminal=True,
                    status="success",
                    stage="completed",
                    progress=100,
                    message="生涯报告生成完成。",
                    reportId=saved_report.id,
                    responseId=getattr(saved_report, "responseId", claimed.responseId),
                    profileId=getattr(saved_report, "profileId", claimed.profileId),
                    generationStatus=saved_report.generationStatus,
                    error=None,
                    failure=None,
                    **_llm_stats_updates(stats),
                )
                return

        user = find_user(user_id)
        if not user:
            raise RuntimeError("登录用户不存在")

        raw_input = load_generation_job_input(job_id)
        if raw_input is None:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="failed",
                message="生成任务缺少问卷数据。",
                **_failure_updates(job_id, "persistence", RuntimeError("generation job input is missing")),
            )
            return

        raw_errors = validate_raw_assessment_fields(raw_input)
        if raw_errors:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="validation_failed",
                message="问卷信息不完整，请补充后重新提交。",
                **_validation_failure_updates(job_id, raw_errors),
            )
            return
        try:
            input_data = AssessmentResponseInput.model_validate(raw_input)
        except ValidationError as error:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="validation_failed",
                message="问卷答案格式不正确，请修改后重新提交。",
                **_failure_updates(job_id, "validation", error),
            )
            return
        typed_errors = validate_assessment_fields(input_data)
        if typed_errors:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="validation_failed",
                message="问卷信息不完整，请补充后重新提交。",
                **_validation_failure_updates(job_id, typed_errors),
            )
            return

        response = None
        response_id = str(uuid4())
        if claimed.responseId:
            existing_response = find_response(claimed.responseId)
            if _response_matches(existing_response, user_id, claimed.responseId):
                response = existing_response
            elif existing_response is None and find_response_owner(claimed.responseId) is None:
                # A checkpoint may have been persisted before the response
                # transaction committed. Reusing the task pointer is safe
                # only when no relational row exists; a foreign or incomplete
                # row gets a fresh UUID below.
                response_id = claimed.responseId
        if response is None:
            now = now_iso()
            payload = input_data.model_dump()
            payload.pop("userId", None)
            response = AssessmentResponse(
                **payload,
                # Only reuse a checkpoint ID after the relational ownership
                # check above. A foreign ID must never reach an upsert.
                id=response_id,
                userId=user_id,
                submittedAt=now,
                createdAt=now,
            )
        _require_job_update(
            job_id,
            claim_token,
            userId=user_id,
            responseId=response.id,
            **_llm_stats_updates(stats),
        )

        def profile_progress(stage: str, progress: int, message: str) -> None:
            _require_job_update(
                job_id,
                claim_token,
                stage=stage,
                progress=progress,
                message=message,
                **_llm_stats_updates(stats),
            )

        try:
            profile = None
            if claimed.profileId:
                existing_profile = find_profile(claimed.profileId)
                if _profile_matches(existing_profile, user_id, response.id, claimed.profileId):
                    profile = existing_profile
            if profile is None:
                profile = await analyze_career_profile(
                    response,
                    progress_callback=profile_progress,
                    llm_stats=stats,
                )
        except ProfileAnalysisError as error:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="profile_failed",
                message="用户画像生成失败。",
                **_failure_updates(job_id, "profile", error),
                **_llm_stats_updates(stats),
            )
            return

        _require_job_update(
            job_id,
            claim_token,
            profileId=profile.id,
            stage="profile_complete",
            progress=55,
            message="结构化用户画像已生成，正在准备生涯报告。",
            **_llm_stats_updates(stats),
        )
        if not save_assessment_progress(
            response,
            profile,
            generation_job_id=job_id,
            claim_token=claim_token,
        ):
            raise asyncio.CancelledError

        def report_progress(stage: str, progress: int, message: str) -> None:
            _require_job_update(
                job_id,
                claim_token,
                stage=stage,
                progress=progress,
                message=message,
                **_llm_stats_updates(stats),
            )

        saved_report = find_report(claimed.reportId) if claimed.reportId else None
        if not _report_matches(saved_report, user_id, response.id, profile.id):
            saved_report = None
        if saved_report:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="success",
                stage="completed",
                progress=100,
                message="生涯报告生成完成。",
                responseId=response.id,
                profileId=profile.id,
                reportId=saved_report.id,
                generationStatus=saved_report.generationStatus,
                error=None,
                failure=None,
                **_llm_stats_updates(stats),
            )
            return

        try:
            report = await generate_report(
                response,
                profile,
                progress_callback=report_progress,
                llm_stats=stats,
            )
        except ReportGenerationError as error:
            _update_running_job(
                job_id,
                claim_token,
                terminal=True,
                status="failed",
                stage="report_failed",
                message="生涯报告生成失败。",
                **_failure_updates(job_id, "report", error),
                **_llm_stats_updates(stats),
            )
            return

        if claimed.reportId and not find_report(claimed.reportId):
            report.id = claimed.reportId
        _require_job_update(
            job_id,
            claim_token,
            stage="saving",
            progress=95,
            message="报告已通过校验，正在保存结果。",
            reportId=report.id,
            **_llm_stats_updates(stats),
        )
        if not save_report(
            report,
            generation_job_id=job_id,
            claim_token=claim_token,
        ):
            raise asyncio.CancelledError
        _update_running_job(
            job_id,
            claim_token,
            terminal=True,
            status="success",
            stage="completed",
            progress=100,
            message="生涯报告生成完成。",
            reportId=report.id,
            responseId=response.id,
            profileId=profile.id,
            generationStatus=report.generationStatus,
            error=None,
            failure=None,
            **_llm_stats_updates(stats),
        )
    except asyncio.CancelledError:
        # User cancellation already made a conditional terminal transition.
        # Process shutdown leaves the lease in place so another worker can recover it.
        raise
    except Exception as error:
        _update_running_job(
            job_id,
            claim_token,
            terminal=True,
            status="failed",
            stage="failed",
            message="生成流程发生异常。",
            **_failure_updates(job_id, "unknown", error),
            **_llm_stats_updates(stats),
        )
    finally:
        if heartbeat:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat


async def run_generation_job(job_id: str) -> None:
    """Compatibility runner for callers/tests; production uses fixed workers."""

    claim_token = str(uuid4())
    claimed = await _claim_when_available(job_id, claim_token)
    if not claimed:
        return
    await _run_claimed_generation_job(claimed, claim_token)


async def _generation_worker_loop(
    worker_id: str,
    stop_event: asyncio.Event,
) -> None:
    settings = get_settings()
    while not stop_event.is_set():
        claim_token = str(uuid4())
        try:
            claimed = claim_next_generation_job(
                claim_token=claim_token,
                lease_seconds=settings.generation_job_lease_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("generation worker failed to claim a job worker=%s", worker_id)
            await asyncio.sleep(1)
            continue

        if not claimed:
            await _wait_for_generation_work()
            continue

        job_id = claimed.jobId
        WORKER_CLAIMS[job_id] = claim_token
        task = asyncio.create_task(
            _run_claimed_generation_job(claimed, claim_token),
            name=f"generation-job-{job_id}",
        )
        ACTIVE_TASKS[job_id] = task
        ACTIVE_TASK_LOOPS[job_id] = asyncio.get_running_loop()
        try:
            await task
        except asyncio.CancelledError:
            if stop_event.is_set():
                raise
            logger.info("generation job task cancelled job_id=%s", job_id)
        except Exception:
            # The job runner normally records its own failure. Keep the fixed
            # worker alive even if a storage/cleanup error escapes that path;
            # the lease will make the claim recoverable after it expires.
            logger.exception("generation worker job crashed worker=%s job_id=%s", worker_id, job_id)
        finally:
            if ACTIVE_TASKS.get(job_id) is task:
                ACTIVE_TASKS.pop(job_id, None)
                ACTIVE_TASK_LOOPS.pop(job_id, None)
            if not stop_event.is_set() and WORKER_CLAIMS.get(job_id) == claim_token:
                WORKER_CLAIMS.pop(job_id, None)
