from sqlalchemy import DateTime, String, ForeignKey, Float, Integer, Text, create_engine, select, text
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from typing import Optional, List
from dotenv import load_dotenv
import os

load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL", "default_local_url")
if not DATABASE_URL:
    raise ValueError("Database Url not found in .env")
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SQL models
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_pass: Mapped[str] = mapped_column(String(255))
    trn_number: Mapped[Optional[str]] = mapped_column(String(15), unique=True)

    # Relationships
    expenses: Mapped[List["Expense"]] = relationship(back_populates="user")
    incomes: Mapped[List["Income"]] = relationship(back_populates="user")

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="expenses")
    category: Mapped["Category"] = relationship(back_populates="expenses")

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    deductible_pct: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationship
    expenses: Mapped[List["Expense"]] = relationship(back_populates="category")
   
class Income(Base):
    __tablename__ = "incomes"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float]
    date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationship
    user: Mapped["User"] = relationship(back_populates="incomes")

class DocumentKnowledge(Base):
    __tablename__ = "document_knowledge"
    text_id: Mapped[int] = mapped_column(primary_key=True)
    document_name: Mapped[str] = mapped_column(String(300))
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    # 1536 is the dimension for OpenAI text-embedding
    embedding: Mapped[Vector] = mapped_column(Vector(1536))

def create_tables():
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        except Exception:
            conn.rollback()

    Base.metadata.create_all(engine)  

    print("All tables created.")  
    

create_tables()