import sqlite3
from Core.models import PatientProfile, FoodItem

DB_PATH = "cdss.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # to read columns by name
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id        TEXT PRIMARY KEY,
            full_name         TEXT NOT NULL,
            dob               TEXT,
            gender            TEXT,
            address           TEXT,
            height_cm         REAL,
            weight_kg         REAL,
            date_of_diagnosis TEXT,
            dependence_level  TEXT,
            cognitive_stage   TEXT,
            mmse_score        INTEGER,
            mna_score         INTEGER,
            iddsi_level       INTEGER,
            has_hypertension  INTEGER,
            has_diabetes      INTEGER
        )
    """)
    conn = get_connection()
    conn.execute("""
            CREATE TABLE IF NOT EXISTS fooditem (
                food_id           TEXT PRIMARY KEY,
                name_en           TEXT NOT NULL,
                name_dz           TEXT,
                name_fr           TEXT,
                texture_level     INTEGER,
                is_thin_liquid    INTEGER,
                is_comfort_food   INTEGER,
                calories_per_100g REAL,
                protein_g         REAL,
                mind_category     TEXT,
                is_low_sodium     INTEGER,
                is_low_gi         INTEGER
            )
        """)
    conn.commit()
    conn.close()

from dataclasses import asdict
from datetime import date
from Core.models import PatientProfile


def save_patient(p: PatientProfile):
    data = asdict(p)                       # form -> dictionary
    data["dob"] = p.dob.isoformat()        # date -> "1945-03-15"
    data["date_of_diagnosis"] = p.date_of_diagnosis.isoformat()
    data["has_hypertension"] = int(p.has_hypertension)   # True -> 1
    data["has_diabetes"] = int(p.has_diabetes)

    cols = ", ".join(data.keys())
    marks = ", ".join("?" for _ in data)
    conn = get_connection()
    conn.execute(
        f"INSERT OR REPLACE INTO patients ({cols}) VALUES ({marks})",
        list(data.values()),
    )
    conn.commit()
    conn.close()


def save_patient(p):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO patients VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            p.patient_id,
            p.full_name,
            p.dob.isoformat(),
            p.gender,
            p.address,
            p.height_cm,
            p.weight_kg,
            p.date_of_diagnosis.isoformat(),
            p.dependence_level,
            p.cognitive_stage,
            p.mmse_score,
            p.mna_score,
            p.iddsi_level,
            int(p.has_hypertension),
            int(p.has_diabetes),
        ),
    )
    conn.commit()
    conn.close()


def save_food(f):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO fooditem VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            f.food_id,
            f.name_en,
            f.name_dz,
            f.name_fr,
            f.texture_level,
            int(f.is_thin_liquid),
            int(f.is_comfort_food),
            f.calories_per_100g,
            f.protein_g,
            f.mind_category,
            int(f.is_low_sodium),
            int(f.is_low_gi),
        ),
    )
    conn.commit()
    conn.close()

def get_food(food_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM fooditem WHERE food_id = ?", (food_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return FoodItem(
        food_id=row["food_id"],
        name_fr=row["name_fr"],
        name_dz=row["name_dz"],
        name_en=row["name_en"],
        texture_level=row["texture_level"],
        is_thin_liquid=bool(row["is_thin_liquid"]),
        is_comfort_food=bool(row["is_comfort_food"]),
        calories_per_100g=row["calories_per_100g"],
        protein_g=row["protein_g"],
        mind_category=row["mind_category"],
        is_low_sodium=bool(row["is_low_sodium"]),
        is_low_gi=bool(row["is_low_gi"]),
    )

def get_patient(patient_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return PatientProfile(
        patient_id=row["patient_id"],
        full_name=row["full_name"],
        dob=date.fromisoformat(row["dob"]),
        gender=row["gender"],
        address=row["address"],
        height_cm=row["height_cm"],
        weight_kg=row["weight_kg"],
        date_of_diagnosis=date.fromisoformat(row["date_of_diagnosis"]),
        dependence_level=row["dependence_level"],
        cognitive_stage=row["cognitive_stage"],
        mmse_score=row["mmse_score"],
        mna_score=row["mna_score"],
        iddsi_level=row["iddsi_level"],
        has_hypertension=bool(row["has_hypertension"]),
        has_diabetes=bool(row["has_diabetes"]),
    )

import csv
def load_foods_from_csv(path="data/foods.csv"):
    with open(path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            food = FoodItem(
                food_id=row["food_id"],
                name_fr=row["name_fr"],
                name_dz=row["name_dz"],
                name_en=row["name_en"],
                texture_level=int(row["texture_level"]),
                is_thin_liquid=bool(int(row["is_thin_liquid"])),
                is_comfort_food=bool(int(row["is_comfort_food"])),
                calories_per_100g=float(row["calories_per_100g"]),
                protein_g=float(row["protein_g"]),
                mind_category=row["mind_category"],
                is_low_sodium=bool(int(row["is_low_sodium"])),
                is_low_gi=bool(int(row["is_low_gi"])),
            )
            save_food(food)

def get_all_foods():
    conn = get_connection()
    ids = [r["food_id"] for r in conn.execute("SELECT food_id FROM fooditem")]
    conn.close()
    return [get_food(i) for i in ids]

def get_all_patient_ids():
    conn = get_connection()
    ids = [r["patient_id"] for r in conn.execute("SELECT patient_id FROM patients")]
    conn.close()
    return ids


if __name__ == "__main__":
    create_tables()
    load_foods_from_csv()
    print("Tables created and foods loaded")
    


