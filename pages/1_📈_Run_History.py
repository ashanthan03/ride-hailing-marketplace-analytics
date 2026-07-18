import sys
import os
import streamlit as st
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.db import get_connection, init_db

st.set_page_config(page_title="Run History", page_icon="📈", layout="wide")
st.title("📈 Run History & Leaderboard")

init_db()
conn = get_connection()

df = pd.read_sql("""
    SELECT run_id, run_timestamp, allocator_type, num_zones, num_riders,
           num_requests, time_steps, total_revenue, fulfillment_rate,
           rider_utilization, avg_surge
    FROM simulation_runs
    ORDER BY run_timestamp DESC
""", conn)

if df.empty:
    st.info("No simulation runs saved yet. Run a simulation from the Home page.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        allocator_filter = st.multiselect(
            "Allocator type", options=df["allocator_type"].unique().tolist(),
            default=df["allocator_type"].unique().tolist()
        )
    with col2:
        sort_metric = st.selectbox(
            "Sort by", ["total_revenue", "fulfillment_rate",
                        "rider_utilization", "avg_surge", "run_timestamp"]
        )
    with col3:
        sort_desc = st.checkbox("Descending", value=True)

    filtered = df[df["allocator_type"].isin(allocator_filter)]
    filtered = filtered.sort_values(sort_metric, ascending=not sort_desc)

    st.metric("Total runs", len(filtered))
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("Revenue by run")
    chart_source = filtered.sort_values("run_timestamp")
    pivoted = chart_source.pivot_table(
        index="run_timestamp", columns="allocator_type",
        values="total_revenue", aggfunc="mean"
    )
    st.line_chart(pivoted)

conn.close()
