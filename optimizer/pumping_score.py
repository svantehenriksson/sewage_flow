def pumping_score(water_level: float, electricity_price: float) -> float:
    """
    Calculate the pumping score (effective cost per kWh) considering pump efficiency.
    
    Pumps are more efficient at higher water levels, so the effective cost is lower
    when the water level is high.
    
    Args:
        water_level: Current water level in meters (0-8m)
        electricity_price: Price of electricity in €/kWh
    
    Returns:
        Effective cost per kWh, adjusted for pump efficiency at this water level
    """
    # Efficiency ranges from ~0.85 at low water to ~1.0 at high water
    # Lower efficiency = higher effective cost
    efficiency = 0.85 + 0.15 * min(water_level / 8.0, 1.0)
    
    # Effective cost is electricity price divided by efficiency
    # (worse efficiency = higher cost for same electricity)
    return electricity_price / efficiency

