import os
import json
from typing import Dict, Any, List
from backend.app.core.config import settings

class MockIAMConnector:
    def __init__(self, data_dir: str = settings.MOCK_ENTERPRISE_DIR):
        self.data_dir = data_dir
        self.users_file = os.path.join(self.data_dir, "iam_users.json")

    def get_users(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def verify_entitlement(self, user_email: str, required_role: str) -> bool:
        users = self.get_users()
        for u in users:
            if u.get("email") == user_email:
                return required_role in u.get("roles", []) or "ADMIN" in u.get("roles", [])
        return False

mock_iam = MockIAMConnector()
