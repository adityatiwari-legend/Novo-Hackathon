from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import Relationship, Requirement, Risk, ReleaseGate

def get_requirement_trace(db: Session, requirement_id: str) -> Dict[str, Any]:
    """
    Returns the forward and backward trace for a specific requirement.
    """
    req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
    if not req:
        return None
        
    forward_rels = db.query(Relationship).filter(
        Relationship.source_entity_type == "REQUIREMENT",
        Relationship.source_entity_id == requirement_id
    ).all()
    
    backward_rels = db.query(Relationship).filter(
        Relationship.target_entity_type == "REQUIREMENT",
        Relationship.target_entity_id == requirement_id
    ).all()
    
    return {
        "requirement": {
            "id": req.requirement_id,
            "text": req.text,
            "status": req.status
        },
        "forward_trace": [{"type": r.target_entity_type, "id": r.target_entity_id, "rel": r.relationship_type} for r in forward_rels],
        "backward_trace": [{"type": r.source_entity_type, "id": r.source_entity_id, "rel": r.relationship_type} for r in backward_rels]
    }

def get_risk_trace(db: Session, risk_id: str) -> Dict[str, Any]:
    """
    Returns the forward and backward trace for a specific risk.
    """
    rk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not rk:
        return None
        
    forward_rels = db.query(Relationship).filter(
        Relationship.source_entity_type == "RISK",
        Relationship.source_entity_id == risk_id
    ).all()
    
    backward_rels = db.query(Relationship).filter(
        Relationship.target_entity_type == "RISK",
        Relationship.target_entity_id == risk_id
    ).all()
    
    return {
        "risk": {
            "id": rk.id,
            "level": rk.risk_level,
            "rationale": rk.rationale
        },
        "forward_trace": [{"type": r.target_entity_type, "id": r.target_entity_id, "rel": r.relationship_type} for r in forward_rels],
        "backward_trace": [{"type": r.source_entity_type, "id": r.source_entity_id, "rel": r.relationship_type} for r in backward_rels]
    }
