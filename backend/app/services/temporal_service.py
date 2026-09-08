from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from backend.app.models.entities import EvidenceItem, Document

def get_applicable_evidence(db: Session, system_id: str, target_date: datetime = None) -> List[EvidenceItem]:
    """
    Returns evidence items for a given system that are valid at target_date.
    If target_date is None, returns currently active evidence.
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc)
        
    if target_date.tzinfo is None:
        target_date = target_date.replace(tzinfo=timezone.utc)
        
    # Join EvidenceItem with Document to filter by system_id and dates
    query = db.query(EvidenceItem).join(Document, EvidenceItem.document_id == Document.id).filter(
        Document.system_id == system_id
    )
    
    items = query.all()
    valid_items = []
    
    for item in items:
        # If the item has its own effective dates, use them. Otherwise, fall back to Document's effective dates.
        eff_from = item.effective_from or item.document.effective_from
        eff_to = item.effective_to or item.document.effective_to
        
        # Check date validity
        is_valid = True
        if eff_from:
            if eff_from.tzinfo is None:
                eff_from = eff_from.replace(tzinfo=timezone.utc)
            if eff_from > target_date:
                is_valid = False
        if eff_to:
            if eff_to.tzinfo is None:
                eff_to = eff_to.replace(tzinfo=timezone.utc)
            if eff_to < target_date:
                is_valid = False
            
        if is_valid:
            valid_items.append(item)
            
    return valid_items
