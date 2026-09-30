import uuid
from datetime import datetime, timezone

from .rules import (
    calc_age_score,
    calc_credit_age,
    calc_credit_limit,
    calc_debt_ratio,
    calc_payment_history,
    decide,
)
from ..schemas.schemas import CreditApplication, ScoreBreakdown, ScoringResult
from ..schemas.rules_schemas import Rules


class Engine:
    def __init__(self, rules: Rules) -> None:
        self.rules = rules

    def score(self, app: CreditApplication) -> ScoringResult:
        debt_points, debt_reason = calc_debt_ratio(app, self.rules)
        payment_points, payment_reason = calc_payment_history(app, self.rules)
        credit_age_points, credit_reason = calc_credit_age(app, self.rules)
        age_points, age_reason = calc_age_score(app, self.rules)

        total = debt_points + payment_points + credit_age_points + age_points
        breakdown = ScoreBreakdown(
            debt_ratio_score=debt_points,
            payment_history_score=payment_points,
            credit_age_score=credit_age_points,
            age_score=age_points,
            total=total,
        )
        decision, risk_tier = decide(breakdown.total, self.rules)

        return ScoringResult(
            application_id=str(uuid.uuid4()),
            applicant_id=app.applicant_id,
            score=breakdown.total,
            decision=decision,
            risk_tier=risk_tier,
            credit_limit=calc_credit_limit(app.monthly_income, decision, self.rules),
            reasons=[debt_reason, payment_reason, credit_reason, age_reason],
            breakdown=breakdown,
            model_version=self.rules.model_version,
            processed_at=datetime.now(timezone.utc),
        )


