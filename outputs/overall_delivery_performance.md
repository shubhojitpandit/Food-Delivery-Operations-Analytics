# Overall Delivery Performance

## Objective

Establish the baseline delivery-time distribution before examining any explanatory dimensions. This report contains descriptive metrics only.

## Input Data

- **Source dataset:** `data/processed/train_clean.csv`.
- **Rows read:** 45,593.
- **Target column:** `Time_taken(min)`.
- `test_clean.csv` was not used for target performance metrics.
- No source dataset was modified and no derived columns were persisted.

## Valid Target Population

The rule is to include only rows where the target is non-null and numeric. The cleaned target was independently parsed with `pandas.to_numeric(errors='coerce')`; the SQL relation used the numeric target column and filtered to SQLite integer/real types. Invalid or missing target rows are excluded from all delivery metrics.

| Population measure | Value |
| --- | --- |
| Total train rows | 45,593 |
| Valid numeric target rows | 45,593 |
| Missing/invalid target rows | 0 |
| Valid target percentage | 100.000000% |

## Core Metrics

All delivery-time values are in minutes. Percentiles use **continuous linear interpolation** with 1-based rank `1 + (n - 1) × p`, equivalent to NumPy `percentile(method='linear')`.

| Metric | Value | Unit |
| --- | --- | --- |
| Valid record count | 45,593 | count |
| Mean delivery time | 26.2946066282 | minutes |
| Median delivery time | 26 | minutes |
| P75 | 32 | minutes |
| P90 | 40 | minutes |
| Minimum delivery time | 10 | minutes |
| Maximum delivery time | 54 | minutes |

## Slow-Delivery Threshold

- **Fixed threshold:** P90 = **40 minutes** from the complete valid training-target population.
- **Classification rule:** slow when `Time_taken(min) > P90` (strictly greater; ties at P90 are not slow). No subgroup-specific threshold is used.
- **Slow numerator:** 4,037.
- **Denominator:** 45,593 valid target records.
- **Slow-delivery rate:** 4,037 / 45,593 = 8.854429% (8.8544%).

## Distribution Observations

### Percentile points

| Point | Delivery time (minutes) |
| --- | --- |
| P25 | 19 |
| P50 / median | 26 |
| P75 | 32 |
| P90 | 40 |
| P95 | 44 |

- **Distinct observed delivery-time values:** 45.
- **Most frequent observed value(s):** 26 minutes (2,123 records each).
- **Frequency by exact delivery-time value:**

| Delivery time (minutes) | Record count |
| --- | --- |
| 10 | 750 |
| 11 | 757 |
| 12 | 746 |
| 13 | 716 |
| 14 | 739 |
| 15 | 1810 |
| 16 | 1706 |
| 17 | 1696 |
| 18 | 1765 |
| 19 | 1824 |
| 20 | 1640 |
| 21 | 1601 |
| 22 | 1626 |
| 23 | 1643 |
| 24 | 1680 |
| 25 | 2050 |
| 26 | 2123 |
| 27 | 1976 |
| 28 | 1965 |
| 29 | 1956 |
| 30 | 1218 |
| 31 | 1213 |
| 32 | 1124 |
| 33 | 1259 |
| 34 | 1172 |
| 35 | 832 |
| 36 | 852 |
| 37 | 828 |
| 38 | 887 |
| 39 | 847 |
| 40 | 555 |
| 41 | 553 |
| 42 | 561 |
| 43 | 567 |
| 44 | 553 |
| 45 | 241 |
| 46 | 274 |
| 47 | 295 |
| 48 | 277 |
| 49 | 280 |
| 50 | 72 |
| 51 | 94 |
| 52 | 79 |
| 53 | 100 |
| 54 | 91 |

These are descriptive properties of the cleaned target distribution; no distributional cause or business explanation is inferred.

## SQL vs Python Validation

SQL was executed from `sql/01_overall_delivery_performance.sql` against a temporary in-memory SQLite table loaded from the cleaned training CSV. Python independently calculated target metrics with NumPy's linear percentile method. SQLite version: `3.50.4`. Standard SQLite lacks built-in `PERCENTILE_CONT`; the SQL query implements the equivalent continuous linear interpolation over row-numbered target values.

Floating-point metrics match when absolute error is at most `1e-09` or relative error is at most `1e-12` (NumPy `isclose` criterion). Counts must match exactly.

| Metric | SQL | Python | Result |
| --- | --- | --- | --- |
| total train rows | 45,593 | 45,593 | MATCH |
| valid target rows | 45,593 | 45,593 | MATCH |
| missing or invalid target rows | 0 | 0 | MATCH |
| valid target percentage | 100 | 100 | MATCH |
| valid record count | 45,593 | 45,593 | MATCH |
| mean delivery time | 26.2946066282 | 26.2946066282 | MATCH |
| median delivery time | 26 | 26 | MATCH |
| p75 delivery time | 32 | 32 | MATCH |
| p90 delivery time | 40 | 40 | MATCH |
| minimum delivery time | 10 | 10 | MATCH |
| maximum delivery time | 54 | 54 | MATCH |
| slow delivery count | 4,037 | 4,037 | MATCH |
| slow delivery rate | 0.0885442941 | 0.0885442941 | MATCH |

Validation checks:

- Total train rows reconciles exactly at 45,593.
- Valid target rows reconciles exactly at 45,593.
- Missing/invalid target rows reconciles exactly at 0.
- Valid metric record count reconciles exactly at 45,593.
- Slow-delivery count reconciles exactly at 4,037.
- All floating-point metrics match within absolute tolerance 1e-09 or relative tolerance 1e-12.
- The slow count uses the overall P90 and strict greater-than comparison; ties at P90 are excluded.
- SHA-256 checks confirm all raw and processed source files are unchanged.
- The cleaned training schema is unchanged; no derived columns were persisted.

### Source file integrity

| File | SHA-256 before | SHA-256 after | Unchanged |
| --- | --- | --- | --- |
| data/raw/train.csv | `d293b6fc7157aef30fb34301216a3432ec895d407ce2ea9edddf942b416cdde1` | `d293b6fc7157aef30fb34301216a3432ec895d407ce2ea9edddf942b416cdde1` | Yes |
| data/raw/test.csv | `7c1b00ca0dac95cc2d969e41bfb952e011dee37206ef6d3c9fa74429647a2ba8` | `7c1b00ca0dac95cc2d969e41bfb952e011dee37206ef6d3c9fa74429647a2ba8` | Yes |
| data/raw/Sample_Submission.csv | `8df327bc95ce263475455744fae5292c271d2f04256dd224dbd859718acdb21a` | `8df327bc95ce263475455744fae5292c271d2f04256dd224dbd859718acdb21a` | Yes |
| data/processed/train_clean.csv | `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` | `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` | Yes |
| data/processed/test_clean.csv | `fa2f8dcfccbff1ea8b152490999c4422bfd484758a352d3e5a81ca63771b1f44` | `fa2f8dcfccbff1ea8b152490999c4422bfd484758a352d3e5a81ca63771b1f44` | Yes |

## Interpretation

The cleaned training set contains 45,593 valid delivery-time records. The observed delivery times range from 10 to 54 minutes; the mean is 26.2946066282, the median is 26, and P90 is 40 minutes. Under the predefined strict `>` rule, 4,037 of 45,593 records (8.8544%) are classified as slow. These statements describe the computed target distribution only.

## Limitations

- The target population is limited to valid observed target values in the cleaned training file; it does not include test records.
- The P90 threshold is distribution-defined for this training population and depends on the specified continuous linear percentile convention.
- SQLite percentile results are computed by the documented row-rank interpolation because standard SQLite does not supply `PERCENTILE_CONT`.
- This baseline is descriptive and observational. It does not explain the observed values or establish causes.
- No explanatory dimensions or business recommendations are included.
