# Credit scoring

An HTTP API scores one credit application and stores the result in Postgres. The score is the sum of four parts defined in `src/scoring/config/rules.yaml`.

## Score

**Debt ratio** is monthly debt divided by monthly income.

| Ratio | Points |
| --- | ---: |
| Up to 0.20 | 300 |
| Up to 0.35 | 240 |
| Up to 0.50 | 160 |
| Up to 0.65 | 80 |
| Above 0.65, or no income | 20 |

**Payment history** counts missed payments: 0 gives 350, 1 gives 260, 2 gives 180, 3 or 4 gives 90, and 5 or more gives 20.

**Credit age** is the length of the history in months: 84 or more gives 200, 48 or more gives 160, 24 or more gives 100, 12 or more gives 50, and under 12 gives 10.

**Age** from 30 to 55 gives 150. Ages 25 to 29 and 56 to 60 give 110. Any other age of 18 or older gives 70. The API rejects an age under 18, or a negative money amount, with HTTP 422.

## Decision

| Total | Decision | Tier | Credit limit |
| --- | --- | --- | --- |
| 800 or more | approved | A | 4 × monthly income |
| 700–799 | approved | B | 4 × monthly income |
| 500–699 | review | C | 1.5 × monthly income |
| Below 500 | rejected | D | 0 |

## Run

Docker Compose starts the API and Postgres. Postgres loads `schema.sql` the first time its data volume is created.

```bash
docker compose up --build
```

The API listens on http://127.0.0.1:8000. Postgres is published on host port 5433.

Score one application:

```bash
curl -s -X POST http://127.0.0.1:8000/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "applicant-1",
    "age": 40,
    "monthly_income": 10000,
    "monthly_debt": 1000,
    "credit_history_months": 84,
    "missed_payments": 0,
    "requested_amount": 5000
  }'
```

This profile scores 1000, is approved at tier A, and receives a credit limit of 40000. Fetch the stored row with the `application_id` from that response:

```bash
curl -s http://127.0.0.1:8000/v1/applications/APPLICATION_ID
```

`docker compose down` stops the containers. `docker compose down -v` also deletes the database volume.

## Tests

Unit tests call the scoring functions, the engine, and the HTTP routes inside the test process. The route tests keep results in memory.

```bash
pip install -e ".[dev]"
pytest
```

The integration test in `src/scoring/db/repository_test.py` runs the real `INSERT` and `SELECT` against Postgres. Pytest skips it when `DATABASE_URL` is unset. With Compose's database published on port 5433:

```bash
DATABASE_URL=postgresql://scoring:scoring@127.0.0.1:5433/scoring pytest src/scoring/db/repository_test.py
```
