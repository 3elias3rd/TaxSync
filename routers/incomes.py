from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from models import get_db
from models import Income, User
from dependencies import require_manager, check_same_company, require_admin
from schemas import CreateIncome, IncomeResponse, PaginatedIncomeResponse
from auth import get_current_user
from math import ceil

router = APIRouter(prefix="/incomes", tags=["incomes"])


# View incomes (any logged in user can access)
@router.get("/", response_model=PaginatedIncomeResponse)
def get_incomes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)    
):
    # Base query scoped to company
    query = db.query(Income).filter(Income.company_id == current_user.company_id)

    total = query.count()
    skip = (page - 1) * page_size

    incomes = query.order_by(Income.date.desc()).offset(skip).limit(page_size).all()

    return PaginatedIncomeResponse.model_validate({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 0,
        "items": incomes
        })

@router.post("/", response_model=IncomeResponse)
def create_income(
    income_data: CreateIncome,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    new_income = Income(
        amount = income_data.amount,
        description = income_data.description,
        company_id = current_user.company_id,
        created_by = current_user.id
    )

    db.add(new_income)
    db.commit()
    db.refresh(new_income)

    return new_income

# Only managers and admin can delete incomes
@router.delete("/{income_id}")
def delete_income(income_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    
    income = db.query(Income).filter(Income.id == income_id).first()

    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    
    check_same_company(resource_company_id=income.company_id, current_user=current_user)

    db.delete(income)

    db.commit()


    return {"message": f"Income {income_id} successfully deleted."}


# Only managers and admin can approve
@router.put("/{income_id}/approve", response_model=IncomeResponse)
def approve_income(
    income_id: int,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    income = db.query(Income).filter(
        Income.id == income_id).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    
    check_same_company(
        resource_company_id=income.company_id,
        current_user=current_user
    )
    
    income.is_approved = True
    db.commit()
    db.refresh(income)
    
    return income