"""Data quality: делим строки на хорошие и плохие (карантин) с причиной.

Плохие строки НЕ удаляются молча — они сохраняются в таблицу dq_rejected,
чтобы человек мог их исправить в исходной системе.
"""
import pandas as pd


def _reject(df: pd.DataFrame, mask: pd.Series, reason: str, table: str, rejects: list) -> pd.DataFrame:
    bad = df[mask]
    for _, row in bad.iterrows():
        rejects.append({"source_table": table, "reason": reason, "record": row.to_json()})
    return df[~mask]


def validate_patients(df: pd.DataFrame, rejects: list) -> pd.DataFrame:
    df = _reject(df, df["full_name"].str.strip() == "", "missing full_name", "patients", rejects)
    bad_date = pd.to_datetime(df["birth_date"], errors="coerce", format="%Y-%m-%d").isna()
    df = _reject(df, bad_date, "invalid birth_date", "patients", rejects)
    df = _reject(df, ~df["sex"].isin(["M", "F"]), "invalid sex", "patients", rejects)
    df = _reject(df, df.duplicated(keep="first"), "duplicate row", "patients", rejects)
    return df


def validate_procedures(df: pd.DataFrame, valid_patients: set, valid_codes: set,
                        rejects: list) -> pd.DataFrame:
    df = _reject(df, df["performed_at"].isna(), "missing performed_at", "procedures", rejects)
    df = _reject(df, ~df["patient_id"].isin(valid_patients), "unknown patient_id", "procedures", rejects)
    df = _reject(df, ~df["procedure_code"].isin(valid_codes), "unknown procedure_code", "procedures", rejects)
    df = _reject(df, df["cost_kzt"] < 0, "negative cost", "procedures", rejects)
    df = _reject(df, df.duplicated(subset=[c for c in df.columns if c != "record_id"], keep="first"),
                 "duplicate record", "procedures", rejects)
    return df
