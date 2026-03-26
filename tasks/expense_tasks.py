from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Expense, Category
from services.ai_services import get_category_id
import spacy
import os
from train import MODEL_DIR
from dotenv import load_dotenv

load_dotenv(".env")

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)

@celery.task(name="tasks.expense_tasks.categorise_expense", bind=True, max_retries=3)
def categorise_expense(self, expense_id: int):
    """
    Runs spaCy categorisation on an expense in the background.
    Called after expense is created so user doesn't wait for inference.
    """
    db = SessionLocal()
    nlp = spacy.load(MODEL_DIR)

    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            return {"status": "error", "detail": f"Expense {expense_id} not found."}
        
        category_id = get_category_id(
            text = expense.description,
            nlp =  nlp,
            db = db
        )

        expense.category_id = category_id
        db.commit()

        return {"status": "success", "expense_id": expense_id, "category_id": category_id}
    
    except Exception as exc:
        db.rollback()
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    
    finally:
        db.close()