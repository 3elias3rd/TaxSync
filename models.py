from sqlalchemy import DateTime, String, ForeignKey, Float, Integer, Text, create_engine, UniqueConstraint, Enum as SQLEnum
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from typing import Optional, List
from dotenv import load_dotenv
import os
import enum

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

class RoleEnum(str, enum.Enum):
    admin    = "admin"
    manager  = "manager"
    employee = "employee"

class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="company")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="company")
    incomes: Mapped[List["Income"]] = relationship(back_populates="company")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_pass: Mapped[str] = mapped_column(String(500))
    trn_number: Mapped[Optional[str]] = mapped_column(String(15), unique=True)
    
    # Foreign key
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), nullable=False)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="users")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="created_by_user")
    incomes: Mapped[List["Income"]] = relationship(back_populates="created_by_user")

class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Foreign keys
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="expenses")
    created_by_user: Mapped["User"] = relationship(foreign_keys=[created_by], back_populates="expenses")
    category: Mapped["Category"] = relationship(back_populates="expenses")

    # Admin approval
    is_approved: Mapped[bool] = mapped_column(default=False, nullable=False)

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    deductible_pct: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationship
    expenses: Mapped[List["Expense"]] = relationship(back_populates="category")
   
class Income(Base):
    __tablename__ = "incomes"
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float]
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Foreign keys
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    
    # Relationship
    created_by_user: Mapped["User"] = relationship(back_populates="incomes")
    company: Mapped["Company"] = relationship(back_populates="incomes")

    # Admin approval
    is_approved: Mapped[bool] = mapped_column(default=False, nullable=False)


class DocumentKnowledge(Base):
    __tablename__ = "document_knowledge"
    __table_args__= (
        UniqueConstraint(
            "document_name",
            "text",
            name="uq_document_text"),
        )
    text_id: Mapped[int] = mapped_column(primary_key=True)
    document_name: Mapped[str] = mapped_column(String(300), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # 1536 is the dimension for OpenAI text-embedding
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)