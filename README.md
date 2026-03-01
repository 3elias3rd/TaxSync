TaxSync API: Automated Financial Ledger Integration

Tax sync was built to help SMEs within the UAE track and synchronise their tax liabilities under corporate tax rules. It allows a business to maintain strict financial consistency and transactional integrity.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-red)

Tech Stack
Python 3.11, FastAPI, PostgreSQL, SQLAlchemy, pgvector, spacy

Architecture: Transaction-safe ledger engine automated tax calculation and RAG-based compliance validation.

### Core Architecture & Features
1. Automated UAE Corporate Tax Engine
Implements 2026 UAE Corporate Tax logic under Federal Tax Authority rules:
* 0% on profit up to AED 375,000
* 9% tax for any profits above the threshold

### How it works
* Profit is calculated using the normalized values from the /incomes and /expenses tables.
* At this point there is no LLM involvement, so tax brackets are applied deterministically  (using fixed math rules).
* Results are returned in a structured Json format to be used for further accounting and bookkeeping purposes.
* Every calculation is performed on the server side to ensure a single source of truth.

2. NLP Expense Categorization (spaCy Layer)
To map messy descriptions to the standardized deductible categories in the UAE I used spaCy's textcat for intent classification.

Example:
* "DEWA BILL" -> rent_and_utilities
* "Luch with potential investors" -> client_entertainment

When the classification impacts tax calculation (e.g.  50% of an expense can be used to reduce profits this is for anything classified as client entertainment as per UAE tax law), the backend does the following:

* Store:
    * Raw description
    * Derived category
    * Expense amount (e.g. AED 1000)
    * Amount reducing profits (AED 500 for AED 1000 example)

* From a backend perspective, this is:
    * Semi-deterministic classification layer
    * Pre-processing pipeline before ledger commit.

3. RAG-Powered Legal Tax Expert (pgvector)

To provide immediate compliance answers, TaxSync features an /ask-tax-expert endpoint built on a Retrieval-Augmented Generation (RAG) architecture. I used pgvector to ingest official 2026 UAE Corporate tax documentation. When a user asks, "Can I deduct my business lunch?":
    1. Query is embedded
    2. Semantic search retrieves relevant legal sections, by retrieving the 10 sections with the lowest comparative cosine distance.
    3. LLM generates an answer by using only the retrieved information as reference. 
The process stated above is used to reduce the risk of hallucination.

From an architecture standpoint:
* Legal text is stored as chunked embeddings using the sliding window approach, ensuring no context is lost at a chunks boundary.
* Cosine similarity search
* Answer generation constrained to the retrieved context.

4. Acid and transaction integrity
Because this is a financial application, TaxSync cannot afford dropped rows or partial updates. 
I used PostgreSQL + SQLAlchemy session management to ensure the following:
* Each ledger update is wrapped in a transaction
* If tax calculation fail -> full rollback
* No partial invoice commits
* No unfinished entries

### Local Development Setup
1. Clone the repository

Bash
git clone https://github.com/yourusername/TaxSync.git
cd TaxSync
2. Configure Environment Variables
Create a .env file in the root directory:

Code snippet
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=taxsync_db
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
3. Build and Run

Bash
docker-compose up --build -d