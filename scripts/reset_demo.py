"""
Reset Demo script for Novo Nordisk Hackathon.
Clears demo records, recreates tables, seeds users, ingests all 10 dummy lifecycle documents,
and restores a clean, audit-ready demonstration state.
"""

import os
import sys
import shutil
from datetime import datetime, timezone

workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.entities import User, GENESIS_HASH, create_audit_log, verify_audit_chain
def reset_demo():
    print("============================================================")
    print("Resetting Demo Environment to Clean Pristine State")
    print("============================================================")

    # 1. Reset vector store
    if os.path.exists(settings.VECTOR_STORE_PATH):
        shutil.rmtree(settings.VECTOR_STORE_PATH)
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        print("  [+] Cleared vector store directory.")

    # 2. Recreate database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("  [+] Dropped and recreated all database tables.")

    # 3. Seed Base Users
    print("[*] Seeding Demo Users...")
    db = SessionLocal()
    demo_users = [
        {"name": "Sarah Jenkins", "email": "owner@demo.local", "role": "SYSTEM_OWNER", "dept": "IT Quality & Validated Systems"},
        {"name": "Dr. Elena Rostova", "email": "qa@demo.local", "role": "QA_COMPLIANCE", "dept": "Global Quality Assurance"},
        {"name": "Henrik Lindqvist", "email": "auditor@demo.local", "role": "AUDITOR", "dept": "Regulatory Affairs & Compliance"},
        {"name": "System Administrator", "email": "admin@demo.local", "role": "ADMIN", "dept": "GxP IT Operations"},
    ]
    for u in demo_users:
        if not db.query(User).filter(User.email == u["email"]).first():
            user = User(
                name=u["name"],
                email=u["email"],
                role=u["role"],
                department=u["dept"],
                permissions=["*"] if u["role"] == "ADMIN" else ["view", "review", "approve"]
            )
            db.add(user)
    db.commit()
    db.close()
    print("  [+] Seeded base users.")

    # 4. Generate and Ingest authentic MES PAS-X (SYS-MES-001) documents
    from scripts.ingest_pasx import ingest_pasx_documents
    ingest_pasx_documents()

    print("\n[+] Demo reset complete! The environment is ready for presentation.")

if __name__ == "__main__":
    reset_demo()
