from datetime import date

import pandas as pd

from pipeline.categorize import categorize_note
from pipeline.generate_data import generate
from pipeline.run import run
from pipeline.transform import age_group, pseudonymize
from pipeline.validate import validate_patients, validate_procedures


def test_pseudonymize_is_stable_and_hides_id():
    assert pseudonymize("PT00001") == pseudonymize("PT00001")
    assert pseudonymize("PT00001") != pseudonymize("PT00002")
    assert "PT00001" not in pseudonymize("PT00001")


def test_age_group_boundaries():
    today = date(2026, 1, 1)
    assert age_group(date(2008, 1, 2), today) == "0-17"   # ещё 17
    assert age_group(date(2008, 1, 1), today) == "18-34"  # ровно 18
    assert age_group(date(1950, 1, 1), today) == "65+"


def test_validate_patients_rejects_bad_rows():
    df = pd.DataFrame([
        {"patient_id": "A", "full_name": "Ok", "birth_date": "1990-01-01", "sex": "M", "city": "x"},
        {"patient_id": "B", "full_name": "", "birth_date": "1990-01-01", "sex": "M", "city": "x"},
        {"patient_id": "C", "full_name": "Bad", "birth_date": "1990-13-45", "sex": "F", "city": "x"},
    ])
    rejects = []
    good = validate_patients(df, rejects)
    assert list(good["patient_id"]) == ["A"]
    assert {r["reason"] for r in rejects} == {"missing full_name", "invalid birth_date"}


def test_validate_procedures_checks_references():
    df = pd.DataFrame([
        {"record_id": 1, "patient_id": "A", "procedure_code": "P1", "performed_at": "2025-01-01", "cost_kzt": 10},
        {"record_id": 2, "patient_id": "Z", "procedure_code": "P1", "performed_at": "2025-01-01", "cost_kzt": 10},
        {"record_id": 3, "patient_id": "A", "procedure_code": "P1", "performed_at": "2025-01-02", "cost_kzt": -5},
    ])
    rejects = []
    good = validate_procedures(df, {"A"}, {"P1"}, rejects)
    assert list(good["record_id"]) == [1]


def test_categorize_rules():
    assert categorize_note("post-op recovery normal") == "post_operative"
    assert categorize_note("") == "none"


def test_full_run_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline.generate_data.RAW", tmp_path / "raw")
    generate(n_patients=50, n_procedures=100)
    db = tmp_path / "wh.db"
    first = run(tmp_path / "raw", db)
    second = run(tmp_path / "raw", db)  # повторный запуск не дублирует данные
    assert first["loaded"] == second["loaded"] > 0
    assert first["rejected"] >= 5
