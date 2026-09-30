from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Decision(StrEnum):
    APPROVED = "approved"
    REVIEW = "review"
    REJECTED = "rejected"


class RiskTier(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class CreditApplication(BaseModel):
    applicant_id: str
    age: int = Field(ge=18)
    monthly_income: float = Field(ge=0)
    monthly_debt: float = Field(ge=0)
    credit_history_months: int
    missed_payments: int
    requested_amount: float = Field(ge=0)


class ScoreBreakdown(BaseModel):
    debt_ratio_score: int
    payment_history_score: int
    credit_age_score: int
    age_score: int
    total: int


class ScoringResult(BaseModel):
    application_id: str
    applicant_id: str
    score: int
    decision: Decision
    risk_tier: RiskTier
    credit_limit: float
    reasons: list[str]
    breakdown: ScoreBreakdown
    model_version: str
    processed_at: datetime
