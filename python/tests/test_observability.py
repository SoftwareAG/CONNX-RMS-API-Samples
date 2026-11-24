import logging
import sys
from pathlib import Path

import httpx
import pyodbc
import pytest
from fastapi.testclient import TestClient

from connx_rms_showcase import api

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import client_example


class FailingRepository:
    def ping(self):
        raise pyodbc.Error("down")

    def list(self, limit, offset):
        raise pyodbc.Error("down")


@pytest.fixture
def failing_api():
    api.app.dependency_overrides[api.get_repository] = lambda: FailingRepository()
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_unavailable_responses_include_retry_after(failing_api):
    for path in ("/ready", "/v1/customers"):
        response = failing_api.get(path)
        assert response.status_code == 503
        assert response.headers["Retry-After"] == str(api.RETRY_AFTER_SECONDS)


def test_request_id_is_added_to_server_logs(failing_api, caplog):
    caplog.handler.addFilter(api._RequestIdFilter())
    with caplog.at_level(logging.INFO, logger="connx_rms_showcase.api"):
        failing_api.get("/v1/customers", headers={"X-Request-ID": "trace-42"})
    request_ids = {record.request_id for record in caplog.records}
    assert request_ids == {"trace-42"}
    assert any("GET /v1/customers -> 503" in record.getMessage() for record in caplog.records)


def test_unsafe_request_id_is_replaced():
    response = TestClient(api.app).get("/health", headers={"X-Request-ID": "bad id\twith spaces"})
    assert response.headers["X-Request-ID"] != "bad id\twith spaces"
    assert len(response.headers["X-Request-ID"]) == 36


def _client(responses):
    seen = []

    def handler(request):
        seen.append(request.headers["X-Request-ID"])
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test"), seen


def test_client_retries_transient_failures_with_same_request_id():
    client, seen = _client([httpx.ConnectError("refused"), httpx.Response(503, headers={"Retry-After": "2"}), httpx.Response(200, json=[])])
    waits = []
    response = client_example.get_with_retry(client, "/v1/customers", sleep=waits.append)
    assert response.status_code == 200
    assert len(seen) == 3 and len(set(seen)) == 1
    assert waits[1] == 2.0  # Retry-After honoured


def test_client_does_not_retry_client_errors():
    client, seen = _client([httpx.Response(404)])
    with pytest.raises(httpx.HTTPStatusError):
        client_example.get_with_retry(client, "/v1/customers/NOPE1", sleep=lambda _: None)
    assert len(seen) == 1


def test_client_gives_up_after_max_attempts():
    client, seen = _client([httpx.Response(503)] * client_example.MAX_ATTEMPTS)
    with pytest.raises(httpx.HTTPStatusError):
        client_example.get_with_retry(client, "/ready", sleep=lambda _: None)
    assert len(seen) == client_example.MAX_ATTEMPTS
