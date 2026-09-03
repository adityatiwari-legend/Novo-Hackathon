from typing import Dict, Any, List
from backend.app.schemas.domain import AgentResult

class StubAgent:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category

    def run(self, **kwargs) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status="stubbed",
            confidence=1.0,
            findings=[],
            citations=[],
            recommendations=[],
            warnings=[f"Agent '{self.name}' is a registered enterprise stub for future integration."],
            metadata={
                "description": self.description,
                "category": self.category,
                "is_stub": True,
                "api_ready": True
            }
        )

change_release_agent = StubAgent(
    name="change_and_release_agent",
    description="Analyzes planned change requests against GAMP 5 category regression impact.",
    category="Lifecycle Management"
)

incident_anomaly_agent = StubAgent(
    name="incident_anomaly_agent",
    description="Detects telemetry anomalies, backup latency spikes, and audit trail gaps.",
    category="Continuous Monitoring"
)

access_review_agent = StubAgent(
    name="access_review_agent",
    description="Performs periodic segregation-of-duties and dormant account evaluations against IAM.",
    category="Identity & Access"
)

workflow_automation_agent = StubAgent(
    name="workflow_automation_agent",
    description="Pre-populates ServiceNow change and CAPA templates following human authorization.",
    category="Enterprise Orchestration"
)

self_healing_agent = StubAgent(
    name="self_healing_agent",
    description="Drafts remediation configuration patches and SOP updates for human review.",
    category="Remediation"
)

REGISTERED_STUB_AGENTS = {
    "change_and_release": change_release_agent,
    "incident_anomaly": incident_anomaly_agent,
    "access_review": access_review_agent,
    "workflow_automation": workflow_automation_agent,
    "self_healing": self_healing_agent
}
