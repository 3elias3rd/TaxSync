import os
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, get_db, RoleEnum
from main import app

from dotenv import load_dotenv
from unittest.mock import MagicMock, patch
from slowapi import Limiter
from services.ai_services import get_nlp

load_dotenv(".env")


TEST_DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@db_test:5432/test_db"


engine = create_engine(TEST_DATABASE_URL)                    
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Enable pgvector before creating tables
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture                                              
def db():
    connection  = engine.connect()
    transaction = connection.begin()
    session     = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    def override_get_nlp():
        mock_nlp = MagicMock()
        # Mock the return value of nlp(text) to return a doc with fake categories
        mock_doc = MagicMock()
        mock_doc.cats = {"food": 1.0, "travel": 1.0, "misc": 1.0}  # fake category scores
        mock_nlp.return_value = mock_doc
        return mock_nlp

    app.dependency_overrides[get_db]  = override_get_db
    app.dependency_overrides[get_nlp] = override_get_nlp   # override nlp

    with patch("routers.expenses.get_category_id", return_value=1):
        yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture                                              
def test_company(db):
    from models import Company
    company = Company(name="Test Company")
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def create_user(db, test_company):
    from models import User
    from auth import hash_password

    def _create_user(username="testuser", password="password123", role=RoleEnum.employee):
        user = User(
            username    = username,
            hashed_pass = hash_password(password),
            role        = role,                              
            trn_number  = None,
            company_id  = test_company.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user                                          
    

    return _create_user


@pytest.fixture
def auth_header(client, create_user):
    def _auth_header(username="testuser", password="password123", role=RoleEnum.employee):
        create_user(username=username, password=password, role=role)
        response = client.post("/token", data={
            "username": username,
            "password": password
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _auth_header