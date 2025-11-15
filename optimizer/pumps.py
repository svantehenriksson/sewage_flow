def small_pump(h: float) -> [float, float]:
    # Return power in kW and flow in m3/h
    h = 30 - h
    
    Q = (-83/4*h + 1128) * 3.6
    P = -15/8*h + 240
    return [P, Q]
  
def big_pump(h: float) -> [float, float]:
    # Return power in kW and flow in m3/h
    h = 30 - h
    Q = (-110/3*h + 2080) * 3.6
    P = -43/15*h + 4269/10
    return [P, Q]
    
    
    
    
