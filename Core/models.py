from dataclasses import dataclass
from datetime import date



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