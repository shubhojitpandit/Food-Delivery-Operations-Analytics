# City Analysis

## Objective

Describe observed delivery-performance differences among city categories. All comparisons are descriptive and observational.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only.
- **Target:** `Time_taken(min)`; valid records have a non-null numeric target.
- **Primary dimension:** `City`.
- **Fixed slow threshold:** 40 minutes, using strict `Time_taken(min) > 40`; no city-specific threshold is calculated.
- City values were read from the cleaned file, where the approved `Metropolitian` → `Metropolitan` standardization has already been applied.

## City Coverage

- Total train rows: **45,593**.
- Total valid targets: **45,593**.
- Missing/invalid target rows: **0**.
- Valid targets with non-null city: **44,393**.
- Valid targets excluded from city comparisons because city is missing: **1,200**.
- Missing city values are not imputed or inferred; those records remain in the overall valid-target population.

## Results

Median and P90 use continuous linear interpolation, rank `1 + (n - 1) × p`, matching NumPy `percentile(method='linear')`. The minimum city sample for ranking or substantive comparison is 30 valid records.

## City Performance Comparison

| City | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| Metropolitan | 34,093 | 27.315226 | 27 | 40 | Meets minimum; ranked |
| Semi-Urban | 164 | 49.73170732 | 49 | 53.7 | Meets minimum; ranked |
| Urban | 10,136 | 22.98401736 | 22 | 36 | Meets minimum; ranked |

### Fastest cities by mean delivery time

| Rank | City | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | Urban | 10,136 | 22.98401736 |
| 2 | Metropolitan | 34,093 | 27.315226 |
| 3 | Semi-Urban | 164 | 49.73170732 |

Values are in minutes; ties share a rank.

### Slowest cities by mean delivery time

| Rank | City | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | Semi-Urban | 164 | 49.73170732 |
| 2 | Metropolitan | 34,093 | 27.315226 |
| 3 | Urban | 10,136 | 22.98401736 |

Values are in minutes; ties share a rank.

### Fastest cities by median delivery time

| Rank | City | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | Urban | 10,136 | 22 |
| 2 | Metropolitan | 34,093 | 27 |
| 3 | Semi-Urban | 164 | 49 |

Values are in minutes; ties share a rank.

### Slowest cities by median delivery time

| Rank | City | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | Semi-Urban | 164 | 49 |
| 2 | Metropolitan | 34,093 | 27 |
| 3 | Urban | 10,136 | 22 |

Values are in minutes; ties share a rank.

### Lowest slow-delivery rate

| Rank | City | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | Urban | 10,136 | 4.7652% |
| 2 | Metropolitan | 34,093 | 9.8349% |
| 3 | Semi-Urban | 164 | 100.0000% |

Rates are shown as percentages; ties share a rank.

### Highest slow-delivery rate

| Rank | City | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | Semi-Urban | 164 | 100.0000% |
| 2 | Metropolitan | 34,093 | 9.8349% |
| 3 | Urban | 10,136 | 4.7652% |

Rates are shown as percentages; ties share a rank.

## Slow-Delivery Analysis

Every city uses the fixed threshold of strictly greater than 40 minutes. Rate = city slow count / all valid deliveries in that city; the numerator and denominator are shown explicitly.

| City | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| Metropolitan | 3,353 | 34,093 | 3,353 / 34,093 | 9.8349% | Meets minimum; ranked |
| Semi-Urban | 164 | 164 | 164 / 164 | 100.0000% | Meets minimum; ranked |
| Urban | 483 | 10,136 | 483 / 10,136 | 4.7652% | Meets minimum; ranked |

## SQL vs Python Validation

SQL from `sql/04_city_analysis.sql` was executed in SQLite `3.50.4` using an in-memory copy of the cleaned train data. Pandas independently reproduced the grouped metrics; NumPy used continuous linear interpolation for medians and P90. Standard SQLite has no built-in `PERCENTILE_CONT`, so the SQL implements the equivalent row-rank interpolation.

Counts and integer ranks must match exactly. Floating metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| City | Metric | SQL | Python | Result |
| --- | --- | --- | --- | --- |
| Metropolitan | delivery count | 34,093 | 34,093 | MATCH |
| Metropolitan | slow delivery count | 3,353 | 3,353 | MATCH |
| Metropolitan | mean delivery time | 27.315226 | 27.315226 | MATCH |
| Metropolitan | median delivery time | 27 | 27 | MATCH |
| Metropolitan | p90 delivery time | 40 | 40 | MATCH |
| Metropolitan | slow delivery rate | 0.09834863 | 0.09834863 | MATCH |
| Metropolitan | fastest mean rank | 2 | 2 | MATCH |
| Metropolitan | slowest mean rank | 2 | 2 | MATCH |
| Metropolitan | fastest median rank | 2 | 2 | MATCH |
| Metropolitan | slowest median rank | 2 | 2 | MATCH |
| Metropolitan | lowest slow rate rank | 2 | 2 | MATCH |
| Metropolitan | highest slow rate rank | 2 | 2 | MATCH |
| Semi-Urban | delivery count | 164 | 164 | MATCH |
| Semi-Urban | slow delivery count | 164 | 164 | MATCH |
| Semi-Urban | mean delivery time | 49.73170732 | 49.73170732 | MATCH |
| Semi-Urban | median delivery time | 49 | 49 | MATCH |
| Semi-Urban | p90 delivery time | 53.7 | 53.7 | MATCH |
| Semi-Urban | slow delivery rate | 1 | 1 | MATCH |
| Semi-Urban | fastest mean rank | 3 | 3 | MATCH |
| Semi-Urban | slowest mean rank | 1 | 1 | MATCH |
| Semi-Urban | fastest median rank | 3 | 3 | MATCH |
| Semi-Urban | slowest median rank | 1 | 1 | MATCH |
| Semi-Urban | lowest slow rate rank | 3 | 3 | MATCH |
| Semi-Urban | highest slow rate rank | 1 | 1 | MATCH |
| Urban | delivery count | 10,136 | 10,136 | MATCH |
| Urban | slow delivery count | 483 | 483 | MATCH |
| Urban | mean delivery time | 22.98401736 | 22.98401736 | MATCH |
| Urban | median delivery time | 22 | 22 | MATCH |
| Urban | p90 delivery time | 36 | 36 | MATCH |
| Urban | slow delivery rate | 0.04765193 | 0.04765193 | MATCH |
| Urban | fastest mean rank | 1 | 1 | MATCH |
| Urban | slowest mean rank | 3 | 3 | MATCH |
| Urban | fastest median rank | 1 | 1 | MATCH |
| Urban | slowest median rank | 3 | 3 | MATCH |
| Urban | lowest slow rate rank | 1 | 1 | MATCH |
| Urban | highest slow rate rank | 3 | 3 | MATCH |

SQL/Python category counts reconcile to 44,393 valid-target rows with city; 1,200 valid-target rows have missing city.
Qualifying-city ranks match for mean, median, and slow-delivery rate in both directions.

## Interpretation

Observed city metrics differ in the displayed summaries and rankings. Rankings are limited to cities with at least 30 valid records and should be read alongside delivery counts, mean, median, P90, and slow-delivery rate. These observed differences do not show that city itself causes delivery performance differences. No causal explanation is made.

## Limitations

- This is an observational, unadjusted city comparison; other dimensions are not analyzed in this step.
- The 30-record minimum is a reporting guardrail and does not guarantee statistical precision.
- Missing city records are excluded only from city-category comparisons.
- Slow delivery uses the globally fixed 40-minute threshold; group medians and P90 values are descriptive city percentiles.
- Results are limited to valid targets in the cleaned training data.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; no columns were persisted.
