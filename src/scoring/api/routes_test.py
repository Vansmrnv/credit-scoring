import uuid

import pytest
from fastapi.testclient import TestClient

from scoring.core.engine import Engine
from scoring.main import create_app
from scoring.schemas.rules_schemas import load_rules
from scoring.schemas.schemas import CreditApplication, ScoringResult

VALID_APPLICATION = {
    "applicant_id": "applicant-1",
    "age": 40,
    "monthly_income": 10_000.0,
    "monthly_debt": 1_000.0,
    "credit_history_months": 84,
    "missed_payments": 0,
    "requested_amount": 5_000.0,
}


class MemoryApplications:
    def __init__(self) -> None:
        self.rows: dict[str, ScoringResult] = {}

    def save(self, result: ScoringResult) -> None:
        self.rows[result.application_id] = result

    def get(self, application_id: str) -> ScoringResult | None:
        return self.rows.get(application_id)


@pytest.fixture
def store() -> MemoryApplications:
    return MemoryApplications()


@pytest.fixture
def client(store: MemoryApplications) -> TestClient:
    return TestClient(create_app(store))


def test_post_application_returns_scoring_result(client: TestClient):
    response = client.post("/v1/applications", json=VALID_APPLICATION)

    assert response.status_code == 200
    body = response.json()
    expected = Engine(load_rules()).score(CreditApplication(**VALID_APPLICATION))
    expected_body = expected.model_dump(mode="json")

    uuid.UUID(body["application_id"])
    assert body["processed_at"]
    for field, value in expected_body.items():
        if field in {"application_id", "processed_at"}:
            continue
        assert body[field] == value


def test_get_returns_the_stored_result(client: TestClient):
    created = client.post("/v1/applications", json=VALID_APPLICATION)

    fetched = client.get(f"/v1/applications/{created.json()['application_id']}")

    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_get_unknown_application_returns_404(client: TestClient):
    response = client.get("/v1/applications/missing")

    assert response.status_code == 404


def test_invalid_application_is_not_stored(client: TestClient, store: MemoryApplications):
    response = client.post("/v1/applications", json={**VALID_APPLICATION, "age": 17})

    assert response.status_code == 422
    assert store.rows == {}


def test_invalid_json_returns_422(client: TestClient):
    response = client.post(
        "/v1/applications",
        content=b"{",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({**VALID_APPLICATION, "age": 17}, id="under_18"),
        pytest.param({**VALID_APPLICATION, "monthly_income": -1}, id="negative_income"),
        pytest.param({**VALID_APPLICATION, "monthly_debt": -1}, id="negative_debt"),
        pytest.param(
            {**VALID_APPLICATION, "requested_amount": -1},
            id="negative_requested_amount",
        ),
        pytest.param(
            {key: value for key, value in VALID_APPLICATION.items() if key != "applicant_id"},
            id="missing_applicant_id",
        ),
    ],
)
def test_invalid_fields_return_422(client: TestClient, payload: dict[str, object]):
    response = client.post("/v1/applications", json=payload)

    assert response.status_code == 422
