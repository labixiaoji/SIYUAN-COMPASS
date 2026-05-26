from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.services.report_generator import generate_report
from app.storage.json_db import find_profile, find_report, find_response, update_report

router = APIRouter(tags=["reports"])


def _get_report_or_404(report_id: str):
    report = find_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"error": "报告不存在"})
    return report


@router.get("/reports")
def get_report_by_query(report_id: str = Query(alias="reportId")):
    return _get_report_or_404(report_id)


@router.get("/reports/{report_id}")
def get_report(report_id: str):
    return _get_report_or_404(report_id)


async def _regenerate_report(report_id: str):
    existing = find_report(report_id)
    if not existing:
        raise HTTPException(status_code=404, detail={"error": "报告不存在"})

    response = find_response(existing.responseId)
    profile = find_profile(existing.profileId)
    if not response or not profile:
        raise HTTPException(status_code=400, detail={"error": "报告输入数据不完整"})

    regenerated = await generate_report(response, profile)
    regenerated.id = existing.id
    regenerated.retryCount = existing.retryCount + 1
    regenerated.createdAt = existing.createdAt
    regenerated.updatedAt = datetime.now(timezone.utc).isoformat()
    update_report(regenerated)

    return {"reportId": regenerated.id, "generationStatus": regenerated.generationStatus}


@router.post("/reports/regenerate")
async def regenerate_report_by_query(report_id: str = Query(alias="reportId")):
    return await _regenerate_report(report_id)


@router.post("/reports/{report_id}/regenerate")
async def regenerate_report(report_id: str):
    return await _regenerate_report(report_id)
