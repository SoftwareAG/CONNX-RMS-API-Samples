"""Example httpx client for the read-only customer API.

Shows two practices worth copying into real clients:

* Retry with backoff. Transient failures (connection errors, timeouts, and HTTP
  502/503/504) are retried a few times, waiting longer each time and honouring
  the API's Retry-After header. Other errors, such as 404 or 422, are not retried.
* Request IDs. Every request carries an X-Request-ID, which the API echoes and
  writes to its logs, so a client-side error can be matched to the server log.
  Retries of the same call reuse the same ID.
"""
import logging
import os
import random
import time
import uuid

import httpx

logger = logging.getLogger("customer_client")

RETRY_STATUSES = {502, 503, 504}
MAX_ATTEMPTS = 4
BASE_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 10.0


def _delay(attempt: int, response: httpx.Response | None) -> float:
    """Seconds to wait before the next attempt: Retry-After if given, else exponential backoff with jitter."""
    retry_after = response.headers.get("Retry-After") if response is not None else None
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), MAX_DELAY_SECONDS)
    return min(BASE_DELAY_SECONDS * 2 ** (attempt - 1), MAX_DELAY_SECONDS) * random.uniform(0.5, 1.0)


def get_with_retry(client: httpx.Client, path: str, *, sleep=time.sleep, **kwargs) -> httpx.Response:
    """GET `path`, retrying transient failures. Raises httpx.HTTPError if all attempts fail."""
    request_id = str(uuid.uuid4())
    headers = {**kwargs.pop("headers", {}), "X-Request-ID": request_id}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(path, headers=headers, **kwargs)
        except httpx.TransportError as exc:  # connection refused, timeout, ...
            if attempt == MAX_ATTEMPTS:
                logger.error("GET %s failed after %d attempts (%s) [request id %s]", path, attempt, type(exc).__name__, request_id)
                raise
            problem, response = type(exc).__name__, None
        else:
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()  # 4xx and other errors are not retried
                return response
            if attempt == MAX_ATTEMPTS:
                logger.error("GET %s failed after %d attempts (HTTP %d) [request id %s]", path, attempt, response.status_code, request_id)
                response.raise_for_status()
            problem = f"HTTP {response.status_code}"
        wait = _delay(attempt, response)
        logger.warning("GET %s: %s, retrying in %.1fs (attempt %d/%d) [request id %s]", path, problem, wait, attempt, MAX_ATTEMPTS, request_id)
        sleep(wait)
    raise AssertionError("unreachable")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # hide httpx's per-request INFO lines
    base_url = os.getenv("CONNX_RMS_API_URL", "http://127.0.0.1:8000").rstrip("/")
    with httpx.Client(base_url=base_url, timeout=10) as client:
        try:
            ready = get_with_retry(client, "/ready")
            print("API:", ready.json(), f"[request id {ready.headers.get('X-Request-ID')}]")
            response = get_with_retry(client, "/v1/customers", params={"limit": 10, "offset": 0})
        except httpx.HTTPError as exc:
            print(f"Request failed: {exc}")
            return 1
        for customer in response.json():
            print(f"{customer['customer_id']}: {customer['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
