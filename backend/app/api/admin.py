from fastapi import APIRouter

from app.storage.json_db import get_metrics, get_recent_reports

router = APIRouter(tags=["admin"])


@router.get("/admin/metrics")
def admin_metrics():
    return {**get_metrics(), "recentReports": get_recent_reports()}
