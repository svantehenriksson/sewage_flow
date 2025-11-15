def small_pump(h: float) -> [float, float]:
    # Return power in kW and flow in m3/h
    
    # 5m -> 190kW
    
    # 0.5, -> 1150m3/h
    # 2m -> 1550m3/h
    # 3.8m -> 1740m3/h

    flow = 1150 + 600 * max(0, min(4, h)) / 4
    
    return [185, flow]

def big_pump(h: float) -> [float, float]:
    # Return power in kW and flow in m3/h
    
    # 1m -> 370kW
    # 2m -> 350kW
    # 3m -> 390kW
    # 4.5 -> 360kW
    
    # 1.5m -> 2500m3/h
    # 3m -> 3200m3/h
    # 4.5m -> 3300m3/h
    # 5m -> 3500m3/h

    flow = 2500 + 1000 * max(0, min(5, h)) / 5
    
    return [350, flow]
