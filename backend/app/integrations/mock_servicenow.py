import os
import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from backend.app.core.config import settings

class MockServiceNowConnector:
    def __init__(self, data_dir: str = settings.MOCK_ENTERPRISE_DIR):
        self.data_dir = data_dir
        self.incidents_file = os.path.join(self.data_dir, "servicenow_incidents.json")
        self.changes_file = os.path.join(self.data_dir, "servicenow_changes.json")
        self.created_tasks_file = os.path.join(self.data_dir, "servicenow_created_tasks.json")
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(self.created_tasks_file):
            with open(self.created_tasks_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_incidents(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.incidents_file):
            with open(self.incidents_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def get_changes(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.changes_file):
            with open(self.changes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def get_tasks(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.created_tasks_file):
            with open(self.created_tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def create_ticket(
        self,
        title: str,
        description: str,
        system_id: str = "SYS-LIMS-001",
        priority: str = "2 - High",
        assigned_group: str = "QA_Compliance_Systems"
    ) -> Dict[str, Any]:
        """
        Creates a mock ServiceNow remediation task ticket.
        Deterministically produces SNOW-TASK-1001 for the primary demo scenario!
        """
        tasks = self.get_tasks()
        next_num = 1001 + len(tasks)
        ticket_id = f"SNOW-TASK-{next_num}"
        
        ticket = {
            "ticket_id": ticket_id,
            "sys_id": f"snt_{next_num}_{int(datetime.now().timestamp())}",
            "number": ticket_id,
            "system_id": system_id,
            "short_description": title,
            "description": description,
            "priority": priority,
            "state": "Open / Work in Progress",
            "assigned_to": "Sarah Jenkins (Technical System Owner)",
            "assignment_group": assigned_group,
            "source": "Agentic AI Co-Pilot (Human-Authorized Workflow)",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "url": f"https://novonordisk.service-now.com/nav_to.do?uri=task.do?sys_id={ticket_id}"
        }
        
        tasks.append(ticket)
        with open(self.created_tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
            
        return ticket

# Global singleton
mock_servicenow = MockServiceNowConnector()
