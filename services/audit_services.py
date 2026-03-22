from sqlalchemy.orm import Session
from models import AuditLog, AuditActionEnum, User


def log_action(
    db: Session,
    action: AuditActionEnum.user_login,
    user: User,
    resource_id: int = None,
    detail: str = None
):
    
    audit = AuditLog(
        action = action,
        user_id = user.id,
        company_id = user.company_id,
        resource_id = resource_id,
        detail = detail
    )

    db.add(audit)