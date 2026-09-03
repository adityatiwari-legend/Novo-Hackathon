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
from scripts.create_mes_lifecycle_documents import generate_all_mes_documents
from scripts.ingest_demo_documents import ingest_all_lifecycle_documents

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

    # 3. Seed Base Users & System A (SYS-LIMS-001)
    from scripts.seed_database import seed as seed_lims
    seed_lims()
    print("  [+] Seeded System A (SYS-LIMS-001) and baseline demo records.")

    # 4. Generate and Ingest authentic MES PAS-X (SYS-MES-001) documents
    generate_all_mes_documents()
    ingest_all_lifecycle_documents()

    print("\n[+] Demo reset complete! The environment is ready for presentation.")

if __name__ == "__main__":
    reset_demo()
