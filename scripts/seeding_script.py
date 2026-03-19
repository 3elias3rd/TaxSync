import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models import get_db, Company, User, Expense, Income
from auth import hash_password
from services.ai_services import get_category_id
import random
from seed_data import company_data, user_data, demo_user, zereebcorp_expenses, zereebcorp_incomes, tilemllc_expenses, tilemllc_incomes, timule_expenses, timule_incomes
from train import MODEL_DIR
import spacy
from datetime import date, timedelta
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


nlp = spacy.load(MODEL_DIR)

# --------------------------------------------
# Company seeding
# --------------------------------------------
def seed_company(db: Session):
    for company in company_data:
        exists = db.query(Company).filter(Company.name == company["name"]).first()

        if not exists:
            new_company = Company(name = company["name"])
            db.add(new_company)
    

# --------------------------------------------
# Employee seeding
# --------------------------------------------
def seed_users(db: Session):
    for user in user_data:
        company = db.query(Company).filter(Company.name == user["company"]).first()
        
        exists = db.query(User).filter(User.username == user["username"], User.company_id == company.id).first()
        demo_acc = db.query(User).filter(User.username == demo_user["username"]).first()

        if not exists:
            new_user = User(
                username = user["username"],
                hashed_pass = hash_password(user["password"]),
                company_id = company.id,
                role = user["role"],

            )

            db.add(new_user)
    demo_user_company = db.query(Company).filter(Company.name == demo_user["company"]).first()
    if not demo_acc:
        add_demo = User(
            username = demo_user["username"],
            hashed_pass = hash_password(demo_user["password"]),
            company_id = demo_user_company.id,
            role = demo_user["role"]
        )
    db.add(add_demo)
    

# --------------------------------------------
# Expense seeding
# --------------------------------------------
def seed_expenses(db: Session, company_name, expense_data):
    random_date = date.today() - timedelta(days=random.randint(0, 365))
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        return
    
    employees = db.query(User).filter(User.company_id == company.id).all()
    if not employees:
        return

    for expense in expense_data:
        exists = db.query(Expense).filter(
            Expense.description == expense["description"],
            Expense.company_id == company.id
        ).first()

        if not exists:
            creator = random.choice(employees)

            db.add(Expense(
                description=expense["description"],
                amount=expense["amount"],
                company_id=company.id,
                category_id=get_category_id(db=db, text=expense["description"], nlp=nlp),
                created_by=creator.id,
                date=random_date
            ))


# --------------------------------------------
# Income seeding
# --------------------------------------------
def seed_incomes(db: Session, company_name, incomes_data):
    random_date = date.today() - timedelta(days=random.randint(0, 365))
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        return
    
    employees = db.query(User).filter(User.company_id == company.id).all()
    if not employees:
        return

    for income in incomes_data:
        exists = db.query(Income).filter(
            Income.description == income["description"],
            Income.company_id == company.id
        ).first()

        if not exists:
            creator = random.choice(employees)

            db.add(Income(
                description=income["description"],
                amount=income["amount"],
                company_id=company.id,
                created_by=creator.id,
                date=random_date
            ))


# --------------------------------------------
# Master function to seed all data
# --------------------------------------------
def seed_db():
    db = next(get_db())
    try:
        seed_company(db)
        seed_users(db)

        seed_expenses(db ,"Zereebcorp", zereebcorp_expenses)
        seed_incomes(db, "Zereebcorp", zereebcorp_incomes)

        seed_expenses(db, "TilemLLC", tilemllc_expenses)
        seed_incomes(db, "TilemLLC", tilemllc_incomes)

        seed_expenses(db, "Timule", timule_expenses)
        seed_incomes(db, "Timule", timule_incomes)

        db.commit()
        print("Db has been successfully seeded")
    except Exception as e:
        db.rollback()
        print("Seeding failed, transaction has been rolled back.")
        print(e)

seed_db()

