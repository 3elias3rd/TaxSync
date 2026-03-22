import pytest
from models import RoleEnum, AuditLog, AuditActionEnum


class TestGetAuditLogs:
    # Manager can access audit logs
    def test_manager_can_access_audit_logs(self, client, auth_header):
        manager_headers = auth_header(username="manager1", role=RoleEnum.manager)
        response = client.get("/audit/", headers=manager_headers)

        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        assert isinstance(data["items"], list)

    # Employee cannot access audit logs
    def test_employee_cannot_access_audit_logs(self, client, auth_header):
        employee_headers = auth_header(username="taxuser", role=RoleEnum.employee)
        response = client.get("/audit/", headers=employee_headers)
        assert response.status_code == 403

    # Unauthenticated cannot access audit logs
    def test_unauthenticated_cannot_access_audit_logs(self, client):
        response = client.get("/audit/")
        assert response.status_code == 401

    # Audit log created on login
    def test_audit_log_created_on_login(self, client, create_user, db):
        create_user(username="taxuser")
        client.post("/token", data={
            "username": "taxuser",
            "password": "password123"
        })
        

        # Check audit log was created
        log = db.query(AuditLog).filter(AuditLog.action == AuditActionEnum.user_login).first()
        assert log is not None
        assert log.action == AuditActionEnum.user_login

    # Audit log created on expense creation
    def test_audit_log_created_expense_creation(self, client, auth_header,db):
        from models import Category, AuditLog
        category = Category(
            name="misc", deductible_pct=1.0
        )
        db.add(category)
        db.commit()

        headers = auth_header(username="taxuser")
        client.post("/expenses/", headers=headers, json={
            "description": "Test expense",
            "amount": 100.00,
            "category_id": category.id
        })

        log = db.query(AuditLog).filter(
            AuditLog.action == AuditActionEnum.expense_created
        ).first()
        assert log is not None
        assert log.action == AuditActionEnum.expense_created
    
    # Pagination works
    def test_audit_logs_pagination(self, client, auth_header):
        headers = auth_header(username="adminuser", role=RoleEnum.admin)
        response = client.get("/audit/?page=1&page_size=5", headers=headers)
        assert response.status_code == 200
        assert response.json()["page"] == 1
        assert response.json()["page_size"] == 5

    # Test filtering by type
    def test_audit_logs_filter_by_action(self, client, auth_header):
        headers = auth_header(username="manager1", role=RoleEnum.manager)
        response = client.get("/audit/?action=user_login", headers=headers)

        assert response.status_code == 200
        # All returned items should be user_login actions
        for item in response.json()["items"]:
            assert item["action"] == "user_login"