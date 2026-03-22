import pytest
from models import Company, User, Income, Expense, Category, RoleEnum
from auth import hash_password
from services.tax_engine import calculate_corporate_tax


class TestTaxEngine:
    # Test profit above threshold
    def test_tax_calculated_above_threshold(self, db, test_company):
        # Seed User
        user = User(
            username = "tax_user",
            hashed_pass = hash_password("pass123"),
            company_id = test_company.id,
            role = RoleEnum.employee
        )
        db.add(user)
        db.flush()

        # Seed category
        category = Category(
            name = "food",
            deductible_pct = 1.0
        )
        db.add(category)
        db.flush()

        # Seed income
        income = Income(
            description = "2025 income",
            amount = 700000,
            created_by = user.id,
            company_id = test_company.id
        )
        db.add(income)
        db.flush()

        # Seed expence
        expense = Expense(
            description = "Total expenses for 2025",
            amount = 200000,
            category_id = category.id,
            created_by = user.id,
            company_id = test_company.id
        )
        db.add(expense)
        db.flush()
        db.commit()

        result = calculate_corporate_tax(year=2026, company_id=test_company.id, db=db)

        assert result["total_revenue"] == 700000
        assert result["total_decuctible_expenses"] == 200000
        assert result["net_taxable_profit"] == 500000
        assert result["taxable_amount"] == 125000
        assert result["tax_payable"] == 11250
    

    def test_tax_calculated_below_threshold(self, db, test_company):
        # Add user
        user = User(
            username = "taxuser",
            hashed_pass = hash_password("pass123"),
            role = RoleEnum.employee,
            company_id = test_company.id
        )
        db.add(user)
        db.flush()

        # Add category
        category = Category(
            name = "Anual expenses",
            deductible_pct = 1.0
        )
        db.add(category)
        db.flush()


        # Add income 
        income = Income(
            description = "Total income for 2025",
            amount = 400000,
            created_by = user.id,
            company_id = test_company.id
        )
        db.add(income)
        db.flush()

        # Add expense
        expense = Expense(
            description = "Total expense for 2025",
            amount  = 100000,
            category_id = category.id,
            created_by = user.id,
            company_id = test_company.id
        )

        db.add(expense)
        db.flush()
        db.commit()

        result = calculate_corporate_tax(year=2026, company_id=test_company.id, db=db)

        assert result["total_revenue"] == 400000
        assert result["total_decuctible_expenses"] == 100000
        assert result["taxable_amount"] == 0
        assert result["tax_payable"] == 0

    def test_partial_deductible_expense(self, db, test_company):
        # Add category
        category = Category(
            name = "Feeding employees",
            deductible_pct = 0.5 
        )
        db.add(category)
        db.flush()

        # Add user
        user = User(
            username = "taxuser",
            hashed_pass = hash_password("pass123"),
            company_id = test_company.id,
            role = RoleEnum.employee
        )
        db.add(user)
        db.flush()

        # Add income 
        income = Income(
            description = "Total income for 2025",
            amount = 400000,
            created_by = user.id,
            company_id = test_company.id
        )
        db.add(income)
        db.flush()

        # Add expense
        expense = Expense(
            description = "Food expenses for February",
            amount = 50000,
            category_id = category.id,
            created_by = user.id,
            company_id = test_company.id
        )
        db.add(expense)
        db.flush()
        db.commit()

        result = calculate_corporate_tax(year=2026, company_id=test_company.id, db=db)

        assert result["total_decuctible_expenses"] == 25000

    # Test company with no income or expense returns 0
    def test_empty_company_returns_zero(self, db, test_company):
        result = calculate_corporate_tax(year=2026, company_id=test_company.id, db=db)

        assert result["total_revenue"]             == 0.0
        assert result["total_decuctible_expenses"] == 0.0
        assert result["net_taxable_profit"]        == 0.0
        assert result["tax_payable"]               == 0.0

    #  Wrong year returns no data
    def test_wrong_year_returns_zero(self, db, test_company):
        user = User(
            username    = "taxuser4",
            hashed_pass = hash_password("password123"),
            company_id  = test_company.id,
            role        = RoleEnum.employee
        )
        db.add(user)
        db.flush()

        db.add(Income(
            description = "Revenue",
            amount      = 500000,
            company_id  = test_company.id,
            created_by  = user.id
        ))
        db.commit()

        # Query wrong year — should return zero
        result = calculate_corporate_tax(year=2020, company_id=test_company.id, db=db)
        assert result["total_revenue"] == 0.0

    # ✅ Company isolation — other company data not included
    def test_company_isolation(self, db, test_company):
        # Create a second company
        other_company = Company(name="Other Company")
        db.add(other_company)
        db.flush()

        user = User(
            username    = "taxuser5",
            hashed_pass = hash_password("password123"),
            company_id  = other_company.id,
            role        = RoleEnum.employee
        )
        db.add(user)
        db.flush()

        # Add income to OTHER company
        db.add(Income(
            description = "Other revenue",
            amount      = 999999,
            company_id  = other_company.id,
            created_by  = user.id
        ))
        db.commit()

        # Calculate for test_company — should not include other company data
        result = calculate_corporate_tax(year=2026, company_id=test_company.id, db=db)
        assert result["total_revenue"] == 0.0