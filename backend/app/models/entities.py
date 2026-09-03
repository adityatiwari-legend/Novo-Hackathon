import uuid
import json
import hashlib
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False)
    department = Column(String(100), nullable=True)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=get_utc_now)

class System(Base):
    __tablename__ = "systems"
    
    id = Column(String(50), primary_key=True)  # e.g., 'SYS-LIMS-001' or uuid
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), nullable=True)
    criticality = Column(String(50), default="GxP-Critical")  # GxP-Critical, Non-Critical
    gxp_status = Column(String(50), default="GxP")
    business_owner = Column(String(150), nullable=True)
    lifecycle_status = Column(String(100), default="PRE-OPERATIONAL / NOT ACTIVATED")
    release_recommendation = Column(String(100), default="HOLD / DEFER - DO NOT RELEASE")
    readiness_score = Column(Integer, default=48)
    last_assessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    
    documents = relationship("Document", back_populates="system")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)  # URS, RISK_ASSESSMENT, SOP, POLICY
    system_id = Column(String(50), ForeignKey("systems.id"), nullable=True)
    version = Column(String(50), default="1.0")
    owner_id = Column(String(150), nullable=True)
    status = Column(String(50), default="Draft")  # Draft, Effective, Archived, Overdue
    review_date = Column(String(50), nullable=True)
    approval_status = Column(String(50), default="Pending")  # Approved, Pending, Rejected, Not found
    source_system = Column(String(100), default="Local Upload")  # Vault, SharePoint, ServiceNow, Local Upload
    file_path = Column(String(500), nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    system = relationship("System", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    embedding_reference = Column(String(100), nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    document = relationship("Document", back_populates="chunks")

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    document_id = Column(String(36), nullable=True)
    check_code = Column(String(50), nullable=False)
    requirement = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False)  # PASS, FAIL, WARNING, NOT_EVALUATED
    severity = Column(String(50), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    evidence = Column(Text, nullable=True)
    citation_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=get_utc_now)

class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    document_id = Column(String(36), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status = Column(String(50), default="OPEN")  # OPEN, IN_REVIEW, REMEDIATED, ACCEPTED
    confidence = Column(Float, default=0.9)
    source_citations = Column(JSON, default=list)
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    finding_id = Column(String(36), nullable=True)
    risk_level = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    impact_type = Column(String(100), nullable=False)  # GxP, Data Integrity, Security, Operational
    likelihood = Column(String(50), nullable=False)  # Low, Medium, High
    impact = Column(String(50), nullable=False)  # Low, Medium, High, Critical
    score = Column(Integer, nullable=False)  # 1 to 25
    rationale = Column(Text, nullable=False)
    control_mapping = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    finding_id = Column(String(36), nullable=True)
    source_agent = Column(String(100), default="recommendation_agent")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    rationale = Column(Text, nullable=False)
    suggested_owner = Column(String(150), nullable=True)
    status = Column(String(50), default="PROPOSED")  # PROPOSED, IN_WORKFLOW, APPROVED, REJECTED, COMPLETED
    confidence = Column(Float, default=0.92)
    created_at = Column(DateTime, default=get_utc_now)

class EvidencePack(Base):
    __tablename__ = "evidence_packs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0")
    scope = Column(String(255), default="Full GxP IT Audit Readiness Assessment")
    file_path = Column(String(500), nullable=True)
    docx_file_path = Column(String(500), nullable=True)
    citations_json = Column(JSON, default=list)
    status = Column(String(50), default="GENERATED")  # GENERATED, REVIEWED, APPROVED
    generated_by = Column(String(150), default="audit_evidence_agent")
    approved_by = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(100), nullable=False)  # REMEDIATION_TASK, APPROVAL_GATE, CAPA_CREATION
    system_id = Column(String(50), nullable=False, index=True)
    recommendation_id = Column(String(36), nullable=True)
    status = Column(String(50), default="PENDING_APPROVAL")  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String(150), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    payload_json = Column(JSON, default=dict)  # Contains details like snow_task_id, target action
    created_at = Column(DateTime, default=get_utc_now)

class Requirement(Base):
    __tablename__ = "requirements"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    requirement_id = Column(String(50), nullable=False, index=True)  # e.g. URS-001
    system_id = Column(String(50), nullable=False, index=True)
    document_id = Column(String(50), nullable=True)
    text = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # FUNCTIONAL, NON_FUNCTIONAL
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(100), nullable=True)
    risk_reference = Column(String(50), nullable=True)  # RSK-MES-001
    verification_reference = Column(String(100), nullable=True)
    status = Column(String(50), default="OPEN")  # VERIFIED, OPEN, NOT_PERFORMED
    created_at = Column(DateTime, default=get_utc_now)

class TraceabilityLink(Base):
    __tablename__ = "traceability_links"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    requirement_id = Column(String(50), nullable=False, index=True)
    fs_id = Column(String(50), nullable=True)
    risk_id = Column(String(50), nullable=True)
    test_id = Column(String(50), nullable=True)
    test_status = Column(String(50), default="NOT_PERFORMED")  # COMPLETE, NOT_PERFORMED, OPEN
    implementation_status = Column(String(50), default="NOT_MET")
    created_at = Column(DateTime, default=get_utc_now)

class ReleaseGate(Base):
    __tablename__ = "release_gates"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    gate_code = Column(String(20), nullable=False, index=True)  # G1, G2, G3, G4, G5, G6
    gate_name = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False)  # MET, NOT_MET, PENDING, BLOCKED
    evidence_doc = Column(String(100), nullable=True)
    evidence_section = Column(String(100), nullable=True)
    blocking_reason = Column(Text, nullable=True)
    prerequisites = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class AuditLog(Base):
    """
    Tamper-Evident Append-Only Audit Trail.
    Never exposes DELETE or UPDATE.
    Hash Chaining: event_hash = SHA256(previous_hash + canonical_event_json)
    """
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    actor_type = Column(String(50), nullable=False)  # USER, AGENT, SYSTEM
    actor_id = Column(String(150), nullable=False)
    user_id = Column(String(36), nullable=True)
    agent_name = Column(String(100), nullable=True)
    action = Column(String(150), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    request_id = Column(String(100), nullable=True)
    details_json = Column(JSON, default=dict)
    previous_hash = Column(String(64), nullable=False)
    event_hash = Column(String(64), nullable=False, index=True)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def format_canonical_ts(dt) -> str:
    if isinstance(dt, str):
        # Truncate any subsecond or timezone differences
        return dt[:19].replace(" ", "T")
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def create_audit_log(
    db,
    actor_type: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict,
    user_id: str = None,
    agent_name: str = None,
    request_id: str = None
) -> AuditLog:
    """
    Appends a new record to the tamper-evident Audit Trail.
    Calculates: event_hash = SHA256(previous_hash + canonical_event_json)
    """
    last_log = db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
    previous_hash = last_log.event_hash if last_log else GENESIS_HASH
    
    timestamp_dt = get_utc_now()
    canonical_ts = format_canonical_ts(timestamp_dt)
    
    canonical_payload = {
        "timestamp": canonical_ts,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "user_id": user_id,
        "agent_name": agent_name,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "request_id": request_id,
        "details": details
    }
    canonical_str = json.dumps(canonical_payload, sort_keys=True, default=str)
    event_hash = hashlib.sha256((previous_hash + canonical_str).encode("utf-8")).hexdigest()
    
    audit_entry = AuditLog(
        timestamp=timestamp_dt,
        actor_type=actor_type,
        actor_id=actor_id,
        user_id=user_id,
        agent_name=agent_name,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        request_id=request_id,
        details_json=details,
        previous_hash=previous_hash,
        event_hash=event_hash
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

def verify_audit_chain(db):
    """
    Verifies the cryptographic integrity of the entire audit chain.
    Returns: (is_valid, records_checked, message)
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()
    if not logs:
        return True, 0, "Audit log is empty. Genesis state intact."
        
    expected_prev = GENESIS_HASH
    for idx, entry in enumerate(logs):
        if entry.previous_hash != expected_prev:
            return False, idx, f"Broken link at entry {entry.id}: previous_hash mismatch"
            
        canonical_payload = {
            "timestamp": format_canonical_ts(entry.timestamp),
            "actor_type": entry.actor_type,
            "actor_id": entry.actor_id,
            "user_id": entry.user_id,
            "agent_name": entry.agent_name,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": str(entry.entity_id),
            "request_id": entry.request_id,
            "details": entry.details_json
        }
        canonical_str = json.dumps(canonical_payload, sort_keys=True, default=str)
        recalculated = hashlib.sha256((expected_prev + canonical_str).encode("utf-8")).hexdigest()
        
        if recalculated != entry.event_hash:
            return False, idx, f"Cryptographic integrity failed at entry {entry.id}: event_hash mismatch"
            
        expected_prev = entry.event_hash
        
    return True, len(logs), "All audit trail records cryptographically verified."


class AuditChecklist(Base):
    __tablename__ = "audit_checklists"

    id = Column(String(50), primary_key=True)  # e.g., 'CKL-TOP25-CORE', 'CKL-PHASE-01'
    title = Column(String(255), nullable=False)
    version = Column(String(50), default="2026.1")
    source_file = Column(String(255), default="Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    questions = relationship("AuditQuestion", back_populates="checklist", cascade="all, delete-orphan")


class AuditQuestion(Base):
    __tablename__ = "audit_questions"

    id = Column(String(50), primary_key=True)  # e.g. 'DA-01-001' or 'CORE-01'
    checklist_id = Column(String(50), ForeignKey("audit_checklists.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    phase_no = Column(String(20), nullable=True)
    lifecycle_phase = Column(String(100), nullable=True)
    audit_domain = Column(String(100), nullable=True)
    control_topic = Column(String(150), nullable=True)
    priority = Column(String(50), default="Critical")  # Critical, High, Medium, Low
    audit_question = Column(Text, nullable=False)
    follow_up_probe = Column(Text, nullable=True)
    audit_rationale = Column(Text, nullable=True)
    expected_evidence = Column(Text, nullable=True)
    sampling_triangulation = Column(Text, nullable=True)
    primary_roles = Column(String(255), nullable=True)
    regulatory_alignment = Column(Text, nullable=True)
    source_urls = Column(Text, nullable=True)
    red_flags = Column(Text, nullable=True)
    sheet_name = Column(String(100), nullable=True)
    row_number = Column(Integer, nullable=True)
    weight = Column(Integer, default=10)

    checklist = relationship("AuditChecklist", back_populates="questions")


class AuditAssessment(Base):
    __tablename__ = "audit_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    system_id = Column(String(50), nullable=False, index=True)
    checklist_id = Column(String(50), nullable=False, index=True)
    assessed_at = Column(DateTime, default=get_utc_now)
    readiness_score = Column(Float, default=0.0)
    total_questions = Column(Integer, default=25)
    passed_count = Column(Integer, default=0)
    partial_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    not_evidenced_count = Column(Integer, default=0)
    na_count = Column(Integer, default=0)
    critical_findings_count = Column(Integer, default=0)
    high_findings_count = Column(Integer, default=0)
    medium_findings_count = Column(Integer, default=0)
    low_findings_count = Column(Integer, default=0)
    items_json = Column(JSON, default=list)
    findings_json = Column(JSON, default=list)
    lifecycle_gaps_json = Column(JSON, default=list)
    status = Column(String(50), default="COMPLETED")

    evidences = relationship("AuditEvidence", back_populates="assessment", cascade="all, delete-orphan")


class AuditEvidence(Base):
    __tablename__ = "audit_evidences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("audit_assessments.id"), nullable=False, index=True)
    question_id = Column(String(50), nullable=False, index=True)
    system_id = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # PASS, PARTIAL, FAIL, NOT_EVIDENCED, NOT_APPLICABLE
    evidence_text = Column(Text, nullable=True)
    evidence_quality = Column(String(50), default="Found")  # Found, Partial, Missing, Conflicting
    confidence = Column(Float, default=0.9)
    citations_json = Column(JSON, default=list)
    gap_description = Column(Text, nullable=True)
    risk_level = Column(String(50), default="LOW")  # CRITICAL, HIGH, MEDIUM, LOW
    recommendation = Column(Text, nullable=True)

    assessment = relationship("AuditAssessment", back_populates="evidences")

