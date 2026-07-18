-- Ride-Hailing Marketplace Analytics & Optimization Simulator
-- Analytical queries used by the Streamlit dashboard and offline analysis.


-- ============================================================
-- Allocator comparison
-- ============================================================

SELECT
    allocator_type,
    COUNT(*)                                                   AS total_allocations,
    ROUND(AVG(fare), 2)                                        AS avg_fare,
    ROUND(SUM(CASE WHEN was_fulfilled THEN 1 ELSE 0 END) * 1.0
          / COUNT(*), 4)                                       AS fulfillment_rate,
    ROUND(AVG(rider_score), 3)                                 AS avg_rider_quality_matched
FROM allocations
GROUP BY allocator_type;

SELECT
    run_id,
    allocator_type,
    total_revenue,
    fulfillment_rate,
    RANK() OVER (PARTITION BY allocator_type ORDER BY total_revenue DESC) AS revenue_rank
FROM simulation_runs
ORDER BY allocator_type, revenue_rank;


-- ============================================================
-- Rider cohort analysis
-- ============================================================

SELECT
    CASE
        WHEN r.rating >= 4.7 THEN 'Top Tier'
        WHEN r.rating >= 4.3 THEN 'Mid Tier'
        ELSE 'Low Tier'
    END                                     AS rider_tier,
    COUNT(*)                                AS num_rider_run_pairs,
    ROUND(AVG(r.total_earnings), 2)         AS avg_earnings,
    ROUND(AVG(CASE WHEN a.was_fulfilled
                   THEN 1.0 ELSE 0 END), 4) AS fulfillment_contribution
FROM riders r
JOIN allocations a
    ON r.run_id = a.run_id AND r.rider_id = a.rider_id
GROUP BY rider_tier
ORDER BY avg_earnings DESC;

SELECT
    run_id,
    rider_id,
    rating,
    acceptance_rate,
    cancellation_rate,
    total_earnings
FROM riders r
WHERE cancellation_rate > 0.15
  AND total_earnings < (
      SELECT AVG(total_earnings) FROM riders r2 WHERE r2.run_id = r.run_id
  )
ORDER BY cancellation_rate DESC;


-- ============================================================
-- Surge pricing analysis
-- ============================================================

SELECT
    ROUND(surge_multiplier, 1)                              AS surge_bucket,
    COUNT(*)                                                 AS total_requests,
    ROUND(AVG(CASE WHEN was_fulfilled
                   THEN 1.0 ELSE 0 END), 4)                  AS fulfillment_rate,
    ROUND(AVG(fare), 2)                                      AS avg_fare
FROM allocations
GROUP BY surge_bucket
ORDER BY surge_bucket;

SELECT
    z.zone_type,
    ROUND(AVG(a.surge_multiplier), 2)      AS avg_surge,
    ROUND(AVG(a.fare), 2)                  AS avg_fare,
    COUNT(*)                               AS total_requests
FROM allocations a
JOIN zones z ON a.zone_id = z.zone_id
GROUP BY z.zone_type
ORDER BY avg_surge DESC;


-- ============================================================
-- Scenario leaderboard
-- ============================================================

SELECT
    run_id,
    allocator_type,
    num_riders,
    num_zones,
    num_requests,
    total_revenue,
    fulfillment_rate,
    RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank
FROM simulation_runs
ORDER BY revenue_rank
LIMIT 10;

SELECT
    run_id,
    run_timestamp,
    total_revenue,
    LAG(total_revenue) OVER (ORDER BY run_timestamp) AS previous_run_revenue,
    ROUND(
        total_revenue - LAG(total_revenue) OVER (ORDER BY run_timestamp),
        2
    ) AS revenue_change
FROM simulation_runs
ORDER BY run_timestamp;
