def gatekeeper_filter(patient, foods):
    safe = []
    for food in foods:
        if patient.iddsi_level < 7:
            if food.texture_level > patient.iddsi_level:
                continue
            if food.is_thin_liquid:
                continue
        if patient.has_hypertension and not food.is_low_sodium:
            continue
        if patient.has_diabetes and not food.is_low_gi:
            continue
        safe.append(food)
    return safe