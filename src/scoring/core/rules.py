from ..schemas.schemas import CreditApplication, Decision, RiskTier
from ..schemas.rules_schemas import Rules


def calc_debt_ratio(app: CreditApplication, rules: Rules) -> tuple[int, str]:
    if app.monthly_income <= 0:
        return rules.debt_ratio.points.critical, "no_income_data"

    ratio = app.monthly_debt / app.monthly_income
    t = rules.debt_ratio.thresholds
    p = rules.debt_ratio.points

    if ratio <= t.excellent:
        return p.excellent, "excellent_debt_ratio"
    if ratio <= t.good:
        return p.good, "good_debt_ratio"
    if ratio <= t.moderate:
        return p.moderate, "moderate_debt_ratio"
    if ratio <= t.high:
        return p.high, "high_debt_ratio"
    return p.critical, "critical_debt_ratio"


def calc_payment_history(app: CreditApplication, rules: Rules) -> tuple[int, str]:
    p = rules.payment_history.points

    if app.missed_payments == 0:
        return p.perfect, "perfect_payment_history"
    if app.missed_payments == 1:
        return p.good, "good_payment_history"
    if app.missed_payments == 2:
        return p.fair, "fair_payment_history"
    elif app.missed_payments <= 4:
        return p.poor, "poor_payment_history"
    else:
        return p.very_poor, "very_poor_payment_history"


def calc_credit_age(app: CreditApplication, rules: Rules) -> tuple[int, str]:
    t = rules.credit_age.thresholds
    p = rules.credit_age.points

    if app.credit_history_months >= t.long:
        return p.long, "long_credit_history"
    if app.credit_history_months >= t.good:
        return p.good, "good_credit_history"
    if app.credit_history_months >= t.moderate:
        return p.moderate, "moderate_credit_history"
    if app.credit_history_months >= t.short:
        return p.short, "short_credit_history"
    else:
        return p.very_short, "very_short_credit_history"


def calc_age_score(app: CreditApplication, rules: Rules) -> tuple[int, str]:
    t = rules.age_score.thresholds
    p = rules.age_score.points

    if t.optimal_min <= app.age <= t.optimal_max:
        return p.optimal, "optimal_age_range"
    if t.good_min <= app.age <= t.good_max:
        return p.good, "good_age_range"
    if app.age >= 18:
        return p.acceptable, "acceptable_age_range"
    else:
        return 0, "invalid"


def decide(total: int, rules: Rules) -> tuple[Decision, RiskTier]:
    thresholds = rules.decisions

    if total >= thresholds.approved_a:
        return Decision.APPROVED, RiskTier.A
    if total >= thresholds.approved_b:
        return Decision.APPROVED, RiskTier.B
    if total >= thresholds.review:
        return Decision.REVIEW, RiskTier.C
    return Decision.REJECTED, RiskTier.D


def calc_credit_limit(monthly_income: float, decision: Decision, rules: Rules) -> float:
    multipliers = rules.credit_limit_multipliers

    if decision == Decision.APPROVED:
        return monthly_income * multipliers.approved
    if decision == Decision.REVIEW:
        return monthly_income * multipliers.review
    return monthly_income * multipliers.rejected
