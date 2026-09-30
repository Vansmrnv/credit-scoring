from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from ..schemas.schemas import ScoreBreakdown, ScoringResult


class ApplicationStore(Protocol):
    def save(self, result: ScoringResult) -> None:
        """Persist a scoring result."""

    def get(self, application_id: str) -> ScoringResult | None:
        """Return a stored result, or None when the id is unknown."""


_INSERT_APPLICATION = """
    INSERT INTO applications (
        application_id,
        applicant_id,
        score,
        decision,
        risk_tier,
        credit_limit,
        reasons,
        debt_ratio_score,
        payment_history_score,
        credit_age_score,
        age_score,
        total,
        model_version,
        processed_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
"""

_SELECT_APPLICATION = """
    SELECT
        application_id,
        applicant_id,
        score,
        decision,
        risk_tier,
        credit_limit,
        reasons,
        debt_ratio_score,
        payment_history_score,
        credit_age_score,
        age_score,
        total,
        model_version,
        processed_at
    FROM applications
    WHERE application_id = %s
"""


class ApplicationRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def save(self, result: ScoringResult) -> None:
        with psycopg.connect(self._database_url) as connection:
            connection.execute(
                _INSERT_APPLICATION,
                (
                    result.application_id,
                    result.applicant_id,
                    result.score,
                    result.decision,
                    result.risk_tier,
                    result.credit_limit,
                    result.reasons,
                    result.breakdown.debt_ratio_score,
                    result.breakdown.payment_history_score,
                    result.breakdown.credit_age_score,
                    result.breakdown.age_score,
                    result.breakdown.total,
                    result.model_version,
                    result.processed_at,
                ),
            )

    def get(self, application_id: str) -> ScoringResult | None:
        with psycopg.connect(self._database_url, row_factory=dict_row) as connection:
            row = connection.execute(_SELECT_APPLICATION, (application_id,)).fetchone()
        if row is None:
            return None
        return ScoringResult(
            application_id=row["application_id"],
            applicant_id=row["applicant_id"],
            score=row["score"],
            decision=row["decision"],
            risk_tier=row["risk_tier"],
            credit_limit=row["credit_limit"],
            reasons=list(row["reasons"]),
            breakdown=ScoreBreakdown(
                debt_ratio_score=row["debt_ratio_score"],
                payment_history_score=row["payment_history_score"],
                credit_age_score=row["credit_age_score"],
                age_score=row["age_score"],
                total=row["total"],
            ),
            model_version=row["model_version"],
            processed_at=row["processed_at"],
        )
