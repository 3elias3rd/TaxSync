from celery_app import celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Company
from services.tax_engine import calculate_corporate_tax
from fastapi_cache import FastAPICache
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@celery.task(name="tasks.tax_tasks.precalculate_tax_reports")
def precalculate_tax_reports():
    """
    Will run every night at 2am.
    Pre-calculates tax reports for all companies and warms the redis cache."""

    db = SessionLocal()
    year = datetime.now().year

    try:
        companies = db.query(Company).all()
        results = []
        
        for company in companies:
            report = calculate_corporate_tax(
                year = year,
                company_id = company.id,
                db = db
            )
            results.append({
                "company_id": company.id,
                "status": "calculated",
                "tax_payable": report["tax_payable"]
            })

            return {
                "status": "success",
                "companies": len(companies),
                "year": year,
                "results": results
            }
        
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    
    finally:
        db.close()