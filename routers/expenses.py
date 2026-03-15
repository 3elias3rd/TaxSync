from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db
from auth import get_current_user
from models import Expense, User
from dependencies import require_manager, check_same_company, require_admin
from schemas import ExpenseCreate, ExpenseResponse
from services.ai_services import get_category_id, get_nlp
from spacy.language import Language

router = APIRouter(prefix="/expenses", tags=["expenses"])


# View expenses (any logged in user can access)
@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expenses = db.query(Expense).filter(
    Expense.company_id == current_user.company_id)\
    .all()

    return expenses

# Create an expense (all users are authorized)
@router.post("/", response_model=ExpenseResponse)
def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    nlp: Language = Depends(get_nlp),
    db: Session = Depends(get_db)
):
    category_id = expense_data.category_id or get_category_id(expense_data.description, nlp, db)

    new_expense = Expense(
        amount = expense_data.amount,
        description = expense_data.description,
        company_id = current_user.company_id,
        created_by = current_user.id,
        
        # Use spacy model to extract category id
        category_id = category_id
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense

# Only managers and admin can delete expenses
@router.delete("/{expense_id}")
def delete_expense(expense_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    
    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    check_same_company(
        resource_company_id=expense.company_id,
        current_user=current_user
    )

    db.delete(expense)

    db.commit()


    return {"message": f"Expense {expense_id} successfuly deleted."}

# Only managers and admin can approve
@router.put("/{expense_id}/approve", response_model=ExpenseResponse)
def approve_expense(
    expense_id: int,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    check_same_company(
        resource_company_id=expense.company_id,
        current_user=current_user
        )
    
    expense.is_approved = True
    db.commit()
    db.refresh(expense)
    
    return expense
