from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch

try:
    import psycopg  # noqa: F401
except ModuleNotFoundError:
    psycopg_module = ModuleType("psycopg")
    psycopg_module.connect = Mock()
    rows_module = ModuleType("psycopg.rows")
    rows_module.dict_row = object()
    types_module = ModuleType("psycopg.types")
    json_module = ModuleType("psycopg.types.json")
    json_module.Jsonb = lambda value: value
    sys.modules["psycopg"] = psycopg_module
    sys.modules["psycopg.rows"] = rows_module
    sys.modules["psycopg.types"] = types_module
    sys.modules["psycopg.types.json"] = json_module

from app.schemas.assessment import AssessmentResponseInput
from app.schemas.generation_job import GenerationJobStatus
from app.services import generation_jobs
from app.services.assessment_validator import REQUIRED_STRING_FIELDS
from app.storage.json_db import GenerationQuotaStorageError
from app.storage import json_db


def make_job(status: str = "queued") -> GenerationJobStatus:
    return GenerationJobStatus(
        jobId="job-1",
        userId="user-1",
        status=status,
        stage=status,
        progress=5,
        message="test",
        createdAt="2026-07-30T00:00:00+00:00",
        updatedAt="2026-07-30T00:00:00+00:00",
    )


def make_complete_raw_input() -> dict[str, object]:
    raw: dict[str, object] = {field: "已填写" for field in REQUIRED_STRING_FIELDS}
    raw.update(
        {
            "educationStage": "本科",
            "grade": "大三",
            "mastersIntention": "就业",
            "phdIntention": "",
            "educationPathReasons": ["个人兴趣"],
            "topValuesRanked": ["成长", "稳定", "自主"],
            "abilityScores": {"logic": 4, "expression": 3, "spatialDesign": 3, "interpersonal": 3},
            "interestScores": {"handsOn": 4, "research": 4, "creation": 3, "helping": 3, "leadership": 2, "detail": 4},
            "praisedTraits": ["认真"],
            "preferredWorkStyle": ["独立完成"],
            "currentPreparations": ["课程学习"],
            "missingResources": ["岗位信息"],
            "jobInfoChannels": ["学校就业平台"],
            "careerConfusions": ["不知道未来适合做什么"],
            "longTermPersistence": 3,
            "userId": "attacker-id",
        }
    )
    return raw


class GenerationJobReservationTest(TestCase):
    @patch.object(generation_jobs, "get_settings")
    @patch.object(generation_jobs, "save_generation_job_if_user_idle")
    def test_create_persists_input_and_applies_daily_quota(self, save_job, settings):
        settings.return_value = SimpleNamespace(
            report_generation_daily_limit=3,
            report_generation_quota_timezone="Asia/Shanghai",
            generation_job_retention_days=30,
        )
        save_job.return_value = None
        input_data = AssessmentResponseInput.model_construct(userId="user-1")

        created = generation_jobs.create_generation_job("user-1", input_data)

        self.assertEqual(created.status, "queued")
        kwargs = save_job.call_args.kwargs
        self.assertEqual(kwargs["daily_limit"], 3)
        self.assertEqual(kwargs["retention_days"], 30)
        self.assertEqual(kwargs["input_data"]["userId"], "user-1")
        self.assertIsNotNone(kwargs["quota_day"])

    @patch.object(generation_jobs, "get_settings")
    @patch.object(generation_jobs, "save_generation_job_if_user_idle")
    def test_create_does_not_persist_omitted_default_answers(self, save_job, settings):
        settings.return_value = SimpleNamespace(
            report_generation_daily_limit=0,
            report_generation_quota_timezone="Asia/Shanghai",
            generation_job_retention_days=30,
        )
        save_job.return_value = None
        input_data = AssessmentResponseInput.model_construct(userId="user-1")

        generation_jobs.create_generation_job("user-1", input_data)

        persisted = save_job.call_args.kwargs["input_data"]
        self.assertNotIn("preferredWorkStyle", persisted)
        self.assertNotIn("longTermPersistence", persisted)

    @patch.object(generation_jobs, "get_settings")
    @patch.object(generation_jobs, "save_generation_job_if_user_idle")
    def test_quota_error_is_exposed_as_service_error(self, save_job, settings):
        settings.return_value = SimpleNamespace(
            report_generation_daily_limit=3,
            report_generation_quota_timezone="Asia/Shanghai",
            generation_job_retention_days=30,
        )
        save_job.side_effect = GenerationQuotaStorageError(limit=3, used=3)

        with self.assertRaises(generation_jobs.GenerationQuotaExceededError) as raised:
            generation_jobs.create_generation_job(
                "user-1",
                AssessmentResponseInput.model_construct(userId="user-1"),
            )

        self.assertEqual(raised.exception.limit, 3)
        self.assertEqual(raised.exception.used, 3)


class GenerationJobRecoveryTest(IsolatedAsyncioTestCase):
    @patch.object(generation_jobs, "get_settings")
    @patch.object(generation_jobs, "delete_expired_generation_jobs")
    @patch.object(generation_jobs, "start_generation_workers")
    def test_startup_starts_fixed_worker_pool(self, start_workers, delete_old, settings):
        settings.return_value = SimpleNamespace(generation_job_retention_days=30)
        start_workers.return_value = 3

        count = generation_jobs.recover_generation_jobs()

        self.assertEqual(count, 3)
        delete_old.assert_called_once_with(30)
        start_workers.assert_called_once_with()

    @patch.object(generation_jobs.asyncio, "sleep", new_callable=AsyncMock)
    @patch.object(generation_jobs, "generation_job_retry_delay")
    @patch.object(generation_jobs, "claim_generation_job")
    @patch.object(generation_jobs, "get_settings")
    async def test_running_job_waits_for_lease_then_is_reclaimed(
        self,
        settings,
        claim,
        retry_delay,
        sleep,
    ):
        settings.return_value = SimpleNamespace(
            generation_job_lease_seconds=300,
            generation_job_heartbeat_seconds=30,
        )
        claim.side_effect = [None, make_job("running")]
        retry_delay.return_value = 0.1

        recovered = await generation_jobs._claim_when_available("job-1", "new-owner")

        self.assertEqual(recovered.jobId, "job-1")
        self.assertEqual(claim.call_count, 2)
        sleep.assert_awaited_once()

    @patch.object(generation_jobs, "analyze_career_profile", new_callable=AsyncMock)
    @patch.object(generation_jobs, "find_user", return_value={"id": "user-1"})
    @patch.object(generation_jobs, "load_generation_job_input", return_value={"educationStage": "本科"})
    @patch.object(generation_jobs, "_update_running_job", return_value=make_job("failed"))
    @patch.object(generation_jobs, "_heartbeat", new_callable=AsyncMock)
    @patch.object(generation_jobs, "_claim_when_available", new_callable=AsyncMock)
    async def test_incomplete_snapshot_fails_without_calling_model(
        self,
        claim,
        _heartbeat,
        update_job,
        _load_input,
        _find_user,
        analyze_profile,
    ):
        claim.return_value = make_job("running")

        await generation_jobs.run_generation_job("job-1")

        analyze_profile.assert_not_awaited()
        self.assertEqual(update_job.call_args.kwargs["stage"], "validation_failed")
        failure = update_job.call_args.kwargs["failure"]
        self.assertEqual(failure["code"], "ASSESSMENT_INCOMPLETE")
        self.assertIn("grade", failure["missingFields"])


class GenerationWorkerLifecycleTest(IsolatedAsyncioTestCase):
    async def test_worker_pool_has_configured_fixed_size(self):
        async def idle_worker(_worker_id, stop_event):
            await stop_event.wait()

        with (
            patch.object(generation_jobs, "get_settings", return_value=SimpleNamespace(generation_worker_count=3)),
            patch.object(generation_jobs, "_generation_worker_loop", new=idle_worker),
        ):
            self.assertEqual(generation_jobs.start_generation_workers(), 3)
            self.assertEqual(len(generation_jobs.WORKER_TASKS), 3)
            await generation_jobs.stop_generation_workers()

        self.assertEqual(generation_jobs.WORKER_TASKS, {})
        self.assertEqual(generation_jobs.WORKER_CLAIMS, {})


class GenerationJobOwnershipTest(IsolatedAsyncioTestCase):
    def test_relational_user_id_overrides_recovery_json(self):
        record = json_db._generation_job_from_row(
            {
                "data": {
                    "jobId": "job-1",
                    "userId": "attacker-id",
                    "status": "queued",
                    "stage": "queued",
                    "progress": 5,
                    "message": "test",
                },
                "user_id": "owner-id",
                "created_at": "2026-07-30T00:00:00+00:00",
                "updated_at": "2026-07-30T00:00:00+00:00",
                "draft_available": True,
            }
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.userId, "owner-id")

    def test_unowned_legacy_job_cannot_fall_back_to_json_user_id(self):
        record = json_db._generation_job_from_row(
            {
                "data": {
                    "jobId": "job-2",
                    "userId": "attacker-id",
                    "status": "queued",
                    "stage": "queued",
                    "progress": 5,
                    "message": "test",
                },
                "user_id": None,
                "created_at": "2026-07-30T00:00:00+00:00",
                "updated_at": "2026-07-30T00:00:00+00:00",
                "draft_available": True,
            }
        )

        self.assertIsNotNone(record)
        self.assertIsNone(record.userId)

    @patch.object(generation_jobs, "save_report")
    @patch.object(generation_jobs, "_update_running_job")
    @patch.object(generation_jobs, "_heartbeat", new_callable=AsyncMock)
    @patch.object(generation_jobs, "find_report")
    @patch.object(generation_jobs, "_claim_when_available", new_callable=AsyncMock)
    async def test_recovery_reuses_report_saved_before_status_commit(
        self,
        claim,
        find_report,
        _heartbeat,
        update_job,
        save_report,
    ):
        claimed = make_job("running").model_copy(update={"reportId": "report-1"})
        claim.return_value = claimed
        find_report.return_value = SimpleNamespace(
            id="report-1",
            generationStatus="success",
        )

        await generation_jobs.run_generation_job("job-1")

        save_report.assert_not_called()
        self.assertEqual(update_job.call_args.kwargs["status"], "success")
        self.assertTrue(update_job.call_args.kwargs["terminal"])


class GenerationJobCancellationTest(TestCase):
    @patch.object(generation_jobs, "ACTIVE_TASK_LOOPS", new_callable=dict)
    @patch.object(generation_jobs, "ACTIVE_TASKS", new_callable=dict)
    @patch.object(generation_jobs, "cancel_generation_job_record")
    @patch.object(generation_jobs, "find_generation_job")
    def test_cancel_commits_terminal_state_before_stopping_local_task(
        self,
        find_job,
        cancel_record,
        active_tasks,
        active_loops,
    ):
        find_job.return_value = make_job("running")
        cancelled = make_job("cancelled")
        cancel_record.return_value = cancelled
        task = Mock(spec=asyncio.Task)
        task.done.return_value = False
        loop = Mock()
        active_tasks["job-1"] = task
        active_loops["job-1"] = loop

        result = generation_jobs.cancel_generation_job("job-1")

        self.assertIs(result, cancelled)
        cancel_record.assert_called_once_with("job-1")
        loop.call_soon_threadsafe.assert_called_once_with(task.cancel)

    @patch.object(generation_jobs, "update_generation_job_conditionally")
    def test_success_update_requires_running_status_and_current_claim(self, update):
        update.return_value = None

        result = generation_jobs._update_running_job(
            "job-1",
            "worker-token",
            terminal=True,
            status="success",
            stage="completed",
        )

        self.assertIsNone(result)
        self.assertEqual(update.call_args.kwargs["expected_statuses"], ("running",))
        self.assertEqual(update.call_args.kwargs["claim_token"], "worker-token")
        self.assertTrue(update.call_args.kwargs["clear_private_state"])
        self.assertTrue(update.call_args.kwargs["clear_input_data"])
        self.assertTrue(update.call_args.kwargs["release_claim"])

    @patch.object(generation_jobs, "update_generation_job_conditionally")
    def test_failed_update_releases_claim_but_keeps_private_input(self, update):
        update.return_value = None

        generation_jobs._update_running_job(
            "job-1",
            "worker-token",
            terminal=True,
            status="failed",
            stage="report_failed",
        )

        self.assertFalse(update.call_args.kwargs["clear_private_state"])
        self.assertFalse(update.call_args.kwargs["clear_input_data"])
        self.assertTrue(update.call_args.kwargs["release_claim"])


class GenerationFailureTest(TestCase):
    def test_failure_is_structured_and_redacted(self):
        failure = generation_jobs.build_generation_failure(
            "job-1",
            "report",
            RuntimeError('模型请求超时，请使用 {"api_key":"secret-value"} 联系 13900138000'),
        )

        self.assertEqual(failure.code, "REPORT_MODEL_TIMEOUT")
        self.assertEqual(failure.stage, "report")
        self.assertNotIn("secret-value", failure.message)
        self.assertNotIn("13900138000", failure.message)
        self.assertEqual(failure.traceId, "job-1")


if __name__ == "__main__":
    import unittest

    unittest.main()
