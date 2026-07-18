# Allocator Design

## Rule-based allocator

Each available rider in a zone is scored as a weighted combination of
rating, acceptance rate, and cancellation rate:

```
score = 0.6 * rating + 0.3 * acceptance_rate - 0.5 * cancellation_rate
```

Requests are assigned to the highest-scoring available riders first.

## Adaptive allocator (contextual bandit)

The adaptive allocator decides, per zone per time step, whether to
serve or skip the zone's queued demand.

**State**: `(zone_id, round(demand / supply, 1))`. Ratio is capped at
a sentinel value of 10 when supply is zero. The state does not include
time-of-day or the current surge multiplier.

**Actions**: `allocate` or `skip`.

**Reward**:
- `-1` for skipping (or when no supply is available)
- `fare / 200` for each request served, normalized against the
  maximum possible base fare

**Update rule**: incremental reward averaging per state-action pair
(equivalent to a multi-armed bandit update), not a full Q-learning
Bellman backup — there is no next-state value term.

**Exploration**: fixed epsilon-greedy, epsilon = 0.1, no decay.

## Limitations

- State excludes time-of-day and surge, so the allocator cannot learn
  time-based demand patterns or react to the price it influences.
- The skip penalty is flat regardless of how much demand was missed.
- The reward function is revenue-only and does not account for rider
  fairness or utilization balance.
- The policy is not persisted or reused across simulation runs.
- Q-table size grows with the number of distinct `(zone, ratio)` pairs
  encountered; this does not scale to continuous state representations.
