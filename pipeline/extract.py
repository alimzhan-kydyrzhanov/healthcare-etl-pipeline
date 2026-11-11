"""E — Extract: читаем сырые файлы как есть, ничего не исправляя."""
import json
from pathlib import Path

import pandas as pd


def extract(raw_dir: Path) -> dict[str, pd.DataFrame]:
    patients = pd.read_csv(raw_dir / "patients.csv", dtype=str, keep_default_na=False)
    procedures = pd.DataFrame(json.loads((raw_dir / "procedures.json").read_text(encoding="utf-8")))
    catalog = pd.DataFrame(json.loads((raw_dir / "procedure_catalog.json").read_text(encoding="utf-8")))
    return {"patients": patients, "procedures": procedures, "catalog": catalog}
