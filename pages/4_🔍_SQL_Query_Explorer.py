import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.db import get_connection, init_db

st.set_page_config(page_title="SQL Query Explorer", page_icon="🔍", layout="wide")
st.title("🔍 SQL Query Explorer")
st.caption("Run SQL queries directly against the simulation history database.")

init_db()

PRESET_QUERIES = {
    "-- Choose a preset --": "",
    "Allocator comparison (summary)": """
        SELECT
            allocator_type,
            COUNT(*) AS total_allocations,
            ROUND(AVG(fare), 2) AS avg_fare,
            ROUND(SUM(CASE WHEN was_fulfilled THEN 1 ELSE 0 END) * 1.0
                  / COUNT(*), 4) AS fulfillment_rate,
            ROUND(AVG(rider_score), 3) AS avg_rider_quality_matched
        FROM allocations
        GROUP BY allocator_type;
    """,
    "Leaderboard (top 10 runs by revenue)": """
        SELECT run_id, allocator_type, num_riders, num_zones,
               total_revenue, fulfillment_rate,
               RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
        FROM simulation_runs
        ORDER BY revenue_rank
        LIMIT 10;
    """,
    "Surge elasticity": """
        SELECT
            ROUND(surge_multiplier, 1) AS surge_bucket,
            COUNT(*) AS total_requests,
            ROUND(AVG(CASE WHEN was_fulfilled THEN 1.0 ELSE 0 END), 4)
                AS fulfillment_rate,
            ROUND(AVG(fare), 2) AS avg_fare
        FROM allocations
        GROUP BY surge_bucket
        ORDER BY surge_bucket;
    """,
    "Zone-type surge comparison": """
        SELECT z.zone_type,
               ROUND(AVG(a.surge_multiplier), 2) AS avg_surge,
               ROUND(AVG(a.fare), 2) AS avg_fare,
               COUNT(*) AS total_requests
        FROM allocations a
        JOIN zones z ON a.zone_id = z.zone_id
        GROUP BY z.zone_type
        ORDER BY avg_surge DESC;
    """,
    "Run-over-run revenue change": """
        SELECT run_id, run_timestamp, total_revenue,
               LAG(total_revenue) OVER (ORDER BY run_timestamp)
                   AS previous_run_revenue,
               ROUND(total_revenue -
                     LAG(total_revenue) OVER (ORDER BY run_timestamp), 2)
                   AS revenue_change
        FROM simulation_runs
        ORDER BY run_timestamp;
    """,
}

preset = st.selectbox("Preset queries", list(PRESET_QUERIES.keys()))

query = st.text_area(
    "SQL query",
    value=PRESET_QUERIES[preset] if PRESET_QUERIES[preset] else
          "SELECT * FROM simulation_runs LIMIT 10;",
    height=180,
)

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]

if st.button("Run query", type="primary"):
    if any(kw in query.upper() for kw in FORBIDDEN_KEYWORDS):
        st.error("Only read-only SELECT queries are allowed here.")
    else:
        try:
            conn = get_connection()
            result = pd.read_sql(query, conn)
            conn.close()
            st.success(f"{len(result)} rows returned")
            st.dataframe(result, use_container_width=True)

            if len(result.columns) >= 2 and len(result) > 1:
                numeric_cols = result.select_dtypes(include="number").columns
                if len(numeric_cols) > 0:
                    st.subheader("Quick chart")
                    st.line_chart(result[numeric_cols])
        except Exception as e:
            st.error(f"Query failed: {e}")

with st.expander("Schema reference"):
    st.code("""
simulation_runs(run_id, run_timestamp, num_zones, num_riders, num_requests,
                time_steps, allocator_type, total_revenue, fulfillment_rate,
                rider_utilization, avg_surge)

allocations(allocation_id, run_id, time_step, zone_id, rider_id,
            allocator_type, fare, surge_multiplier, was_fulfilled, rider_score)

riders(row_id, run_id, rider_id, rating, acceptance_rate, cancellation_rate,
       home_zone_id, total_rides_completed, total_earnings)

zones(zone_id, zone_name, zone_type)

surge_events(surge_id, run_id, time_step, zone_id, surge,
             demand_count, supply_count)
    """, language="sql")
