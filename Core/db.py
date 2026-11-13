import sqlite3
from Core.models import PatientProfile, FoodItem
import json
from datetime import date, datetime
from Core.models import PatientProfile, FoodItem, MealPlan, MealEntry

DB_PATH = "cdss.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # to read columns by name
    return conn


def create_tables():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_preferences (
            patient_id  TEXT NOT NULL,
            food_id     TEXT NOT NULL,
            preference  TEXT NOT NULL,
            note        TEXT,
            source      TEXT,
            PRIMARY KEY (patient_id, food_id)
        )
    """)
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
    try:
        conn.execute("ALTER TABLE fooditem ADD COLUMN meal_types TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE patients ADD COLUMN updated_at TEXT")
    except sqlite3.OperationalError:
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id         TEXT NOT NULL,
            appointment_date   TEXT NOT NULL,
            appointment_status TEXT,
            nutritionist_notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS symptoms (
            symptom_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id  TEXT NOT NULL,
            symptom     TEXT NOT NULL,
            severity    TEXT,
            date_noted  TEXT,
            notes       TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_requests (
            request_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id     TEXT NOT NULL,
            title          TEXT NOT NULL,
            note           TEXT,
            status         TEXT,
            date_requested TEXT,
            result         TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS food_overrides (
            patient_id  TEXT NOT NULL,
            food_id     TEXT NOT NULL,
            decision    TEXT NOT NULL,
            reason      TEXT,
            source      TEXT,
            PRIMARY KEY (patient_id, food_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            plan_id                      TEXT PRIMARY KEY,
            patient_id                   TEXT NOT NULL,
            generated_date               TEXT,
            validation_status            TEXT,
            is_validated_by_nutritionist INTEGER,
            validation_date              TEXT,
            total_daily_calories         REAL,
            clinical_alerts              TEXT,
            behavioral_notes             TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE fooditem ADD COLUMN meal_types TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE meal_plans ADD COLUMN validation_notes TEXT")
    except sqlite3.OperationalError:
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS plan_edits (
            edit_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id     TEXT NOT NULL,
            edit_time   TEXT,
            action      TEXT,
            description TEXT,
            reason      TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_entries (
            entry_id          TEXT PRIMARY KEY,
            plan_id           TEXT NOT NULL,
            food_id           TEXT NOT NULL,
            day_of_week       TEXT,
            meal_type         TEXT,
            portion_grams     REAL,
            applied_rationale TEXT
        )
    """)
    try:
        conn.execute("ALTER TABLE meal_plans ADD COLUMN validation_notes TEXT")
    except sqlite3.OperationalError:
        pass   # the column already exists
    conn.commit()
    conn.close()

def request_test(patient_id, title, note):
    conn = get_connection()
    conn.execute(
        "INSERT INTO test_requests "
        "(patient_id, title, note, status, date_requested) "
        "VALUES (?,?,?,?,?)",
        (patient_id, title, note, "requested", date.today().isoformat()),
    )
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            plan_id                      TEXT PRIMARY KEY,
            patient_id                   TEXT NOT NULL,
            generated_date               TEXT,
            validation_status            TEXT,
            is_validated_by_nutritionist INTEGER,
            validation_date              TEXT,
            total_daily_calories         REAL,
            clinical_alerts              TEXT,
            behavioral_notes             TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_preferences (
            patient_id  TEXT NOT NULL,
            food_id     TEXT NOT NULL,
            preference  TEXT NOT NULL,
            note        TEXT,
            source      TEXT,
            PRIMARY KEY (patient_id, food_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_entries (
            entry_id          TEXT PRIMARY KEY,
            plan_id           TEXT NOT NULL,
            food_id           TEXT NOT NULL,
            day_of_week       TEXT,
            meal_type         TEXT,
            portion_grams     REAL,
            applied_rationale TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_preference(patient_id, food_id, preference, note, source):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO patient_preferences "
        "(patient_id, food_id, preference, note, source) VALUES (?,?,?,?,?)",
        (patient_id, food_id, preference, note, source),
    )
    conn.commit()
    conn.close()


def delete_preference(patient_id, food_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM patient_preferences WHERE patient_id = ? AND food_id = ?",
        (patient_id, food_id),
    )
    conn.commit()
    conn.close()


def get_preferences(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT food_id, preference, note, source "
        "FROM patient_preferences WHERE patient_id = ?",
        (patient_id,),
    ).fetchall()
    conn.close()
    return {r["food_id"]: dict(r) for r in rows}



def save_meal_plan(plan):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO meal_plans "
        "(plan_id, patient_id, generated_date, validation_status, "
        "is_validated_by_nutritionist, validation_date, total_daily_calories, "
        "clinical_alerts, behavioral_notes, validation_notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            plan.plan_id,
            plan.patient_id,
            plan.generated_date.isoformat(),
            plan.validation_status,
            int(plan.is_validated_by_nutritionist),
            plan.validation_date,
            plan.total_daily_calories,
            json.dumps(plan.clinical_alerts),
            json.dumps(plan.behavioral_notes),
            plan.validation_notes,
        ),
    )
    for e in plan.entries:
        conn.execute(
            "INSERT OR REPLACE INTO meal_entries VALUES (?,?,?,?,?,?,?)",
            (e.entry_id, plan.plan_id, e.food_id, e.day_of_week,
             e.meal_type, e.portion_grams, e.applied_rationale),
        )
    conn.commit()
    conn.close()


def get_latest_meal_plan(patient_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM meal_plans WHERE patient_id = ? "
        "ORDER BY generated_date DESC LIMIT 1",
        (patient_id,),
    ).fetchone()
    if row is None:
        conn.close()
        return None

    entry_rows = conn.execute(
        "SELECT * FROM meal_entries WHERE plan_id = ? ORDER BY entry_id",
        (row["plan_id"],),
    ).fetchall()
    conn.close()

    entries = [
        MealEntry(
            entry_id=r["entry_id"],
            food_id=r["food_id"],
            day_of_week=r["day_of_week"],
            meal_type=r["meal_type"],
            portion_grams=r["portion_grams"],
            applied_rationale=r["applied_rationale"],
        )
        for r in entry_rows
    ]

    return MealPlan(
        plan_id=row["plan_id"],
        patient_id=row["patient_id"],
        generated_date=datetime.fromisoformat(row["generated_date"]),
        validation_status=row["validation_status"],
        is_validated_by_nutritionist=bool(row["is_validated_by_nutritionist"]),
        validation_date=row["validation_date"],
        total_daily_calories=row["total_daily_calories"],
        clinical_alerts=json.loads(row["clinical_alerts"]),
        behavioral_notes=json.loads(row["behavioral_notes"]),
        entries=entries,
        validation_notes=row["validation_notes"],
    )

def review_meal_plan(plan_id, approved, notes):
    status = "Approved" if approved else "Rejected"
    conn = get_connection()
    conn.execute(
        "UPDATE meal_plans SET validation_status = ?, "
        "is_validated_by_nutritionist = ?, validation_date = ?, "
        "validation_notes = ? "
        "WHERE plan_id = ? AND validation_status = 'Pending Validation'",
        (status, int(approved), datetime.now().isoformat(), notes, plan_id),
    )
    conn.commit()
    conn.close()

def get_test_requests(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT title, note, status, date_requested, result "
        "FROM test_requests WHERE patient_id = ? "
        "ORDER BY date_requested DESC",
        (patient_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_override(patient_id, food_id, decision, reason, source):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO food_overrides "
        "(patient_id, food_id, decision, reason, source) "
        "VALUES (?,?,?,?,?)",
        (patient_id, food_id, decision, reason, source),
    )
    conn.commit()
    conn.close()


def delete_override(patient_id, food_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM food_overrides WHERE patient_id = ? AND food_id = ?",
        (patient_id, food_id),
    )
    conn.commit()
    conn.close()


def get_overrides(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT food_id, decision, reason, source "
        "FROM food_overrides WHERE patient_id = ?",
        (patient_id,),
    ).fetchall()
    conn.close()
    return {r["food_id"]: dict(r) for r in rows}

def add_symptom(patient_id, symptom, severity, date_noted, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO symptoms "
        "(patient_id, symptom, severity, date_noted, notes) "
        "VALUES (?,?,?,?,?)",
        (patient_id, symptom, severity, date_noted.isoformat(), notes),
    )
    conn.commit()
    conn.close()


def get_symptoms(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT symptom_id, symptom, severity, date_noted, notes "
        "FROM symptoms WHERE patient_id = ? "
        "ORDER BY date_noted DESC",
        (patient_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

from dataclasses import asdict
from datetime import date
from Core.models import PatientProfile



def update_patient(p):
    conn = get_connection()
    conn.execute(
        "UPDATE patients SET full_name = ?, dob = ?, gender = ?, address = ?, "
        "height_cm = ?, weight_kg = ?, date_of_diagnosis = ?, "
        "dependence_level = ?, cognitive_stage = ?, mmse_score = ?, "
        "mna_score = ?, iddsi_level = ?, has_hypertension = ?, "
        "has_diabetes = ?, updated_at = ? "
        "WHERE patient_id = ?",
        (
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
            datetime.now().isoformat(),
            p.patient_id,
        ),
    )
    conn.commit()
    conn.close()


def get_profile_updated_at(patient_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT updated_at FROM patients WHERE patient_id = ?", (patient_id,)
    ).fetchone()
    conn.close()
    return row["updated_at"] if row else None

def save_patient(p):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO patients "
        "(patient_id, full_name, dob, gender, address, height_cm, weight_kg, "
        "date_of_diagnosis, dependence_level, cognitive_stage, mmse_score, "
        "mna_score, iddsi_level, has_hypertension, has_diabetes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
        "INSERT OR REPLACE INTO fooditem VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
            f.meal_types,
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
        meal_types=row["meal_types"],
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
                meal_types=row["meal_types"],
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
    
def get_patient_summaries():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.patient_id,
               p.full_name,
               (SELECT MIN(a.appointment_date)
                FROM appointments a
                WHERE a.patient_id = p.patient_id
                  AND a.appointment_status = 'scheduled'
                  AND a.appointment_date >= date('now')) AS next_appointment
        FROM patients p
        ORDER BY p.full_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_appointment(patient_id, appt_date, status, notes):
    conn = get_connection()
    conn.execute(
        "INSERT INTO appointments "
        "(patient_id, appointment_date, appointment_status, nutritionist_notes) "
        "VALUES (?,?,?,?)",
        (patient_id, appt_date.isoformat(), status, notes),
    )
    conn.commit()
    conn.close()


def get_appointments(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT appointment_date, appointment_status, nutritionist_notes "
        "FROM appointments WHERE patient_id = ? "
        "ORDER BY appointment_date DESC",
        (patient_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _is_pending(conn, plan_id):
    row = conn.execute(
        "SELECT validation_status FROM meal_plans WHERE plan_id = ?", (plan_id,)
    ).fetchone()
    return row is not None and row["validation_status"] == "Pending Validation"


def _recalculate_calories(conn, plan_id):
    row = conn.execute(
        "SELECT SUM(e.portion_grams / 100.0 * f.calories_per_100g) AS total "
        "FROM meal_entries e JOIN fooditem f ON e.food_id = f.food_id "
        "WHERE e.plan_id = ?",
        (plan_id,),
    ).fetchone()
    total = row["total"] or 0
    conn.execute(
        "UPDATE meal_plans SET total_daily_calories = ? WHERE plan_id = ?",
        (round(total / 7, 1), plan_id),
    )


def _log_edit(conn, plan_id, action, description, reason):
    conn.execute(
        "INSERT INTO plan_edits (plan_id, edit_time, action, description, reason) "
        "VALUES (?,?,?,?,?)",
        (plan_id, datetime.now().isoformat(timespec="seconds"),
         action, description, reason),
    )


def update_entry(plan_id, entry_id, food_id, portion_grams, description, reason):
    conn = get_connection()
    if not _is_pending(conn, plan_id):
        conn.close()
        return False
    conn.execute(
        "UPDATE meal_entries SET food_id = ?, portion_grams = ?, "
        "applied_rationale = ? WHERE entry_id = ? AND plan_id = ?",
        (food_id, portion_grams, f"Manual edit: {reason}", entry_id, plan_id),
    )
    _recalculate_calories(conn, plan_id)
    _log_edit(conn, plan_id, "changed", description, reason)
    conn.commit()
    conn.close()
    return True


def delete_entry(plan_id, entry_id, description, reason):
    conn = get_connection()
    if not _is_pending(conn, plan_id):
        conn.close()
        return False
    conn.execute(
        "DELETE FROM meal_entries WHERE entry_id = ? AND plan_id = ?",
        (entry_id, plan_id),
    )
    _recalculate_calories(conn, plan_id)
    _log_edit(conn, plan_id, "removed", description, reason)
    conn.commit()
    conn.close()
    return True


def add_entry(plan_id, day, meal_type, food_id, portion_grams, description, reason):
    conn = get_connection()
    if not _is_pending(conn, plan_id):
        conn.close()
        return False
    entry_id = f"{plan_id}-M{datetime.now().strftime('%H%M%S%f')}"
    conn.execute(
        "INSERT INTO meal_entries "
        "(entry_id, plan_id, food_id, day_of_week, meal_type, portion_grams, "
        "applied_rationale) VALUES (?,?,?,?,?,?,?)",
        (entry_id, plan_id, food_id, day, meal_type, portion_grams,
         f"Manual edit: {reason}"),
    )
    _recalculate_calories(conn, plan_id)
    _log_edit(conn, plan_id, "added", description, reason)
    conn.commit()
    conn.close()
    return True


def get_plan_edits(plan_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT edit_time, action, description, reason "
        "FROM plan_edits WHERE plan_id = ? ORDER BY edit_id DESC",
        (plan_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

