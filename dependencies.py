from fastapi import Depends, HTTPException
from auth import get_current_user
from models import User, RoleEnum

# Check if the user is a manager or admin
def require_manager(current_user: User = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.manager, RoleEnum.admin]:
        raise HTTPException (status_code=403, detail="You do not have the access for this task.")
    return current_user

# Check if the user is an admin
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="You do not have the access for this task.")
    return current_user

def check_same_company(resource_company_id: int, current_user: User):
    if resource_company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied, resource belongs to a different company")
    
def block_demo_user(current_user: User = Depends(get_current_user)):
    if current_user.username == "demo_employee":
        raise HTTPException(
            status_code=403,
            detail="Demo accounts are read-only and cannot perform this action"
        )
    return current_user