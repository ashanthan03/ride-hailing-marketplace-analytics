-- Ride-Hailing Marketplace Analytics & Optimization Simulator
-- Database schema for persisted simulation runs and analytics.

CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    num_zones           INTEGER NOT NULL,
    num_riders          INTEGER NOT NULL,
    num_requests        INTEGER NOT NULL,
    time_steps          INTEGER NOT NULL,
    allocator_type      TEXT NOT NULL,
    total_revenue       REAL,
    fulfillment_rate    REAL,
    rider_utilization   REAL,
    avg_surge           REAL
);

CREATE TABLE IF NOT EXISTS zones (
    zone_id     INTEGER PRIMARY KEY,
    zone_name   TEXT,
    zone_type   TEXT
);

-- rider_id is unique only within a run; riders are regenerated per run
CREATE TABLE IF NOT EXISTS riders (
    row_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id                  INTEGER REFERENCES simulation_runs(run_id),
    rider_id                INTEGER NOT NULL,
    rating                  REAL,
    acceptance_rate         REAL,
    cancellation_rate       REAL,
    home_zone_id            INTEGER REFERENCES zones(zone_id),
    total_rides_completed   INTEGER DEFAULT 0,
    total_earnings          REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS allocations (
    allocation_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER REFERENCES simulation_runs(run_id),
    time_step           INTEGER NOT NULL,
    zone_id             INTEGER REFERENCES zones(zone_id),
    rider_id            INTEGER,
    allocator_type      TEXT NOT NULL,
    fare                REAL,
    surge_multiplier    REAL,
    was_fulfilled       BOOLEAN,
    rider_score         REAL
);

CREATE TABLE IF NOT EXISTS surge_events (
    surge_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER REFERENCES simulation_runs(run_id),
    time_step           INTEGER,
    zone_id             INTEGER,
    surge               REAL,
    demand_count        INTEGER,
    supply_count        INTEGER
);

CREATE INDEX IF NOT EXISTS idx_allocations_run       ON allocations(run_id);
CREATE INDEX IF NOT EXISTS idx_allocations_allocator ON allocations(allocator_type);
CREATE INDEX IF NOT EXISTS idx_allocations_zone      ON allocations(zone_id);
CREATE INDEX IF NOT EXISTS idx_riders_run            ON riders(run_id, rider_id);
