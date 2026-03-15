import pytest
from models import RoleEnum


class TestGetExpenses:
    def test_get_expenses_authenticated(self, client, auth_header):   
        headers  = auth_header()
        response = client.get("/expenses/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_expenses_unauthenticated(self, client):
        response = client.get("/expenses/")
        assert response.status_code == 401


class TestCreateExpense:
    def test_create_expense_success(self, client, auth_header, db):
        from models import Category
        category = Category(name="food", deductible_pct=1.0)
        db.add(category)
        db.commit()

        headers  = auth_header()
        response = client.post("/expenses/", headers=headers, json={
            "description": "Team lunch",
            "amount":      50.00,
            "category_id": category.id
        })
        assert response.status_code == 200
        assert response.json()["description"] == "Team lunch"
        assert response.json()["amount"]       == 50.00
        assert response.json()["is_approved"]  == False

    def test_create_expense_unauthenticated(self, client):
        response = client.post("/expenses/", json={
            "description": "Team lunch",
            "amount":      50.00,
        })
        assert response.status_code == 401

    def test_create_expense_negative_amount(self, client, auth_header):
        headers  = auth_header()
        response = client.post("/expenses/", headers=headers, json={
            "description": "Bad expense",
            "amount":      -50.00    
        })
        assert response.status_code == 422


class TestApproveExpense:
    def test_approve_expense_as_manager(self, client, auth_header, db):
        from models import Category, Expense
        category = Category(name="travel", deductible_pct=1.0)
        db.add(category)
        db.commit()

        employee_headers = auth_header(username="employee1", role=RoleEnum.employee)
        client.post("/expenses/", headers=employee_headers, json={
            "description": "Flight",
            "amount":      200.00,
            "category_id": category.id
        })

        expense        = db.query(Expense).first()
        manager_headers = auth_header(username="manager1", role=RoleEnum.manager)
        response       = client.put(f"/expenses/{expense.id}/approve", headers=manager_headers)

        assert response.status_code == 200          
        assert response.json()["is_approved"] == True

    def test_approve_expense_as_employee_forbidden(self, client, auth_header, db):
        from models import Category, Expense
        category = Category(name="travel", deductible_pct=1.0)
        db.add(category)
        db.commit()

        employee_headers = auth_header(username="employee2", role=RoleEnum.employee)
        client.post("/expenses/", headers=employee_headers, json={   
            "description": "Flight",
            "amount":      200.00,
            "category_id": category.id
        })

        expense  = db.query(Expense).first()
        response = client.put(f"/expenses/{expense.id}/approve", headers=employee_headers)  

        assert response.status_code == 403