from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from routers import expenses, incomes, users

from contextlib import asynccontextmanager
from pathlib import Path

from schemas import Report, UserRegister
from train import MODEL_DIR
from scripts.seed_categories import seed_categories

from sqlalchemy.orm import Session

from models import get_db, User
from services.tax_engine import calculate_corporate_tax
from auth import verify_password, create_access_token, get_current_user, hash_password
from services.ai_services import get_relevant_chunks, generate_answer
from scripts.embeddings_to_db import set_law_to_db

import spacy

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Load the model from disk
        app.state.nlp = spacy.load(MODEL_DIR)
    
    except Exception as e:
        print(f"Failed to load model: {e}")
    
    yield
    print("Shutting down API")

app = FastAPI(
    lifespan = lifespan,
    title = "TaxSync API",
    description = """
## TaxSync API

A multi-tenant tax management API for UAE businesses.

### Features
- JWT Authentication with role-based access control
- Multi-tenant company isolation
- Expense and income tracking with AI categorisation
- Corporate tax reporting
- AI-powered tax advisor
""",
    version      = "1.0.0",
    contact      = {
        "name": "TaxSync Support",
        "email": "support@taxsync.com"
    },
    license_info = {
        "name": "Private"
    },
    # ✅ Swagger UI at /docs, disable ReDoc
    docs_url     = "/docs",
    redoc_url    = None
)
app.include_router(expenses.router)
app.include_router(incomes.router)
app.include_router(users.router )
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
        trn_number = user_data.trn_number,
        company_id = user_data.company_id,
        role = user_data.role # Defaults to employee
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

@app.get("/final_report", response_model=Report)
def get_report(
    year: int = 2026,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):

    report_data = calculate_corporate_tax(year=year, company_id=current_user.company_id, db=db)

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