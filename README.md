# 🚀 Ride-Hailing Marketplace Analytics & Optimization Simulator

A data-driven simulation of a ride-hailing marketplace (Rapido/Uber-style system) that models demand-supply imbalance, surge pricing, rider allocation, and revenue optimization.

This project analyzes how rider supply impacts:
- Revenue
- Fulfillment rate
- Rider utilization
- Surge pricing intensity
- Demand-supply imbalance

It also includes an optional Reinforcement Learning-based allocation engine.

---

## 📌 Business Problem

Ride-hailing platforms face constant imbalance between:

- Rider Supply
- Customer Demand

If supply is low:
- Surge increases
- Revenue per ride increases
- Fulfillment rate drops
- Rider utilization spikes

If supply is high:
- Fulfillment improves
- Surge drops
- Revenue stabilizes
- Rider utilization decreases

This simulator models these trade-offs quantitatively.

---

## 🧠 Key Metrics Modeled

- **Total Revenue**
- **Fulfillment Rate (%)**
- **Rider Utilization (%)**
- **Revenue vs Rider Count Curve**
- **Demand vs Supply Imbalance**
- **Surge Intensity Heatmap**

---

## ⚙️ Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Reinforcement Learning (Q-Learning Logic)

---

## 📊 Features

### 1️⃣ Interactive Controls
- Adjust number of zones
- Adjust rider count
- Adjust request volume
- Adjust simulation time steps
- Toggle Reinforcement Learning allocator

### 2️⃣ Revenue Analysis
- Revenue over time
- Revenue vs rider supply curve
- Profit saturation visualization

### 3️⃣ Operational Metrics
- Fulfillment rate
- Rider utilization
- High surge zone detection

### 4️⃣ Surge Heatmap
Visual representation of demand pressure across zones.

---

## 🧮 Core Insight Demonstrated

Example Scenario:

| Riders | Requests | Fulfillment | Utilization | Revenue |
|--------|----------|-------------|-------------|----------|
| 205    | 6000     | ~41%        | ~98%        | ~₹98K    |
| 2000   | 6000     | 100%        | ~24%        | ~₹148K   |

Insights:
- Increasing supply improves fulfillment
- Utilization decreases with excess supply
- Revenue plateaus beyond optimal rider count
- Surge intensity reduces with high supply

---

## ▶️ How To Run

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ride-hailing-marketplace-analytics
