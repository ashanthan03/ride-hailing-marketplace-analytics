import numpy as np
import pandas as pd
from backend.pricing import calculate_surge
from backend.rl_allocator import QAllocator


def run_simulation(
    num_zones,
    num_riders,
    num_requests,
    time_steps,
    use_rl=True
):

    # -------------------------
    # Initialize RL Allocator
    # -------------------------
    allocator = QAllocator(num_zones) if use_rl else None

    # -------------------------
    # Create Riders
    # -------------------------
    riders = pd.DataFrame({
        "rider_id": range(num_riders),
        "zone_id": np.random.randint(0, num_zones, num_riders),
        "is_available": True,
        "busy_until": 0
    })

    # -------------------------
    # Create Requests
    # -------------------------
    requests = pd.DataFrame({
        "request_id": range(num_requests),
        "zone_id": np.random.randint(0, num_zones, num_requests),
        "base_fare": np.random.randint(50, 200, num_requests),
        "time_step": np.random.randint(0, time_steps, num_requests)
    })

    allocation_log = []
    surge_log = []

    total_revenue = 0
    total_busy_time = 0
    fulfilled_requests = 0

    # -------------------------
    # Simulation Loop
    # -------------------------
    for t in range(time_steps):

        # Free riders whose ride ended
        riders.loc[riders["busy_until"] <= t, "is_available"] = True

        current_requests = requests[requests["time_step"] == t]

        demand_per_zone = current_requests["zone_id"].value_counts()

        for zone in range(num_zones):

            demand = demand_per_zone.get(zone, 0)

            available_riders = riders[
                (riders["zone_id"] == zone) &
                (riders["is_available"])
            ]

            supply = len(available_riders)

            # -------------------------
            # Surge Calculation
            # -------------------------
            surge = calculate_surge(demand, supply, 0.6)
            surge_log.append({
                "time_step": t,
                "zone_id": zone,
                "surge": surge
            })

            # -------------------------
            # RL Decision
            # -------------------------
            if use_rl:
                ratio = demand / supply if supply > 0 else 10
                state = allocator.get_state(zone, ratio)
                action = allocator.choose_action(state)

                if action == "skip" or supply == 0:
                    allocator.update(state, action, -1)
                    continue
            else:
                if supply == 0:
                    continue

            zone_requests = current_requests[
                current_requests["zone_id"] == zone
            ]

            num_allocations = min(demand, supply)

            selected_riders = available_riders.head(num_allocations)
            selected_requests = zone_requests.head(num_allocations)

            for (_, req), (_, rider) in zip(
                selected_requests.iterrows(),
                selected_riders.iterrows()
            ):

                duration = np.random.randint(3, 8)

                # ---- FIXED UTILIZATION LOGIC ----
                actual_duration = min(duration, time_steps - t)
                total_busy_time += actual_duration

                # Mark rider busy
                riders.loc[
                    riders["rider_id"] == rider["rider_id"],
                    "is_available"
                ] = False

                riders.loc[
                    riders["rider_id"] == rider["rider_id"],
                    "busy_until"
                ] = t + duration

                fare = req["base_fare"] * surge
                total_revenue += fare * 0.2

                fulfilled_requests += 1

                allocation_log.append({
                    "time_step": t,
                    "zone_id": zone,
                    "fare": fare,
                    "surge": surge
                })

                # RL reward
                if use_rl:
                    reward = fare / 200  # normalized reward
                    allocator.update(state, "allocate", reward)

    # -------------------------
    # Final Metrics
    # -------------------------
    total_possible_time = num_riders * time_steps
    utilization = total_busy_time / total_possible_time

    fulfillment_rate = fulfilled_requests / num_requests

    return (
        pd.DataFrame(allocation_log),
        pd.DataFrame(surge_log),
        total_revenue,
        fulfillment_rate,
        utilization
    )
