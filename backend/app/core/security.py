import os
import re
import hashlib
from typing import List, Optional
from fastapi import HTTPException, status, Header

class Roles:
    ADMIN = "ADMIN"
    QA_COMPLIANCE = "QA_COMPLIANCE"
    SYSTEM_OWNER = "SYSTEM_OWNER"
    IT_OPS = "IT_OPS"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"

ROLE_PERMISSIONS = {
    Roles.ADMIN: ["*"],
    Roles.QA_COMPLIANCE: [
        "view_dashboard", "view_documents", "upload_documents", "run_compliance",
        "view_risk", "generate_evidence", "approve_workflow", "reject_workflow", "view_audit_trail"
    ],
    Roles.SYSTEM_OWNER: [
        "view_dashboard", "view_documents", "upload_documents", "run_compliance",
        "view_risk", "generate_evidence", "view_audit_trail", "create_workflow"
    ],
    Roles.IT_OPS: [
        "view_dashboard", "view_documents", "view_risk", "view_audit_trail"
    ],
    Roles.AUDITOR: [
        "view_dashboard", "view_documents", "view_compliance", "view_risk",
        "view_evidence", "generate_evidence", "view_audit_trail"
    ],
    Roles.VIEWER: [
        "view_dashboard", "view_documents", "view_compliance", "view_risk"
    ]
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

def sanitize_filename(filename: str) -> str:
    """Strip out path traversal characters and unsafe characters."""
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    return clean

def validate_uploaded_file(filename: str, file_size: int):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        )

def compute_sha256(data) -> str:
    """Compute SHA-256 hash of bytes, file path, or string."""
    if isinstance(data, bytes):
        return hashlib.sha256(data).hexdigest()
    if isinstance(data, str):
        if os.path.isfile(data):
            h = hashlib.sha256()
            with open(data, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

def check_permission(user_role: str, required_permission: str) -> bool:
    if user_role == Roles.ADMIN:
        return True
    perms = ROLE_PERMISSIONS.get(user_role, [])
    return required_permission in perms or "*" in perms
