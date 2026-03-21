from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from math import ceil
from models import get_db, AuditLog, User, AuditActionEnum
from dependencies import require_manager
from schemas import PaginatedAuditLogResponse
from typing import Optional

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/", response_model=PaginatedAuditLogResponse)
def get_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    action: Optional[AuditActionEnum] = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)\
    .filter(AuditLog.company_id == current_user.company_id)\
    .order_by(AuditLog.timestamp.desc())

    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.offset((page-1) * page_size).limit(page_size).all()

    return PaginatedAuditLogResponse.model_validate({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 0,
        "items": logs
    })