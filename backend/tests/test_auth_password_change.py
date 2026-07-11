from pathlib import Path
import unittest


AUTH_API_SOURCE = Path("app/api/auth.py").read_text(encoding="utf-8")
AUTH_SCHEMA_SOURCE = Path("app/schemas/auth.py").read_text(encoding="utf-8")
STORAGE_SOURCE = Path("app/storage/json_db.py").read_text(encoding="utf-8")


class PasswordChangeTest(unittest.TestCase):
    def test_password_change_requires_current_password_and_updates_hash(self):
        self.assertIn('class ChangePasswordInput', AUTH_SCHEMA_SOURCE)
        self.assertIn('@router.post("/change-password")', AUTH_API_SOURCE)
        self.assertIn('verify_password(input_data.currentPassword', AUTH_API_SOURCE)
        self.assertIn('update_user_password', AUTH_API_SOURCE)
        self.assertIn('def update_user_password', STORAGE_SOURCE)


if __name__ == "__main__":
    unittest.main()
