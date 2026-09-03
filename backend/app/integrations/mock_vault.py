import os
import json
from typing import Dict, Any, List
from backend.app.core.config import settings

class MockVaultConnector:
    def __init__(self, data_dir: str = settings.MOCK_ENTERPRISE_DIR):
        self.data_dir = data_dir
        self.docs_file = os.path.join(self.data_dir, "vault_documents.json")

    def get_documents(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.docs_file):
            with open(self.docs_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def get_document_lifecycle(self, doc_number: str) -> Dict[str, Any]:
        docs = self.get_documents()
        for d in docs:
            if d.get("document_number") == doc_number or doc_number in d.get("title", ""):
                return d
        return {
            "document_number": doc_number,
            "lifecycle_state": "Draft",
            "version": "1.0",
            "qa_reviewer": "Not Assigned"
        }

mock_vault = MockVaultConnector()
