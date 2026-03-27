from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import AuditLog, AuditActionEnum
import os
from dotenv import load_dotenv

load_dotenv(".env")

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

@celery.task(name="tasks.audit_tasks.process_audit_log")
def process_audit_log(
    action: str,
    user_id: int,
    company_id: int,
    resource_id: int = None,
    detail: str = None,
):
    """Fire and forget. Writes audit log entries in the background."""
    db = SessionLocal()
    try:
        audit = AuditLog(
            action=AuditActionEnum(action),
            user_id=user_id,
            company_id=company_id,
            resource_id=resource_id,
            detail=detail,
        )
        db.add(audit)
        db.commit()
        return {"status": "success", "action": action}

    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}

    finally:
        db.close()