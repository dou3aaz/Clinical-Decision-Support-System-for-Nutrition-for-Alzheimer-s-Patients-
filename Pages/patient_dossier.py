import streamlit as st
from datetime import date
from Core.models import PatientProfile
from Core.db import create_tables, save_patient, get_patient

create_tables()

st.title("Add patient")
st.caption("Fields marked * are required. Clinical fields start empty on purpose: "
           "a default value could be mistaken for a real measurement.")

with st.form("dossier_form"):
    patient_id = st.text_input("Patient ID *")
    full_name = st.text_input("Full name *")
    dob = st.date_input("Date of birth *", value=None,
                        min_value=date(1900, 1, 1), max_value=date.today())
    gender = st.selectbox("Gender *", ["F", "M"], index=None, placeholder="Select...")
    address = st.text_input("Address")
    height_cm = st.number_input("Height (cm) *", min_value=50.0, max_value=250.0, value=None)
    weight_kg = st.number_input("Weight (kg) *", min_value=20.0, max_value=250.0, value=None)
    date_of_diagnosis = st.date_input("Date of diagnosis *", value=None,
                                      min_value=date(1990, 1, 1), max_value=date.today())
    dependence_level = st.selectbox("Dependence level *", ["low", "moderate", "high"],
                                    index=None, placeholder="Select...")
    cognitive_stage = st.selectbox("Cognitive stage *", ["mild", "moderate", "severe"],
                                   index=None, placeholder="Select...")
    mmse_score = st.number_input("MMSE score (0-30) *", min_value=0, max_value=30,
                                 value=None, step=1)
    mna_score = st.number_input("MNA score (0-30) *", min_value=0, max_value=30,
                                value=None, step=1)
    iddsi_level = st.selectbox("IDDSI level *", [0, 1, 2, 3, 4, 5, 6, 7],
                               index=None, placeholder="Select...")
    hypertension = st.radio("Hypertension *", ["Yes", "No"], index=None, horizontal=True)
    diabetes = st.radio("Diabetes *", ["Yes", "No"], index=None, horizontal=True)

    submitted = st.form_submit_button("Save patient")

if submitted:
    patient_id = patient_id.strip()
    required = {
        "Patient ID": patient_id,
        "Full name": full_name.strip(),
        "Date of birth": dob,
        "Gender": gender,
        "Height": height_cm,
        "Weight": weight_kg,
        "Date of diagnosis": date_of_diagnosis,
        "Dependence level": dependence_level,
        "Cognitive stage": cognitive_stage,
        "MMSE score": mmse_score,
        "MNA score": mna_score,
        "IDDSI level": iddsi_level,
        "Hypertension": hypertension,
        "Diabetes": diabetes,
    }
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        st.error("Please fill in: " + ", ".join(missing))
        st.stop()

    if get_patient(patient_id) is not None:
        st.error("A patient with this ID already exists. Please use a different ID.")
        st.stop()

    p = PatientProfile(
        patient_id=patient_id,
        full_name=full_name.strip(),
        dob=dob,
        gender=gender,
        address=address,
        height_cm=float(height_cm),
        weight_kg=float(weight_kg),
        date_of_diagnosis=date_of_diagnosis,
        dependence_level=dependence_level,
        cognitive_stage=cognitive_stage,
        mmse_score=int(mmse_score),
        mna_score=int(mna_score),
        iddsi_level=int(iddsi_level),
        has_hypertension=(hypertension == "Yes"),
        has_diabetes=(diabetes == "Yes"),
    )
    save_patient(p)
    st.success("Patient saved!")
    st.write(get_patient(patient_id))