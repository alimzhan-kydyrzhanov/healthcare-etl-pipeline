"""Генерирует СИНТЕТИЧЕСКИЕ данные клиники (никаких реальных пациентов).

Специально добавляет ошибки, которые встречаются в реальной базе клиники:
пустые поля, дубли, неверные даты, неизвестные коды процедур.
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

FIRST = ["Aigerim", "Nursultan", "Dana", "Timur", "Aliya", "Yerlan", "Madina", "Arman", "Saule", "Daniyar"]
LAST = ["Abenov", "Seitkali", "Nurlanova", "Kassymov", "Zhumabek", "Ospanova", "Bekov", "Tulegen"]
PROCEDURES = {
    "P100": ("Blood test", "diagnostics", 3500),
    "P200": ("MRI scan", "diagnostics", 45000),
    "P300": ("Appendectomy", "surgery", 250000),
    "P310": ("Knee arthroscopy", "surgery", 320000),
    "P400": ("Physiotherapy session", "therapy", 8000),
    "P500": ("Dental filling", "dentistry", 15000),
}
NOTES = ["patient stable after surgery", "routine check, no issues", "follow-up MRI recommended",
         "pain in the knee, refer to physio", "tooth sensitivity", "post-op recovery normal", ""]


def generate(n_patients: int = 200, n_procedures: int = 800, seed: int = 42) -> None:
    rnd = random.Random(seed)
    RAW.mkdir(parents=True, exist_ok=True)

    patients = []
    for i in range(1, n_patients + 1):
        birth = date(1950, 1, 1) + timedelta(days=rnd.randint(0, 25000))
        patients.append({
            "patient_id": f"PT{i:05d}",
            "full_name": f"{rnd.choice(FIRST)} {rnd.choice(LAST)}",
            "birth_date": birth.isoformat(),
            "sex": rnd.choice(["M", "F"]),
            "city": rnd.choice(["Almaty", "Astana", "Shymkent", "Prague"]),
        })
    # ошибки: пустое имя, неверная дата, дубль
    patients[3]["full_name"] = ""
    patients[7]["birth_date"] = "1990-13-45"
    patients.append(dict(patients[10]))

    with open(RAW / "patients.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=patients[0].keys())
        w.writeheader()
        w.writerows(patients)

    records = []
    for i in range(1, n_procedures + 1):
        code = rnd.choice(list(PROCEDURES))
        records.append({
            "record_id": i,
            "patient_id": f"PT{rnd.randint(1, n_patients):05d}",
            "procedure_code": code,
            "performed_at": (date(2025, 1, 1) + timedelta(days=rnd.randint(0, 600))).isoformat(),
            "cost_kzt": PROCEDURES[code][2],
            "doctor_note": rnd.choice(NOTES),
        })
    # ошибки: неизвестный пациент, неизвестный код, отрицательная стоимость, пустая дата, дубль
    records[5]["patient_id"] = "PT99999"
    records[6]["procedure_code"] = "X999"
    records[7]["cost_kzt"] = -100
    records[8]["performed_at"] = None
    records.append(dict(records[20]))

    (RAW / "procedures.json").write_text(json.dumps(records, indent=1), encoding="utf-8")
    (RAW / "procedure_catalog.json").write_text(json.dumps(
        [{"procedure_code": c, "name": n, "category": cat, "base_cost_kzt": cost}
         for c, (n, cat, cost) in PROCEDURES.items()], indent=1), encoding="utf-8")
    print(f"Synthetic data written to {RAW}")


if __name__ == "__main__":
    generate()
