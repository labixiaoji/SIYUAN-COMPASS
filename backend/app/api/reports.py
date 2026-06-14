from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.profile_analyzer import ProfileAnalysisError, analyze_career_profile
from app.services.report_generator import ReportGenerationError, generate_report
from app.services.auth import require_user
from app.storage.json_db import find_profile, find_report, find_response, get_user_reports, update_profile, update_report

router = APIRouter(tags=["reports"])


def _get_report_or_404(report_id: str, user):
    report = find_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"error": "报告不存在"})
    if user["role"] != "admin" and report.userId != user["id"]:
        raise HTTPException(status_code=403, detail={"error": "无权查看该报告"})
    return report


@router.get("/reports")
def get_report_by_query(
    report_id: str = Query(alias="reportId"),
    user=Depends(require_user),
):
    return _get_report_or_404(report_id, user)


@router.get("/reports/mine")
def get_my_reports(user=Depends(require_user)):
    return {"reports": get_user_reports(user["id"])}


@router.get("/reports/{report_id}")
def get_report(report_id: str, user=Depends(require_user)):
    return _get_report_or_404(report_id, user)


async def _regenerate_report(report_id: str, user):
    existing = _get_report_or_404(report_id, user)

    response = find_response(existing.responseId)
    existing_profile = find_profile(existing.profileId)
    if not response or not existing_profile:
        raise HTTPException(status_code=400, detail={"error": "报告输入数据不完整"})

    try:
        profile = await analyze_career_profile(response)
    except ProfileAnalysisError as error:
        raise HTTPException(
            status_code=502,
            detail={"stage": "用户画像重新生成失败", "error": str(error)},
        ) from error

    profile.id = existing_profile.id
    profile.createdAt = existing_profile.createdAt

    try:
        regenerated = await generate_report(response, profile)
    except ReportGenerationError as error:
        raise HTTPException(
            status_code=502,
            detail={"stage": "生涯报告重新生成失败", "error": str(error)},
        ) from error
    regenerated.id = existing.id
    regenerated.retryCount = existing.retryCount + 1
    regenerated.createdAt = existing.createdAt
    regenerated.updatedAt = datetime.now(timezone.utc).isoformat()
    update_profile(profile)
    update_report(regenerated)

    return {"reportId": regenerated.id, "generationStatus": regenerated.generationStatus}


@router.post("/reports/regenerate")
async def regenerate_report_by_query(
    report_id: str = Query(alias="reportId"),
    user=Depends(require_user),
):
    return await _regenerate_report(report_id, user)


@router.post("/reports/{report_id}/regenerate")
async def regenerate_report(report_id: str, user=Depends(require_user)):
    return await _regenerate_report(report_id, user)
