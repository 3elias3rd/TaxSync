from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db, User
from dependencies import require_manager, check_same_company
from schemas import UserResponse
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):  
    return current_user

# Get all users for a given company (manager and above)
@router.get("/", response_model=list[UserResponse])
def get_all_users(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    
    company_users = db.query(User)\
        .filter(User.company_id == current_user.company_id)\
        .all()

    return  company_users

#  Get user endpoin (manager and above)
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter( User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    check_same_company(user.company_id, current_user)

    return user