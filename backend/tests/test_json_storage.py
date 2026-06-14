from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.schemas.assessment import AssessmentResponse
from app.schemas.generation_job import GenerationJobStatus
from app.schemas.profile import CareerProfile
from app.schemas.report import CareerBlueprintReport
from app.storage import json_db


class JsonStorageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        data_dir = Path(self.temp_dir.name)
        json_db.DATA_DIR = data_dir
        json_db.TABLE_FILES = {
            name: data_dir / path.name
            for name, path in json_db.TABLE_FILES.items()
        }
        json_db.ensure_storage()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_split_storage_and_reconstruction(self) -> None:
        response = AssessmentResponse(
            id="assessment-1",
            userId="user-1",
            submittedAt="2026-06-13T00:00:00+00:00",
            createdAt="2026-06-13T00:00:00+00:00",
            grade="大三",
            gender="女",
            collegeMajor="计算机科学与技术",
            hometown="江苏苏州",
            mastersIntention="明确考虑",
            mastersPlan="考虑人工智能方向硕士",
            phdIntention="不太考虑",
            phdPlan="先在硕士阶段验证科研兴趣",
            educationPathReasons=["提升学历和平台", "目标职业需要更高学历"],
            educationCertainty=4,
            fiveYearCity="上海",
            fiveYearIncome="暂不设定",
            fiveYearIndustry="人工智能",
            fiveYearRole="算法工程师",
            fiveYearFamilyStatus="单身专注学业事业",
            fiveYearHousingPlan="先租房",
            fiveYearHobbiesSkills="跑步和英语",
            tenYearCity="上海或杭州",
            tenYearIncome="暂不设定",
            tenYearIndustry="人工智能",
            tenYearRole="技术负责人",
            tenYearFamilyStatus="暂不确定",
            tenYearHousingPlan="根据家庭情况决定",
            tenYearHobbiesSkills="持续运动和学习",
            topValuesRanked=[
                "成长 / 学习新技能的机会",
                "自由 / 弹性 / 不被控制",
                "意义感 / 帮助他人或创造价值",
            ],
            abilityScores={
                "logic": 5,
                "expression": 3,
                "spatialDesign": 3,
                "interpersonal": 4,
            },
            interestScores={
                "handsOn": 4,
                "research": 4,
                "creation": 5,
                "helping": 3,
                "leadership": 3,
                "detail": 4,
            },
            currentPreparations=["修读相关课程", "做过项目作品"],
            missingResources=["缺项目 / 实习经历", "缺清晰计划"],
            majorOutcomeAwareness="听说过一些",
            targetJobAwareness="有一点了解",
            jobInfoChannels=["招聘网站", "宣讲会"],
            healthEnergyStatus="一般，偶尔运动",
            exerciseFrequency="每周1至2次",
            careerConfusions=["不确定自己适合哪个行业"],
            mainConfusionText="不确定更适合算法还是产品岗位",
        )
        profile = CareerProfile(
            id="profile-1",
            userId="user-1",
            responseId=response.id,
            modelName="test-model",
            promptVersion="test-v1",
            createdAt=response.createdAt,
            summary="测试画像",
        )

        json_db.save_assessment_progress(response, profile)

        stored_response = json_db._read_table("assessment_responses")[0]
        self.assertNotIn("abilityScores", stored_response)
        self.assertNotIn("topValuesRanked", stored_response)
        self.assertEqual(
            json_db.find_response(response.id).model_dump(),
            response.model_dump(),
        )

        report = CareerBlueprintReport(
            id="report-1",
            userId="user-1",
            responseId=response.id,
            profileId=profile.id,
            title="我的生涯蓝图",
            content="测试报告",
            wordCount=4,
            generationStatus="success",
            qualityStatus="passed",
            modelName="test-model",
            promptVersion="test-v1",
            inputSnapshot={"response": response, "profile": profile},
            retryCount=0,
            createdAt=response.createdAt,
            updatedAt=response.createdAt,
        )
        json_db.save_report(report)

        self.assertNotIn(
            "inputSnapshot",
            json_db._read_table("reports")[0],
        )
        self.assertEqual(
            json_db.find_report(report.id).inputSnapshot["response"]["id"],
            response.id,
        )

        edited_report = report.model_copy(
            update={
                "title": "管理员修订报告",
                "editedBy": "admin-1",
                "editedAt": "2026-06-13T01:00:00+00:00",
                "updatedAt": "2026-06-13T01:00:00+00:00",
            }
        )
        json_db.update_report(edited_report)

        self.assertEqual(len(json_db._read_table("report_versions")), 2)
        self.assertEqual(
            json_db._read_table("report_versions")[1]["source"],
            "admin_edit",
        )
        self.assertEqual(len(json_db._read_table("admin_audit_logs")), 1)

        job = GenerationJobStatus(
            jobId="job-1",
            status="queued",
            stage="queued",
            progress=5,
            message="等待生成",
            userId="user-1",
        )
        json_db.save_generation_job(job)
        self.assertEqual(json_db.find_generation_job(job.jobId), job)


if __name__ == "__main__":
    unittest.main()
