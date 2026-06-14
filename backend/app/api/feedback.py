from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.report import ReportFeedback, ReportFeedbackInput
from app.services.auth import require_user
from app.storage.json_db import find_report, save_feedback

router = APIRouter(tags=["feedback"])


def valid_score(value: int) -> bool:
    return isinstance(value, int) and 1 <= value <= 5


def _submit_feedback(report_id: str, input_data: ReportFeedbackInput, user):
    report = find_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"error": "报告不存在"})
    if user["role"] != "admin" and report.userId != user["id"]:
        raise HTTPException(status_code=403, detail={"error": "无权反馈该报告"})

    invalid = [
        key
        for key in ["understandingScore", "insightScore", "actionScore", "recommendScore"]
        if not valid_score(getattr(input_data, key))
    ]
    if invalid:
        raise HTTPException(status_code=400, detail={"error": f"评分字段无效：{', '.join(invalid)}"})

    feedback = ReportFeedback(
        id=str(uuid4()),
        reportId=report_id,
        userId=report.userId,
        understandingScore=input_data.understandingScore,
        insightScore=input_data.insightScore,
        actionScore=input_data.actionScore,
        recommendScore=input_data.recommendScore,
        comment=input_data.comment if isinstance(input_data.comment, str) else None,
        createdAt=datetime.now(timezone.utc).isoformat(),
    )
    save_feedback(feedback)

    return {"feedbackId": feedback.id, "createdAt": feedback.createdAt}


@router.post("/reports/feedback")
def submit_feedback_by_query(
    input_data: ReportFeedbackInput,
    report_id: str = Query(alias="reportId"),
    user=Depends(require_user),
):
    return _submit_feedback(report_id, input_data, user)


@router.post("/reports/{report_id}/feedback")
def submit_feedback(
    report_id: str,
    input_data: ReportFeedbackInput,
    user=Depends(require_user),
):
    return _submit_feedback(report_id, input_data, user)
