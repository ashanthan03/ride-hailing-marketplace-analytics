import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.db import get_connection, init_db

st.set_page_config(page_title="Allocator Comparison", page_icon="⚖️", layout="wide")
st.title("⚖️ Rule-Based vs. Adaptive Allocator Comparison")

init_db()
conn = get_connection()

metric = st.selectbox(
    "Metric to compare",
    ["total_revenue", "fulfillment_rate", "rider_utilization", "avg_surge"]
)

df = pd.read_sql(f"""
    SELECT allocator_type, {metric}
    FROM simulation_runs
    WHERE allocator_type IN ('rule_based', 'rl_qlearning')
""", conn)

rule_based = df[df.allocator_type == "rule_based"][metric].dropna().values
rl = df[df.allocator_type == "rl_qlearning"][metric].dropna().values

if len(rule_based) < 2 or len(rl) < 2:
    st.warning(
        f"Not enough runs to compare statistically. "
        f"rule_based: {len(rule_based)} runs, rl_qlearning: {len(rl)} runs. "
        f"Run experiment_harness.py to generate more."
    )
else:
    def confidence_interval(data, confidence=0.95):
        n = len(data)
        mean = np.mean(data)
        sem = stats.sem(data)
        margin = sem * stats.t.ppf((1 + confidence) / 2, n - 1)
        return mean, mean - margin, mean + margin

    def cohens_d(a, b):
        n1, n2 = len(a), len(b)
        pooled_std = np.sqrt(
            ((n1 - 1) * np.var(a, ddof=1) + (n2 - 1) * np.var(b, ddof=1))
            / (n1 + n2 - 2)
        )
        return (np.mean(a) - np.mean(b)) / pooled_std

    col1, col2 = st.columns(2)
    for label, data, col in [("rule_based", rule_based, col1),
                              ("rl_qlearning", rl, col2)]:
        mean, lo, hi = confidence_interval(data)
        with col:
            st.metric(label, f"{mean:.4f}", help=f"95% CI: [{lo:.4f}, {hi:.4f}]")
            st.caption(f"n={len(data)}, std={np.std(data, ddof=1):.4f}, "
                       f"95% CI=[{lo:.4f}, {hi:.4f}]")

    t_stat, t_pval = stats.ttest_ind(rl, rule_based, equal_var=False)
    u_stat, u_pval = stats.mannwhitneyu(rl, rule_based, alternative="two-sided")
    d = cohens_d(rl, rule_based)
    pct_change = (np.mean(rl) - np.mean(rule_based)) / np.mean(rule_based) * 100

    st.subheader("Statistical test results")
    results_df = pd.DataFrame({
        "Test": ["Welch's t-test", "Mann-Whitney U (primary)"],
        "Statistic": [f"{t_stat:.3f}", f"{u_stat:.1f}"],
        "p-value": [f"{t_pval:.5f}", f"{u_pval:.5f}"],
    })
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.metric("Cohen's d (effect size)", f"{d:.3f}")
    st.metric(f"RL vs rule-based change in {metric}", f"{pct_change:+.2f}%")

    alpha = 0.05
    if u_pval < alpha:
        st.success(
            f"Statistically significant at alpha={alpha} "
            f"(Mann-Whitney U, p={u_pval:.5f})"
        )
    else:
        st.warning(
            f"Not statistically significant at alpha={alpha} "
            f"(Mann-Whitney U, p={u_pval:.5f})"
        )

    st.subheader("Distribution comparison")
    hist_df = pd.DataFrame({
        "rule_based": pd.Series(rule_based),
        "rl_qlearning": pd.Series(rl),
    })
    st.bar_chart(hist_df)

conn.close()
