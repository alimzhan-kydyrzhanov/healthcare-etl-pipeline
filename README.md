# Healthcare ETL Pipeline

An end-to-end ETL pipeline for (synthetic) clinic data: Python + pandas + SQL, data quality checks,
GDPR-style pseudonymization, a star-schema warehouse in SQLite and an optional Generative AI (LLM) step
that classifies free-text doctor notes.

```
data/raw (CSV + JSON)
   │  extract.py      read raw files as-is
   ▼
validate.py           data quality: missing values, invalid dates, duplicates,
   │                  broken references → dq_rejected (quarantine) with a reason
   ▼
transform.py          types, pseudonymized patient_key (SHA-256 + salt),
   │                  age groups, LLM / rule-based note categories
   ▼
load.py               SQLite star schema in one transaction (idempotent full reload)
   ▼
sql/reports.sql       analytics: revenue by month, top procedure per age group (window function),
                      data quality summary
```

## Run

```bash
pip install -r requirements.txt
python -m pipeline.generate_data      # synthetic data with deliberate errors
python -m pipeline.run                # run the pipeline + print reports
python -m pytest -q                   # tests
```

Docker: `docker build -t health-etl . && docker run --rm health-etl`

Optional GenAI step: `USE_LLM=1 ANTHROPIC_API_KEY=... python -m pipeline.run`

CI: GitHub Actions runs the tests and the full pipeline on every push.

All data is synthetic — no real patients.
