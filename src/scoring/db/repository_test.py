import os
from pathlib import Path

import psycopg
import pytest

from scoring.core.engine import Engine
from scoring.db.repository import ApplicationRepository
from scoring.schemas.rules_schemas import load_rules
from scoring.schemas.schemas import CreditApplication

_SCHEMA = Path(__file__).with_name("schema.sql").read_text()


@pytest.fixture
def repository() -> ApplicationRepository:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set")
    with psycopg.connect(database_url) as connection:
        connection.execute(_SCHEMA)
    return ApplicationRepository(database_url)


def test_save_and_get_round_trip(repository: ApplicationRepository):
    result = Engine(load_rules()).score(
        CreditApplication(
            applicant_id="applicant-1",
            age=40,
            monthly_income=10_000.0,
            monthly_debt=1_000.0,
            credit_history_months=84,
            missed_payments=0,
            requested_amount=5_000.0,
        )
    )

    repository.save(result)
    try:
        assert repository.get(result.application_id) == result
        assert repository.get("missing") is None
    finally:
        with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
            connection.execute(
                "DELETE FROM applications WHERE application_id = %s",
                (result.application_id,),
            )
