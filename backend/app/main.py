from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import engine, Base
import backend.app.models.entities  # Ensure all models are registered with Base

# Import API routers
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.query import router as query_router
from backend.app.api.routes.compliance import router as compliance_router
from backend.app.api.routes.evidence import router as evidence_router
from backend.app.api.routes.workflows import router as workflows_router
from backend.app.api.routes.dashboard import router as dashboard_router
from backend.app.api.routes.audit_log import router as audit_log_router
from backend.app.api.routes.agents import router as agents_router
from backend.app.api.routes.simulation import router as simulation_router
from backend.app.api.routes.audit_checklist import router as audit_checklist_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto create tables on startup
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Agentic AI Co-Pilot for Always-On GxP IT System Management",
    description=(
        "Production-quality Hackathon prototype for Novo Nordisk. "
        "Transforms fragmented compliance repositories into a continuous, audit-ready AI workflow. "
        "\n\n**Regulatory Notice**: Prototype aligned with GxP / ALCOA+ principles. "
        "Designed with human approval and auditability. Production deployment would require formal "
        "validation, qualification, security assessment, and organizational controls."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(query_router, prefix=settings.API_V1_STR)
app.include_router(compliance_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(workflows_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(audit_log_router, prefix=settings.API_V1_STR)
app.include_router(agents_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(audit_checklist_router, prefix=settings.API_V1_STR)

from backend.app.services.llm_provider import get_llm_provider

@app.get(f"{settings.API_V1_STR}/ai/health", tags=["AI Provider Health"])
def get_ai_health():
    return get_llm_provider().health_check()

@app.get("/")
def root():
    return {
        "project": "Agentic AI Co-Pilot for GxP IT System Management",
        "company": "Novo Nordisk Hackathon 2026",
        "status": "OPERATIONAL",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "compliance_disclaimer": "Prototype aligned with GxP / ALCOA+ principles. Designed with human approval and auditability."
    }

@app.get("/health")
def health_check():
    return {
        "status": "Healthy",
        "demo_mode": settings.DEMO_MODE,
        "mock_servicenow": settings.MOCK_SERVICENOW,
        "mock_vault": settings.MOCK_VAULT
    }
