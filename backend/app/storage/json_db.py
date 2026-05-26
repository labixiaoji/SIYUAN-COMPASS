from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.assessment import AssessmentResponse
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintReport, ReportFeedback

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_PATH = ROOT_DIR / "data" / "db.json"

INITIAL_DB: dict[str, list[Any]] = {
    "users": [],
    "responses": [],
    "profiles": [],
    "reports": [],
    "feedback": [],
}


def ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps(INITIAL_DB, ensure_ascii=False, indent=2), encoding="utf-8")


def read_db() -> dict[str, list[Any]]:
    ensure_db()
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def write_db(db: dict[str, list[Any]]) -> None:
    ensure_db()
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def get_or_create_user(user_id: str | None = None) -> dict[str, str]:
    from app.services.report_generator import now_iso
    from uuid import uuid4

    db = read_db()
    existing = next((user for user in db["users"] if user["id"] == user_id), None) if user_id else None
    if existing:
        return existing

    now = now_iso()
    user = {"id": user_id or str(uuid4()), "createdAt": now, "updatedAt": now}
    db["users"].append(user)
    write_db(db)
    return user


def save_assessment_bundle(response: AssessmentResponse, profile: CareerProfile, report: CareerBlueprintReport) -> None:
    db = read_db()
    db["responses"].append(response.model_dump(mode="json"))
    db["profiles"].append(profile.model_dump(mode="json"))
    db["reports"].append(report.model_dump(mode="json"))
    write_db(db)


def find_report(report_id: str) -> CareerBlueprintReport | None:
    report = next((item for item in read_db()["reports"] if item["id"] == report_id), None)
    return CareerBlueprintReport.model_validate(report) if report else None


def find_response(response_id: str) -> AssessmentResponse | None:
    response = next((item for item in read_db()["responses"] if item["id"] == response_id), None)
    return AssessmentResponse.model_validate(response) if response else None


def find_profile(profile_id: str) -> CareerProfile | None:
    profile = next((item for item in read_db()["profiles"] if item["id"] == profile_id), None)
    return CareerProfile.model_validate(profile) if profile else None


def update_report(report: CareerBlueprintReport) -> None:
    db = read_db()
    index = next((idx for idx, item in enumerate(db["reports"]) if item["id"] == report.id), -1)
    if index >= 0:
        db["reports"][index] = report.model_dump(mode="json")
        write_db(db)


def save_feedback(feedback: ReportFeedback) -> None:
    db = read_db()
    db["feedback"].append(feedback.model_dump(mode="json"))
    write_db(db)


def get_metrics() -> dict[str, Any]:
    db = read_db()
    scores = db["feedback"]

    def average(key: str) -> float:
        if not scores:
            return 0
        return round(sum(item[key] for item in scores) / len(scores), 1)

    return {
        "assessmentCount": len(db["responses"]),
        "reportSuccessCount": len([report for report in db["reports"] if report["generationStatus"] == "success"]),
        "reportFailedCount": len([report for report in db["reports"] if report["generationStatus"] == "failed"]),
        "feedbackCount": len(db["feedback"]),
        "averageUnderstandingScore": average("understandingScore"),
        "averageInsightScore": average("insightScore"),
        "averageActionScore": average("actionScore"),
        "averageRecommendScore": average("recommendScore"),
        "lowScoreReports": [
            item["reportId"]
            for item in db["feedback"]
            if min(item["understandingScore"], item["insightScore"], item["actionScore"], item["recommendScore"]) <= 2
        ],
    }


def get_recent_reports(limit: int = 8) -> list[dict[str, Any]]:
    return list(reversed(read_db()["reports"][-limit:]))
