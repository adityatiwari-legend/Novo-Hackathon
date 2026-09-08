import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Configure SQLite or PostgreSQL
db_url = settings.DATABASE_URL
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if "gxp_copilot.db" in db_url:
        root_db = os.path.join(settings.WORKSPACE_ROOT, "gxp_copilot.db")
        if os.path.exists(root_db):
            normalized_path = root_db.replace("\\", "/")
            db_url = f"sqlite:///{normalized_path}"

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
