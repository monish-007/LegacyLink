"""Dodo Payments metering integration boundary.

Replace ``report_usage`` with the Dodo Payments SDK/API call when credentials and
the meter event ID are available. The middleware deliberately fails open so a
temporary billing-provider outage never takes the API down.
"""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def report_usage(*, customer_id: str | None, endpoint: str, status_code: int, duration_ms: int) -> None:
    """Send one API-request usage event to Dodo Payments (placeholder)."""
    logger.info(
        "Dodo usage event ready: customer_id=%s endpoint=%s status=%s duration_ms=%s",
        customer_id,
        endpoint,
        status_code,
        duration_ms,
    )


async def dodo_usage_metering(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Meter each non-health request without retaining raw authentication data."""
    started = perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        if request.url.path != "/health":
            try:
                await report_usage(
                    customer_id=request.headers.get("X-Customer-Id"),
                    endpoint=request.url.path,
                    status_code=response.status_code if response else 500,
                    duration_ms=round((perf_counter() - started) * 1000),
                )
            except Exception:
                logger.exception("Dodo Payments usage reporting failed")
