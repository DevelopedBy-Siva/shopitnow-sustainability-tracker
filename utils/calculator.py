def estimate_emission(
    material_factor, weight_kg, qty, distance_km, transport_factor=0.0002
):
    material_emission = material_factor * weight_kg * qty
    transport_emission = transport_factor * (weight_kg * qty) * distance_km
    return round(material_emission + transport_emission, 3)


def calculate_savings(co2_baseline, co2_actual):
    return max(co2_baseline - co2_actual, 0.0)
