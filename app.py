import streamlit as st
from datetime import date
from Core.db import (create_tables, get_patient_summaries, get_patient,get_appointments, add_appointment,add_symptom, get_profile_updated_at, get_symptoms,get_all_foods, request_test, get_test_requests,save_override, delete_override, get_overrides, update_patient)
from Core.rules import get_block_reasons
from Core.db import (create_tables, get_patient_summaries, get_patient, get_appointments, add_appointment, add_symptom, get_symptoms, get_all_foods, request_test, get_test_requests, save_override, delete_override, get_overrides, save_meal_plan, get_latest_meal_plan, review_meal_plan)
from Core.rules import (get_block_reasons, get_final_allowed_foods, generate_meal_plan, make_default_log, DAYS)
from Core.db import (create_tables, get_patient_summaries, get_patient,get_appointments, add_appointment,add_symptom, get_symptoms,get_all_foods, request_test, get_test_requests,save_override, delete_override, get_overrides,save_meal_plan, get_latest_meal_plan, review_meal_plan,update_entry, delete_entry, add_entry, get_plan_edits,save_preference,get_preferences, delete_preference)
from Core.rules import (get_block_reasons, get_final_allowed_foods,generate_meal_plan, make_default_log, DAYS, MEAL_TYPES, PORTIONS, allowed_for_slot)
from datetime import date, datetime
from Core.models import PatientProfile

def with_current(options, value):
    return options if value in options else options + [value]

st.set_page_config(page_title="CDSS", layout="wide")
create_tables()

st.title("My Patients")
st.info("To open a patient's dossier, tick the checkbox next to their name.")



patients = get_patient_summaries()
if not patients:
    st.info("No patients yet. Add one on the Patient Dossier page.")
    st.stop()

table = [
    {
        "Patient ID": p["patient_id"],
        "Name": p["full_name"],
        "Next appointment": p["next_appointment"] or "None",
    }
    for p in patients
]

event = st.dataframe(
    table, hide_index=True, on_select="rerun",
    selection_mode="single-row", use_container_width=True,
)

if not event.selection.rows:
    st.caption("Click a row to open the patient's dossier.")
    st.stop()

selected = patients[event.selection.rows[0]]
patient = get_patient(selected["patient_id"])

st.divider()
st.header(f"Dossier: {patient.full_name}")

tab_profile, tab_symptoms, tab_daily, tab_tests, tab_appts, tab_foods, tab_plan = st.tabs(
    ["Profile", "Clinical symptoms", "Daily symptoms", "Tests",
     "Appointments", "Foods", "Meal plan"]
)

with tab_profile:
    details = {
        "Patient ID": patient.patient_id,
        "Name": patient.full_name,
        "Date of birth": patient.dob,
        "Gender": patient.gender,
        "Address": patient.address,
        "Height (cm)": patient.height_cm,
        "Weight (kg)": patient.weight_kg,
        "Date of diagnosis": patient.date_of_diagnosis,
        "Dependence level": patient.dependence_level,
        "Cognitive stage": patient.cognitive_stage,
        "MMSE score": patient.mmse_score,
        "MNA score": patient.mna_score,
        "IDDSI level": patient.iddsi_level,
        "Hypertension": "Yes" if patient.has_hypertension else "No",
        "Diabetes": "Yes" if patient.has_diabetes else "No",
    }
    for label, value in details.items():
        st.write(f"**{label}:** {value}")
    with st.expander("Edit profile"):
        st.caption("The patient ID cannot be changed.")
        with st.form("edit_profile"):
            e_name = st.text_input("Full name", value=patient.full_name)
            e_dob = st.date_input("Date of birth", value=patient.dob,
                                  min_value=date(1900, 1, 1), max_value=date.today())
            genders = with_current(["F", "M"], patient.gender)
            e_gender = st.selectbox("Gender", genders, index=genders.index(patient.gender))
            e_address = st.text_input("Address", value=patient.address)
            e_height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0,
                                       value=float(patient.height_cm))
            e_weight = st.number_input("Weight (kg)", min_value=20.0, max_value=250.0,
                                       value=float(patient.weight_kg))
            e_diag = st.date_input("Date of diagnosis", value=patient.date_of_diagnosis,
                                   min_value=date(1900, 1, 1), max_value=date.today())
            deps = with_current(["low", "moderate", "high"], patient.dependence_level)
            e_dep = st.selectbox("Dependence level", deps,
                                 index=deps.index(patient.dependence_level))
            stages = with_current(["mild", "moderate", "severe"], patient.cognitive_stage)
            e_stage = st.selectbox("Cognitive stage", stages,
                                   index=stages.index(patient.cognitive_stage))
            e_mmse = st.number_input("MMSE score (0-30)", min_value=0, max_value=30,
                                     value=int(patient.mmse_score))
            e_mna = st.number_input("MNA score (0-30)", min_value=0, max_value=30,
                                    value=int(patient.mna_score))
            levels = with_current([0, 1, 2, 3, 4, 5, 6, 7], patient.iddsi_level)
            e_iddsi = st.selectbox("IDDSI level", levels,
                                   index=levels.index(patient.iddsi_level))
            e_hyp = st.checkbox("Hypertension", value=patient.has_hypertension)
            e_dia = st.checkbox("Diabetes", value=patient.has_diabetes)

            if st.form_submit_button("Save changes"):
                if e_name.strip():
                    update_patient(PatientProfile(
                        patient_id=patient.patient_id,
                        full_name=e_name.strip(),
                        dob=e_dob,
                        gender=e_gender,
                        address=e_address,
                        height_cm=e_height,
                        weight_kg=e_weight,
                        date_of_diagnosis=e_diag,
                        dependence_level=e_dep,
                        cognitive_stage=e_stage,
                        mmse_score=e_mmse,
                        mna_score=e_mna,
                        iddsi_level=e_iddsi,
                        has_hypertension=e_hyp,
                        has_diabetes=e_dia,
                    ))
                    st.rerun()
                else:
                    st.error("Full name is required.")

with tab_symptoms:
    symptoms = get_symptoms(patient.patient_id)
    if symptoms:
        st.dataframe(symptoms, hide_index=True, use_container_width=True)
    else:
        st.write("No symptoms recorded.")

    with st.form("new_symptom"):
        symptom = st.text_input("Symptom (e.g. difficulty swallowing, loss of appetite)")
        severity = st.selectbox("Severity", ["mild", "moderate", "severe"])
        date_noted = st.date_input("Date noted", value=date.today())
        symptom_notes = st.text_area("Symptom notes")
        if st.form_submit_button("Add symptom"):
            if symptom.strip():
                add_symptom(patient.patient_id, symptom, severity, date_noted, symptom_notes)
                st.rerun()
            else:
                st.error("Please write the symptom.")

with tab_daily:
    st.info("Coming later: symptoms entered daily by the caregiver.")

with tab_tests:
    tests = get_test_requests(patient.patient_id)
    if tests:
        st.dataframe(tests, hide_index=True, use_container_width=True)
    else:
        st.write("The patient hasn't done any test.")

    with st.popover("Request a test"):
        with st.form("new_test"):
            test_title = st.text_input("Test title (e.g. blood glucose, albumin)")
            test_note = st.text_area("Note for the caregiver")
            if st.form_submit_button("Send request"):
                if test_title.strip():
                    request_test(patient.patient_id, test_title, test_note)
                    st.rerun()
                else:
                    st.error("Please write the test title.")

with tab_appts:
    appts = get_appointments(patient.patient_id)
    if appts:
        st.dataframe(appts, hide_index=True, use_container_width=True)
    else:
        st.write("No appointments yet.")

    with st.form("new_appointment"):
        appt_date = st.date_input("Date", value=date.today())
        status = st.selectbox("Status", ["scheduled", "completed", "cancelled"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Add appointment"):
            add_appointment(patient.patient_id, appt_date, status, notes)
            st.rerun()

with tab_foods:
    foods = get_all_foods()
    overrides = get_overrides(patient.patient_id)

    allowed = []
    not_allowed = []
    for food in foods:
        override = overrides.get(food.food_id)
        if override:
            final = override["decision"]
            why = override["reason"]
            decided_by = override["source"]
        else:
            reasons = get_block_reasons(patient, food)
            if reasons:
                final = "not allowed"
                why = "; ".join(reasons)
            else:
                final = "allowed"
                why = "Passes all safety rules"
            decided_by = "system"

        row = {"Food": food.name_en, "Why": why, "Decided by": decided_by}
        if final == "allowed":
            allowed.append(row)
        else:
            not_allowed.append(row)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"Allowed ({len(allowed)})")
        if allowed:
            st.dataframe(allowed, hide_index=True, use_container_width=True)
    with col2:
        st.subheader(f"Not allowed ({len(not_allowed)})")
        if not_allowed:
            st.dataframe(not_allowed, hide_index=True, use_container_width=True)

    st.subheader("Edit a decision")
    food_ids = {f.name_en: f.food_id for f in foods}
    with st.form("override_form"):
        chosen = st.selectbox("Food", list(food_ids.keys()))
        decision = st.radio("Decision", ["allowed", "not allowed"], horizontal=True)
        reason = st.text_input("Reason (e.g. patient refuses it, allergy, clinical judgment)")
        save_clicked = st.form_submit_button("Save decision")
        reset_clicked = st.form_submit_button("Reset to system decision")

        if save_clicked:
            if reason.strip():
                save_override(patient.patient_id, food_ids[chosen], decision,
                              reason, "nutritionist")
                st.rerun()
            else:
                st.error("A reason is required.")
        if reset_clicked:
            delete_override(patient.patient_id, food_ids[chosen])
            st.rerun()
            st.divider()
    st.subheader("Patient preferences")
    st.caption("Liked foods are favoured and disliked foods are avoided when a plan is "
               "generated. If the patient refuses a food completely, mark it "
               "'not allowed' above instead.")

    preferences = get_preferences(patient.patient_id)
    names_by_id = {f.food_id: f.name_en for f in foods}
    if preferences:
        st.dataframe(
            [
                {"Food": names_by_id.get(food_id, food_id),
                 "Preference": p["preference"],
                 "Note": p["note"],
                 "Source": p["source"]}
                for food_id, p in preferences.items()
            ],
            hide_index=True, use_container_width=True,
        )
    else:
        st.write("No preferences recorded.")

    pref_foods = get_final_allowed_foods(patient, foods, overrides)
    pref_ids = {f.name_en: f.food_id for f in pref_foods}
    if not pref_ids:
        st.write("No allowed foods to set preferences for.")
    else:
        with st.form("preference_form", clear_on_submit=True):
            pref_food = st.selectbox("Food", list(pref_ids.keys()))
            pref_choice = st.radio("Preference", ["likes", "dislikes"], horizontal=True)
            pref_note = st.text_input("Note (optional)")
            save_pref = st.form_submit_button("Save preference")
            remove_pref = st.form_submit_button("Remove preference")

            if save_pref:
                save_preference(patient.patient_id, pref_ids[pref_food],
                                pref_choice, pref_note, "nutritionist")
                st.rerun()
            if remove_pref:
                delete_preference(patient.patient_id, pref_ids[pref_food])
                st.rerun()

with tab_plan:
    plan = get_latest_meal_plan(patient.patient_id)
    changed_at = get_profile_updated_at(patient.patient_id)
    plan_is_stale = (
        plan is not None
        and changed_at is not None
        and plan.generated_date < datetime.fromisoformat(changed_at)
    )

    if (plan is not None and plan.validation_status == "Pending Validation"
            and get_plan_edits(plan.plan_id)):
        st.warning("The current draft has manual edits. Generating a new plan will replace it.")

    if st.button("Generate meal plan"):
        all_foods = get_all_foods()
        overrides = get_overrides(patient.patient_id)
        allowed_foods = get_final_allowed_foods(patient, all_foods, overrides)
        new_plan = generate_meal_plan(patient, make_default_log(), allowed_foods,get_preferences(patient.patient_id))
        if new_plan is None:
            st.error("No food is allowed for this patient, so no plan can be generated.")
        else:
            save_meal_plan(new_plan)
            st.rerun()

    if plan is None:
        st.write("No meal plan yet.")
    else:
        all_foods = get_all_foods()
        names = {f.food_id: f.name_en for f in all_foods}

        st.subheader("Latest plan")
        colors = {"Approved": "green", "Rejected": "red", "Pending Validation": "orange"}
        st.markdown(f"**Status:** :{colors[plan.validation_status]}[{plan.validation_status}]")
        st.write(f"**Generated:** {plan.generated_date:%Y-%m-%d %H:%M}")
        st.write(f"**Average daily calories:** {plan.total_daily_calories} kcal")
        if plan_is_stale:
            st.error("The patient's profile was edited after this plan was generated, "
                     "so the plan may no longer be safe. Please generate a new plan.")

        for alert in plan.clinical_alerts:
            st.warning(alert)
        for note in plan.behavioral_notes:
            st.info(note)

        rows = []
        for day in DAYS:
            row = {"Day": day}
            for meal in MEAL_TYPES:
                row[meal] = "—"
            for e in plan.entries:
                if e.day_of_week == day:
                    text = f"{names[e.food_id]} ({int(e.portion_grams)} g)"
                    if row[e.meal_type] == "—":
                        row[e.meal_type] = text
                    else:
                        row[e.meal_type] += " + " + text
            rows.append(row)
        st.dataframe(rows, hide_index=True, use_container_width=True)

        with st.expander("Why these foods? (rationale per meal)"):
            st.dataframe(
                [
                    {"Day": e.day_of_week, "Meal": e.meal_type,
                     "Food": names[e.food_id], "Why": e.applied_rationale}
                    for e in plan.entries
                ],
                hide_index=True, use_container_width=True,
            )

        if plan.validation_status == "Pending Validation" and plan_is_stale:
            st.warning("Generate a new plan before reviewing.")
        elif plan.validation_status == "Pending Validation":
            st.divider()
            st.subheader("Edit the draft plan")
            st.caption("Every change is logged with your reason. "
                       "Only foods allowed for the slot's meal type are offered.")

            allowed_foods = get_final_allowed_foods(
                patient, all_foods, get_overrides(patient.patient_id))

            st.markdown("**Change or remove a slot**")
            slot_labels = {}
            for e in plan.entries:
                label = (f"{e.day_of_week} · {e.meal_type} · "
                         f"{names[e.food_id]} ({int(e.portion_grams)} g)")
                slot_labels[label] = e

            if slot_labels:
                chosen_label = st.selectbox("Slot", list(slot_labels.keys()))
                entry = slot_labels[chosen_label]

                food_options = {
                    f.name_en: f.food_id
                    for f in allowed_for_slot(allowed_foods, entry.meal_type)
                }
                current_name = names[entry.food_id]
                if current_name not in food_options:
                    food_options[current_name] = entry.food_id
                food_names = list(food_options.keys())

                with st.form(f"edit_{entry.entry_id}", clear_on_submit=True):
                    new_food = st.selectbox(
                        "Food", food_names, index=food_names.index(current_name),
                        key=f"food_{entry.entry_id}")
                    new_portion = st.number_input(
                        "Portion (g)", min_value=20.0, max_value=500.0,
                        value=float(entry.portion_grams), step=10.0,
                        key=f"portion_{entry.entry_id}")
                    edit_reason = st.text_input(
                        "Reason (required)", key=f"reason_{entry.entry_id}")
                    save_clicked = st.form_submit_button("Save change")
                    remove_clicked = st.form_submit_button("Remove this slot")

                    if save_clicked:
                        if not edit_reason.strip():
                            st.error("A reason is required.")
                        elif (food_options[new_food] == entry.food_id
                              and new_portion == entry.portion_grams):
                            st.info("Nothing was changed.")
                        else:
                            description = (
                                f"{entry.day_of_week} {entry.meal_type}: "
                                f"{current_name} {int(entry.portion_grams)} g → "
                                f"{new_food} {int(new_portion)} g")
                            update_entry(plan.plan_id, entry.entry_id,
                                         food_options[new_food], new_portion,
                                         description, edit_reason)
                            st.rerun()

                    if remove_clicked:
                        if not edit_reason.strip():
                            st.error("A reason is required.")
                        else:
                            description = (
                                f"{entry.day_of_week} {entry.meal_type}: "
                                f"removed {current_name} {int(entry.portion_grams)} g")
                            delete_entry(plan.plan_id, entry.entry_id,
                                         description, edit_reason)
                            st.rerun()
            else:
                st.write("This plan has no slots left.")

            st.markdown("**Add a slot**")
            add_day = st.selectbox("Day", DAYS, key="add_day")
            add_meal = st.selectbox("Meal type", MEAL_TYPES, key="add_meal")
            add_options = {
                f.name_en: f.food_id
                for f in allowed_for_slot(allowed_foods, add_meal)
            }
            if not add_options:
                st.warning("No allowed food suits this meal type.")
            else:
                with st.form(f"add_slot_{add_meal}", clear_on_submit=True):
                    add_food = st.selectbox("Food", list(add_options.keys()))
                    add_portion = st.number_input(
                        "Portion (g)", min_value=20.0, max_value=500.0,
                        value=float(PORTIONS[add_meal]), step=10.0)
                    add_reason = st.text_input("Reason (required)")
                    if st.form_submit_button("Add slot"):
                        if add_reason.strip():
                            description = (f"{add_day} {add_meal}: added "
                                           f"{add_food} {int(add_portion)} g")
                            add_entry(plan.plan_id, add_day, add_meal,
                                      add_options[add_food], add_portion,
                                      description, add_reason)
                            st.rerun()
                        else:
                            st.error("A reason is required.")

        edits = get_plan_edits(plan.plan_id)
        if edits:
            with st.expander(f"Edit log ({len(edits)})"):
                st.dataframe(edits, hide_index=True, use_container_width=True)

        st.divider()
        st.subheader("Review")

        if plan.validation_status == "Pending Validation":
            with st.form("review_form"):
                review_notes = st.text_area("Nutritionist notes (required if rejecting)")
                approve_clicked = st.form_submit_button("Approve plan")
                reject_clicked = st.form_submit_button("Reject plan")

                if approve_clicked:
                    review_meal_plan(plan.plan_id, True, review_notes)
                    st.rerun()
                if reject_clicked:
                    if review_notes.strip():
                        review_meal_plan(plan.plan_id, False, review_notes)
                        st.rerun()
                    else:
                        st.error("Please write a note explaining why the plan is rejected.")
        else:
            st.write(f"Reviewed on {plan.validation_date[:10]}.")
            if plan.validation_notes:
                st.write(f"**Notes:** {plan.validation_notes}")
            if plan.validation_status == "Rejected":
                st.info("Adjust the food decisions in the Foods tab, then generate a new plan.")

