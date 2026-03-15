import pytest

class TestRegister:
    def test_register_success(self, client, test_company):
        response = client.post("/register", json={
            "username": "newuser",
            "password": "password123",
            "trn_number": None,
            "company_id": test_company.id,
            "role": "employee"
        })
        assert response.status_code == 200
        assert response.json() == {"message": "User newuser registered successfully"}
    
    def test_register_duplicate_username(self, client, test_company, create_user):
        create_user(username="existinguser")

        response = client.post("/register", json={
            "username": "existinguser",
            "password": "password123",
            "trn_number": None,
            "company_id": test_company.id,
            "role": "employee"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Username not available"
    
class TestLogin:
    def test_login_success(self, client, create_user):
        create_user(username="loginuser", password="password123")

        response = client.post("/token", data={
            "username": "loginuser",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password (self, client, create_user):
        create_user(username="loginuser", password="password123")

        response = client.post("/token", data={
            "username": "loginuser",
            "password": "wrongpassword"
        })

        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_nonexistent_user(self, client):
        response = client.post("/token", data={
            "username": "ghostuser",
            "password": "password123"
        })

        assert response.status_code == 400