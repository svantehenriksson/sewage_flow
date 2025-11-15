def tunnel_volume(h: float) -> float:
    """
    Compute tunnel volume [m³] as a function of water level h [m].

    Piecewise definition from HSY spec:
      - 0   ≤ h ≤ 0.4   : constant 350 m³
      - 0.4 < h ≤ 6.0   : V = (((1000 * (h - 0.4)**2) / 2) * 5) + 350
      - 6.0 < h ≤ 8.7   : V = (5500 * (h - 5.9) * 5) + 75975
      - 8.7 < h ≤ 14.1  : V = (((5.5 * 5500 / 2)
                                - ((5.5 - (h - 8.6))**2 * 1000 / 2)) * 5) \
                               + 150225
    """
    if h < 0:
        raise ValueError("Water level h cannot be negative")

    # 0 – 0.4 m
    if h <= 0.4:
        return 350.0

    # 0.4 – 6 m
    if h <= 6.0:
        return (((1000.0 * (h - 0.4)**2) / 2.0) * 5.0) + 350.0

    # 6 – 8.7 m
    if h <= 8.7:
        return (5500.0 * (h - 5.9) * 5.0) + 75975.0

    # 8.7 – 14.1 m
    if h <= 14.1:
        return (((5.5 * 5500.0 / 2.0)
                 - ((5.5 - (h - 8.6))**2 * 1000.0 / 2.0)) * 5.0) + 150225.0

    # Above design range
    raise ValueError("Water level h exceeds model range (h > 14.1 m)")