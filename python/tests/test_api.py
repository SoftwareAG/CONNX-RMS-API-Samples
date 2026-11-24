from fastapi.testclient import TestClient

from connx_rms_showcase import api
from connx_rms_showcase.models import Customer


class FakeRepository:
    def ping(self):
        return None

    def list(self, limit, offset):
        return [Customer(customerid="00001", customername=" Ada Demo ", customercity="Boston")][offset : offset + limit]

    def get(self, customer_id):
        return Customer(customerid=customer_id, customername="Ada Demo")


def test_health_and_request_id():
    response = TestClient(api.app).get("/health", headers={"X-Request-ID": "test-123"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-123"


def test_ready_and_list():
    api.app.dependency_overrides[api.get_repository] = lambda: FakeRepository()
    try:
        client = TestClient(api.app)
        assert client.get("/ready").json() == {"status": "ready"}
        response = client.get("/v1/customers?limit=1")
        assert response.status_code == 200
        assert response.json()[0]["customer_id"] == "00001"
    finally:
        api.app.dependency_overrides.clear()
