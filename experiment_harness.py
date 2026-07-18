"""
Runs repeated simulations across both allocator types under a fixed
configuration, varying only the random seed, and persists each run to
the database for statistical comparison.

Usage:
    python analysis/experiment_harness.py --n-seeds 25
"""

import argparse
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backend.db import init_db, get_connection, save_run, seed_zones
from backend.simulation_engine import run_simulation


FIXED_CONFIG = {
    "num_zones": 8,
    "num_riders": 150,
    "num_requests": 2000,
    "time_steps": 100,
}

USE_RL_VALUES = [False, True]


def run_batch(n_seeds: int) -> list:
    init_db()
    conn = get_connection()
    seed_zones(conn, FIXED_CONFIG["num_zones"])
    run_ids = []

    for use_rl in USE_RL_VALUES:
        for seed in range(n_seeds):
            allocation_df, surge_df, kpis, riders_df, allocator_type = run_simulation(
                num_zones=FIXED_CONFIG["num_zones"],
                num_riders=FIXED_CONFIG["num_riders"],
                num_requests=FIXED_CONFIG["num_requests"],
                time_steps=FIXED_CONFIG["time_steps"],
                use_rl=use_rl,
                seed=seed,
            )

            config = dict(FIXED_CONFIG)
            config["allocator_type"] = allocator_type

            run_id = save_run(conn, config, kpis, allocation_df, riders_df, surge_df)
            run_ids.append(run_id)
            print(f"[{allocator_type}] seed={seed} -> run_id={run_id} "
                  f"revenue={kpis['revenue']:.2f} "
                  f"fulfillment={kpis['fulfillment_rate']:.4f}")

    conn.close()
    return run_ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-seeds", type=int, default=25)
    args = parser.parse_args()
    run_batch(args.n_seeds)
