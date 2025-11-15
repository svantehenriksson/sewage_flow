def pumping_score(water_level: float, electricity_price: float) -> float:
    multiplier = 0.7 + 0.3 * water_level / 8
    
    return electricity_price / multiplier