from __future__ import annotations

import unittest
import sys
from types import ModuleType
from unittest.mock import patch

from fastapi import HTTPException

try:
    import psycopg  # noqa: F401
except ModuleNotFoundError:
    psycopg_module = ModuleType("psycopg")
    psycopg_module.connect = None
    rows_module = ModuleType("psycopg.rows")
    rows_module.dict_row = object()
    types_module = ModuleType("psycopg.types")
    json_module = ModuleType("psycopg.types.json")
    json_module.Jsonb = lambda value: value
    sys.modules["psycopg"] = psycopg_module
    sys.modules["psycopg.rows"] = rows_module
    sys.modules["psycopg.types"] = types_module
    sys.modules["psycopg.types.json"] = json_module

from app.api import assessments
from app.schemas.assessment_draft import AssessmentDraftUpsert
from app.schemas.generation_job import GenerationFailure, GenerationJobStatus
from app.storage.json_db import AssessmentDraftConflictError


def draft_record(user_id: str = "user-1") -> dict[str, object]:
    return {
        "id": "draft-1",
        "userId": user_id,
        "answers": {"collegeMajor": "计算机"},
        "currentStep": 2,
        "version": 1,
        "createdAt": "2026-08-13T00:00:00+00:00",
        "updatedAt": "2026-08-13T00:01:00+00:00",
        "expiresAt": "2026-09-12T00:01:00+00:00",
    }


class AssessmentDraftApiTest(unittest.TestCase):
    def test_read_uses_authenticated_user_scope(self):
        with patch.object(assessments, "get_assessment_draft", return_value=draft_record()) as read:
            result = assessments.read_assessment_draft({"id": "authenticated-user"})

        read.assert_called_once_with("authenticated-user")
        self.assertEqual(result.draft.userId, "user-1")

    def test_save_uses_authenticated_user_and_ignores_payload_user_id(self):
        payload = AssessmentDraftUpsert(
            answers={"collegeMajor": "计算机", "userId": "attacker"},
            currentStep=2,
            version=0,
        )
        with patch.object(assessments, "save_assessment_draft", return_value=draft_record("authenticated-user")) as save:
            result = assessments.upsert_assessment_draft(payload, {"id": "authenticated-user"})

        save.assert_called_once_with(
            "authenticated-user",
            payload.answers,
            payload.currentStep,
            version=payload.version,
        )
        self.assertEqual(result.userId, "authenticated-user")

    def test_stale_save_returns_conflict(self):
        with patch.object(
            assessments,
            "save_assessment_draft",
            side_effect=AssessmentDraftConflictError(draft_record()),
        ):
            with self.assertRaises(HTTPException) as raised:
                assessments.upsert_assessment_draft(
                    AssessmentDraftUpsert(answers={}, currentStep=0, version=1),
                    {"id": "user-1"},
                )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail["draft"]["version"], 1)


class AssessmentJobPrivacyApiTest(unittest.TestCase):
    def failed_job(self, user_id: str = "user-1") -> GenerationJobStatus:
        return GenerationJobStatus(
            jobId="job-1",
            userId=user_id,
            status="failed",
            stage="report_failed",
            progress=88,
            message="生涯报告生成失败。",
            error="模型请求失败：已脱敏",
            failure=GenerationFailure(
                code="REPORT_MODEL_TIMEOUT",
                stage="report",
                message="模型请求超时",
                retryable=True,
                traceId="job-1",
            ),
        )

    def test_student_polling_hides_structured_admin_failure(self):
        with patch.object(assessments, "get_generation_job", return_value=self.failed_job()):
            result = assessments.get_assessment_job(
                "job-1",
                {"id": "user-1", "role": "student"},
            )

        self.assertIsNone(result.failure)
        self.assertEqual(result.error, "模型请求超时")

    def test_student_cancel_response_also_hides_structured_failure(self):
        with patch.object(assessments, "get_generation_job", return_value=self.failed_job()):
            result = assessments.cancel_assessment_job(
                "job-1",
                {"id": "user-1", "role": "student"},
            )

        self.assertIsNone(result.failure)
        self.assertEqual(result.error, "模型请求超时")

    def test_student_cannot_read_another_account_job_diagnostics(self):
        with patch.object(assessments, "get_generation_job", return_value=self.failed_job()):
            with self.assertRaises(HTTPException) as raised:
                assessments.get_assessment_job(
                    "job-1",
                    {"id": "user-2", "role": "student"},
                )

        self.assertEqual(raised.exception.status_code, 403)

    def test_student_recovery_reads_only_owner_job(self):
        recovery = {
            "jobId": "job-1",
            "answers": {"collegeMajor": "计算机"},
            "currentStep": 4,
            "version": 3,
            "source": "job_input",
        }
        with patch.object(assessments, "get_generation_job", return_value=self.failed_job()), patch.object(
            assessments,
            "load_generation_job_recovery_draft",
            return_value=recovery,
        ) as load:
            result = assessments.get_assessment_job_draft(
                "job-1",
                {"id": "user-1", "role": "student"},
            )

        load.assert_called_once_with("job-1", user_id="user-1")
        self.assertEqual(result.answers["collegeMajor"], "计算机")
        self.assertEqual(result.currentStep, 4)


if __name__ == "__main__":
    unittest.main()
