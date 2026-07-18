import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.db import get_connection, init_db

st.set_page_config(page_title="Rider Insights", page_icon="🧑‍✈️", layout="wide")
st.title("🧑‍✈️ Rider Cohort & Churn-Risk Insights")

init_db()
conn = get_connection()

run_options = pd.read_sql(
    "SELECT run_id, run_timestamp, allocator_type FROM simulation_runs "
    "ORDER BY run_timestamp DESC",
    conn
)

if run_options.empty:
    st.info("No runs saved yet. Run a simulation from the Home page.")
else:
    scope = st.radio("Scope", ["All runs", "Specific run"], horizontal=True)

    run_filter_sql = ""
    selected_run_id = None
    if scope == "Specific run":
        run_label = run_options.apply(
            lambda r: f"Run {r.run_id} ({r.allocator_type}, {r.run_timestamp})",
            axis=1
        )
        selected = st.selectbox("Choose a run", run_label)
        selected_run_id = int(selected.split()[1])
        run_filter_sql = f"WHERE r.run_id = {selected_run_id}"

    st.subheader("Rider tier breakdown")
    tier_df = pd.read_sql(f"""
        SELECT
            CASE
                WHEN r.rating >= 4.7 THEN 'Top Tier'
                WHEN r.rating >= 4.3 THEN 'Mid Tier'
                ELSE 'Low Tier'
            END AS rider_tier,
            COUNT(*) AS num_rider_run_pairs,
            ROUND(AVG(r.total_earnings), 2) AS avg_earnings,
            ROUND(AVG(CASE WHEN a.was_fulfilled THEN 1.0 ELSE 0 END), 4)
                AS fulfillment_contribution
        FROM riders r
        JOIN allocations a
            ON r.run_id = a.run_id AND r.rider_id = a.rider_id
        {run_filter_sql}
        GROUP BY rider_tier
        ORDER BY avg_earnings DESC
    """, conn)
    st.dataframe(tier_df, use_container_width=True, hide_index=True)
    if not tier_df.empty:
        st.bar_chart(tier_df.set_index("rider_tier")["avg_earnings"])

    st.subheader("Riders at churn risk")
    churn_scope_clause = f"AND run_id = {selected_run_id}" if scope == "Specific run" else ""
    churn_df = pd.read_sql(f"""
        SELECT run_id, rider_id, rating, acceptance_rate,
               cancellation_rate, total_earnings
        FROM riders r
        WHERE cancellation_rate > 0.15
          AND total_earnings < (
              SELECT AVG(total_earnings) FROM riders r2
              WHERE r2.run_id = r.run_id
          )
          {churn_scope_clause}
        ORDER BY cancellation_rate DESC
        LIMIT 50
    """, conn)
    st.dataframe(churn_df, use_container_width=True, hide_index=True)

conn.close()
