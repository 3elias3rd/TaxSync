from models import  Category, Expense, Income, select

from sqlalchemy import  func, extract

from schemas import Report

from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Database Url not found in .env")


def calculate_corporate_tax(year, db) -> Report:

    total_revenue = 0.0
    total_expenses = 0.0
    total_deductible_expenses = 0.0         
    
    # Add each income object to get total revenue filtered by year
    total_revenue = db.scalar(
        select(func.sum(Income.amount)).where(extract('year', Income.date) == year)
        ) or 0.0
            
    stmt = select(Expense, Category).join(Expense.category).where(extract('year', Expense.date) == year)
    for row in db.execute(stmt):
        expense_obj = row.Expense
        category_obj = row.Category

        # Add each expense object to get total expenses
        total_expenses += expense_obj.amount

        # Calculate decuctable expense for each expense then add it to the total
        deductible_expense = expense_obj.amount * category_obj.deductible_pct
        total_deductible_expenses += deductible_expense


    net_taxable_profit = total_revenue - total_deductible_expenses

    taxable_amount = 0.0
    tax_payable = 0.0

    # UAE tax logic
    if net_taxable_profit > 375000:
        taxable_amount = net_taxable_profit - 375000
        tax_payable = taxable_amount * 0.09


        
    return {
        "period": year,
        "total_revenue": total_revenue,
        "total_decuctible_expenses": total_deductible_expenses,
        "net_taxable_profit": round(net_taxable_profit, 2),
        "taxable_amount": round(taxable_amount, 2),
        "tax_payable": round(tax_payable, 2)
        }
