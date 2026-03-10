from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timedelta, timezone

from schemas import CreateIncome, ExpenseCreate, IncomeResponse, ExpenseResponse, Report, UserRegister
from train import MODEL_DIR
from categories_to_db import seed_categories

from sqlalchemy import select, exists
from sqlalchemy.orm import Session

from models import Expense, Category, Income, get_db, User
from services.tax_engine import calculate_corporate_tax
from auth import verify_password, create_access_token, get_current_user, hash_password, oauth2_scheme
from services.ai_services import get_relevant_chunks, generate_answer
from scripts.embeddings_to_db import set_law_to_db
from scripts.tax_law import tax_law

import spacy
from spacy.language import Language

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Load the model from disk
        app.state.nlp = spacy.load(MODEL_DIR)
    
    except Exception:
        print(f"Failed to load model: {Exception}")
    
    yield
    print("Shuting down API")

app = FastAPI(lifespan=lifespan)

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
def serve_homepage(request: Request):
    # Load index.html and send it to the browser
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if username is avalable
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username not available")

    # Store new user
    new_user =User(
        username = user_data.username,
        hashed_pass = hash_password(user_data.password),
        trn_number = user_data.trn_number
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)    
    
    return {"message": f"User {new_user.username} registered successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    # Check if user exists
    # If user exists then check password
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_pass):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = create_access_token(username=user.username)
    
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users/me")
def read_me(current_user: User = Depends(get_current_user)):  
    return {
        "id": current_user.id,
        "username": current_user.username
    }

def get_nlp(request: Request):

    return request.app.state.nlp

@app.post("/expense",response_model=ExpenseResponse)
def add_expense(expense: ExpenseCreate, nlp: Language = Depends(get_nlp), db: Session = Depends(get_db)):

    new_expense = Expense(**expense.model_dump())
    new_expense.user_id = 1
    
    # Check if user entered category id
    if not new_expense.category_id:
        doc = nlp(expense.description)
        cats = doc.cats
        top_tabel = max(cats, key=cats.get)
        
        category_obj = db.scalar(select(Category).where(Category.name==top_tabel))

        if not category_obj:
            raise HTTPException(status_code=400, detail=f"AI predicted {top_tabel}, this label is not in DB")

        new_expense.category_id = category_obj.id

        # new_expense = Expense(**expense_data)   

    existing = db.scalar(select(exists(select(Category).where(Category.id==new_expense.category_id))))
    if not existing:
        raise HTTPException(status_code=404, detail="Category does not exist")

    # Add new expense
    db.add(new_expense)

    db.commit()

    db.refresh(new_expense, ["category"])

    return new_expense

@app.post("/income", response_model=IncomeResponse)
def add_income(income: CreateIncome, db: Session = Depends(get_db)):
    new_income = Income(**income.model_dump())
    new_income.user_id = 1
    
    db.add(new_income)
    db.commit()

    db.refresh(new_income)

    return new_income

@app.get("/final_report", response_model=Report)
def get_report(year: int = 2026, db: Session = Depends(get_db)):
    report_data = calculate_corporate_tax(year, db)

    return report_data

@app.get("/ask-tax-advisor")
async def ask_advisor(question: str, db: Session = Depends(get_db)):

    # 1. Get info from the dabatase
    context_chunks = get_relevant_chunks(query_text=question, db=db)
    context_text = "\n".join([context.text for context in context_chunks])

    answer = generate_answer(question=question, context=context_text)

    return {"answer": answer}

@app.post("/append-law")
def append_law(background_task: BackgroundTasks):
    background_task.add_task(set_law_to_db)
    return {"status": "process starting"}

@app.post("/seed_categories")
def seed_categories_to_db():
    return seed_categories()