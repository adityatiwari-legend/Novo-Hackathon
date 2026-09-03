from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.integrations.mock_monitoring import continuous_monitor

router = APIRouter(prefix="/simulation", tags=["Continuous Compliance Simulation"])

@router.post("/trigger")
def trigger_simulation(system_id: str = "SYS-LIMS-001", db: Session = Depends(get_db)):
    """
    Triggers simulated background expiration of SOP_Document_Management.docx.
    Readiness drops 82% -> 76%, new finding and recommendation generated, audit log appended.
    """
    return continuous_monitor.trigger_document_expiration_event(db, system_id=system_id)

@router.post("/reset")
def reset_simulation(system_id: str = "SYS-LIMS-001", db: Session = Depends(get_db)):
    """Resets the simulation back to initial state (82% readiness)."""
    return continuous_monitor.reset_simulation(db, system_id=system_id)

@router.get("/status")
def get_simulation_status():
    return {
        "simulation_active": continuous_monitor.simulation_active,
        "description": "Continuous Compliance Monitor watches document expiration and telemetry."
    }
