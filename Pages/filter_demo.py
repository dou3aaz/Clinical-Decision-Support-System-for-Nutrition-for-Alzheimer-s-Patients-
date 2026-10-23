import streamlit as st
from Core.db import get_patient, get_all_patient_ids, get_all_foods
from Core.rules import gatekeeper_filter

st.title("Stage 1: Safety Filter")

ids = get_all_patient_ids()
if not ids:
    st.info("Save a patient on the Patient Dossier page first.")
    st.stop()

patient_id = st.selectbox("Patient", ids)
patient = get_patient(patient_id)

st.write(
    f"IDDSI level: {patient.iddsi_level} | "
    f"Hypertension: {patient.has_hypertension} | "
    f"Diabetes: {patient.has_diabetes}"
)

foods = get_all_foods()
safe = gatekeeper_filter(patient, foods)
removed = [f for f in foods if f not in safe]

st.subheader(f"Allowed foods ({len(safe)})")
if safe:
    st.table([{"Food": f.name_en, "Texture": f.texture_level} for f in safe])
else:
    st.write("No food is safe for this patient.")

st.subheader(f"Removed foods ({len(removed)})")
if removed:
    st.table([{"Food": f.name_en, "Texture": f.texture_level} for f in removed])