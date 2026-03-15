import pytest
from models import RoleEnum


class TestRolePermissions:
    def test_employee_cannot_approve_expense(self, client, auth_header):
        headers  = auth_header(role=RoleEnum.employee)
        response = client.put("/expenses/1/approve", headers=headers)
        assert response.status_code == 403

    def test_manager_can_approve_expense(self, client, auth_header, db):
        from models import Category, Expense
        category = Category(name="misc", deductible_pct=1.0)
        db.add(category)
        db.commit()

        employee_headers = auth_header(username="emp2", role=RoleEnum.employee)
        client.post("/expenses/", headers=employee_headers, json={
            "description": "Misc expense",
            "amount":      100.00,
            "category_id": category.id
        })

        expense = db.query(Expense).first()
        headers = auth_header(username="mgr", role=RoleEnum.manager)
        response = client.put(f"/expenses/{expense.id}/approve", headers=headers)
        assert response.status_code == 200

    def test_admin_can_approve_expense(self, client, auth_header, db):
        from models import Category, Expense
        category = Category(name="misc", deductible_pct=1.0)
        db.add(category)
        db.commit()

        employee_headers = auth_header(username="emp", role=RoleEnum.employee)
        client.post("/expenses/", headers=employee_headers, json={
            "description": "Misc expense",
            "amount":      100.00,
            "category_id": category.id
        })

        expense  = db.query(Expense).first()
        headers  = auth_header(username="adm", role=RoleEnum.admin)
        response = client.put(f"/expenses/{expense.id}/approve", headers=headers)
        assert response.status_code == 200

    def test_unauthenticated_cannot_access_protected_route(self, client):  
        response = client.get("/expenses/")                                 
        assert response.status_code == 401


class TestCompanyIsolation:
    def test_user_cannot_approve_other_company_expense(self, client, db):
        from models import Category, Company, Expense, User
        from auth import hash_password

        company_a = Company(name="Company A")
        company_b = Company(name="Company B")
        db.add_all([company_a, company_b])
        db.commit()

        manager_b = User(
            username    = "manager_b",
            hashed_pass = hash_password("password123"),
            company_id  = company_b.id,
            role        = RoleEnum.manager
        )
        db.add(manager_b)
        db.commit()

        category = Category(name="misc", deductible_pct=1.0)
        db.add(category)
        db.commit()                                          

        expense_a = Expense(
            description = "Company A expense",
            amount      = 100.00,
            company_id  = company_a.id,
            created_by  = manager_b.id,
            category_id = category.id,
            is_approved = False
        )
        db.add(expense_a)
        db.commit()

        login = client.post("/token", data={
            "username": "manager_b",
            "password": "password123"
        })

        headers  = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = client.put(f"/expenses/{expense_a.id}/approve", headers=headers)
        assert response.status_code == 403