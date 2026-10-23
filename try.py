from datetime import date
from Core.models import PatientProfile
from Core.db import create_tables, save_patient, save_food
import streamlit as st

p = PatientProfile(
    patient_id="P001", full_name="Test Patient", dob=date(1945, 3, 15),
    gender="F", address="Algiers", height_cm=160.0, weight_kg=58.0,
    date_of_diagnosis=date(2023, 6, 1), dependence_level="moderate",
    cognitive_stage="moderate", mmse_score=18, mna_score=15,
    iddsi_level=4, has_hypertension=True, has_diabetes=False,
)
st.write(p)
from Core.models import FoodItem

food = FoodItem(
    food_id="F001", name_fr="Soupe de lentilles", name_dz="Chorba adass",
    name_en="Lentil soup", texture_level=4, is_thin_liquid=False,
    is_comfort_food=True, calories_per_100g=90.0, protein_g=6.0,
    mind_category="legumes", is_low_sodium=True, is_low_gi=True,
)
save_food(food)

from Core.db import create_tables, save_patient, save_food
from Core.db import create_tables, save_patient
create_tables()
save_patient(p)

import os
import sqlite3

st.write("Database file:", os.path.abspath("cdss.db"))
conn = sqlite3.connect("cdss.db")
st.write("Patients in db:", conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0])
conn.close()

from Core.db import get_food
st.write(get_food("F001")) 
