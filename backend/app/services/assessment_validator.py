from app.schemas.assessment import AssessmentResponseInput

REQUIRED_STRING_FIELDS = [
    "grade",
    "collegeMajor",
    "preferredCity",
    "educationPath",
    "phdIntention",
    "futureRoleType",
    "lifePreference",
    "majorOutcomeAwareness",
    "targetJobAwareness",
    "healthEnergyStatus",
]


def _has_text(value: object) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def _has_array(value: object, minimum: int = 1) -> bool:
    return isinstance(value, list) and len(value) >= minimum


def validate_assessment(input_data: AssessmentResponseInput) -> list[str]:
    data = input_data.model_dump()
    errors: list[str] = []

    for field in REQUIRED_STRING_FIELDS:
        if not _has_text(data.get(field)):
            errors.append(f"{field} 不能为空")

    if not _has_array(input_data.careerConfusions):
        errors.append("careerConfusions 至少选择 1 项")
    if len(input_data.careerConfusions) > 3:
        errors.append("careerConfusions 最多选择 3 项")
    if not _has_array(input_data.educationPathReasons):
        errors.append("educationPathReasons 至少选择 1 项")
    if not _has_array(input_data.fiveYearPriorities):
        errors.append("fiveYearPriorities 至少选择 1 项")
    if len(input_data.fiveYearPriorities) > 3:
        errors.append("fiveYearPriorities 最多选择 3 项")
    if not _has_array(input_data.targetIndustries):
        errors.append("targetIndustries 至少选择 1 项")
    if len(input_data.targetIndustries) > 2:
        errors.append("targetIndustries 最多选择 2 项")
    if not _has_array(input_data.topValuesRanked, 3):
        errors.append("topValuesRanked 需要选择 3 项")
    if not _has_array(input_data.currentPreparations):
        errors.append("currentPreparations 至少选择 1 项")
    if not _has_array(input_data.missingResources):
        errors.append("missingResources 至少选择 1 项")
    if len(input_data.missingResources) > 3:
        errors.append("missingResources 最多选择 3 项")

    return errors
