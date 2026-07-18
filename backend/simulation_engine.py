import numpy as np
import pandas as pd
from backend.pricing import calculate_surge
from backend.rl_allocator import QAllocator

RATING_WEIGHT = 0.6
ACCEPTANCE_WEIGHT = 0.3
CANCELLATION_PENALTY_WEIGHT = 0.5


def compute_rider_score(rating, acceptance_rate, cancellation_rate):
    """Weighted score used to rank available riders for a request."""
    return (
        RATING_WEIGHT * rating
        + ACCEPTANCE_WEIGHT * acceptance_rate
        - CANCELLATION_PENALTY_WEIGHT * cancellation_rate
    )


def run_simulation(
    num_zones,
    num_riders,
    num_requests,
    time_steps,
    use_rl=True,
    seed=None,
):
    if seed is not None:
        np.random.seed(seed)

    allocator_type = "rl_qlearning" if use_rl else "rule_based"

    allocator = QAllocator(num_zones) if use_rl else None

    riders = pd.DataFrame({
        "rider_id": range(num_riders),
        "zone_id": np.random.randint(0, num_zones, num_riders),
        "is_available": True,
        "busy_until": 0,
        "rating": np.clip(np.random.normal(4.5, 0.3, num_riders), 3.0, 5.0),
        "acceptance_rate": np.clip(np.random.normal(0.85, 0.10, num_riders), 0.4, 1.0),
        "cancellation_rate": np.clip(np.random.normal(0.08, 0.06, num_riders), 0.0, 0.5),
        "total_earnings": 0.0,
        "total_rides_completed": 0,
    })
    riders["score"] = compute_rider_score(
        riders["rating"], riders["acceptance_rate"], riders["cancellation_rate"]
    )

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

    for t in range(time_steps):

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

            surge = calculate_surge(demand, supply, 0.6)
            surge_log.append({
                "time_step": t,
                "zone_id": zone,
                "surge": surge
            })

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

            selected_riders = available_riders.sort_values(
                "score", ascending=False
            ).head(num_allocations)
            selected_requests = zone_requests.head(num_allocations)

            for (_, req), (_, rider) in zip(
                selected_requests.iterrows(),
                selected_riders.iterrows()
            ):

                duration = np.random.randint(3, 8)
                actual_duration = min(duration, time_steps - t)
                total_busy_time += actual_duration

                riders.loc[
                    riders["rider_id"] == rider["rider_id"], "is_available"
                ] = False
                riders.loc[
                    riders["rider_id"] == rider["rider_id"], "busy_until"
                ] = t + duration

                fare = req["base_fare"] * surge
                driver_share = fare * 0.2
                total_revenue += driver_share

                riders.loc[
                    riders["rider_id"] == rider["rider_id"], "total_earnings"
                ] += driver_share
                riders.loc[
                    riders["rider_id"] == rider["rider_id"], "total_rides_completed"
                ] += 1

                fulfilled_requests += 1

                allocation_log.append({
                    "time_step": t,
                    "zone_id": zone,
                    "rider_id": rider["rider_id"],
                    "allocator_type": allocator_type,
                    "fare": fare,
                    "surge_multiplier": surge,
                    "was_fulfilled": True,
                    "rider_score": rider["score"],
                })

                if use_rl:
                    reward = fare / 200
                    allocator.update(state, "allocate", reward)

    total_possible_time = num_riders * time_steps
    utilization = total_busy_time / total_possible_time
    fulfillment_rate = fulfilled_requests / num_requests

    kpis = {
        "revenue": total_revenue,
        "fulfillment_rate": fulfillment_rate,
        "utilization": utilization,
        "avg_surge": pd.DataFrame(surge_log)["surge"].mean() if surge_log else 0.0,
    }

    riders_out = riders[[
        "rider_id", "rating", "acceptance_rate", "cancellation_rate",
        "zone_id", "total_rides_completed", "total_earnings"
    ]].rename(columns={"zone_id": "home_zone_id"})

    return (
        pd.DataFrame(allocation_log),
        pd.DataFrame(surge_log),
        kpis,
        riders_out,
        allocator_type,
    )
