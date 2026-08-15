"""Strict JSON contracts for the legacy customer-data SOAP response."""

from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects undeclared fields and type coercion."""

    model_config = ConfigDict(extra="forbid", strict=True)


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CustomerProfile(StrictModel):
    internal_id: str = Field(min_length=1, examples=["991029384"])
    full_name: str = Field(min_length=1, max_length=200, examples=["Monish K C"])
    risk_tier: RiskTier


class DepositBalances(StrictModel):
    checking: Decimal = Field(ge=0, max_digits=14, decimal_places=2, examples=["1542.50"])
    savings: Decimal = Field(ge=0, max_digits=14, decimal_places=2, examples=["10500.00"])
    currency: str = Field(pattern=r"^[A-Z]{3}$", examples=["INR"])


class Mortgage(StrictModel):
    loan_id: str = Field(min_length=1, examples=["ML-55412"])
    principal_remaining: Decimal = Field(ge=0, max_digits=16, decimal_places=2, examples=["4500000.00"])
    interest_rate: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2, examples=["7.5"])
    next_payment_due: date


class Accounts(StrictModel):
    deposit: DepositBalances
    mortgage: Mortgage


class Transaction(StrictModel):
    date: date
    merchant: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(max_digits=14, decimal_places=2, examples=["-450.00"])


class CustomerDataResponse(StrictModel):
    customer_profile: CustomerProfile
    accounts: Accounts
    recent_transactions: list[Transaction]
