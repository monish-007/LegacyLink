"""FastAPI REST wrapper for the supplied legacy SOAP customer record."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from .metering import dodo_usage_metering
from .models import CustomerDataResponse
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