# Weather Analysis

## Objective

Describe how observed delivery performance differs across weather conditions. This is a descriptive association analysis, not a causal analysis.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only; test data is not used.
- **Target:** `Time_taken(min)`.
- **Primary dimension:** `Weatherconditions`.
- **Valid-target rule:** include only rows where the target is non-null and numeric.
- **Missing weather treatment:** do not infer a category; exclude missing weather only from category comparisons while retaining those rows in the valid-target population.
- **Fixed slow threshold:** **40 minutes**, using the strict rule `Time_taken(min) > 40`. No weather-specific threshold is calculated.

## Results

- Total training rows: **45,593**.
- Total valid numeric targets: **45,593**.
- Missing/invalid target rows: **0**.
- Valid targets with non-null weather: **44,977**.
- Valid targets excluded because weather is missing: **616**.

## Comparison Across Weather Categories

Median and P90 use continuous linear interpolation with rank `1 + (n - 1) × p`, equivalent to NumPy `percentile(method='linear')`. Groups need at least 30 valid records for comparative interpretation; smaller groups, if present, are descriptive only.

| Weather condition | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| conditions Cloudy | 7,536 | 28.91733015 | 28 | 43 | Meets minimum |
| conditions Fog | 7,654 | 28.91612229 | 28 | 43 | Meets minimum |
| conditions Sandstorms | 7,495 | 25.87551701 | 26 | 38 | Meets minimum |
| conditions Stormy | 7,586 | 25.87081466 | 26 | 37 | Meets minimum |
| conditions Sunny | 7,284 | 21.85694673 | 20 | 33 | Meets minimum |
| conditions Windy | 7,422 | 26.11883589 | 26 | 38 | Meets minimum |

## Slow-Delivery Analysis

All groups use the fixed global threshold of strictly greater than 40 minutes. Each rate is calculated as the slow delivery count divided by all valid deliveries in that weather category; the numerator and denominator are explicit.

| Weather condition | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| conditions Cloudy | 1,118 | 7,536 | 1,118 / 7,536 | 14.8355% | Meets minimum |
| conditions Fog | 1,151 | 7,654 | 1,151 / 7,654 | 15.0379% | Meets minimum |
| conditions Sandstorms | 474 | 7,495 | 474 / 7,495 | 6.3242% | Meets minimum |
| conditions Stormy | 425 | 7,586 | 425 / 7,586 | 5.6024% | Meets minimum |
| conditions Sunny | 337 | 7,284 | 337 / 7,284 | 4.6266% | Meets minimum |
| conditions Windy | 476 | 7,422 | 476 / 7,422 | 6.4134% | Meets minimum |

The fixed threshold classified 3,981 of 44,977 categorized valid-target records as slow; 616 additional valid-target records had missing weather and are not allocated to any weather group.

## SQL vs Python Validation

SQL from `sql/03_weather_analysis.sql` was executed against an in-memory SQLite table loaded from the cleaned training file (SQLite `3.50.4`). Pandas independently grouped the same valid-target population; NumPy computed median/P90 with continuous linear interpolation. Standard SQLite has no built-in `PERCENTILE_CONT`, so the SQL query implements rank interpolation at `1 + (n - 1) × p`.

Counts must match exactly. Floating-point values use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Category | Metric | SQL | Python | Result |
| --- | --- | --- | --- | --- |
| conditions Cloudy | delivery count | 7,536 | 7,536 | MATCH |
| conditions Cloudy | slow delivery count | 1,118 | 1,118 | MATCH |
| conditions Cloudy | mean delivery time | 28.91733015 | 28.91733015 | MATCH |
| conditions Cloudy | median delivery time | 28 | 28 | MATCH |
| conditions Cloudy | p90 delivery time | 43 | 43 | MATCH |
| conditions Cloudy | slow delivery rate | 0.14835456 | 0.14835456 | MATCH |
| conditions Fog | delivery count | 7,654 | 7,654 | MATCH |
| conditions Fog | slow delivery count | 1,151 | 1,151 | MATCH |
| conditions Fog | mean delivery time | 28.91612229 | 28.91612229 | MATCH |
| conditions Fog | median delivery time | 28 | 28 | MATCH |
| conditions Fog | p90 delivery time | 43 | 43 | MATCH |
| conditions Fog | slow delivery rate | 0.15037889 | 0.15037889 | MATCH |
| conditions Sandstorms | delivery count | 7,495 | 7,495 | MATCH |
| conditions Sandstorms | slow delivery count | 474 | 474 | MATCH |
| conditions Sandstorms | mean delivery time | 25.87551701 | 25.87551701 | MATCH |
| conditions Sandstorms | median delivery time | 26 | 26 | MATCH |
| conditions Sandstorms | p90 delivery time | 38 | 38 | MATCH |
| conditions Sandstorms | slow delivery rate | 0.06324216 | 0.06324216 | MATCH |
| conditions Stormy | delivery count | 7,586 | 7,586 | MATCH |
| conditions Stormy | slow delivery count | 425 | 425 | MATCH |
| conditions Stormy | mean delivery time | 25.87081466 | 25.87081466 | MATCH |
| conditions Stormy | median delivery time | 26 | 26 | MATCH |
| conditions Stormy | p90 delivery time | 37 | 37 | MATCH |
| conditions Stormy | slow delivery rate | 0.05602426 | 0.05602426 | MATCH |
| conditions Sunny | delivery count | 7,284 | 7,284 | MATCH |
| conditions Sunny | slow delivery count | 337 | 337 | MATCH |
| conditions Sunny | mean delivery time | 21.85694673 | 21.85694673 | MATCH |
| conditions Sunny | median delivery time | 20 | 20 | MATCH |
| conditions Sunny | p90 delivery time | 33 | 33 | MATCH |
| conditions Sunny | slow delivery rate | 0.04626579 | 0.04626579 | MATCH |
| conditions Windy | delivery count | 7,422 | 7,422 | MATCH |
| conditions Windy | slow delivery count | 476 | 476 | MATCH |
| conditions Windy | mean delivery time | 26.11883589 | 26.11883589 | MATCH |
| conditions Windy | median delivery time | 26 | 26 | MATCH |
| conditions Windy | p90 delivery time | 38 | 38 | MATCH |
| conditions Windy | slow delivery rate | 0.06413366 | 0.06413366 | MATCH |

Grouped delivery counts total 44,977; the remaining 616 valid-target rows have no weather category.

## Interpretation

The metrics describe observed delivery-time differences across weather categories only. conditions Cloudy has 7,536 valid deliveries, mean 28.91733015 minutes, median 28 minutes, and P90 43 minutes; conditions Fog has 7,654 valid deliveries, mean 28.91612229 minutes, median 28 minutes, and P90 43 minutes; conditions Sandstorms has 7,495 valid deliveries, mean 25.87551701 minutes, median 26 minutes, and P90 38 minutes; conditions Stormy has 7,586 valid deliveries, mean 25.87081466 minutes, median 26 minutes, and P90 37 minutes; conditions Sunny has 7,284 valid deliveries, mean 21.85694673 minutes, median 20 minutes, and P90 33 minutes; conditions Windy has 7,422 valid deliveries, mean 26.11883589 minutes, median 26 minutes, and P90 38 minutes. These are associations in the observed data and do not establish that weather causes delivery-time differences. Categories below 30 valid records, if any, are descriptive only and are not ranked or substantively compared.

## Limitations

- This observational comparison does not establish causation.
- Missing weather values are excluded only from weather-group comparison; no category is imputed or inferred.
- Group P90 values describe within-category distributions; the slow classification still uses only the fixed global 40-minute threshold.
- Results cover valid observed targets in the cleaned training data and may not generalize beyond this dataset.
- No traffic, city, vehicle, courier, distance, time-pattern, or combined-factor analysis is included.

Read-only validation: the cleaned training file SHA-256 before/after analysis is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c`; no derived columns were persisted.
