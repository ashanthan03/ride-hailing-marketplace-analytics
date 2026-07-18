# Rapido Intelligent Marketplace Simulator

A ride-hailing marketplace simulation platform that models supply-demand
imbalance, dynamic surge pricing, and rider allocation strategies across
multiple operational zones — with a SQL-backed analytics layer for
rigorous, statistically-grounded comparison of allocation strategies.

**Live app**: [ride-hailing-marketplace-analytics.streamlit.app](https://ride-hailing-marketplace-analytics.streamlit.app)

## Overview

The simulator generates ride requests and rider availability across
configurable zones and time steps, applies a demand-to-supply surge
pricing model, and allocates riders to requests using one of two
strategies:

- **Rule-based allocator** — scores each available rider on a weighted
  combination of rating, acceptance rate, and cancellation rate, and
  assigns the highest-scoring riders first.
- **Adaptive allocator** — a tabular, epsilon-greedy contextual bandit
  that learns, per zone and demand-supply ratio, whether to serve or
  skip incoming demand. See [`docs/RL_DESIGN.md`](docs/RL_DESIGN.md)
  for the full design, including its limitations.

Every simulation run is persisted to a SQLite database, enabling
cross-run analysis: allocator comparison with statistical significance
testing, rider cohort segmentation, surge pricing elasticity, and a
run leaderboard — all queryable through SQL.

## Features

- Interactive Streamlit dashboard with configurable zones, riders,
  request volume, and simulation duration
- Two allocation strategies, selectable at runtime
- Persistent run history stored in SQLite
- **Run History** page — sortable, filterable leaderboard of past runs
- **Allocator Comparison** page — Welch's t-test, Mann-Whitney U test,
  Cohen's d, and 95% confidence intervals comparing allocator outcomes
- **Rider Insights** page — rider quality-tier segmentation and
  churn-risk identification
- **SQL Query Explorer** page — preset analytical queries plus a
  free-text SQL box for ad-hoc analysis

## Tech stack

Python, Streamlit, Pandas, NumPy, Plotly, SciPy, SQLite

## Project structure

```
app.py                          # Main dashboard (Home page)
backend/
├── simulation_engine.py        # Core simulation loop and allocation logic
├── pricing.py                  # Surge pricing model
├── rl_allocator.py             # Adaptive allocator
└── db.py                       # Database persistence layer
pages/
├── 1_Run_History.py            # Historical run leaderboard
├── 2_Allocator_Comparison.py   # Statistical comparison of allocators
├── 3_Rider_Insights.py         # Rider cohort and churn analysis
└── 4_SQL_Query_Explorer.py     # Interactive SQL query tool
sql/
├── schema.sql                  # Database schema
├── queries.sql                 # Analytical queries
└── README.md                   # SQL layer documentation
analysis/
├── experiment_harness.py       # Multi-seed experiment runner
└── statistical_comparison.py   # Command-line statistical comparison
docs/
└── RL_DESIGN.md                # Adaptive allocator design specification
```

## Setup

```bash
git clone https://github.com/ashanthan03/ride-hailing-marketplace-analytics.git
cd ride-hailing-marketplace-analytics
pip install -r requirements.txt
streamlit run app.py
```

The database is created automatically on first run. No manual setup
is required.

## Running statistical experiments

To generate enough runs for a statistically meaningful allocator
comparison:

```bash
python analysis/experiment_harness.py --n-seeds 25
python analysis/statistical_comparison.py --metric total_revenue
python analysis/statistical_comparison.py --metric fulfillment_rate
```

Or use the **Allocator Comparison** page in the dashboard for the same
analysis interactively.

## SQL analytics

See [`sql/README.md`](sql/README.md) for the full schema and query
reference. Highlights include window-function-based leaderboards,
CTEs for run-over-run comparison, and cohort analysis joining rider
and allocation data.

## License

MIT
