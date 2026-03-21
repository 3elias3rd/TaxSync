import pytest
from models import RoleEnum

class TestGetIncome:
    def test_get_incomes_authenticated(self, client, auth_header):
        headers = auth_header()
        response = client.get("/incomes/", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)
    
    def test_get_incomes_unauthenticated(self, client, db):
        response = client.get("/incomes/")
        assert response.status_code == 401


class TestCreateIncome:
    def test_create_income_success(self, client, auth_header):
        headers = auth_header()
        response = client.post("/incomes/", headers=headers, json={
            "description": "February income",
            "amount": 45000            
        })
        assert response.status_code == 200

        data = response.json()

        assert data["description"] == "February income"
        assert data["amount"] == 45000 
        assert data["is_approved"] == False
    
    def test_create_income_unauthenticated(self, client):
        response = client.post("/incomes/", json={
            "description": "February income",
            "amount": 45000 
        })

        assert response.status_code == 401
    
    def test_create_expense_negative_amount(self, client, auth_header):
        headers = auth_header()
        response = client.post("/incomes/", headers=headers, json={
            "description": "February income",
            "amount": -4500
        })
        assert response.status_code == 422
    

class TestDeleteIncome:
    def test_delete_income_as_admin(self, client, auth_header, db):
        from models import Income

        employee_headers = auth_header(username="employee1", role=RoleEnum.employee)
        client.post("/incomes/", headers=employee_headers, json={
            "description": "February income",
            "amount": 45000
        })

        income = db.query(Income).first()
        admin_headers = auth_header(username="admin1", role=RoleEnum.admin)
        response = client.delete(f"/incomes/{income.id}", headers=admin_headers)

        assert response.status_code == 200

    def test_delete_income_as_manager_forbidden(self, client, auth_header, db):
        from models import Income

        employee_headers = auth_header(username="employee1", role=RoleEnum.employee)
        client.post("/incomes/", headers=employee_headers, json={
            "description": "February income",
            "amount": 45000
        })

        income = db.query(Income).first()

        manager_headers = auth_header(username="manager1", role=RoleEnum.manager)
        response = client.delete(f"/incomes/{income.id}", headers=manager_headers)

        assert response.status_code == 403


class TestApproveExpense:
    def test_approve_income_as_manager(self, client, auth_header, db):
        from models import Income

        employee_headers = auth_header(username="employee1", role=RoleEnum.employee)
        client.post("/incomes/", headers=employee_headers, json={
            "description": "February income",
            "amount": 45000
        })

        income = db.query(Income).first()

        manager_headers = auth_header(username="manager1", role=RoleEnum.manager)
        response = client.put(f"/incomes/{income.id}/approve", headers=manager_headers)

        data = response.json()
        assert response.status_code == 200
        assert data["is_approved"] == True
    
    def test_approve_expense_as_employee_forbidden(self, client, auth_header, db):
        from models import Income

        employee_headers = auth_header(username="employee1", role=RoleEnum.employee)
        client.post("/incomes/", headers=employee_headers, json={
            "description": "February income",
            "amount": 45000
        })

        income = db.query(Income).first()

        response = client.put(f"/incomes/{income.id}/approved", headers=employee_headers)

        assert response.status_code == 403
