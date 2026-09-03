from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models import AuditLog, verify_audit_chain
from backend.app.schemas.domain import AuditLogResponse, AuditChainVerificationResponse

router = APIRouter(prefix="/audit-log", tags=["Tamper-Evident Audit Trail"])

@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns the append-only audit log events in reverse chronological order.
    No DELETE or UPDATE endpoints exist for this ledger.
    """
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(limit).all()

@router.get("/verify", response_model=AuditChainVerificationResponse)
def verify_hash_chain(db: Session = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 hash chaining of all audit events:
    event_hash = SHA256(previous_hash + canonical_event_json)
    """
    is_valid, count, message = verify_audit_chain(db)
    return AuditChainVerificationResponse(
        is_valid=is_valid,
        records_checked=count,
        message=message
    )
