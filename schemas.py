from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from datetime import datetime, timezone
from typing import Optional, List



# User related models
class UserBase(BaseModel):
    username: str = Field(...,min_length=3, max_length=50)
    trn_number: Optional[str] = Field(pattern=r"^\d{15}$", default=None)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=20)


class UserResponse(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(min_length=3, max_length=50, default=None)
    password: Optional[str] = Field(min_length=8, max_length=20, default=None)
    trn_number: Optional[str] = Field(pattern=r"^\d{15}$", default=None)


class UserWithExpense(UserResponse):
    expense: List["ExpenseResponse"] = []


class UserWithIncome(UserResponse):
    income: List["IncomeResponse"] = []

# Category related models
class CategoryBase(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    deductible_pct: float = Field(ge=0, le=1, default=1.0)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(min_length=3, max_length=50, default=None)
    deductible_pct: Optional[float] = Field(ge=0.0, le=1.0, default=1.0)


class CategoryWithExpense(CategoryResponse):

    expenses: List["ExpenseResponse"] = []


# Expense related models
class ExpensesBase(BaseModel):
    description: str = Field(..., max_length=50)
    amount: float = Field(..., gt=0 )
    category_id: Optional[int]
    date: datetime = datetime.now(timezone.utc)

    @field_validator('date')
    @classmethod
    def validate_date_not_future(cls, value):
        if value > datetime.now(timezone.utc):
            raise ValueError("The date of the expense cannot be in the future")
        return value


class ExpenseCreate(ExpensesBase):
    pass


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(max_length=50, default=None)
    amount: Optional[float] = Field(gt=0, default=None)
    category_id: int


class ExpenseResponse(ExpensesBase):
    id: int
    date: datetime 
    category: CategoryResponse

    model_config = ConfigDict(from_attributes=True)


    @computed_field
    @property
    def get_deductible_amount(self) -> float:
        
        return round(self.category.deductible_pct * self.amount, 2)


# Income related models
class IncomeBase(BaseModel):
    description: str = Field(..., max_length=50)
    amount: float = Field(..., gt=0)


class CreateIncome(IncomeBase):
    pass

class UpdateIncome(BaseModel):
    description: Optional[str] = Field(default=None, max_length=50)
    amount: Optional[float] = Field(default=None, gt=0)


class IncomeResponse(IncomeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Report(BaseModel):
    period: int
    total_revenue: float
    total_decuctible_expenses: float
    net_taxable_profit: float

    # 9% tax 
    tax_free_allowance: float = 375000
    taxable_amount: float
    tax_payable: float