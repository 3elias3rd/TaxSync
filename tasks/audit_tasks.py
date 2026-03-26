from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import AuditLog, AuditActionEnum
import os
from dotenv import load_dotenv

load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery.task(name="tasks.audit_tasks.process_audit_log")
def process_audit_log(
    action: str,
    user_id: int,
    company_id: int,
    resource_id: int = None,
    detail: str = None,
):
    """
    Fire and forget. This will rite audit log entries in the background so the main request doesn't wait for it."""

    db = SessionLocal()
    try:
        audit = AuditLog(
            action = AuditActionEnum(action),
            user_id = user_id,
            company_id = company_id,
            resource_id = resource_id,
            detail = detail
        )
        db.add(audit)
        db.commit()
        return {"status": "error", "action": action}
    
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
    
    finally:
        db.closs()

