"""Оркестратор пайплайна: extract -> validate -> transform -> load -> отчёт."""
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from pipeline.extract import extract
from pipeline.load import load, run_report
from pipeline.transform import build_date_dim, transform_patients, transform_procedures
from pipeline.validate import validate_patients, validate_procedures

ROOT = Path(__file__).resolve().parent.parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("etl")


def run(raw_dir: Path = ROOT / "data" / "raw", db_path: Path = ROOT / "data" / "warehouse.db") -> dict:
    run_id, started = uuid.uuid4().hex[:8], datetime.now().isoformat(timespec="seconds")
    log.info("Run %s started", run_id)

    raw = extract(raw_dir)
    log.info("Extracted: %s", {k: len(v) for k, v in raw.items()})

    rejects: list[dict] = []
    patients = validate_patients(raw["patients"], rejects)
    procedures = validate_procedures(raw["procedures"], set(patients["patient_id"]),
                                     set(raw["catalog"]["procedure_code"]), rejects)
    log.info("Validation: %d rows rejected", len(rejects))

    fact = transform_procedures(procedures)
    tables = {
        "dim_patient": transform_patients(patients),
        "dim_procedure": raw["catalog"],
        "dim_date": build_date_dim(fact["date_key"]),
        "fact_procedure": fact,
    }
    loaded = load(db_path, tables)

    with sqlite3.connect(db_path) as con:
        con.executemany("INSERT INTO dq_rejected (run_id, source_table, reason, record) VALUES (?,?,?,?)",
                        [(run_id, r["source_table"], r["reason"], r["record"]) for r in rejects])
        con.execute("INSERT INTO etl_runs VALUES (?,?,?,?,?,?)",
                    (run_id, started, datetime.now().isoformat(timespec="seconds"),
                     loaded, len(rejects), "success"))
    log.info("Loaded %d fact rows into %s", loaded, db_path)
    return {"run_id": run_id, "loaded": loaded, "rejected": len(rejects)}


if __name__ == "__main__":
    run()
    db = ROOT / "data" / "warehouse.db"
    for report in ["data_quality_summary", "top_procedures_by_age_group", "monthly_revenue_by_category"]:
        print(f"\n=== {report} ===")
        print(run_report(db, report).head(12).to_string(index=False))
