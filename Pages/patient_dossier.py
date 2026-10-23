import streamlit as st
from datetime import date
from Core.models import PatientProfile
from Core.db import create_tables, save_patient, get_patient

create_tables()

st.title("Patient Dossier")

with st.form("dossier_form"):
    patient_id = st.text_input("Patient ID")
    full_name = st.text_input("Full name")
    dob = st.date_input("Date of birth", value=date(1945, 1, 1),
                        min_value=date(1900, 1, 1), max_value=date.today())
    gender = st.selectbox("Gender", ["F", "M"])
    address = st.text_input("Address")
    height_cm = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=160.0)
    weight_kg = st.number_input("Weight (kg)", min_value=20.0, max_value=250.0, value=60.0)
    date_of_diagnosis = st.date_input("Date of diagnosis", value=date.today(),
                                      min_value=date(1990, 1, 1), max_value=date.today())
    dependence_level = st.selectbox("Dependence level", ["low", "moderate", "high"])
    cognitive_stage = st.selectbox("Cognitive stage", ["mild", "moderate", "severe"])
    mmse_score = st.number_input("MMSE score (0-30)", min_value=0, max_value=30, value=20)
    mna_score = st.number_input("MNA score (0-30)", min_value=0, max_value=30, value=20)
    iddsi_level = st.selectbox("IDDSI level", [0, 1, 2, 3, 4, 5, 6, 7], index=7)
    has_hypertension = st.checkbox("Hypertension")
    has_diabetes = st.checkbox("Diabetes")

    submitted = st.form_submit_button("Save patient")

if submitted:
    p = PatientProfile(
        patient_id=patient_id,
        full_name=full_name,
        dob=dob,
        gender=gender,
        address=address,
        height_cm=height_cm,
        weight_kg=weight_kg,
        date_of_diagnosis=date_of_diagnosis,
        dependence_level=dependence_level,
        cognitive_stage=cognitive_stage,
        mmse_score=mmse_score,
        mna_score=mna_score,
        iddsi_level=iddsi_level,
        has_hypertension=has_hypertension,
        has_diabetes=has_diabetes,
    )
    save_patient(p)
    st.success("Patient saved!")
    st.write(get_patient(patient_id))