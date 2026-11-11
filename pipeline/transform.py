"""T — Transform: чистим, приводим типы, псевдонимизируем персональные данные (GDPR)."""
import hashlib
import os
from datetime import date

import pandas as pd

from pipeline.categorize import categorize_note

# Соль хранится вне кода (переменная окружения). Без неё хэш можно подобрать перебором ID.
SALT = os.getenv("PSEUDO_SALT", "dev-only-salt")


def pseudonymize(patient_id: str) -> str:
    """Один и тот же пациент -> один и тот же ключ, но вернуть исходный ID без соли нельзя."""
    return hashlib.sha256(f"{SALT}:{patient_id}".encode()).hexdigest()[:16]


def age_group(birth: date, today: date) -> str:
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    for limit, label in [(18, "0-17"), (35, "18-34"), (50, "35-49"), (65, "50-64")]:
        if age < limit:
            return label
    return "65+"


def transform_patients(df: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    today = today or date.today()
    out = pd.DataFrame({
        "patient_key": df["patient_id"].map(pseudonymize),
        "sex": df["sex"],
        "age_group": pd.to_datetime(df["birth_date"]).dt.date.map(lambda b: age_group(b, today)),
        "city": df["city"].str.strip().str.title(),
    })
    # Имя и точная дата рождения в аналитику не попадают — минимизация данных (GDPR).
    return out


def transform_procedures(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "record_id": df["record_id"].astype(int),
        "patient_key": df["patient_id"].map(pseudonymize),
        "procedure_code": df["procedure_code"],
        "date_key": pd.to_datetime(df["performed_at"]).dt.strftime("%Y%m%d").astype(int),
        "cost_kzt": df["cost_kzt"].astype(int),
        "note_category": df["doctor_note"].fillna("").map(categorize_note),
    })


def build_date_dim(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(dates.astype(str), format="%Y%m%d").drop_duplicates().sort_values()
    return pd.DataFrame({
        "date_key": d.dt.strftime("%Y%m%d").astype(int),
        "date": d.dt.strftime("%Y-%m-%d"),
        "year": d.dt.year, "month": d.dt.month, "quarter": d.dt.quarter,
        "weekday": d.dt.day_name(),
    })
