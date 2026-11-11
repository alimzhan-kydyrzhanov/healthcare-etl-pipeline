"""L — Load: загружаем в SQLite в одной транзакции (всё или ничего)."""
import sqlite3
from pathlib import Path

import pandas as pd

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def load(db_path: Path, tables: dict[str, pd.DataFrame]) -> int:
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
        with con:  # транзакция: если что-то упадёт — откат, база не останется «наполовину»
            # Полная перезагрузка: запуск можно повторять сколько угодно (идемпотентность).
            for t in ["fact_procedure", "dim_patient", "dim_procedure", "dim_date"]:
                con.execute(f"DELETE FROM {t}")
            for name in ["dim_patient", "dim_procedure", "dim_date", "fact_procedure"]:
                tables[name].to_sql(name, con, if_exists="append", index=False)
        return len(tables["fact_procedure"])
    finally:
        con.close()


def run_report(db_path: Path, name: str) -> pd.DataFrame:
    """Достаёт запрос из reports.sql по метке `-- name: ...`."""
    text = (SQL_DIR / "reports.sql").read_text(encoding="utf-8")
    query = text.split(f"-- name: {name}")[1].split("-- name:")[0]
    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query(query, con)
