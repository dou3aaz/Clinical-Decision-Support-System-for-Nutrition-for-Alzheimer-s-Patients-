from dataclasses import dataclass
from datetime import date, datetime



@dataclass
class FoodItem:
    food_id: str
    name_fr: str
    name_dz: str
    name_en: str
    texture_level: int          # IDDSI level of the food (0-7)
    is_thin_liquid: bool        # True = aspiration risk if unthickened
    is_comfort_food: bool
    calories_per_100g: float
    protein_g: float
    mind_category: str          # e.g. "leafy_greens", "berries", "fish"
    is_low_sodium: bool
    is_low_gi: bool
    meal_types: str             # meals it suits, separated by ";" e.g. "breakfast;snack"

@dataclass
class PatientProfile:
    patient_id: str
    full_name: str
    dob: date
    gender: str
    address: str
    height_cm: float
    weight_kg: float
    date_of_diagnosis: date
    dependence_level: str
    cognitive_stage: str
    mmse_score: int
    mna_score: int
    iddsi_level: int
    has_hypertension: bool
    has_diabetes: bool

@dataclass
class DailySymptomLog:
    log_id: str
    log_date: date
    agitation_level: str      # "none", "mild", "moderate", "severe"
    is_aggressive: bool
    mood_state: str
    appetite_status: list
    fluid_intake_ml: int

@dataclass
class MealEntry:
    entry_id: str
    food_id: str
    day_of_week: str
    meal_type: str
    portion_grams: float
    applied_rationale: str


@dataclass
class MealPlan:
    plan_id: str
    patient_id: str
    generated_date: datetime
    validation_status: str
    is_validated_by_nutritionist: bool
    validation_date: str | None
    total_daily_calories: float
    clinical_alerts: list
    behavioral_notes: list
    entries: list
    validation_notes: str | None = None