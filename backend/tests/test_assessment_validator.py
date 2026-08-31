import unittest

from app.services.assessment_validator import validate_raw_assessment_fields


class RawAssessmentValidatorTest(unittest.TestCase):
    def test_missing_snapshot_fields_are_named_before_model_generation(self):
        errors = validate_raw_assessment_fields({"educationStage": "本科"})

        self.assertIn("grade", errors)
        self.assertIn("longTermPersistence", errors)
        self.assertIn("abilityScores", errors)
        self.assertIn("interestScores", errors)
        self.assertIn("preferredWorkStyle", errors)

    def test_empty_answer_does_not_get_replaced_by_a_default(self):
        errors = validate_raw_assessment_fields(
            {
                "educationStage": "本科",
                "longTermPersistence": None,
                "abilityScores": {},
                "interestScores": {},
            }
        )

        self.assertIn("longTermPersistence", errors)
        self.assertIn("grade", errors)

    def test_incomplete_score_maps_are_rejected_before_type_defaults(self):
        errors = validate_raw_assessment_fields(
            {
                "abilityScores": {"logic": 4},
                "interestScores": {"handsOn": 4},
            }
        )

        self.assertEqual(errors["abilityScores"], "请完成能力评分")
        self.assertEqual(errors["interestScores"], "请完成兴趣评分")


if __name__ == "__main__":
    unittest.main()
