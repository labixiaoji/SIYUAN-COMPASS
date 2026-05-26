from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.assessment import AssessmentResponse, AssessmentResponseInput, AssessmentSubmitResult
from app.services.assessment_validator import validate_assessment
from app.services.profile_builder import build_career_profile
from app.services.report_generator import generate_report
from app.storage.json_db import get_or_create_user, save_assessment_bundle

router = APIRouter(tags=["assessments"])


@router.post("/assessments", response_model=AssessmentSubmitResult)
async def submit_assessment(input_data: AssessmentResponseInput) -> AssessmentSubmitResult:
    errors = validate_assessment(input_data)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    user = get_or_create_user(input_data.userId)
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

    profile = build_career_profile(response)
    report = await generate_report(response, profile)
    save_assessment_bundle(response, profile, report)

    return AssessmentSubmitResult(
        userId=user["id"],
        responseId=response.id,
        profileId=profile.id,
        reportId=report.id,
        generationStatus=report.generationStatus,
    )
