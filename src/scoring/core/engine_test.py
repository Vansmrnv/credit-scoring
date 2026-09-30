import uuid
from datetime import datetime, timedelta, timezone

import pytest

from scoring.core.engine import Engine
from scoring.core.rules import (
    calc_age_score,
    calc_credit_age,
    calc_credit_limit,
    calc_debt_ratio,
    calc_payment_history,
    decide,
)
from scoring.schemas.rules_schemas import load_rules
from scoring.schemas.schemas import CreditApplication, Decision, RiskTier, ScoreBreakdown

RULES = load_rules()


def _application(**overrides) -> CreditApplication:
    fields = {
        "applicant_id": "applicant-1",
        "age": 40,
        "monthly_income": 10_000.0,
        "monthly_debt": 1_000.0,
        "credit_history_months": 84,
        "missed_payments": 0,
        "requested_amount": 5_000.0,
    }
    fields.update(overrides)
    return CreditApplication(**fields)


@pytest.fixture
def engine() -> Engine:
    return Engine(RULES)


def test_engine_stores_rules(engine):
    assert engine.rules == RULES


@pytest.mark.parametrize(
    ("application", "decision", "risk_tier"),
    [
        pytest.param(
            _application(),
            Decision.APPROVED,
            RiskTier.A,
            id="approved_a",
        ),
        pytest.param(
            _application(
                applicant_id="applicant-2",
                age=22,
                monthly_income=8_000.0,
                monthly_debt=1_600.0,
                credit_history_months=24,
                missed_payments=1,
            ),
            Decision.APPROVED,
            RiskTier.B,
            id="approved_b",
        ),
        pytest.param(
            _application(
                applicant_id="applicant-3",
                age=22,
                monthly_income=5_000.0,
                monthly_debt=2_500.0,
                credit_history_months=24,
                missed_payments=2,
            ),
            Decision.REVIEW,
            RiskTier.C,
            id="review",
        ),
        pytest.param(
            _application(
                applicant_id="applicant-4",
                age=70,
                monthly_income=1_000.0,
                monthly_debt=900.0,
                credit_history_months=3,
                missed_payments=8,
            ),
            Decision.REJECTED,
            RiskTier.D,
            id="rejected",
        ),
        pytest.param(
            _application(
                applicant_id="applicant-5",
                age=18,
                monthly_income=0.0,
                monthly_debt=0.0,
                credit_history_months=84,
                missed_payments=0,
            ),
            Decision.REVIEW,
            RiskTier.C,
            id="no_income",
        ),
    ],
)
def test_score(engine, application, decision, risk_tier):
    result = engine.score(application)

    debt_points, debt_reason = calc_debt_ratio(application, RULES)
    payment_points, payment_reason = calc_payment_history(application, RULES)
    credit_age_points, credit_reason = calc_credit_age(application, RULES)
    age_points, age_reason = calc_age_score(application, RULES)
    total = debt_points + payment_points + credit_age_points + age_points

    assert (decision, risk_tier) == decide(total, RULES)
    assert result.applicant_id == application.applicant_id
    assert result.score == total
    assert result.decision == decision
    assert result.risk_tier == risk_tier
    assert result.credit_limit == calc_credit_limit(application.monthly_income, decision, RULES)
    assert result.reasons == [debt_reason, payment_reason, credit_reason, age_reason]
    assert result.breakdown == ScoreBreakdown(
        debt_ratio_score=debt_points,
        payment_history_score=payment_points,
        credit_age_score=credit_age_points,
        age_score=age_points,
        total=total,
    )
    assert result.model_version == RULES.model_version
    assert result.application_id == str(uuid.UUID(result.application_id))
    assert result.processed_at.tzinfo == timezone.utc
    assert datetime.now(timezone.utc) - result.processed_at < timedelta(seconds=5)


def test_score_assigns_a_new_application_id(engine):
    application = _application()

    first = engine.score(application)
    second = engine.score(application)

    assert first.application_id != second.application_id
