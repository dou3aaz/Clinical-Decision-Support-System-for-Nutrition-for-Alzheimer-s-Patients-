from datetime import date
from Core.models import PatientProfile, FoodItem
from Core.rules import gatekeeper_filter, score_foods, get_final_allowed_foods, generate_meal_plan, make_default_log


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
        protein_g=5.0, mind_category="none", is_low_sodium=True, is_low_gi=True, meal_types="breakfast;lunch;snack;dinner",
    
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

from Core.models import PatientProfile, FoodItem, DailySymptomLog
from Core.rules import gatekeeper_filter, score_foods


def make_log(**changes):
    data = dict(
        log_id="L1", log_date=date(2026, 10, 26), agitation_level="none",
        is_aggressive=False, mood_state="calm", appetite_status=[],
        fluid_intake_ml=1500,
    )
    data.update(changes)
    return DailySymptomLog(**data)


def test_comfort_food_boosted_when_agitated():
    patient = make_patient()
    log = make_log(agitation_level="severe")
    comfort = make_food(is_comfort_food=True)
    plain = make_food(is_comfort_food=False)
    results = score_foods(patient, log, [plain, comfort])
    assert results[0]["food"] is comfort

def test_override_not_allowed_removes_food():
    patient = make_patient()
    food = make_food(food_id="X")
    overrides = {"X": {"decision": "not allowed", "reason": "refuses", "source": "nutritionist"}}
    assert get_final_allowed_foods(patient, [food], overrides) == []


def test_new_plan_is_pending_validation():
    patient = make_patient()
    plan = generate_meal_plan(patient, make_default_log(), [make_food()])
    assert plan.validation_status == "Pending Validation"
    assert plan.is_validated_by_nutritionist is False

def test_breakfast_changes_between_days():
    patient = make_patient()
    a = make_food(food_id="A", meal_types="breakfast")
    b = make_food(food_id="B", meal_types="breakfast")
    plan = generate_meal_plan(patient, make_default_log(), [a, b])
    breakfasts = [e.food_id for e in plan.entries if e.meal_type == "breakfast"]
    assert breakfasts[0] != breakfasts[1]

def test_liked_food_ranks_higher():
    patient = make_patient()
    log = make_log()
    liked = make_food(food_id="L")
    plain = make_food(food_id="P")
    prefs = {"L": {"preference": "likes", "note": "", "source": "nutritionist"}}
    results = score_foods(patient, log, [plain, liked], prefs)
    assert results[0]["food"] is liked

def test_disliked_food_ranks_lower():
    patient = make_patient()
    log = make_log()
    disliked = make_food(food_id="D")
    plain = make_food(food_id="P")
    prefs = {"D": {"preference": "dislikes", "note": "", "source": "nutritionist"}}
    results = score_foods(patient, log, [disliked, plain], prefs)
    assert results[0]["food"] is plain
    assert results[-1]["food"] is disliked 