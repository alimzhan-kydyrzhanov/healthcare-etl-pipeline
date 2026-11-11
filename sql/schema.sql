-- Star schema: одна таблица фактов + измерения вокруг неё.
-- Факт = событие (проведённая процедура), измерения = «кто / что / когда».

CREATE TABLE IF NOT EXISTS dim_patient (
    patient_key  TEXT PRIMARY KEY,      -- псевдоним, не настоящий ID
    sex          TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    age_group    TEXT NOT NULL,
    city         TEXT
);

CREATE TABLE IF NOT EXISTS dim_procedure (
    procedure_code TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    category       TEXT NOT NULL,
    base_cost_kzt  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,       -- 20250131
    date     TEXT NOT NULL,
    year     INTEGER, month INTEGER, quarter INTEGER, weekday TEXT
);

CREATE TABLE IF NOT EXISTS fact_procedure (
    record_id      INTEGER PRIMARY KEY,
    patient_key    TEXT    NOT NULL REFERENCES dim_patient(patient_key),
    procedure_code TEXT    NOT NULL REFERENCES dim_procedure(procedure_code),
    date_key       INTEGER NOT NULL REFERENCES dim_date(date_key),
    cost_kzt       INTEGER NOT NULL CHECK (cost_kzt >= 0),
    note_category  TEXT
);

CREATE INDEX IF NOT EXISTS ix_fact_date ON fact_procedure(date_key);
CREATE INDEX IF NOT EXISTS ix_fact_patient ON fact_procedure(patient_key);

CREATE TABLE IF NOT EXISTS dq_rejected (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT,
    source_table TEXT,
    reason       TEXT,
    record       TEXT
);

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id      TEXT PRIMARY KEY,
    started_at  TEXT, finished_at TEXT,
    rows_loaded INTEGER, rows_rejected INTEGER, status TEXT
);
