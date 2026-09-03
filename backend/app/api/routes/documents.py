import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import sanitize_filename, validate_uploaded_file
from backend.app.models.entities import Document, DocumentChunk, create_audit_log
from backend.app.schemas.domain import DocumentResponse, DocumentChunkResponse
from backend.app.services.document_parser import parse_document
from backend.app.services.vector_store import vector_store
from backend.app.services.draft_service import draft_service

router = APIRouter(prefix="/documents", tags=["Documents"])

class DraftSectionRequest(BaseModel):
    section_name: str = "6. QA Approval & Validation Sign-Off"
    document_title: str = "System_A_URS.docx"
    system_name: str = "System A: Validated LIMS"
    finding_context: str = "QA approval missing from URS."

class ExportDraftRequest(BaseModel):
    draft_text: str
    section_name: str
    document_title: str

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    system_id: str = Form("SYS-LIMS-001"),
    source_system: str = Form("Local Upload"),
    db: Session = Depends(get_db)
):
    safe_name = sanitize_filename(file.filename)
    contents = await file.read()
    validate_uploaded_file(safe_name, len(contents))
    
    # Save file to upload directory
    target_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(target_path, "wb") as f:
        f.write(contents)
        
    # Ingestion & Parsing
    parsed = parse_document(target_path, default_system_id=system_id)
    
    # Check if duplicate or update existing
    existing = db.query(Document).filter(
        Document.title == parsed.title,
        Document.system_id == system_id
    ).first()
    
    if existing:
        doc = existing
        doc.file_path = target_path
        doc.checksum = parsed.checksum
        doc.version = parsed.version
        doc.approval_status = parsed.approval_status
        doc.review_date = parsed.review_date
        doc.owner_id = parsed.owner
        doc.metadata_json = {"sections": parsed.sections}
    else:
        doc = Document(
            title=parsed.title,
            document_type=parsed.document_type,
            system_id=system_id,
            version=parsed.version,
            owner_id=parsed.owner,
            status="Effective" if parsed.approval_status == "Approved" else "Draft",
            review_date=parsed.review_date,
            approval_status=parsed.approval_status,
            source_system=source_system,
            file_path=target_path,
            checksum=parsed.checksum,
            metadata_json={"sections": parsed.sections}
        )
        db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Persist Chunks and Index in Vector Store
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
    db.commit()
    
    vector_chunks = []
    for c in parsed.chunks:
        chunk_rec = DocumentChunk(
            document_id=doc.id,
            chunk_index=c.chunk_index,
            content=c.content,
            page_number=c.page_number,
            section=c.section,
            embedding_reference=f"vec_{doc.id}_{c.chunk_index}",
            metadata_json=c.metadata
        )
        db.add(chunk_rec)
        
        vector_chunks.append({
            "id": f"{doc.id}_{c.chunk_index}",
            "document_id": doc.id,
            "document_title": doc.title,
            "system_id": system_id,
            "content": c.content,
            "page_number": c.page_number,
            "section": c.section,
            "metadata": c.metadata
        })
    db.commit()
    
    # Add to hybrid vector store
    vector_store.add_chunks(vector_chunks)
    
    # Append-only Tamper-Evident Audit Trail
    create_audit_log(
        db=db,
        actor_type="USER",
        actor_id="qa@demo.local",
        action="Uploaded GxP Document",
        entity_type="DOCUMENT",
        entity_id=doc.id,
        details={
            "filename": safe_name,
            "document_type": doc.document_type,
            "version": doc.version,
            "checksum": doc.checksum,
            "chunks_indexed": len(parsed.chunks)
        }
    )
    
    return doc

@router.get("", response_model=List[DocumentResponse])
def list_documents(system_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Document)
    if system_id:
        query = query.filter(Document.system_id == system_id)
    docs = query.order_by(Document.created_at.desc()).all()
    for d in docs:
        d.chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).count()
    return docs

@router.get("/{id}", response_model=DocumentResponse)
def get_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
    return doc

@router.get("/{id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(id: str, db: Session = Depends(get_db)):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == id).order_by(DocumentChunk.chunk_index.asc()).all()
    return chunks

@router.post("/draft-section")
def draft_missing_section(req: DraftSectionRequest):
    """Generates an AI draft for missing compliance sections."""
    return draft_service.generate_draft_section(
        section_name=req.section_name,
        document_title=req.document_title,
        system_name=req.system_name,
        finding_context=req.finding_context
    )

@router.post("/draft-section/export")
def export_draft_docx(req: ExportDraftRequest):
    """Exports AI generated draft as a formal DOCX with regulatory watermark."""
    filepath = draft_service.export_draft_docx(
        draft_text=req.draft_text,
        section_name=req.section_name,
        document_title=req.document_title
    )
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
