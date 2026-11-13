from datetime import date, datetime
from Core.models import MealPlan, MealEntry, DailySymptomLog

def get_block_reasons(patient, food):
    reasons = []
    if patient.iddsi_level < 7:
        if food.texture_level > patient.iddsi_level:
            reasons.append(
                f"Texture level {food.texture_level} is above IDDSI level {patient.iddsi_level}"
            )
        if food.is_thin_liquid:
            reasons.append("Thin liquid (aspiration risk)")
    if patient.has_hypertension and not food.is_low_sodium:
        reasons.append("High sodium (hypertension)")
    if patient.has_diabetes and not food.is_low_gi:
        reasons.append("High glycemic index (diabetes)")
    return reasons


def gatekeeper_filter(patient, foods):
    safe = []
    for food in foods:
        if len(get_block_reasons(patient, food)) == 0:
            safe.append(food)
    return safe

MIND_POINTS = {
    "leafy_greens": 2, "berries": 2, "nuts": 2, "legumes": 2,
    "fish": 2, "poultry": 2,
    "vegetables": 1, "grains": 1,
    "fried_food": -2, "cheese": -2, "pastries_sweets": -2,
}

LOW_FLUID_ML = 1000


def is_hydrating(food):
    # Stand-in rule until FoodItem gets a real "hydrating" field
    return food.is_thin_liquid or (
        food.texture_level <= 4 and food.calories_per_100g < 100
    )



def score_foods(patient, log, foods, preferences=None):
    if preferences is None:
        preferences = {}

    agitated = log.is_aggressive or log.agitation_level != "none"
    low_fluid = log.fluid_intake_ml < LOW_FLUID_ML

    results = []
    for food in foods:
        score = 0
        reasons = []

        mind = MIND_POINTS.get(food.mind_category, 0)
        if mind != 0:
            score += mind
            reasons.append(f"MIND diet ({food.mind_category}): {mind} points")

        if patient.mna_score < 17 and (
            food.protein_g >= 5 or food.calories_per_100g >= 120
        ):
            score += 3
            reasons.append("Fortification (MNA < 17): 3 points")

        if low_fluid and is_hydrating(food):
            score += 3
            reasons.append("Low fluid intake, hydrating food: 3 points")

        if agitated and food.is_comfort_food:
            score += 3
            reasons.append("Agitation, comfort food: 3 points")

        preference = preferences.get(food.food_id)
        if preference:
            if preference["preference"] == "likes":
                score += 2
                reasons.append("Patient likes this food: 2 points")
            elif preference["preference"] == "dislikes":
                score -= 3
                reasons.append("Patient dislikes this food: -3 points")

        results.append({"food": food, "score": score, "reasons": reasons})

    results.sort(key=lambda r: r["score"], reverse=True)
    return results

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"]
MEAL_TYPES = ["breakfast", "lunch", "snack", "dinner", "hydration"]
PORTIONS = {"breakfast": 150, "lunch": 200, "snack": 100,"dinner": 200, "hydration": 150}
MAX_USES_PER_WEEK = 3


def make_default_log():
    return DailySymptomLog(
        log_id="DEFAULT", log_date=date.today(), agitation_level="none",
        is_aggressive=False, mood_state="unknown", appetite_status=[],
        fluid_intake_ml=1500,
    )


def get_final_allowed_foods(patient, foods, overrides):
    allowed = []
    for food in foods:
        override = overrides.get(food.food_id)
        if override:
            if override["decision"] == "allowed":
                allowed.append(food)
        elif len(get_block_reasons(patient, food)) == 0:
            allowed.append(food)
    return allowed


def pick_food(pool, used, today, last_food):
    def candidates(under_cap, not_negative, avoid_last):
        found = []
        for r in pool:
            food_id = r["food"].food_id
            if food_id in today:
                continue
            if avoid_last and food_id == last_food:
                continue
            if under_cap and used.get(food_id, 0) >= MAX_USES_PER_WEEK:
                continue
            if not_negative and r["score"] < 0:
                continue
            found.append(r)
        return found

    # strictest rules first, then relax them one at a time
    steps = [
        (True, True, True),
        (False, True, True),
        (False, True, False),
        (False, False, True),
        (False, False, False),
    ]
    found = []
    for under_cap, not_negative, avoid_last in steps:
        found = candidates(under_cap, not_negative, avoid_last)
        if found:
            break
    if not found:
        found = pool

    best = found[0]
    for r in found:
        r_value = r["score"] - used.get(r["food"].food_id, 0)
        best_value = best["score"] - used.get(best["food"].food_id, 0)
        if r_value > best_value:
            best = r
    return best


def build_alerts(patient, log, allowed_foods, has_hydrating):
    clinical = []
    behavioral = []

    if patient.iddsi_level < 7:
        clinical.append(
            f"Dysphagia: foods limited to texture level {patient.iddsi_level} "
            "or below, thin liquids excluded."
        )
    if 1 <= patient.iddsi_level <= 3:
        clinical.append(f"Liquids must be thickened to IDDSI level {patient.iddsi_level}.")
    if patient.has_hypertension:
        clinical.append("Hypertension: high-sodium foods excluded.")
    if patient.has_diabetes:
        clinical.append("Diabetes: high-glycemic foods excluded.")
    if patient.mna_score < 17:
        clinical.append(
            f"Malnutrition risk (MNA {patient.mna_score}): "
            "calorie and protein fortification applied."
        )
    for food in allowed_foods:
        reasons = get_block_reasons(patient, food)
        if reasons:
            clinical.append(
                f"Nutritionist override: {food.name_en} is allowed despite: "
                + "; ".join(reasons)
            )
    if len(allowed_foods) < 5:
        clinical.append(
            f"Only {len(allowed_foods)} foods are allowed: the plan has limited variety."
        )
    if not has_hydrating:
        clinical.append(
            "No hydrating food is allowed: arrange fluids (thickened if needed) separately."
        )

    if log.log_id == "DEFAULT":
        behavioral.append(
            "No caregiver log yet: default assumptions used "
            "(no agitation, normal fluid intake)."
        )
    if log.is_aggressive or log.agitation_level != "none":
        behavioral.append("Agitation or aggression reported: comfort foods prioritized.")
    if log.fluid_intake_ml < LOW_FLUID_ML:
        behavioral.append(
            f"Low fluid intake ({log.fluid_intake_ml} ml): hydrating foods prioritized."
        )
    return clinical, behavioral

def foods_for_meal(scored, meal):
    return [r for r in scored if meal in (r["food"].meal_types or "").split(";")]

def allowed_for_slot(foods, meal):
    result = []
    for food in foods:
        if meal == "hydration":
            if is_hydrating(food):
                result.append(food)
        elif meal in (food.meal_types or "").split(";"):
            result.append(food)
    return result

def generate_meal_plan(patient, log, allowed_foods, preferences=None):
    if not allowed_foods:
        return None

    scored = score_foods(patient, log, allowed_foods, preferences)
    hydrating = [r for r in scored if is_hydrating(r["food"])]

    now = datetime.now()
    plan_id = f"{patient.patient_id}-{now.strftime('%Y%m%d%H%M%S')}"

    used = {} 
    entries = []
    total_calories = 0.0
    n = 0
    used = {}
    last={}
    empty_slots = []
    for day in DAYS:
        today = []
        for meal in MEAL_TYPES:
            if meal == "hydration":
                pool = hydrating
            else:
                pool = foods_for_meal(scored, meal)
            if not pool:
                    if meal != "hydration" and meal not in empty_slots:
                     empty_slots.append(meal)
                    continue
            choice = pick_food(pool, used, today, last.get(meal))
            food = choice["food"]
            grams = PORTIONS[meal]

            n += 1
            if choice["reasons"]:
                rationale = "; ".join(choice["reasons"])
            else:
                rationale = "Passes all safety rules"

            entries.append(MealEntry(
                entry_id=f"{plan_id}-{n:02d}",
                food_id=food.food_id,
                day_of_week=day,
                meal_type=meal,
                portion_grams=float(grams),
                applied_rationale=rationale,
            ))
            used[food.food_id] = used.get(food.food_id, 0) + 1
            today.append(food.food_id)
            last[meal] = food.food_id
            total_calories += grams / 100 * food.calories_per_100g

    clinical, behavioral = build_alerts(patient, log, allowed_foods, len(hydrating) > 0)
    if preferences:
        behavioral.append("Patient preferences (likes and dislikes) were taken into account.")
    for meal in empty_slots:
        clinical.append(f"No allowed food suits {meal}: those slots are empty.")

    return MealPlan(
        plan_id=plan_id,
        patient_id=patient.patient_id,
        generated_date=now,
        validation_status="Pending Validation",
        is_validated_by_nutritionist=False,
        validation_date=None,
        total_daily_calories=round(total_calories / 7, 1),
        clinical_alerts=clinical,
        behavioral_notes=behavioral,
        entries=entries,
    )