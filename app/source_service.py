"""Server-configured SOAP source fetching and metadata-only Supabase audit storage."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class SourceConfigurationError(ValueError):
    """Raised for invalid server-side source configuration."""


class SourceFetchError(RuntimeError):
    """Raised when a configured SOAP source cannot be fetched."""


@dataclass(frozen=True)
class SoapSource:
    source_id: str
    url: str
    method: str
    headers_env: str | None = None
    body_env: str | None = None

    def public_metadata(self) -> dict[str, str]:
        parsed = urlparse(self.url)
        return {"id": self.source_id, "host": parsed.netloc, "method": self.method}


def configured_sources() -> dict[str, SoapSource]:
    """Load trusted sources from the deployment environment, never from clients."""
    raw_sources = os.getenv("LEGACYLINK_SOURCES_JSON", "[]")
    try:
        values = json.loads(raw_sources)
    except json.JSONDecodeError as error:
        raise SourceConfigurationError("LEGACYLINK_SOURCES_JSON is not valid JSON") from error
    if not isinstance(values, list):
        raise SourceConfigurationError("LEGACYLINK_SOURCES_JSON must be a JSON list")

    sources: dict[str, SoapSource] = {}
    for value in values:
        if not isinstance(value, dict):
            raise SourceConfigurationError("Each SOAP source must be a JSON object")
        source_id = value.get("id")
        url = value.get("url")
        method = str(value.get("method", "POST")).upper()
        if not isinstance(source_id, str) or not source_id or not isinstance(url, str):
            raise SourceConfigurationError("Each SOAP source needs a non-empty id and url")
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise SourceConfigurationError(f"Source {source_id!r} must use an absolute HTTP(S) URL")
        if parsed.scheme == "http" and os.getenv("LEGACYLINK_ALLOW_HTTP", "false").lower() != "true":
            raise SourceConfigurationError(f"Source {source_id!r} uses HTTP; enable it only for local demos")
        if method not in {"GET", "POST"}:
            raise SourceConfigurationError(f"Source {source_id!r} must use GET or POST")
        if source_id in sources:
            raise SourceConfigurationError(f"Duplicate source id: {source_id}")
        sources[source_id] = SoapSource(
            source_id=source_id,
            url=url,
            method=method,
            headers_env=value.get("headers_env"),
            body_env=value.get("body_env"),
        )
    return sources


def fetch_source(source: SoapSource) -> bytes:
    """Fetch a trusted server-configured source with credentials kept in env vars."""
    headers = {"Accept": "application/xml, text/xml", "User-Agent": "LegacyLink/1.0"}
    if source.headers_env:
        try:
            configured_headers = json.loads(os.environ[source.headers_env])
        except KeyError as error:
            raise SourceConfigurationError(f"Missing header environment variable: {source.headers_env}") from error
        except json.JSONDecodeError as error:
            raise SourceConfigurationError(f"{source.headers_env} must contain a JSON object") from error
        if not isinstance(configured_headers, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in configured_headers.items()
        ):
            raise SourceConfigurationError(f"{source.headers_env} must contain string headers")
        headers.update(configured_headers)

    body = os.environ.get(source.body_env, "").encode("utf-8") if source.body_env else None
    request = Request(source.url, data=body, headers=headers, method=source.method)
    try:
        with urlopen(request, timeout=15) as response:
            return response.read(1_000_001)
    except OSError as error:
        raise SourceFetchError(f"Could not fetch configured source {source.source_id!r}") from error


def record_analysis(source_id: str, analysis: dict[str, object]) -> bool:
    """Persist safe analysis metadata only when Supabase audit credentials exist."""
    supabase_url = os.getenv("SUPABASE_URL")
    # Supabase's current secret keys (sb_secret_...) and legacy service-role keys
    # both authorize the Data API through the apikey header. Never send a secret
    # key as an Authorization bearer token: new opaque keys are not JWTs.
    secret_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not secret_key:
        return False

    payload = json.dumps({"source_id": source_id, "analysis": analysis}).encode("utf-8")
    request = Request(
        f"{supabase_url.rstrip('/')}/rest/v1/migration_runs",
        data=payload,
        headers={
            "apikey": secret_key,
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10):
            return True
    except OSError as error:
        raise SourceFetchError("Could not write migration audit metadata to Supabase") from error
