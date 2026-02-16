def calculate_surge(demand, supply, alpha):
    if supply == 0:
        return 3.0

    ratio = demand / supply
    surge = 1 + alpha * (ratio - 1)

    return round(min(max(surge, 1.0), 3.0), 2)