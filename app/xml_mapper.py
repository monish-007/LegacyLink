"""Namespace-aware conversion from the legacy SOAP XML document to API models."""

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from .models import Accounts, CustomerDataResponse, CustomerProfile, DepositBalances, Mortgage, RiskTier, Transaction

CUSTOMER_NAMESPACE = "http://legacybank.com/customers"
NS = {"cus": CUSTOMER_NAMESPACE, "soapenv": "http://schemas.xmlsoap.org/soap/envelope/"}


class XmlMappingError(ValueError):
    """Raised when the legacy document is malformed or does not match its contract."""


def _required_text(parent: ET.Element, path: str) -> str:
    element = parent.find(path, NS)
    if element is None or element.text is None or not (value := element.text.strip()):
        raise XmlMappingError(f"Missing required XML element: {path}")
    return value


def _decimal(parent: ET.Element, path: str) -> Decimal:
    try:
        return Decimal(_required_text(parent, path))
    except InvalidOperation as error:
        raise XmlMappingError(f"Invalid decimal in XML element: {path}") from error


def _date(parent: ET.Element, path: str) -> date:
    try:
        return date.fromisoformat(_required_text(parent, path))
    except ValueError as error:
        raise XmlMappingError(f"Invalid ISO date in XML element: {path}") from error


def load_customer_data(xml_path: Path) -> CustomerDataResponse:
    """Load, map, and strictly validate a ``GetCustomerDataResponse`` document."""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as error:
        raise XmlMappingError("The legacy XML document is not well-formed") from error

    response = root.find(".//cus:GetCustomerDataResponse", NS)
    if response is None:
        raise XmlMappingError("Missing GetCustomerDataResponse element")
    profile = response.find("cus:CustomerProfile", NS)
    accounts = response.find("cus:Accounts", NS)
    deposit = accounts.find("cus:Deposit", NS) if accounts is not None else None
    mortgage = accounts.find("cus:Mortgage", NS) if accounts is not None else None
    transactions = response.find("cus:RecentTransactions", NS)
    if profile is None or accounts is None or deposit is None or mortgage is None or transactions is None:
        raise XmlMappingError("The customer response is missing a required section")

    try:
        return CustomerDataResponse(
            customer_profile=CustomerProfile(
                internal_id=_required_text(profile, "cus:InternalID"),
                full_name=_required_text(profile, "cus:FullName"),
                risk_tier=RiskTier(_required_text(profile, "cus:RiskTier")),
            ),
            accounts=Accounts(
                deposit=DepositBalances(
                    checking=_decimal(deposit, "cus:Checking"),
                    savings=_decimal(deposit, "cus:Savings"),
                    currency=_required_text(deposit, "cus:Currency"),
                ),
                mortgage=Mortgage(
                    loan_id=_required_text(mortgage, "cus:LoanID"),
                    principal_remaining=_decimal(mortgage, "cus:PrincipalRemaining"),
                    interest_rate=_decimal(mortgage, "cus:InterestRate"),
                    next_payment_due=_date(mortgage, "cus:NextPaymentDue"),
                ),
            ),
            recent_transactions=[
                Transaction(
                    date=_date(transaction, "cus:Date"),
                    merchant=_required_text(transaction, "cus:Merchant"),
                    amount=_decimal(transaction, "cus:Amount"),
                )
                for transaction in transactions.findall("cus:Tx", NS)
            ],
        )
    except (ValidationError, ValueError) as error:
        raise XmlMappingError(f"The XML values violate the API contract: {error}") from error
