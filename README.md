# TaxSync API
### Automated Multi-Tenant Financial Ledger & Tax Compliance Engine for UAE SMEs

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-red)](https://sqlalchemy.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)](https://docker.com)
[![pytest](https://img.shields.io/badge/pytest-passing-green)](https://pytest.org)

🔗 [Live API Docs](https://taxsync.onrender.com/docs#/) &nbsp;|&nbsp; 📺 [YouTube Demo](https://youtu.be/8bOVD1PNnQY)

---

## Overview

TaxSync is a production-grade REST API built to help UAE SMEs track expenses, 
incomes and corporate tax liabilities under Federal Tax Authority rules. It 
supports multiple companies on a single deployment, with strict per-company 
data isolation and role-based access control enforced at every endpoint.

---

## Tech Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| Runtime          | Python 3.11                         |
| Framework        | FastAPI                             |
| Database         | PostgreSQL + pgvector               |
| ORM              | SQLAlchemy (mapped columns)         |
| Migrations       | Alembic                             |
| Auth             | JWT + bcrypt (OAuth2 Password Flow) |
| NLP              | spaCy (textcat)                     |
| AI               | OpenAI GPT-4o-mini + RAG            |
| Containerisation | Docker + Docker Compose             |
| Testing          | pytest + TestClient                 |
| Deployment       | Render                              |

## Core Features

### 1. Multi-Tenant Architecture with RBAC
TaxSync supports multiple companies on a single deployment. Every user belongs 
to a company and is assigned a fixed role — `admin`, `manager`, or `employee`. 
All data is strictly isolated per company at the database query level.

**Role permission matrix:**

| Action                   | admin     | manager  | employee  |
|--------------------------|-----------|----------|-----------|
| View expenses/incomes    |    ✅    |    ✅    |    ✅    |
| Create expenses/incomes  |    ✅    |    ✅    |    ✅    |
| Approve expenses/incomes |    ✅    |    ✅    |    ❌    |
| View all company users   |    ✅    |    ❌    |    ❌    |
| View single user         |    ✅    |    ✅    |    ❌    |

### 2. JWT Authentication (OAuth2 Password Flow)
Authentication is implemented using signed JSON Web Tokens with bcrypt password 
hashing. Every protected route validates the token signature and expiry before 
granting access. Roles and company membership are resolved from the token on 
every request — no additional database calls needed for authorization.
```
POST /register    Create a new user account
POST /token       Authenticate and receive a JWT Bearer token
GET  /users/me    Return the authenticated user's profile
```

### 3. Automated UAE Corporate Tax Engine
TaxSync implements 2026 UAE Corporate Tax logic deterministically on the server 
side:

- **0%** on profit up to AED 375,000
- **9%** on profit above the threshold

Profit is calculated from normalised income and deductible expense values. Every 
calculation is performed server-side to ensure a single source of truth. Results 
are returned as a structured JSON report scoped to the authenticated user's company.
```
GET /final_report?year=2026
```

### 4. NLP Expense Categorisation (spaCy)
To map free-text expense descriptions to standardised UAE deductible categories, 
TaxSync uses a custom trained spaCy `textcat` model for intent classification.
```
"DEWA bill"                          → rent_and_utilities   (100% deductible)
"Lunch with potential investors"     → client_entertainment (50% deductible)
"Staff salary payment"               → salaries_and_visas   (100% deductible)
```

When a category impacts tax calculation (e.g. client entertainment is 50% 
deductible under UAE law), the backend stores:
- Raw description
- Derived category
- Expense amount
- Deductible amount (computed from `deductible_pct`)

### 5. RAG-Powered Tax Advisor (pgvector + GPT-4o-mini)
TaxSync features an `/ask-tax-advisor` endpoint built on a Retrieval-Augmented 
Generation architecture backed by official 2026 UAE Corporate Tax documentation.
```
User: "Can I deduct my business lunch?"
         ↓
Query embedded via OpenAI text-embedding-3-small
         ↓
pgvector cosine similarity search retrieves 10 most relevant legal sections
         ↓
GPT-4o-mini generates an answer constrained to retrieved context only
         ↓
Hallucination risk reduced — model cannot reference outside knowledge
```

Legal text is stored as chunked embeddings using a sliding window approach to 
preserve context at chunk boundaries.

### 6. ACID Transaction Integrity
Because TaxSync is a financial application, every ledger operation is wrapped 
in a SQLAlchemy session transaction:

- Failed tax calculations trigger a full rollback
- No partial expense or income commits
- No dropped rows or incomplete entries
- Session lifecycle managed via FastAPI `Depends(get_db)` — every request gets 
  its own isolated session that is guaranteed to close

---

## API Endpoints

### Auth
| Method | Endpoint    | Role   | Description                 |
|--------|-------------|--------|-----------------------------|
| POST   | `/register` | Public | Register a new user         |
| POST   | `/token`    | Public | Login and receive JWT token |
| GET    | `/users/me` | Any    | Get current user profile    |

### Expenses
| Method | Endpoint                 | Role     | Description              |
|--------|--------------------------|----------|--------------------------|
| GET    | `/expenses/`             | Any      | Get all company expenses |
| POST   | `/expenses/`             | Any      | Create an expense        |
| PUT    | `/expenses/{id}/approve` | Manager+ | Approve an expense       |
| DELETE | `/expenses/{id}`         | Manager+ | Delete an expense        |

### Incomes
| Method | Endpoint                | Role      | Description             |
|--------|-------------------------|-----------|-------------------------|
| GET    | `/incomes/`             | Any       | Get all company incomes |
| POST   | `/incomes/`             | Any       | Create an income        |
| PUT    | `/incomes/{id}/approve` | Manager+  | Approve an income       |
| DELETE | `/incomes/{id}`         | Manager+  | Delete an income        |

### Users
| Method | Endpoint      | Role     | Description           |
|--------|---------------|----------|-----------------------|
| GET    | `/users/`     | Admin    | Get all company users |
| GET    | `/users/{id}` | Manager+ | Get a single user     |

### Reports & AI
| Method | Endpoint           | Role | Description              |
|--------|--------------------|------|--------------------------|
| GET    | `/final_report`    | Any  | Get corporate tax report |
| GET    | `/ask-tax-advisor` | Any  | Query the AI tax advisor |

---

## Database Schema
```
companies
    └── users (company_id FK, role enum)
    └── expenses (company_id FK, created_by FK, category_id FK, is_approved)
    └── incomes (company_id FK, created_by FK, is_approved)

categories
    └── expenses (category_id FK, deductible_pct)

document_knowledge
    └── embedding (pgvector 1536 dimensions)
```

---

## Testing

TaxSync includes a pytest test suite with full isolation using a dedicated test 
database and per-test transaction rollbacks.
```bash
pytest tests/ -v
```

**Test coverage includes:**
- JWT authentication flow (register, login, token validation)
- Pydantic schema validation (422 on invalid input)
- Role-based permission enforcement (403 on unauthorised actions)
- Multi-tenant company isolation (403 on cross-company access attempts)
- Expense creation and approval lifecycle
- External AI dependency mocking via `unittest.mock.patch`

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- OpenAI API key

### Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/TaxSync.git
cd TaxSync
```

**2. Configure environment variables**

Create a `.env` file in the root directory:
```bash
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_NAME=taxsync_db
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
SECRET_KEY=your-generated-secret-key
OPENAI_API_KEY=your-openai-key
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

**3. Build and run**
```bash
docker-compose up --build -d
```

**4. Run migrations**
```bash
docker exec -it <container_name> alembic upgrade head
```

**5. Seed the database**
```bash
docker exec -it <container_name> python scripts/seeding_script.py
```

**6. View the API docs**
```
http://localhost:8000/docs
```

---

## Deployment

TaxSync is deployed on Render with a managed PostgreSQL database.
Environment variables are configured directly in the Render dashboard.
Migrations are run via the Render shell after each deploy.

---

## Project Structure
```
TaxSync/
├── main.py                  # App entry point, core endpoints
├── models.py                # SQLAlchemy models + RoleEnum
├── schemas.py               # Pydantic request/response schemas
├── auth.py                  # JWT + password hashing
├── dependencies.py          # RBAC dependency functions
├── models                   # trained spaCy model
├── train.py                 # spaCy training script
├── train_data.py            # cats used in training model
├── requirements.txt
├── routers/
│   ├── expenses.py
│   ├── incomes.py
│   └── users.py
├── services/
│   ├── ai_services.py       # spaCy, OpenAI, RAG logic
│   └── tax_engine.py        # Corporate tax calculation
├── scripts/
│   ├── embeddinds_to_db.py
│   ├── seed_data.py
│   ├── seeding_scipt.py
│   └──tax_law.py
├── migrations/              # Alembic migrations
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_expenses.py
├── templates/
│   └──index.html
├── docker-compose.yml
└── Dockerfile
```