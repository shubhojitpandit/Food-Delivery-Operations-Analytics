# Traffic Analysis

## Objective

Describe how observed delivery performance differs across road traffic density categories. This is a descriptive association analysis, not a causal analysis.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only; test data is not used.
- **Target:** `Time_taken(min)`.
- **Dimension:** `Road_traffic_density`.
- **Valid-target rule:** include only rows with a non-null numeric target.
- **Slow threshold:** fixed at **40 minutes** from Step 5.1; a slow delivery is strictly `Time_taken(min) > 40`.
- The threshold was not recalculated for traffic groups.

## Results

- Total training rows: **45,593**.
- Valid numeric-target rows: **45,593**.
- Missing/invalid target rows: **0**.
- Valid targets with a non-null traffic category: **44,992**.
- Valid targets excluded from category comparisons because traffic is missing: **601**.
- This exclusion applies only to the traffic-category comparison; those records remain in the overall valid-target population.

## Comparison Across Traffic Categories

Percentiles use continuous linear interpolation (rank `1 + (n - 1) × p`, equivalent to NumPy `percentile(method='linear')`). The framework's minimum of 30 valid records is used as an interpretation guardrail.

| Road traffic density | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| High | 4,425 | 27.24 | 27 | 38 | Meets minimum |
| Jam | 14,143 | 31.17662448 | 31 | 44 | Meets minimum |
| Low | 15,477 | 21.2669768 | 20 | 29 | Meets minimum |
| Medium | 10,947 | 26.69964374 | 27 | 38 | Meets minimum |

## Slow-Delivery Analysis

Every category uses the already-fixed global threshold of > 40 minutes. Slow-delivery rate is the slow count divided by all valid target deliveries in that category; numerator and denominator are shown explicitly.

| Road traffic density | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| High | 280 | 4,425 | 280 / 4,425 | 6.3277% | Meets minimum |
| Jam | 2,830 | 14,143 | 2,830 / 14,143 | 20.0099% | Meets minimum |
| Low | 214 | 15,477 | 214 / 15,477 | 1.3827% | Meets minimum |
| Medium | 659 | 10,947 | 659 / 10,947 | 6.0199% | Meets minimum |

- The fixed threshold classified 3,983 of 44,992 categorized valid-target rows as slow. A further 601 valid-target row(s) with missing traffic categories are outside this grouped comparison.

## SQL vs Python Validation

SQL was executed from `sql/02_traffic_analysis.sql` against an in-memory SQLite table loaded from the cleaned training CSV (SQLite `3.50.4`). Python independently grouped the same numeric target population with Pandas and computed median/P90 using NumPy continuous linear interpolation. SQLite has no standard built-in `PERCENTILE_CONT`; the query implements the same rank interpolation by category.

Counts are required to match exactly. Floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Category | Metric | SQL | Python | Result |
| --- | --- | --- | --- | --- |
| High | delivery count | 4,425 | 4,425 | MATCH |
| High | slow delivery count | 280 | 280 | MATCH |
| High | mean delivery time | 27.24 | 27.24 | MATCH |
| High | median delivery time | 27 | 27 | MATCH |
| High | p90 delivery time | 38 | 38 | MATCH |
| High | slow delivery rate | 0.06327684 | 0.06327684 | MATCH |
| Jam | delivery count | 14,143 | 14,143 | MATCH |
| Jam | slow delivery count | 2,830 | 2,830 | MATCH |
| Jam | mean delivery time | 31.17662448 | 31.17662448 | MATCH |
| Jam | median delivery time | 31 | 31 | MATCH |
| Jam | p90 delivery time | 44 | 44 | MATCH |
| Jam | slow delivery rate | 0.20009899 | 0.20009899 | MATCH |
| Low | delivery count | 15,477 | 15,477 | MATCH |
| Low | slow delivery count | 214 | 214 | MATCH |
| Low | mean delivery time | 21.2669768 | 21.2669768 | MATCH |
| Low | median delivery time | 20 | 20 | MATCH |
| Low | p90 delivery time | 29 | 29 | MATCH |
| Low | slow delivery rate | 0.01382697 | 0.01382697 | MATCH |
| Medium | delivery count | 10,947 | 10,947 | MATCH |
| Medium | slow delivery count | 659 | 659 | MATCH |
| Medium | mean delivery time | 26.69964374 | 26.69964374 | MATCH |
| Medium | median delivery time | 27 | 27 | MATCH |
| Medium | p90 delivery time | 38 | 38 | MATCH |
| Medium | slow delivery rate | 0.06019914 | 0.06019914 | MATCH |

- Total train rows: 45,593; valid target rows: 45,593; invalid/missing target rows: 0.
- Valid target rows with non-null traffic: 44,992; valid target rows with missing traffic excluded from groups: 601.
- SQL/Python category counts reconcile to the same eligible population.

## Interpretation

The grouped metrics describe observed delivery-time differences by road traffic category only. High has 4,425 valid deliveries, a mean of 27.24 minutes, a median of 27 minutes, and a P90 of 38 minutes; Jam has 14,143 valid deliveries, a mean of 31.17662448 minutes, a median of 31 minutes, and a P90 of 44 minutes; Low has 15,477 valid deliveries, a mean of 21.2669768 minutes, a median of 20 minutes, and a P90 of 29 minutes; Medium has 10,947 valid deliveries, a mean of 26.69964374 minutes, a median of 27 minutes, and a P90 of 38 minutes. These are associations in the observed data and do not establish that traffic causes the delivery-time differences. Groups below 30 records, if any, are descriptive only and are not substantively compared or ranked.

## Limitations

- The analysis is observational; no causal conclusion is supported.
- Records with missing traffic category are not assigned a fabricated category and are excluded only from grouped traffic comparisons.
- P90 is group-specific for this required comparison; the slow threshold is not. All slow rates use the fixed global 40-minute threshold.
- Results describe valid observed target records in the cleaned training file and may not generalize beyond this dataset.
- Only road traffic density is analyzed in this step; no other explanatory dimensions or combined factors are included.

Read-only validation: SHA-256 of `data/processed/train_clean.csv` is unchanged (`c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c`); cleaned column count remains 23. No derived columns were persisted.
