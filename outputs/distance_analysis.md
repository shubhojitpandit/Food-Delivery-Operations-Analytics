# Distance / Geographic Analysis

## Objective

Describe the observed association between approximate straight-line geographic distance and delivery performance. Distance is not route, road-network, driving, or travelled distance.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only.
- **Target population:** non-null numeric `Time_taken(min)` records.
- **Coordinates:** restaurant and delivery latitude/longitude fields only.
- **Slow threshold:** fixed at 40 minutes; slow means strictly `Time_taken(min) > 40`.
- **Percentiles:** continuous linear interpolation at rank `1 + (n - 1) × p`.
- **Minimum band size:** 30 records for ranking or substantive comparison; smaller bands are descriptive.
- Total train rows: **45,593**; valid numeric targets: **45,593**.

## Coordinate Data Quality

A row is coordinate-valid only if all four values are numeric and satisfy latitude [-90, 90] and longitude [-180, 180]. The counts below are row-level exclusions where noted; per-field counts are also shown.

| Coordinate field / row set | Valid coordinate rows / values | Missing rows / values | Invalid coordinate rows | Non-numeric rows / values | Out-of-range rows / values | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Any of four coordinates | 45,593 | 0 | 0 | 0 | 0 | — | — |
| Restaurant_latitude | 45,593 | 0 | — | 0 | 0 | -30.905562 | 30.914057 |
| Restaurant_longitude | 45,593 | 0 | — | 0 | 0 | -88.366217 | 88.433452 |
| Delivery_location_latitude | 45,593 | 0 | — | 0 | 0 | 0.01 | 31.054057 |
| Delivery_location_longitude | 45,593 | 0 | — | 0 | 0 | 0.01 | 88.563452 |

- Rows excluded from distance calculation for missing or implausible coordinates: **0**.
- Valid coordinates: **45,593**; missing coordinate rows: **0**; non-numeric coordinate rows: **0**; out-of-range coordinate rows: **0**.
- Combined numeric latitude range: -30.905562 to 31.054057; combined numeric longitude range: -88.366217 to 88.563452.
- No coordinates were repaired or silently removed. A value of 0.01 is within the broad geographic bounds but is reported as a suspicious pattern.

Exact `0.01` values by coordinate field:

| Coordinate field | Values equal to 0.01 |
| --- | --- |
| Restaurant_latitude | 0 |
| Restaurant_longitude | 0 |
| Delivery_location_latitude | 327 |
| Delivery_location_longitude | 327 |

## Haversine Distance Method

For latitude/longitude in radians, let `Δφ` be the latitude difference and `Δλ` the longitude difference. The Haversine term is `a = sin²(Δφ/2) + cos(φ₁) cos(φ₂) sin²(Δλ/2)`; central angle is `c = 2 asin(√a)`; distance is `R × c`.
- Mean Earth radius assumption: **6,371.0088 km**.
- Haversine is calculated in Python for every coordinate-valid row; the SQL independently recalculates it for validation. Values are held only in memory and are not written to the cleaned CSV.
- The result approximates straight-line distance over a spherical Earth; it is not actual road/network or travelled distance.

## Distance Distribution

| Count | Minimum (km) | P25 (km) | Median (km) | P75 (km) | P90 (km) | Maximum (km) | Mean (km) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 45,593 | 1.46506943 | 4.66349958 | 9.26429378 | 13.76399624 | 19.3958335 | 19692.70180715 | 99.30404798 |

- Zero-distance records: **0**.
- Negative distances: **0** (must be zero).
- Missing derived distances among valid targets: **0**.
- Distances greater than 15 km (the predeclared top band): **9,065**; retained and flagged for context rather than removed.
- Of those, rows with a delivery latitude or longitude equal to 0.01: **0**.

## Distance-Band Analysis

Bands are exhaustive, mutually exclusive half-open ranges: **[0,1), [1,2), [2,3), [3,5), [5,10), [10,15), and [15,∞) km**. Exact boundary values enter the band beginning at that boundary. Each coordinate-valid target is assigned to exactly one band.

### Results

| Distance band | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-1 km | 0 | — | — | — | 0 / 0 | — | No records |
| 1-2 km | 4,074 | 21.42439863 | 20 | 30 | 67 / 4,074 | 1.6446% | Meets minimum |
| 2-3 km | 526 | 21.43726236 | 20 | 31 | 8 / 526 | 1.5209% | Meets minimum |
| 3-5 km | 7,564 | 22.58262824 | 22 | 32 | 140 / 7,564 | 1.8509% | Meets minimum |
| 5-10 km | 12,186 | 24.36935828 | 25 | 34 | 371 / 12,186 | 3.0445% | Meets minimum |
| 10-15 km | 12,178 | 29.86582362 | 29 | 43 | 1,974 / 12,178 | 16.2096% | Meets minimum |
| 15+ km | 9,065 | 29.65306122 | 29 | 43 | 1,477 / 9,065 | 16.2934% | Meets minimum |

### Rankings

#### Fastest by mean delivery time

| Rank | Distance band | Delivery count | Mean (min) |
| --- | --- | --- | --- |
| 1 | 1-2 km | 4,074 | 21.42439863 |
| 2 | 2-3 km | 526 | 21.43726236 |
| 3 | 3-5 km | 7,564 | 22.58262824 |
| 4 | 5-10 km | 12,186 | 24.36935828 |
| 5 | 15+ km | 9,065 | 29.65306122 |
| 6 | 10-15 km | 12,178 | 29.86582362 |

#### Slowest by mean delivery time

| Rank | Distance band | Delivery count | Mean (min) |
| --- | --- | --- | --- |
| 1 | 10-15 km | 12,178 | 29.86582362 |
| 2 | 15+ km | 9,065 | 29.65306122 |
| 3 | 5-10 km | 12,186 | 24.36935828 |
| 4 | 3-5 km | 7,564 | 22.58262824 |
| 5 | 2-3 km | 526 | 21.43726236 |
| 6 | 1-2 km | 4,074 | 21.42439863 |

#### Fastest by median delivery time

| Rank | Distance band | Delivery count | Median (min) |
| --- | --- | --- | --- |
| 1 | 1-2 km | 4,074 | 20 |
| 1 | 2-3 km | 526 | 20 |
| 3 | 3-5 km | 7,564 | 22 |
| 4 | 5-10 km | 12,186 | 25 |
| 5 | 10-15 km | 12,178 | 29 |
| 5 | 15+ km | 9,065 | 29 |

#### Slowest by median delivery time

| Rank | Distance band | Delivery count | Median (min) |
| --- | --- | --- | --- |
| 1 | 10-15 km | 12,178 | 29 |
| 1 | 15+ km | 9,065 | 29 |
| 3 | 5-10 km | 12,186 | 25 |
| 4 | 3-5 km | 7,564 | 22 |
| 5 | 1-2 km | 4,074 | 20 |
| 5 | 2-3 km | 526 | 20 |

#### Lowest slow-delivery rate

| Rank | Distance band | Delivery count | Slow rate |
| --- | --- | --- | --- |
| 1 | 2-3 km | 526 | 1.5209% |
| 2 | 1-2 km | 4,074 | 1.6446% |
| 3 | 3-5 km | 7,564 | 1.8509% |
| 4 | 5-10 km | 12,186 | 3.0445% |
| 5 | 10-15 km | 12,178 | 16.2096% |
| 6 | 15+ km | 9,065 | 16.2934% |

#### Highest slow-delivery rate

| Rank | Distance band | Delivery count | Slow rate |
| --- | --- | --- | --- |
| 1 | 15+ km | 9,065 | 16.2934% |
| 2 | 10-15 km | 12,178 | 16.2096% |
| 3 | 5-10 km | 12,186 | 3.0445% |
| 4 | 3-5 km | 7,564 | 1.8509% |
| 5 | 1-2 km | 4,074 | 1.6446% |
| 6 | 2-3 km | 526 | 1.5209% |

### Slow-Delivery Analysis

Slow rate = slow deliveries in the distance band / all valid deliveries in that band. Classification uses the unchanged global rule `Time_taken(min) > 40`.

| Distance band | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| 0-1 km | 0 | 0 | Not defined | — | No records |
| 1-2 km | 67 | 4,074 | 67 / 4,074 | 1.6446% | Meets minimum; ranked |
| 2-3 km | 8 | 526 | 8 / 526 | 1.5209% | Meets minimum; ranked |
| 3-5 km | 140 | 7,564 | 140 / 7,564 | 1.8509% | Meets minimum; ranked |
| 5-10 km | 371 | 12,186 | 371 / 12,186 | 3.0445% | Meets minimum; ranked |
| 10-15 km | 1,974 | 12,178 | 1,974 / 12,178 | 16.2096% | Meets minimum; ranked |
| 15+ km | 1,477 | 9,065 | 1,477 / 9,065 | 16.2934% | Meets minimum; ranked |

## Distance vs Delivery Time

Correlations use valid targets with four plausible numeric coordinates and a calculable Haversine distance. Both are descriptive association measures.

### Pearson Correlation

- Pearson correlation between approximate straight-line distance and delivery time: **-0.00250807**.
- Independently checked with NumPy's correlation matrix and a direct centered-covariance calculation.

### Spearman Correlation

- Spearman rank correlation: **0.31378161**.
- Independently checked by correlating average ranks with NumPy and a direct centered-rank covariance calculation.

Neither coefficient is causal. Straight-line distance does not account for road network, route choice, traffic, road conditions, pickup delay, or geographic barriers, and is only an approximation of actual travel conditions.

## Extreme Distance Check

The following are the 10 largest coordinate-valid distances, shown only for context/data inspection. No records are excluded because of large distance.

| ID | Approx. straight-line distance (km) | Time_taken(min) | City | Road_traffic_density | Weatherconditions | Type_of_vehicle |
| --- | --- | --- | --- | --- | --- | --- |
| 0xbf01 | 19692.70180715 | 28 | Metropolitan | NULL | NULL | scooter |
| 0xc014 | 19688.02848227 | 46 | Metropolitan | Jam | conditions Stormy | motorcycle |
| 0xbf10 | 19683.71474898 | 22 | Metropolitan | Jam | conditions Stormy | motorcycle |
| 0xc012 | 19677.2077312 | 15 | Urban | Low | conditions Cloudy | scooter |
| 0x3ef | 19070.43445074 | 32 | Metropolitan | NULL | NULL | bicycle |
| 0x462 | 19070.36418053 | 15 | Metropolitan | NULL | NULL | motorcycle |
| 0x509 | 19069.1852858 | 29 | Metropolitan | NULL | NULL | bicycle |
| 0x3ed | 19068.27330049 | 44 | Metropolitan | NULL | NULL | electric_scooter |
| 0x481 | 19067.15488338 | 29 | Metropolitan | NULL | NULL | electric_scooter |
| 0x4d7 | 19066.17707742 | 21 | Urban | Jam | conditions Cloudy | motorcycle |

The context columns are reproduced for these top-distance records only; they are not used to form combined-factor groups or draw causal conclusions.

## SQL vs Python Validation

SQL was executed from `sql/08_distance_analysis.sql` against an in-memory SQLite table (version `3.50.4`). Python independently calculated the Haversine distances and distance bands; SQL recalculated the same Haversine values from source coordinates for row-level verification.

Counts and ranks were compared exactly. Floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation area | Checks | Result |
| --- | --- | --- |
| Coordinate quality fields | 31 | MATCH |
| Haversine row-level values | 45,593 distances; max abs diff 5.46e-11 km | MATCH |
| Distance distribution | 13 | MATCH |
| Distance-band metrics and rankings | 81 | MATCH |
| Pearson/Spearman correlations | 4 | MATCH |
| Top-10 records and ordering | 10 | MATCH |

SQL and Python agreed on coordinate filtering, all seven distance-band counts and metrics, ranks, distance-distribution percentiles, both correlations, and top-10 row order. Negative and missing derived distances were checked explicitly; no negative values occurred.

## Interpretation

The band summaries and correlation coefficients describe observed associations between approximate straight-line geographic distance and delivery time. They do not show that distance causes slower delivery or explain delivery performance on its own. The distance measure is not actual road/network or travelled distance.

## Limitations

- Haversine distance assumes a spherical Earth and measures straight-line separation, not a route.
- Straight-line distance does not account for road network, route choice, traffic, road conditions, pickup delay, or geographic barriers.
- Coordinate plausibility bounds are broad. A value may fall inside those bounds yet remain suspicious; exact 0.01 values are reported but not repaired.
- Distances above 15 km are retained in the predeclared upper band and highlighted; the analysis does not classify them as errors or delete them.
- Correlation is descriptive and unadjusted; this step does not combine distance with other explanatory dimensions or establish causation.
- Findings are limited to valid numeric targets and valid coordinate rows in the cleaned training data.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the input schema is unchanged and no derived distance column was persisted.
