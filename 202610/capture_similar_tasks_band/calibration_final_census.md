# Final-bar census (calibrated build)

Sampler: `scripts/dev/capture_related_calibrate` with the final release build.

## Census snapshot (vault commit 6af37e5e, labeled state)


Queries: 496 open tasks across 53 routes, 0 query errors, 0 bad responses.

Closed window pinned at BOB_NOW=2026-10-21 11:50:47.

## Firing rates (top non-self score >= bar)

| Bar | Queries | Share |
| --- | --- | --- |
| 0.70 | 12 | 2.4% |
| 0.60 | 23 | 4.6% |
| 0.55 | 31 | 6.2% |
| 0.50 | 48 | 9.7% |

## Top-band counts at the starting bars

| Band | Queries |
| --- | --- |
| same_title | 2 |
| possible_duplicate | 6 |
| similar | 45 |
| closed_duplicate | 2 |
| hold | 63 |
| no_match | 378 |

Fired: 55. Worksheet rows: 100 (68 unique unordered pairs; 165 directed candidates).

Sampled across band, 0.05 score bin, and closed/open strata; top matches preferred within each stratum. No-match queries are excluded from the worksheet. Raw score counts are not predicted band firing rates: short-query rules still apply.

## Timings (selected executable, ms)

| Draft | Runs | Median | p95 |
| --- | --- | --- | --- |
| qualifying | 30 | 85.6 | 90.2 |
| non_creating | 30 | 3.4 | 4.4 |
| template | 30 | 3.0 | 3.8 |
| spawn_floor | 30 | 2.7 | 3.3 |


## Live vault cross-check (2026-10-21, read-only)


Queries: 489 open tasks across 53 routes, 0 query errors, 0 bad responses.

Closed window pinned at BOB_NOW=2026-10-21 17:32:31.

## Firing rates (top non-self score >= bar)

| Bar | Queries | Share |
| --- | --- | --- |
| 0.70 | 12 | 2.5% |
| 0.60 | 23 | 4.7% |
| 0.55 | 31 | 6.3% |
| 0.50 | 48 | 9.8% |

## Top-band counts at the current bars

| Band | Queries |
| --- | --- |
| same_title | 2 |
| possible_duplicate | 6 |
| similar | 45 |
| closed_duplicate | 2 |
| hold | 65 |
| no_match | 369 |

Fired: 55. Worksheet rows: 100 (69 unique unordered pairs; 167 directed candidates).

Sampled across band, 0.05 score bin, and closed/open strata; top matches preferred within each stratum. No-match queries are excluded from the worksheet. Raw score counts are not predicted band firing rates: short-query rules still apply.

## Timings (selected executable, ms)

| Draft | Runs | Median | p95 |
| --- | --- | --- | --- |
| qualifying | 30 | 87.3 | 94.9 |
| non_creating | 30 | 3.6 | 4.3 |
| template | 30 | 2.9 | 3.5 |
| spawn_floor | 30 | 2.6 | 3.2 |
