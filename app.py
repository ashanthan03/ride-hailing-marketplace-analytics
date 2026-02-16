import streamlit as st
import plotly.express as px
import pandas as pd
from backend.simulation_engine import run_simulation

st.set_page_config(page_title="Rapido Operations Dashboard", layout="wide")

st.title("🚀 Rapido Intelligent Marketplace Simulator")

# =============================
# Sidebar Controls
# =============================
st.sidebar.header("Simulation Controls")

num_zones = st.sidebar.slider("Zones", 4, 25, 16)
num_riders = st.sidebar.slider("Riders", 100, 2000, 800)
num_requests = st.sidebar.slider("Requests", 1000, 15000, 6000)
time_steps = st.sidebar.slider("Time Steps", 20, 100, 60)

if st.button("Run Simulation"):

    df, surge_df, revenue, fulfillment_rate, utilization = run_simulation(
        num_zones,
        num_riders,
        num_requests,
        time_steps,
        use_rl=False
    )

    # =============================
    # KPI Section
    # =============================
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Revenue", f"₹ {round(revenue, 2)}")
    col2.metric("Fulfillment Rate", f"{round(fulfillment_rate * 100, 2)} %")
    col3.metric("Rider Utilization", f"{round(utilization * 100, 2)} %")

    # =============================
    # Revenue Over Time
    # =============================
    st.subheader("Revenue Over Time")
    revenue_time = df.groupby("time_step")["fare"].sum()
    st.line_chart(revenue_time)

    # =============================
    # Demand vs Supply Imbalance
    # =============================
    st.subheader("Demand vs Supply Imbalance")

    demand_per_zone = df.groupby("zone_id").size()
    avg_supply = num_riders / num_zones

    imbalance_df = demand_per_zone.reset_index()
    imbalance_df.columns = ["zone_id", "completed_rides"]
    imbalance_df["avg_supply"] = avg_supply
    imbalance_df["imbalance_ratio"] = imbalance_df["completed_rides"] / avg_supply

    st.bar_chart(imbalance_df.set_index("zone_id")["imbalance_ratio"])

    # =============================
    # Surge Effectiveness
    # =============================
    st.subheader("Surge Effectiveness")

    avg_surge = surge_df["surge"].mean()
    high_surge_zones = surge_df[surge_df["surge"] > 1.5]["zone_id"].nunique()

    col4, col5 = st.columns(2)
    col4.metric("Average Surge Multiplier", round(avg_surge, 2))
    col5.metric("High Surge Zones (>1.5x)", high_surge_zones)

    # =============================
    # Revenue vs Rider Count Curve
    # =============================
    st.subheader("Revenue vs Rider Count")

    rider_range = range(200, 2001, 300)
    revenues = []

    for r in rider_range:
        _, _, rev_temp, _, _ = run_simulation(
            num_zones,
            r,
            num_requests,
            time_steps,
            use_rl=False
        )
        revenues.append(rev_temp)

    curve_df = pd.DataFrame({
        "Riders": list(rider_range),
        "Revenue": revenues
    })

    fig_curve = px.line(curve_df, x="Riders", y="Revenue", markers=True)
    st.plotly_chart(fig_curve, use_container_width=True)

    # =============================
    # Surge Intensity Heatmap
    # =============================
    st.subheader("Average Surge Intensity Heatmap")

    avg_surge_zone = surge_df.groupby("zone_id")["surge"].mean().reset_index()

    grid_size = int(num_zones ** 0.5)

    avg_surge_zone["row"] = avg_surge_zone["zone_id"] // grid_size
    avg_surge_zone["col"] = avg_surge_zone["zone_id"] % grid_size

    heatmap_data = avg_surge_zone.pivot(
        index="row",
        columns="col",
        values="surge"
    ).fillna(1)

    fig_heat = px.imshow(
        heatmap_data,
        text_auto=True,
        color_continuous_scale="OrRd",
        aspect="auto"
    )

    st.plotly_chart(fig_heat, use_container_width=True)

    # =============================
    # Executive Insights (Improved)
    # =============================
    st.markdown("### 📊 Executive Insights")

    insights_triggered = False

    if fulfillment_rate < 0.8:
        st.warning("Low fulfillment rate detected. Consider increasing rider supply.")
        insights_triggered = True

    if utilization < 0.4:
        st.info("Low rider utilization detected. Oversupply may be reducing surge and revenue.")
        insights_triggered = True

    if avg_surge > 1.8:
        st.success("High surge conditions detected. Revenue optimized but customer wait times may increase.")
        insights_triggered = True

    if not insights_triggered:
        st.success("Marketplace is balanced. Supply and demand are operating efficiently.")
