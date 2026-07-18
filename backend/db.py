import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "simulation_history.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def seed_zones(conn: sqlite3.Connection, num_zones: int) -> None:
    zone_types = ["CBD", "residential", "airport", "suburb"]
    cur = conn.cursor()
    for zone_id in range(num_zones):
        zone_type = zone_types[zone_id % len(zone_types)]
        cur.execute("""
            INSERT OR IGNORE INTO zones (zone_id, zone_name, zone_type)
            VALUES (?, ?, ?)
        """, (zone_id, f"Zone {zone_id}", zone_type))
    conn.commit()


def save_run(conn: sqlite3.Connection, config: dict, kpis: dict,
             allocations_df: pd.DataFrame, riders_df: pd.DataFrame = None,
             surge_df: pd.DataFrame = None) -> int:
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO simulation_runs
            (num_zones, num_riders, num_requests, time_steps, allocator_type,
             total_revenue, fulfillment_rate, rider_utilization, avg_surge)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        config["num_zones"], config["num_riders"], config["num_requests"],
        config["time_steps"], config["allocator_type"],
        kpis["revenue"], kpis["fulfillment_rate"],
        kpis["utilization"], kpis["avg_surge"],
    ))
    run_id = cur.lastrowid

    if riders_df is not None and not riders_df.empty:
        riders_out = riders_df.copy()
        riders_out["run_id"] = run_id
        riders_out.to_sql("riders", conn, if_exists="append", index=False)

    if allocations_df is not None and not allocations_df.empty:
        alloc = allocations_df.copy()
        alloc["run_id"] = run_id
        alloc.to_sql("allocations", conn, if_exists="append", index=False)

    if surge_df is not None and not surge_df.empty:
        surge_out = surge_df.copy()
        surge_out["run_id"] = run_id
        surge_out.to_sql("surge_events", conn, if_exists="append", index=False)

    conn.commit()
    return run_id


def run_query(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
