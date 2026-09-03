from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.entities import System, Document
from backend.app.schemas.domain import AgentResult

class SystemKnowledgeAgent:
    def __init__(self):
        self.name = "system_knowledge_agent"

    def run(self, db: Session, system_id: str = "SYS-LIMS-001") -> AgentResult:
        system = db.query(System).filter(System.id == system_id).first()
        docs = db.query(Document).filter(Document.system_id == system_id).all()
        
        system_info = {
            "id": system.id if system else system_id,
            "name": system.name if system else "Validated LIMS",
            "criticality": system.criticality if system else "GxP-Critical",
            "business_owner": system.business_owner if system else "Dr. Marcus Vance",
            "documents_count": len(docs)
        }
        
        applicable_sops = []
        urs_docs = []
        stale_docs = []
        
        citations = []
        for d in docs:
            citations.append({
                "document": d.title,
                "version": d.version,
                "type": d.document_type,
                "status": d.status,
                "approval_status": d.approval_status
            })
            if d.document_type == "SOP":
                applicable_sops.append(f"{d.title} (v{d.version})")
            elif d.document_type == "URS":
                urs_docs.append(f"{d.title} (v{d.version}, status: {d.approval_status})")
            if d.status == "Overdue":
                stale_docs.append(d.title)
                
        return AgentResult(
            agent=self.name,
            status="completed",
            confidence=0.98,
            findings=[],
            citations=citations,
            recommendations=[],
            warnings=[f"Identified {len(stale_docs)} stale documents: {', '.join(stale_docs)}"] if stale_docs else [],
            metadata={
                "system": system_info,
                "applicable_sops": applicable_sops,
                "urs_documents": urs_docs,
                "stale_documents": stale_docs
            }
        )

system_knowledge_agent = SystemKnowledgeAgent()
