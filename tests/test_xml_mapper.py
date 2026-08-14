"""Tests for conversion of the legacy SOAP response into API data."""

from pathlib import Path

import pytest

from app.models import RiskTier
from app.xml_mapper import XmlMappingError, load_customer_data


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "raw_schema.xml"


def test_load_customer_data_maps_the_supplied_soap_response() -> None:
    result = load_customer_data(FIXTURE_PATH)

    assert result.customer_profile.internal_id == "991029384"
    assert result.customer_profile.full_name == "Monish K C"
    assert result.customer_profile.risk_tier is RiskTier.LOW
    assert str(result.accounts.deposit.checking) == "1542.50"
    assert result.accounts.deposit.currency == "INR"
    assert result.accounts.mortgage.loan_id == "ML-55412"
    assert result.accounts.mortgage.next_payment_due.isoformat() == "2026-09-01"
    assert [(item.merchant, str(item.amount)) for item in result.recent_transactions] == [
        ("AWS Cloud Services", "-450.00"),
        ("Dodo Payments Inc", "12500.00"),
    ]


def test_load_customer_data_rejects_malformed_xml(tmp_path: Path) -> None:
    xml_file = tmp_path / "malformed.xml"
    xml_file.write_text("<soapenv:Envelope>", encoding="utf-8")

    with pytest.raises(XmlMappingError, match="not well-formed"):
        load_customer_data(xml_file)


def test_load_customer_data_requires_customer_response(tmp_path: Path) -> None:
    xml_file = tmp_path / "missing-response.xml"
    xml_file.write_text(
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" />',
        encoding="utf-8",
    )

    with pytest.raises(XmlMappingError, match="Missing GetCustomerDataResponse"):
        load_customer_data(xml_file)


@pytest.mark.parametrize(
    ("source", "replacement", "error_message"),
    [
        ("<cus:Checking>1542.50</cus:Checking>", "<cus:Checking>not-money</cus:Checking>", "Invalid decimal"),
        ("<cus:NextPaymentDue>2026-09-01</cus:NextPaymentDue>", "<cus:NextPaymentDue>not-a-date</cus:NextPaymentDue>", "Invalid ISO date"),
        ("<cus:FullName>Monish K C</cus:FullName>", "<cus:FullName></cus:FullName>", "Missing required XML element"),
    ],
)
def test_load_customer_data_rejects_invalid_required_values(
    tmp_path: Path, source: str, replacement: str, error_message: str
) -> None:
    xml_file = tmp_path / "invalid-value.xml"
    xml_file.write_text(FIXTURE_PATH.read_text(encoding="utf-8").replace(source, replacement), encoding="utf-8")

    with pytest.raises(XmlMappingError, match=error_message):
        load_customer_data(xml_file)
