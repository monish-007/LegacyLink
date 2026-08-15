"""Tests for conversion of the legacy SOAP response into API data."""

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.main import app, get_migration_report, lifespan
from app.migration_analyzer import analyze_soap_payload
from app.source_service import SourceConfigurationError, configured_sources
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


def test_migration_report_proves_validation_without_exposing_soap_authentication() -> None:
    async def get_report() -> dict[str, object]:
        async with lifespan(app):
            return await get_migration_report(SimpleNamespace(app=app))

    report = asyncio.run(get_report())
    assert report["status"] == "validated"
    assert report["source"]["authentication_headers_exposed"] is False
    assert len(report["source"]["sha256"]) == 64
    assert report["validation_summary"]["deployment_requires_human_approval"] is True


def test_analyzer_discovers_types_and_redacts_sensitive_values() -> None:
    analysis = analyze_soap_payload(
        b"<Envelope><Body><Customer><FullName>Ada Lovelace</FullName><Balance>42.50</Balance>"
        b"<AuthToken>do-not-return-me</AuthToken></Customer></Body></Envelope>"
    )

    fields = analysis["fields"]
    assert any(field["inferred_type"] == "decimal" for field in fields)
    assert any(field["sensitive"] is True for field in fields)
    assert "do-not-return-me" not in str(analysis)
    assert analysis["summary"]["persistence"] == "none"


def test_source_configuration_rejects_unapproved_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEGACYLINK_SOURCES_JSON", '[{"id":"bank","url":"http://example.test/soap"}]')
    monkeypatch.delenv("LEGACYLINK_ALLOW_HTTP", raising=False)

    with pytest.raises(SourceConfigurationError, match="uses HTTP"):
        configured_sources()
