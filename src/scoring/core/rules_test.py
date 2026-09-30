import pytest

from pydantic import ValidationError

from scoring.schemas.rules_schemas import load_rules
from scoring.schemas.schemas import CreditApplication, Decision, RiskTier
from scoring.core.rules import (
    calc_age_score,
    calc_credit_age,
    calc_debt_ratio,
    calc_payment_history,
    decide, calc_credit_limit,
)

RULES = load_rules()
INCOME = 10_000.0
DEBT = 0
_THRESHOLDS = RULES.debt_ratio.thresholds
_POINTS = RULES.debt_ratio.points


def _application(
    monthly_income: float,
    monthly_debt: float,
    *,
    age: int = 30,
    credit_history_months: int = 24,
    missed_payments: int = 0,
) -> CreditApplication:
    return CreditApplication(
        applicant_id="1",
        age=age,
        monthly_income=monthly_income,
        monthly_debt=monthly_debt,
        credit_history_months=credit_history_months,
        missed_payments=missed_payments,
        requested_amount=5_000.0,
    )



def _debt_at(ratio: float) -> float:
    return INCOME * ratio


@pytest.mark.parametrize(
    ("monthly_income", "monthly_debt", "expected"),
    [
        pytest.param(
            0,
            1_000,
            (_POINTS.critical, "no_income_data"),
            id="zero_income",
        ),
        pytest.param(
            INCOME,
            0,
            (_POINTS.excellent, "excellent_debt_ratio"),
            id="zero_debt",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.excellent),
            (_POINTS.excellent, "excellent_debt_ratio"),
            id="at_excellent",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.excellent) + 0.01,
            (_POINTS.good, "good_debt_ratio"),
            id="above_excellent",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.good),
            (_POINTS.good, "good_debt_ratio"),
            id="at_good",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.good) + 0.01,
            (_POINTS.moderate, "moderate_debt_ratio"),
            id="above_good",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.moderate),
            (_POINTS.moderate, "moderate_debt_ratio"),
            id="at_moderate",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.moderate) + 0.01,
            (_POINTS.high, "high_debt_ratio"),
            id="above_moderate",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.high),
            (_POINTS.high, "high_debt_ratio"),
            id="at_high",
        ),
        pytest.param(
            INCOME,
            _debt_at(_THRESHOLDS.high) + 0.01,
            (_POINTS.critical, "critical_debt_ratio"),
            id="above_high",
        ),
    ],
)
def test_calc_debt_ratio(monthly_income, monthly_debt, expected):
    application = _application(monthly_income, monthly_debt)
    assert calc_debt_ratio(application, RULES) == expected



def _payment_history(missed_payments) -> CreditApplication:
    return CreditApplication(
        applicant_id="1",
        age=30,
        monthly_income=INCOME,
        monthly_debt=DEBT,
        credit_history_months=24,
        missed_payments=missed_payments,
        requested_amount=5_000.0,
    )


@pytest.mark.parametrize(
    ("missed_payments", "expected"),
    [
        pytest.param(
            0,
            (RULES.payment_history.points.perfect, "perfect_payment_history"),
            id="at_perfect"
        ),
        pytest.param(
            1,
            (RULES.payment_history.points.good, "good_payment_history"),
            id="at_good"
        ),
        pytest.param(
            2,
            (RULES.payment_history.points.fair, "fair_payment_history"),
            id="at_fair"
        ),
        pytest.param(
            3,
            (RULES.payment_history.points.poor, "poor_payment_history"),
            id="below_fair"
        ),
        pytest.param(
            4,
            (RULES.payment_history.points.poor, "poor_payment_history"),
            id="at_poor"
        ),
        pytest.param(
            5,
            (RULES.payment_history.points.very_poor, "very_poor_payment_history"),
            id="at_very_poor"
        ),

    ]
)
def test_calc_payment_history(missed_payments, expected):
    application = _payment_history(missed_payments)
    assert calc_payment_history(application, RULES) == expected


_CREDIT_AGE_THRESHOLDS = RULES.credit_age.thresholds
_CREDIT_AGE_POINTS = RULES.credit_age.points


@pytest.mark.parametrize(
    ("credit_history_months", "expected"),
    [
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.long,
            (_CREDIT_AGE_POINTS.long, "long_credit_history"),
            id="at_long",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.long - 1,
            (_CREDIT_AGE_POINTS.good, "good_credit_history"),
            id="below_long",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.good,
            (_CREDIT_AGE_POINTS.good, "good_credit_history"),
            id="at_good",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.good - 1,
            (_CREDIT_AGE_POINTS.moderate, "moderate_credit_history"),
            id="below_good",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.moderate,
            (_CREDIT_AGE_POINTS.moderate, "moderate_credit_history"),
            id="at_moderate",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.moderate - 1,
            (_CREDIT_AGE_POINTS.short, "short_credit_history"),
            id="below_moderate",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.short,
            (_CREDIT_AGE_POINTS.short, "short_credit_history"),
            id="at_short",
        ),
        pytest.param(
            _CREDIT_AGE_THRESHOLDS.short - 1,
            (_CREDIT_AGE_POINTS.very_short, "very_short_credit_history"),
            id="below_short",
        ),
    ],
)
def test_calc_credit_age(credit_history_months, expected):
    application = _application(INCOME, DEBT, credit_history_months=credit_history_months)
    assert calc_credit_age(application, RULES) == expected


_AGE_THRESHOLDS = RULES.age_score.thresholds
_AGE_POINTS = RULES.age_score.points


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        pytest.param(
            _AGE_THRESHOLDS.optimal_min,
            (_AGE_POINTS.optimal, "optimal_age_range"),
            id="at_optimal_min",
        ),
        pytest.param(
            _AGE_THRESHOLDS.optimal_max,
            (_AGE_POINTS.optimal, "optimal_age_range"),
            id="at_optimal_max",
        ),
        pytest.param(
            _AGE_THRESHOLDS.optimal_min - 1,
            (_AGE_POINTS.good, "good_age_range"),
            id="just_below_optimal",
        ),
        pytest.param(
            _AGE_THRESHOLDS.optimal_max + 1,
            (_AGE_POINTS.good, "good_age_range"),
            id="just_above_optimal",
        ),
        pytest.param(
            _AGE_THRESHOLDS.good_min,
            (_AGE_POINTS.good, "good_age_range"),
            id="at_good_min",
        ),
        pytest.param(
            _AGE_THRESHOLDS.good_max,
            (_AGE_POINTS.good, "good_age_range"),
            id="at_good_max",
        ),
        pytest.param(
            _AGE_THRESHOLDS.good_min - 1,
            (_AGE_POINTS.acceptable, "acceptable_age_range"),
            id="just_below_good",
        ),
        pytest.param(
            _AGE_THRESHOLDS.good_max + 1,
            (_AGE_POINTS.acceptable, "acceptable_age_range"),
            id="just_above_good",
        ),
        pytest.param(
            18,
            (_AGE_POINTS.acceptable, "acceptable_age_range"),
            id="at_minimum_age",
        ),
    ],
)
def test_calc_age_score(age, expected):
    application = _application(INCOME, DEBT, age=age)
    assert calc_age_score(application, RULES) == expected


_DECISIONS = RULES.decisions


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        pytest.param(
            _DECISIONS.approved_a,
            (Decision.APPROVED, RiskTier.A),
            id="at_approved_a",
        ),
        pytest.param(
            _DECISIONS.approved_a - 1,
            (Decision.APPROVED, RiskTier.B),
            id="below_approved_a",
        ),
        pytest.param(
            _DECISIONS.approved_b,
            (Decision.APPROVED, RiskTier.B),
            id="at_approved_b",
        ),
        pytest.param(
            _DECISIONS.approved_b - 1,
            (Decision.REVIEW, RiskTier.C),
            id="below_approved_b",
        ),
        pytest.param(
            _DECISIONS.review,
            (Decision.REVIEW, RiskTier.C),
            id="at_review",
        ),
        pytest.param(
            _DECISIONS.review - 1,
            (Decision.REJECTED, RiskTier.D),
            id="below_review",
        ),
    ],
)
def test_decide(total, expected):
    assert decide(total, RULES) == expected


def at_limit(monthly_income, multiplier):
    return monthly_income * multiplier


_MULTIPLIERS = RULES.credit_limit_multipliers
_INCOME_FOR_LIMIT = 2_500.0


@pytest.mark.parametrize(
    ("monthly_income", "decision", "expected"),
    [
        pytest.param(
            _INCOME_FOR_LIMIT,
            Decision.APPROVED,
            at_limit(_INCOME_FOR_LIMIT, _MULTIPLIERS.approved),
            id="approved",
        ),
        pytest.param(
            _INCOME_FOR_LIMIT,
            Decision.REVIEW,
            at_limit(_INCOME_FOR_LIMIT, _MULTIPLIERS.review),
            id="review",
        ),
        pytest.param(
            _INCOME_FOR_LIMIT,
            Decision.REJECTED,
            at_limit(_INCOME_FOR_LIMIT, _MULTIPLIERS.rejected),
            id="rejected",
        ),
    ],
)
def test_calc_credit_limit(monthly_income, decision, expected):
    assert calc_credit_limit(monthly_income, decision, RULES) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("age", 17, id="under_18"),
        pytest.param("monthly_income", -1, id="negative_income"),
        pytest.param("monthly_debt", -1, id="negative_debt"),
        pytest.param("requested_amount", -1, id="negative_requested_amount"),
    ],
)
def test_credit_application_rejects_invalid_boundary_values(field, value):
    application = {
        "applicant_id": "1",
        "age": 30,
        "monthly_income": INCOME,
        "monthly_debt": 0,
        "credit_history_months": 24,
        "missed_payments": 0,
        "requested_amount": 5_000.0,
    }
    application[field] = value
    with pytest.raises(ValidationError):
        CreditApplication(**application)