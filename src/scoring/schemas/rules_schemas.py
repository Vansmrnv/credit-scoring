from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.yaml"


class DebtRatioThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    excellent: float
    good: float
    moderate: float
    high: float


class DebtRatioPoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    excellent: int
    good: int
    moderate: int
    high: int
    critical: int


class DebtRatio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thresholds: DebtRatioThresholds
    points: DebtRatioPoints


class PaymentHistoryPoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    perfect: int
    good: int
    fair: int
    poor: int
    very_poor: int


class PaymentHistory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: PaymentHistoryPoints


class CreditAgeThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    long: int
    good: int
    moderate: int
    short: int


class CreditAgePoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    long: int
    good: int
    moderate: int
    short: int
    very_short: int


class CreditAge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thresholds: CreditAgeThresholds
    points: CreditAgePoints


class AgeScoreThresholds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    optimal_min: int
    optimal_max: int
    good_min: int
    good_max: int


class AgeScorePoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    optimal: int
    good: int
    acceptable: int


class AgeScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thresholds: AgeScoreThresholds
    points: AgeScorePoints


class Decisions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_a: int
    approved_b: int
    review: int


class CreditLimitMultipliers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: float
    review: float
    rejected: float


class Rules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_version: str
    debt_ratio: DebtRatio
    payment_history: PaymentHistory
    credit_age: CreditAge
    age_score: AgeScore
    decisions: Decisions
    credit_limit_multipliers: CreditLimitMultipliers


def load_rules(path: Path = _RULES_PATH) -> Rules:
    with path.open() as rules_file:
        data = yaml.safe_load(rules_file)
    return Rules.model_validate(data)
