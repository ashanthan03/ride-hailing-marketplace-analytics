"""
Compares rule-based and adaptive allocator outcomes using Welch's
t-test, Mann-Whitney U, and Cohen's d, with 95% confidence intervals.

Usage:
    python analysis/statistical_comparison.py --metric total_revenue
"""

import argparse
import sys
import os

import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from backend.db import get_connection


def load_metric(conn, metric: str) -> pd.DataFrame:
    query = f"""
        SELECT allocator_type, {metric}
        FROM simulation_runs
        WHERE allocator_type IN ('rule_based', 'rl_qlearning')
    """
    return pd.read_sql(query, conn)


def confidence_interval(data: np.ndarray, confidence: float = 0.95):
    n = len(data)
    mean = np.mean(data)
    sem = stats.sem(data)
    margin = sem * stats.t.ppf((1 + confidence) / 2, n - 1)
    return mean, mean - margin, mean + margin


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(
        ((n1 - 1) * np.var(a, ddof=1) + (n2 - 1) * np.var(b, ddof=1))
        / (n1 + n2 - 2)
    )
    return (np.mean(a) - np.mean(b)) / pooled_std


def compare(metric: str):
    conn = get_connection()
    df = load_metric(conn, metric)
    conn.close()

    rule_based = df[df.allocator_type == "rule_based"][metric].dropna().values
    rl = df[df.allocator_type == "rl_qlearning"][metric].dropna().values

    if len(rule_based) < 2 or len(rl) < 2:
        print(f"Not enough runs yet. rule_based n={len(rule_based)}, "
              f"rl_qlearning n={len(rl)}.")
        return

    print(f"\n=== Comparing metric: {metric} ===\n")

    for label, data in [("rule_based", rule_based), ("rl_qlearning", rl)]:
        mean, lo, hi = confidence_interval(data)
        print(f"{label:14s} n={len(data):3d}  mean={mean:.4f}  "
              f"std={np.std(data, ddof=1):.4f}  95% CI=[{lo:.4f}, {hi:.4f}]")

    t_stat, t_pval = stats.ttest_ind(rl, rule_based, equal_var=False)
    print(f"\nWelch's t-test:      t={t_stat:.3f}  p={t_pval:.5f}")

    u_stat, u_pval = stats.mannwhitneyu(rl, rule_based, alternative="two-sided")
    print(f"Mann-Whitney U test: U={u_stat:.1f}  p={u_pval:.5f}")

    d = cohens_d(rl, rule_based)
    print(f"Cohen's d (effect size): {d:.3f}")

    pct_change = (np.mean(rl) - np.mean(rule_based)) / np.mean(rule_based) * 100
    print(f"\nRL vs rule-based: {pct_change:+.2f}% change in {metric}")

    alpha = 0.05
    if u_pval < alpha:
        print(f"Statistically significant at alpha={alpha} "
              f"(Mann-Whitney U, p={u_pval:.5f})")
    else:
        print(f"Not statistically significant at alpha={alpha} "
              f"(Mann-Whitney U, p={u_pval:.5f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", type=str, default="total_revenue",
                         choices=["total_revenue", "fulfillment_rate",
                                  "rider_utilization", "avg_surge"])
    args = parser.parse_args()
    compare(args.metric)
