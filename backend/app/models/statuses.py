from enum import Enum

class EvidenceState(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    UNAPPROVED = "UNAPPROVED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICTING = "CONFLICTING"
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    OVERDUE = "OVERDUE"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"

def map_legacy_status(legacy_status: str) -> str:
    """Helper to map legacy/internal statuses to canonical EvidenceState."""
    status_upper = legacy_status.upper() if legacy_status else ""
    
    if "DRAFT" in status_upper or "PENDING" in status_upper or "UNAPPROVED" in status_upper:
        return EvidenceState.UNAPPROVED.value
    elif "APPROVED" in status_upper or "EFFECTIVE" in status_upper or "SIGNED" in status_upper:
        return EvidenceState.PRESENT.value
    elif "NOT MET" in status_upper or "BLOCKED" in status_upper:
        return EvidenceState.BLOCKED.value
    elif "MET" in status_upper or "PASS" in status_upper or "COMPLETE" in status_upper:
        return EvidenceState.VERIFIED.value
    elif "FAIL" in status_upper or "NOT_PERFORMED" in status_upper or "NOT PERFORMED" in status_upper:
        return EvidenceState.NOT_VERIFIED.value
    elif "OPEN" in status_upper:
        return EvidenceState.OPEN.value
    elif "CLOSED" in status_upper or "REMEDIATED" in status_upper:
        return EvidenceState.CLOSED.value
    elif "EXPIRED" in status_upper:
        return EvidenceState.EXPIRED.value
    else:
        return EvidenceState.UNKNOWN.value
