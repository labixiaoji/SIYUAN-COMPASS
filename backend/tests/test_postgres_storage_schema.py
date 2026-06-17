from pathlib import Path
import unittest


STORAGE_SOURCE = Path("app/storage/json_db.py").read_text(encoding="utf-8")


class PostgresStorageSchemaTest(unittest.TestCase):
    def test_postgres_schema_contains_expected_tables(self):
        for table in [
            "users",
            "assessment_responses",
            "assessment_scores",
            "assessment_choices",
            "career_profiles",
            "reports",
            "report_versions",
            "generation_jobs",
            "report_feedback",
            "admin_audit_logs",
        ]:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", STORAGE_SOURCE)

    def test_assessment_list_fields_are_normalized_choices(self):
        expected_fields = (
            "educationPathReasons",
            "topValuesRanked",
            "currentPreparations",
            "missingResources",
            "jobInfoChannels",
            "careerConfusions",
        )
        for field in expected_fields:
            self.assertIn(field, STORAGE_SOURCE)


if __name__ == "__main__":
    unittest.main()
