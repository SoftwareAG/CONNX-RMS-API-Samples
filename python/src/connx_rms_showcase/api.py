import logging
import re
import time
import uuid
from collections.abc import Generator
from contextvars import ContextVar
from typing import Annotated

import pyodbc
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from .config import get_settings
from .models import Customer
from .repository import CustomerNotFoundError, CustomerRepository

# Seconds a client should wait before retrying after a 503 (sent as Retry-After).
RETRY_AFTER_SECONDS = 5

# Client-supplied request IDs are echoed and logged, so accept only short, safe
# values; anything else (for example, containing newlines) is replaced.
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,64}")
_request_id: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    """Add the current request ID to every log record as %(request_id)s."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
for _handler in logging.getLogger().handlers:
    _handler.addFilter(_RequestIdFilter())
logger = logging.getLogger(__name__)
app = FastAPI(title="CONNX RMS Customer API", version="1.0.0", description="Read-only access to OpenVMS RMS CUSTOMER data via CONNX.")

_UNAVAILABLE_HEADERS = {"Retry-After": str(RETRY_AFTER_SECONDS)}


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if _REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())
    token = _request_id.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info("%s %s -> %d (%.0f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        _request_id.reset(token)


def get_repository() -> Generator[CustomerRepository, None, None]:
    yield CustomerRepository(get_settings())


RepositoryDep = Annotated[CustomerRepository, Depends(get_repository)]


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def ready(repository: RepositoryDep) -> dict[str, str]:
    try:
        repository.ping()
        return {"status": "ready"}
    except pyodbc.Error:
        logger.exception("CONNX readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"}, headers=_UNAVAILABLE_HEADERS)


@app.get("/v1/customers", response_model=list[Customer], response_model_by_alias=False, tags=["customers"])
def list_customers(
    repository: RepositoryDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Customer]:
    try:
        return repository.list(limit, offset)
    except pyodbc.Error:
        logger.exception("CONNX query failed while listing customers")
        raise HTTPException(status_code=503, detail="Customer data service is unavailable", headers=_UNAVAILABLE_HEADERS) from None


@app.get("/v1/customers/{customer_id}", response_model=Customer, response_model_by_alias=False, tags=["customers"])
def get_customer(customer_id: str, repository: RepositoryDep) -> Customer:
    try:
        return repository.get(customer_id)
    except CustomerNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found") from None
    except pyodbc.Error:
        logger.exception("CONNX query failed while retrieving customer")
        raise HTTPException(status_code=503, detail="Customer data service is unavailable", headers=_UNAVAILABLE_HEADERS) from None
