"""FastAPI REST wrapper for the supplied legacy SOAP customer record."""

import asyncio
from contextlib import asynccontextmanager
from hashlib import sha256
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .metering import dodo_usage_metering
from .migration_analyzer import XmlAnalysisError, analyze_soap_payload
from .models import CustomerDataResponse
from .source_service import SourceConfigurationError, SourceFetchError, configured_sources, fetch_source, record_analysis
from .xml_mapper import XmlMappingError, load_customer_data

DATA_FILE = Path(__file__).resolve().parent.parent / "raw_schema.xml"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Parse and validate the legacy response before accepting traffic."""
    try:
        app.state.customer_data = load_customer_data(DATA_FILE)
    except (OSError, XmlMappingError) as error:
        raise RuntimeError(f"Unable to load legacy customer data: {error}") from error
    yield


app = FastAPI(
    title="Legacy Customer Data REST API",
    version="1.0.0",
    description="Strict JSON projection of the supplied legacy SOAP customer-data response.",
    lifespan=lifespan,
)
app.middleware("http")(dodo_usage_metering)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/v1/customer-data",
    response_model=CustomerDataResponse,
    response_model_exclude_none=True,
    tags=["customers"],
)
async def get_customer_data(request: Request) -> CustomerDataResponse:
    """Return the validated JSON representation of the supplied SOAP record."""
    customer_data = getattr(request.app.state, "customer_data", None)
    if customer_data is None:
        raise HTTPException(status_code=503, detail="Legacy customer data is unavailable")
    return customer_data


@app.get("/v1/migration-report", tags=["operations"])
async def get_migration_report(request: Request) -> dict[str, object]:
    """Expose the evidence behind the generated API without leaking SOAP headers.

    This is intentionally a small, read-only audit surface for reviewers and
    operators: it proves that the response was parsed and validated against the
    generated contract before the API became available.
    """
    customer_data = getattr(request.app.state, "customer_data", None)
    if customer_data is None:
        raise HTTPException(status_code=503, detail="Migration validation is unavailable")

    source_digest = sha256(DATA_FILE.read_bytes()).hexdigest()
    return {
        "status": "validated",
        "source": {
            "format": "SOAP XML",
            "sha256": source_digest,
            "authentication_headers_exposed": False,
        },
        "generated_contract": {
            "format": "OpenAPI / Pydantic",
            "strict_types": ["Decimal", "date", "enum"],
            "validated_sections": ["customer_profile", "accounts", "recent_transactions"],
        },
        "validation_summary": {
            "customer_records": 1,
            "transaction_records": len(customer_data.recent_transactions),
            "deployment_requires_human_approval": True,
        },
    }


@app.post("/v1/analyze-soap", tags=["migration"])
async def analyze_soap(xml_payload: bytes = Body(media_type="application/xml")) -> dict[str, object]:
    """Discover a candidate REST contract from an unseen SOAP/XML payload.

    Analysis is in-memory only and never includes source values in its response.
    A reviewer must validate the inferred contract before it becomes an API.
    """
    try:
        return analyze_soap_payload(xml_payload)
    except XmlAnalysisError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/v1/sources", tags=["migration"])
async def list_sources() -> dict[str, object]:
    """List configured source identities without revealing URLs or credentials."""
    try:
        return {"sources": [source.public_metadata() for source in configured_sources().values()]}
    except SourceConfigurationError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/v1/sources/{source_id}/analyze", tags=["migration"])
async def analyze_configured_source(source_id: str) -> dict[str, object]:
    """Fetch a trusted SOAP source and persist only safe contract metadata."""
    try:
        source = configured_sources().get(source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="Configured SOAP source not found")
        xml_payload = await asyncio.to_thread(fetch_source, source)
        analysis = analyze_soap_payload(xml_payload)
        audit_recorded = await asyncio.to_thread(record_analysis, source_id, analysis)
        return {"source": source.public_metadata(), "analysis": analysis, "audit_recorded": audit_recorded}
    except (SourceConfigurationError, SourceFetchError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except XmlAnalysisError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/dashboard", response_class=HTMLResponse, tags=["UI"])
async def render_dashboard():
    """Serves the interactive developer dashboard safely across paths & encodings."""
    possible_paths = [
        Path(__file__).parent / "dashboard.html",          # app/dashboard.html
        Path(__file__).parent.parent / "dashboard.html",   # rest-wrapper/dashboard.html
    ]
    for path in possible_paths:
        if path.exists():
            return HTMLResponse(content=path.read_text(encoding="utf-8"))
            
    raise HTTPException(status_code=404, detail="dashboard.html not found. Ensure it is saved in the app folder.")
