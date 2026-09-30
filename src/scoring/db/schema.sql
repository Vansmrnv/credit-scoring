CREATE TABLE IF NOT EXISTS applications (
    application_id TEXT PRIMARY KEY,
    applicant_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approved', 'review', 'rejected')),
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('A', 'B', 'C', 'D')),
    credit_limit DOUBLE PRECISION NOT NULL,
    reasons TEXT[] NOT NULL,
    debt_ratio_score INTEGER NOT NULL,
    payment_history_score INTEGER NOT NULL,
    credit_age_score INTEGER NOT NULL,
    age_score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    model_version TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL
);
