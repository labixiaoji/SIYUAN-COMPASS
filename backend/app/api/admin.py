from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.report import AdminReportUpdate
from app.services.auth import require_admin
from app.services.report_quality_check import check_report_quality, count_chineseish_words
from app.storage.json_db import find_report, get_admin_records, get_metrics, get_recent_reports, update_report

router = APIRouter(tags=["admin"])


@router.get("/admin/metrics")
def admin_metrics(_admin=Depends(require_admin)):
    return {**get_metrics(), "recentReports": get_recent_reports()}


@router.get("/admin/records")
def admin_records(_admin=Depends(require_admin)):
    return {"records": get_admin_records()}


@router.put("/admin/reports/{report_id}")
def edit_report(
    report_id: str,
    input_data: AdminReportUpdate,
    admin=Depends(require_admin),
):
    report = find_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"error": "报告不存在"})

    quality = check_report_quality(input_data.content)
    report.title = input_data.title.strip()
    report.content = input_data.content.strip()
    report.wordCount = count_chineseish_words(report.content)
    report.qualityStatus = quality["status"]
    report.errorMessage = "；".join(quality["warnings"]) or None
    report.updatedAt = datetime.now(timezone.utc).isoformat()
    report.editedAt = report.updatedAt
    report.editedBy = admin["id"]
    update_report(report)
    return report
