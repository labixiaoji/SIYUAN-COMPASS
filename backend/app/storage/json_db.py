from __future__ import annotations

import json
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from app.schemas.assessment import AssessmentResponse
from app.schemas.generation_job import GenerationJobStatus
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintReport, ReportFeedback

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"

TABLE_FILES = {
    "users": DATA_DIR / "users.json",
    "assessment_responses": DATA_DIR / "assessment_responses.json",
    "assessment_scores": DATA_DIR / "assessment_scores.json",
    "assessment_choices": DATA_DIR / "assessment_choices.json",
    "career_profiles": DATA_DIR / "career_profiles.json",
    "reports": DATA_DIR / "reports.json",
    "report_versions": DATA_DIR / "report_versions.json",
    "generation_jobs": DATA_DIR / "generation_jobs.json",
    "report_feedback": DATA_DIR / "report_feedback.json",
    "admin_audit_logs": DATA_DIR / "admin_audit_logs.json",
}

ASSESSMENT_LIST_FIELDS = (
    "educationPathReasons",
    "topValuesRanked",
    "currentPreparations",
    "missingResources",
    "jobInfoChannels",
    "careerConfusions",
)

_LOCK = RLock()


def _synchronized(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with _LOCK:
            return function(*args, **kwargs)

    return wrapper


def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path in TABLE_FILES.values():
        if not path.exists():
            _write_path(path, [])


def _write_path(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _read_table(table: str) -> list[dict[str, Any]]:
    with _LOCK:
        ensure_storage()
        path = TABLE_FILES[table]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"数据文件格式错误：{path.name}") from error
        if not isinstance(data, list):
            raise RuntimeError(f"数据文件必须是 JSON 数组：{path.name}")
        return data


def _write_table(table: str, records: list[dict[str, Any]]) -> None:
    with _LOCK:
        ensure_storage()
        _write_path(TABLE_FILES[table], records)


def _upsert(items: list[dict[str, Any]], record: dict[str, Any], key: str = "id") -> None:
    index = next(
        (idx for idx, item in enumerate(items) if item.get(key) == record.get(key)),
        -1,
    )
    if index >= 0:
        items[index] = record
    else:
        items.append(record)


def _find_record(table: str, record_id: str, key: str = "id") -> dict[str, Any] | None:
    return next(
        (record for record in _read_table(table) if record.get(key) == record_id),
        None,
    )


@_synchronized
def get_or_create_user(user_id: str | None = None) -> dict[str, Any]:
    from app.services.report_generator import now_iso

    existing = find_user(user_id) if user_id else None
    if existing:
        return existing

    now = now_iso()
    user = {"id": user_id or str(uuid4()), "createdAt": now, "updatedAt": now}
    users = _read_table("users")
    users.append(user)
    _write_table("users", users)
    return user


def find_user(user_id: str) -> dict[str, Any] | None:
    return _find_record("users", user_id)


def find_user_by_username(username: str) -> dict[str, Any] | None:
    return next(
        (user for user in _read_table("users") if user.get("username") == username),
        None,
    )


@_synchronized
def create_account(
    *,
    username: str,
    display_name: str,
    password_hash: str,
    role: Literal["student", "admin"],
) -> dict[str, Any]:
    from app.services.report_generator import now_iso

    now = now_iso()
    user = {
        "id": str(uuid4()),
        "username": username,
        "displayName": display_name,
        "passwordHash": password_hash,
        "role": role,
        "createdAt": now,
        "updatedAt": now,
    }
    users = _read_table("users")
    users.append(user)
    _write_table("users", users)
    return user


@_synchronized
def ensure_admin_account() -> None:
    from app.core.config import get_settings
    from app.services.auth import hash_password, normalize_username

    settings = get_settings()
    username = normalize_username(settings.admin_username)
    if find_user_by_username(username):
        return
    create_account(
        username=username,
        display_name=settings.admin_display_name,
        password_hash=hash_password(settings.admin_password),
        role="admin",
    )


@_synchronized
def save_assessment_progress(response: AssessmentResponse, profile: CareerProfile) -> None:
    response_record = response.model_dump(mode="json")
    score_record = {
        "id": response.id,
        "assessmentId": response.id,
        "abilityScores": response_record.pop("abilityScores"),
        "interestScores": response_record.pop("interestScores"),
    }

    choice_records = []
    for question_code in ASSESSMENT_LIST_FIELDS:
        values = response_record.pop(question_code)
        choice_records.extend(
            {
                "id": f"{response.id}:{question_code}:{sort_order}",
                "assessmentId": response.id,
                "questionCode": question_code,
                "optionValue": value,
                "sortOrder": sort_order,
            }
            for sort_order, value in enumerate(values)
        )

    responses = _read_table("assessment_responses")
    scores = _read_table("assessment_scores")
    choices = [
        item
        for item in _read_table("assessment_choices")
        if item.get("assessmentId") != response.id
    ]
    profiles = _read_table("career_profiles")

    _upsert(responses, response_record)
    _upsert(scores, score_record)
    choices.extend(choice_records)
    _upsert(profiles, profile.model_dump(mode="json"))

    _write_table("assessment_responses", responses)
    _write_table("assessment_scores", scores)
    _write_table("assessment_choices", choices)
    _write_table("career_profiles", profiles)


def _report_storage_record(report: CareerBlueprintReport) -> dict[str, Any]:
    record = report.model_dump(mode="json")
    record.pop("inputSnapshot", None)
    return record


def _save_report_version(report: CareerBlueprintReport, source: str) -> None:
    versions = _read_table("report_versions")
    report_versions = [
        version for version in versions if version.get("reportId") == report.id
    ]
    versions.append(
        {
            "id": str(uuid4()),
            "reportId": report.id,
            "versionNumber": len(report_versions) + 1,
            "title": report.title,
            "content": report.content,
            "wordCount": report.wordCount,
            "qualityStatus": report.qualityStatus,
            "source": source,
            "createdAt": report.updatedAt,
            "createdBy": report.editedBy,
        }
    )
    _write_table("report_versions", versions)


@_synchronized
def save_report(report: CareerBlueprintReport) -> None:
    reports = _read_table("reports")
    _upsert(reports, _report_storage_record(report))
    _write_table("reports", reports)
    _save_report_version(report, "ai_generated")


def find_report(report_id: str) -> CareerBlueprintReport | None:
    record = _find_record("reports", report_id)
    if not record:
        return None

    response = find_response(record["responseId"])
    profile = find_profile(record["profileId"])
    record["inputSnapshot"] = {
        "response": response.model_dump(mode="json") if response else None,
        "profile": profile.model_dump(mode="json") if profile else None,
    }
    return CareerBlueprintReport.model_validate(record)


def find_response(response_id: str) -> AssessmentResponse | None:
    response = _find_record("assessment_responses", response_id)
    score = _find_record("assessment_scores", response_id, key="assessmentId")
    if not response or not score:
        return None

    choices = [
        choice
        for choice in _read_table("assessment_choices")
        if choice.get("assessmentId") == response_id
    ]
    payload = dict(response)
    payload["abilityScores"] = score["abilityScores"]
    payload["interestScores"] = score["interestScores"]
    for question_code in ASSESSMENT_LIST_FIELDS:
        payload[question_code] = [
            item["optionValue"]
            for item in sorted(
                (
                    choice
                    for choice in choices
                    if choice.get("questionCode") == question_code
                ),
                key=lambda item: item.get("sortOrder", 0),
            )
        ]
    return AssessmentResponse.model_validate(payload)


def find_profile(profile_id: str) -> CareerProfile | None:
    profile = _find_record("career_profiles", profile_id)
    return CareerProfile.model_validate(profile) if profile else None


@_synchronized
def update_profile(profile: CareerProfile) -> None:
    profiles = _read_table("career_profiles")
    if not any(item.get("id") == profile.id for item in profiles):
        return
    _upsert(profiles, profile.model_dump(mode="json"))
    _write_table("career_profiles", profiles)


@_synchronized
def update_report(report: CareerBlueprintReport) -> None:
    reports = _read_table("reports")
    previous = next((item for item in reports if item.get("id") == report.id), None)
    if not previous:
        return

    _upsert(reports, _report_storage_record(report))
    _write_table("reports", reports)
    source = "admin_edit" if report.editedBy else "ai_regenerated"
    _save_report_version(report, source)

    if report.editedBy:
        audit_logs = _read_table("admin_audit_logs")
        audit_logs.append(
            {
                "id": str(uuid4()),
                "adminId": report.editedBy,
                "action": "report.update",
                "targetType": "report",
                "targetId": report.id,
                "createdAt": report.updatedAt,
                "details": {
                    "previousTitle": previous.get("title"),
                    "newTitle": report.title,
                },
            }
        )
        _write_table("admin_audit_logs", audit_logs)


@_synchronized
def save_feedback(feedback: ReportFeedback) -> None:
    feedback_records = _read_table("report_feedback")
    feedback_records.append(feedback.model_dump(mode="json"))
    _write_table("report_feedback", feedback_records)


@_synchronized
def save_generation_job(job: GenerationJobStatus) -> None:
    jobs = _read_table("generation_jobs")
    _upsert(jobs, job.model_dump(mode="json"), key="jobId")
    if len(jobs) > 100:
        jobs = jobs[-100:]
    _write_table("generation_jobs", jobs)


def find_generation_job(job_id: str) -> GenerationJobStatus | None:
    job = _find_record("generation_jobs", job_id, key="jobId")
    return GenerationJobStatus.model_validate(job) if job else None


def get_metrics() -> dict[str, Any]:
    responses = _read_table("assessment_responses")
    reports = _read_table("reports")
    scores = _read_table("report_feedback")

    def average(key: str) -> float:
        if not scores:
            return 0
        return round(sum(item[key] for item in scores) / len(scores), 1)

    return {
        "assessmentCount": len(responses),
        "reportSuccessCount": len(
            [report for report in reports if report["generationStatus"] == "success"]
        ),
        "reportFailedCount": len(
            [report for report in reports if report["generationStatus"] == "failed"]
        ),
        "feedbackCount": len(scores),
        "averageUnderstandingScore": average("understandingScore"),
        "averageInsightScore": average("insightScore"),
        "averageActionScore": average("actionScore"),
        "averageRecommendScore": average("recommendScore"),
        "lowScoreReports": [
            item["reportId"]
            for item in scores
            if min(
                item["understandingScore"],
                item["insightScore"],
                item["actionScore"],
                item["recommendScore"],
            )
            <= 2
        ],
    }


def get_recent_reports(limit: int = 8) -> list[dict[str, Any]]:
    return list(reversed(_read_table("reports")[-limit:]))


def get_user_reports(user_id: str) -> list[dict[str, Any]]:
    return list(
        reversed(
            [
                report
                for report in _read_table("reports")
                if report["userId"] == user_id
            ]
        )
    )


def get_admin_records() -> list[dict[str, Any]]:
    users = {user["id"]: user for user in _read_table("users")}
    responses = {
        response["id"]: response for response in _read_table("assessment_responses")
    }
    records = []
    for report in reversed(_read_table("reports")):
        user = users.get(report["userId"], {})
        response = responses.get(report["responseId"], {})
        records.append(
            {
                "report": report,
                "student": {
                    "id": report["userId"],
                    "username": user.get("username") or "未知用户",
                    "displayName": user.get("displayName") or "未知用户",
                },
                "assessment": {
                    "grade": response.get("grade", ""),
                    "collegeMajor": response.get("collegeMajor", ""),
                    "submittedAt": response.get(
                        "submittedAt",
                        report["createdAt"],
                    ),
                },
            }
        )
    return records
