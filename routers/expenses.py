from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from sqlalchemy.orm import Session, joinedload
from models import get_db
from auth import get_current_user
from models import Expense, User, AuditActionEnum
from dependencies import require_manager, check_same_company, require_admin, block_demo_user
from schemas import ExpenseCreate, ExpenseResponse, PaginatedExpenseResponse
from services.ai_services import get_category_id, get_nlp
from services.audit_services import log_action

from tasks.expense_tasks import categorise_expense
from tasks.audit_tasks import process_audit_log

from spacy.language import Language
from math import ceil

router = APIRouter(prefix="/expenses", tags=["expenses"])


# View expenses (any logged in user can access)
@router.get("/", response_model=PaginatedExpenseResponse)
@cache(expire=60) # 1 minute TTL
def get_expenses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    total = db.query(Expense).filter(Expense.company_id == current_user.company_id).count() # Total count of expenses

    skip = (page -1) * page_size # Calculate offset

    expenses = db.query(Expense)\
        .options(joinedload(Expense.category))\
        .filter(Expense.company_id == current_user.company_id)\
        .order_by(Expense.date.desc())\
        .offset(skip)\
        .limit(page_size)\
        .all()

    return PaginatedExpenseResponse.model_validate({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total/page_size) if total > 0 else 0,
        "items": expenses
    })

# Clear expense cache
async def invalidate_expense_cache():
    await FastAPICache.get_backend().clear(namespace="taxsync-cache")


# Create an expense (all users are authorized)
@router.post("/", response_model=ExpenseResponse)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    _: User = Depends(block_demo_user),
    nlp: Language = Depends(get_nlp),
    db: Session = Depends(get_db)
):
    new_expense = Expense(
        amount = expense_data.amount,
        description = expense_data.description,
        company_id = current_user.company_id,
        category_id = expense_data.category_id, # May be none
        created_by = current_user.id,
        date = expense_data.date,
        
        # Use spacy model to extract category id
        
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # Dispatch categorisation a background task if not provided
    if not expense_data.category_id:
        categorise_expense.delay(new_expense.id) # Fire and forget

    # Dispatch logging to background
    process_audit_log.delay(
        action = "expense_created",
        user_id = current_user.id,
        company_id = current_user.company_id,
        resource_id = new_expense.id,
        detail = f"Created expense: {new_expense.description} -- AED {new_expense.amount}"
    )

    await invalidate_expense_cache()
    return new_expense

# Only managers and admin can delete expenses
@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user: User = Depends(require_admin),
    _: User = Depends(block_demo_user),
    db: Session = Depends(get_db)
):
    
    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    check_same_company(
        resource_company_id=expense.company_id,
        current_user=current_user
    )

    # Log expense before deleting
    log_action(
        db = db,
        action = AuditActionEnum.expense_deleted,
        user = current_user,
        resource_id = expense_id,
        detail = f"Deleted expense: {expense.description} -- AED {expense.amount}" 
    )

    db.delete(expense)
    db.commit()

    await invalidate_expense_cache()
    return {"message": f"Expense {expense_id} successfuly deleted."}

# Only managers and admin can approve
@router.put("/{expense_id}/approve", response_model=ExpenseResponse)
async def approve_expense(
    expense_id: int,
    current_user: User = Depends(require_manager),
    _: User = Depends(block_demo_user),
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

    log_action(
        db = db,
        action = AuditActionEnum.expense_approved,
        user = current_user,
        resource_id = expense_id,
        detail = f"Approved expense: {expense.description} -- AED {expense.amount}"
    )
    
    db.commit()
    db.refresh(expense)

    await invalidate_expense_cache()
    return expense


