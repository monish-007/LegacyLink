"""Privacy-aware discovery of a SOAP/XML payload's candidate REST contract."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re
from xml.etree import ElementTree as ET


SENSITIVE_TOKENS = {"auth", "token", "password", "secret", "ssn", "pan", "accountnumber"}
MAX_XML_BYTES = 1_000_000
MAX_FIELDS = 100


class XmlAnalysisError(ValueError):
    """Raised when an XML payload cannot safely be analyzed."""


def _local_name(name: str) -> str:
    return name.rsplit("}", maxsplit=1)[-1]


def _snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).replace("-", "_").lower()


def _infer_type(value: str) -> tuple[str, float]:
    try:
        date.fromisoformat(value)
        return "date", 0.98
    except ValueError:
        pass
    try:
        Decimal(value)
        return "decimal", 0.93
    except InvalidOperation:
        return "string", 0.75


def analyze_soap_payload(xml_bytes: bytes) -> dict[str, object]:
    """Return contract candidates only; never return values from the source XML."""
    if not xml_bytes:
        raise XmlAnalysisError("An XML payload is required")
    if len(xml_bytes) > MAX_XML_BYTES:
        raise XmlAnalysisError(f"XML payload exceeds the {MAX_XML_BYTES:,}-byte analysis limit")

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as error:
        raise XmlAnalysisError("The XML payload is not well-formed") from error

    fields: list[dict[str, object]] = []
    sensitive_fields: list[str] = []

    def visit(element: ET.Element, ancestors: list[str]) -> None:
        children = list(element)
        path = ancestors + [_local_name(element.tag)]
        if children:
            for child in children:
                visit(child, path)
            return

        value = (element.text or "").strip()
        if not value:
            return
        if len(fields) >= MAX_FIELDS:
            raise XmlAnalysisError(f"XML payload exceeds the {MAX_FIELDS}-field analysis limit")
        source_path = "/".join(path)
        json_path = ".".join(_snake_case(part) for part in path[1:])
        is_sensitive = any(token in _snake_case(source_path).replace("_", "") for token in SENSITIVE_TOKENS)
        inferred_type, confidence = _infer_type(value)
        fields.append(
            {
                "source_path": source_path,
                "proposed_json_path": json_path,
                "inferred_type": inferred_type,
                "confidence": confidence,
                "sensitive": is_sensitive,
            }
        )
        if is_sensitive:
            sensitive_fields.append(source_path)

    visit(root, [])
    if not fields:
        raise XmlAnalysisError("No non-empty XML fields were found")

    return {
        "status": "analyzed",
        "fields": fields,
        "summary": {
            "field_count": len(fields),
            "sensitive_field_count": len(sensitive_fields),
            "sensitive_source_paths": sensitive_fields,
            "raw_values_returned": False,
            "persistence": "none",
        },
    }
