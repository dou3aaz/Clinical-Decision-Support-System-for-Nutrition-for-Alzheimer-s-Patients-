from datetime import date
from Core.models import PatientProfile, FoodItem
from Core.rules import gatekeeper_filter


def make_patient(**changes):
    data = dict(
        patient_id="P1", full_name="Test", dob=date(1945, 1, 1), gender="F",
        address="Algiers", height_cm=160.0, weight_kg=60.0,
        date_of_diagnosis=date(2023, 1, 1), dependence_level="moderate",
        cognitive_stage="moderate", mmse_score=18, mna_score=20,
        iddsi_level=7, has_hypertension=False, has_diabetes=False,
    )
    data.update(changes)
    return PatientProfile(**data)


def make_food(**changes):
    data = dict(
        food_id="F1", name_fr="x", name_dz="x", name_en="x", texture_level=7,
        is_thin_liquid=False, is_comfort_food=False, calories_per_100g=100.0,
        protein_g=5.0, mind_category="none", is_low_sodium=True, is_low_gi=True,
    )
    data.update(changes)
    return FoodItem(**data)


def test_solid_food_removed_for_iddsi_4():
    patient = make_patient(iddsi_level=4)
    solid = make_food(texture_level=7)
    assert gatekeeper_filter(patient, [solid]) == []


def test_thin_liquid_removed_for_dysphagia():
    patient = make_patient(iddsi_level=4)
    water = make_food(texture_level=0, is_thin_liquid=True)
    assert gatekeeper_filter(patient, [water]) == []