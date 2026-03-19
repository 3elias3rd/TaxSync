from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from models import Income, User
from dependencies import require_manager, check_same_company, require_admin, block_demo_user
from schemas import CreateIncome, IncomeResponse
from auth import get_current_user

router = APIRouter(prefix="/incomes", tags=["incomes"])


# View incomes (any logged in user can access)
@router.get("/", response_model=list[IncomeResponse])
def get_incomes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    incomes = db.query(Income).filter(Income.company_id == current_user.company_id).all()

    return incomes

@router.post("/", response_model=IncomeResponse)
def create_income(
    income_data: CreateIncome,
    current_user: User = Depends(get_current_user),
    _: User = Depends(block_demo_user),
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
def delete_income(
    income_id: int,
    current_user: User = Depends(require_admin),
    _: User = Depends(block_demo_user),
    db: Session = Depends(get_db)
):
    
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
    _: User = Depends(block_demo_user),
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