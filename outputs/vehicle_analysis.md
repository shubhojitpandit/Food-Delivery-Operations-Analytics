# Vehicle Analysis

## Objective

Describe observed delivery-performance differences across vehicle type and vehicle condition as two separate dimensions. No causal interpretation is made.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only.
- **Target:** `Time_taken(min)`, included only when non-null and numeric.
- **Dimensions:** `Type_of_vehicle` and `Vehicle_condition`, analyzed separately.
- **Slow threshold:** fixed at 40 minutes from Step 5.1; a slow delivery is strictly `Time_taken(min) > 40`. No dimension-specific threshold was calculated.
- Continuous linear interpolation was used for median and P90: rank `1 + (n - 1) × p`.
- At least 30 valid deliveries are required for rankings or substantive comparisons; smaller groups, if any, are descriptive only.

Total train rows: **45,593**; valid numeric targets: **45,593**; missing/invalid target rows: **0**.

## Vehicle Type Analysis

### Results

- Valid targets overall: **45,593**.
- Valid targets with non-missing Type_of_vehicle: **45,593**.
- Valid targets excluded because Type_of_vehicle is missing: **0**.
- Missing values are not inferred; the excluded rows remain in the overall target population.
- The dimension is compared as categorical values; no ordinal meaning is imposed.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| bicycle | 68 | 26.42647059 | 26 | 39 | Meets minimum; ranked |
| electric_scooter | 3,814 | 24.47011012 | 24 | 37 | Meets minimum; ranked |
| motorcycle | 26,435 | 27.6056743 | 26 | 42 | Meets minimum; ranked |
| scooter | 15,276 | 24.48075412 | 24 | 37 | Meets minimum; ranked |

### Rankings

#### Fastest by mean delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | electric_scooter | 3,814 | 24.47011012 |
| 2 | scooter | 15,276 | 24.48075412 |
| 3 | bicycle | 68 | 26.42647059 |
| 4 | motorcycle | 26,435 | 27.6056743 |

#### Slowest by mean delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | motorcycle | 26,435 | 27.6056743 |
| 2 | bicycle | 68 | 26.42647059 |
| 3 | scooter | 15,276 | 24.48075412 |
| 4 | electric_scooter | 3,814 | 24.47011012 |

#### Fastest by median delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | electric_scooter | 3,814 | 24 |
| 1 | scooter | 15,276 | 24 |
| 3 | bicycle | 68 | 26 |
| 3 | motorcycle | 26,435 | 26 |

#### Slowest by median delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | bicycle | 68 | 26 |
| 1 | motorcycle | 26,435 | 26 |
| 3 | electric_scooter | 3,814 | 24 |
| 3 | scooter | 15,276 | 24 |

#### Lowest slow-delivery rate

| Rank | Category | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | electric_scooter | 3,814 | 4.7457% |
| 2 | scooter | 15,276 | 4.8507% |
| 3 | bicycle | 68 | 5.8824% |
| 4 | motorcycle | 26,435 | 11.7685% |

#### Highest slow-delivery rate

| Rank | Category | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | motorcycle | 26,435 | 11.7685% |
| 2 | bicycle | 68 | 5.8824% |
| 3 | scooter | 15,276 | 4.8507% |
| 4 | electric_scooter | 3,814 | 4.7457% |

### Slow-Delivery Analysis

The fixed global threshold is strictly greater than 40 minutes. Slow-delivery rate = slow deliveries in the group / all valid deliveries in the group; numerator and denominator are displayed.

| Category | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| bicycle | 4 | 68 | 4 / 68 | 5.8824% | Meets minimum; ranked |
| electric_scooter | 181 | 3,814 | 181 / 3,814 | 4.7457% | Meets minimum; ranked |
| motorcycle | 3,111 | 26,435 | 3,111 / 26,435 | 11.7685% | Meets minimum; ranked |
| scooter | 741 | 15,276 | 741 / 15,276 | 4.8507% | Meets minimum; ranked |

Category counts sum to 45,593 valid-target records.

## Vehicle Condition Analysis

### Results

- Valid targets overall: **45,593**.
- Valid targets with non-missing Vehicle_condition: **45,593**.
- Valid targets excluded because Vehicle_condition is missing: **0**.
- Missing values are not inferred; the excluded rows remain in the overall target population.
- The dimension is compared as categorical values; no ordinal meaning is imposed.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| 0 | 15,009 | 30.07222333 | 28 | 44 | Meets minimum; ranked |
| 1 | 15,030 | 24.35508982 | 24 | 37 | Meets minimum; ranked |
| 2 | 15,034 | 24.45543435 | 24 | 37 | Meets minimum; ranked |
| 3 | 520 | 26.49230769 | 26 | 39 | Meets minimum; ranked |

### Rankings

#### Fastest by mean delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | 1 | 15,030 | 24.35508982 |
| 2 | 2 | 15,034 | 24.45543435 |
| 3 | 3 | 520 | 26.49230769 |
| 4 | 0 | 15,009 | 30.07222333 |

#### Slowest by mean delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | 0 | 15,009 | 30.07222333 |
| 2 | 3 | 520 | 26.49230769 |
| 3 | 2 | 15,034 | 24.45543435 |
| 4 | 1 | 15,030 | 24.35508982 |

#### Fastest by median delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | 1 | 15,030 | 24 |
| 1 | 2 | 15,034 | 24 |
| 3 | 3 | 520 | 26 |
| 4 | 0 | 15,009 | 28 |

#### Slowest by median delivery time

| Rank | Category | Delivery count | Value (minutes) |
| --- | --- | --- | --- |
| 1 | 0 | 15,009 | 28 |
| 2 | 3 | 520 | 26 |
| 3 | 1 | 15,030 | 24 |
| 3 | 2 | 15,034 | 24 |

#### Lowest slow-delivery rate

| Rank | Category | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | 2 | 15,034 | 4.7359% |
| 2 | 1 | 15,030 | 4.8170% |
| 3 | 3 | 520 | 8.6538% |
| 4 | 0 | 15,009 | 17.0298% |

#### Highest slow-delivery rate

| Rank | Category | Delivery count | Slow-delivery rate |
| --- | --- | --- | --- |
| 1 | 0 | 15,009 | 17.0298% |
| 2 | 3 | 520 | 8.6538% |
| 3 | 1 | 15,030 | 4.8170% |
| 4 | 2 | 15,034 | 4.7359% |

### Slow-Delivery Analysis

The fixed global threshold is strictly greater than 40 minutes. Slow-delivery rate = slow deliveries in the group / all valid deliveries in the group; numerator and denominator are displayed.

| Category | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| 0 | 2,556 | 15,009 | 2,556 / 15,009 | 17.0298% | Meets minimum; ranked |
| 1 | 724 | 15,030 | 724 / 15,030 | 4.8170% | Meets minimum; ranked |
| 2 | 712 | 15,034 | 712 / 15,034 | 4.7359% | Meets minimum; ranked |
| 3 | 45 | 520 | 45 / 520 | 8.6538% | Meets minimum; ranked |

Category counts sum to 45,593 valid-target records.

## SQL vs Python Validation

SQL was executed from `sql/05_vehicle_analysis.sql` against an in-memory SQLite table (version `3.50.4`). Python independently grouped each dimension with Pandas and calculated median/P90 using NumPy's `percentile(method='linear')`. Standard SQLite does not provide built-in `PERCENTILE_CONT`; the SQL implements the same continuous rank interpolation.

Counts and qualifying-group rankings must match exactly. Floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Dimension | Category | Metric | SQL | Python | Result |
| --- | --- | --- | --- | --- | --- |
| Type_of_vehicle | bicycle | delivery count | 68 | 68 | MATCH |
| Type_of_vehicle | bicycle | slow delivery count | 4 | 4 | MATCH |
| Type_of_vehicle | bicycle | mean delivery time | 26.42647059 | 26.42647059 | MATCH |
| Type_of_vehicle | bicycle | median delivery time | 26 | 26 | MATCH |
| Type_of_vehicle | bicycle | p90 delivery time | 39 | 39 | MATCH |
| Type_of_vehicle | bicycle | slow delivery rate | 0.05882353 | 0.05882353 | MATCH |
| Type_of_vehicle | bicycle | fastest mean rank | 3 | 3 | MATCH |
| Type_of_vehicle | bicycle | slowest mean rank | 2 | 2 | MATCH |
| Type_of_vehicle | bicycle | fastest median rank | 3 | 3 | MATCH |
| Type_of_vehicle | bicycle | slowest median rank | 1 | 1 | MATCH |
| Type_of_vehicle | bicycle | lowest slow rate rank | 3 | 3 | MATCH |
| Type_of_vehicle | bicycle | highest slow rate rank | 2 | 2 | MATCH |
| Type_of_vehicle | electric_scooter | delivery count | 3,814 | 3,814 | MATCH |
| Type_of_vehicle | electric_scooter | slow delivery count | 181 | 181 | MATCH |
| Type_of_vehicle | electric_scooter | mean delivery time | 24.47011012 | 24.47011012 | MATCH |
| Type_of_vehicle | electric_scooter | median delivery time | 24 | 24 | MATCH |
| Type_of_vehicle | electric_scooter | p90 delivery time | 37 | 37 | MATCH |
| Type_of_vehicle | electric_scooter | slow delivery rate | 0.04745674 | 0.04745674 | MATCH |
| Type_of_vehicle | electric_scooter | fastest mean rank | 1 | 1 | MATCH |
| Type_of_vehicle | electric_scooter | slowest mean rank | 4 | 4 | MATCH |
| Type_of_vehicle | electric_scooter | fastest median rank | 1 | 1 | MATCH |
| Type_of_vehicle | electric_scooter | slowest median rank | 3 | 3 | MATCH |
| Type_of_vehicle | electric_scooter | lowest slow rate rank | 1 | 1 | MATCH |
| Type_of_vehicle | electric_scooter | highest slow rate rank | 4 | 4 | MATCH |
| Type_of_vehicle | motorcycle | delivery count | 26,435 | 26,435 | MATCH |
| Type_of_vehicle | motorcycle | slow delivery count | 3,111 | 3,111 | MATCH |
| Type_of_vehicle | motorcycle | mean delivery time | 27.6056743 | 27.6056743 | MATCH |
| Type_of_vehicle | motorcycle | median delivery time | 26 | 26 | MATCH |
| Type_of_vehicle | motorcycle | p90 delivery time | 42 | 42 | MATCH |
| Type_of_vehicle | motorcycle | slow delivery rate | 0.11768489 | 0.11768489 | MATCH |
| Type_of_vehicle | motorcycle | fastest mean rank | 4 | 4 | MATCH |
| Type_of_vehicle | motorcycle | slowest mean rank | 1 | 1 | MATCH |
| Type_of_vehicle | motorcycle | fastest median rank | 3 | 3 | MATCH |
| Type_of_vehicle | motorcycle | slowest median rank | 1 | 1 | MATCH |
| Type_of_vehicle | motorcycle | lowest slow rate rank | 4 | 4 | MATCH |
| Type_of_vehicle | motorcycle | highest slow rate rank | 1 | 1 | MATCH |
| Type_of_vehicle | scooter | delivery count | 15,276 | 15,276 | MATCH |
| Type_of_vehicle | scooter | slow delivery count | 741 | 741 | MATCH |
| Type_of_vehicle | scooter | mean delivery time | 24.48075412 | 24.48075412 | MATCH |
| Type_of_vehicle | scooter | median delivery time | 24 | 24 | MATCH |
| Type_of_vehicle | scooter | p90 delivery time | 37 | 37 | MATCH |
| Type_of_vehicle | scooter | slow delivery rate | 0.04850746 | 0.04850746 | MATCH |
| Type_of_vehicle | scooter | fastest mean rank | 2 | 2 | MATCH |
| Type_of_vehicle | scooter | slowest mean rank | 3 | 3 | MATCH |
| Type_of_vehicle | scooter | fastest median rank | 1 | 1 | MATCH |
| Type_of_vehicle | scooter | slowest median rank | 3 | 3 | MATCH |
| Type_of_vehicle | scooter | lowest slow rate rank | 2 | 2 | MATCH |
| Type_of_vehicle | scooter | highest slow rate rank | 3 | 3 | MATCH |
| Vehicle_condition | 0 | delivery count | 15,009 | 15,009 | MATCH |
| Vehicle_condition | 0 | slow delivery count | 2,556 | 2,556 | MATCH |
| Vehicle_condition | 0 | mean delivery time | 30.07222333 | 30.07222333 | MATCH |
| Vehicle_condition | 0 | median delivery time | 28 | 28 | MATCH |
| Vehicle_condition | 0 | p90 delivery time | 44 | 44 | MATCH |
| Vehicle_condition | 0 | slow delivery rate | 0.17029782 | 0.17029782 | MATCH |
| Vehicle_condition | 0 | fastest mean rank | 4 | 4 | MATCH |
| Vehicle_condition | 0 | slowest mean rank | 1 | 1 | MATCH |
| Vehicle_condition | 0 | fastest median rank | 4 | 4 | MATCH |
| Vehicle_condition | 0 | slowest median rank | 1 | 1 | MATCH |
| Vehicle_condition | 0 | lowest slow rate rank | 4 | 4 | MATCH |
| Vehicle_condition | 0 | highest slow rate rank | 1 | 1 | MATCH |
| Vehicle_condition | 1 | delivery count | 15,030 | 15,030 | MATCH |
| Vehicle_condition | 1 | slow delivery count | 724 | 724 | MATCH |
| Vehicle_condition | 1 | mean delivery time | 24.35508982 | 24.35508982 | MATCH |
| Vehicle_condition | 1 | median delivery time | 24 | 24 | MATCH |
| Vehicle_condition | 1 | p90 delivery time | 37 | 37 | MATCH |
| Vehicle_condition | 1 | slow delivery rate | 0.04817033 | 0.04817033 | MATCH |
| Vehicle_condition | 1 | fastest mean rank | 1 | 1 | MATCH |
| Vehicle_condition | 1 | slowest mean rank | 4 | 4 | MATCH |
| Vehicle_condition | 1 | fastest median rank | 1 | 1 | MATCH |
| Vehicle_condition | 1 | slowest median rank | 3 | 3 | MATCH |
| Vehicle_condition | 1 | lowest slow rate rank | 2 | 2 | MATCH |
| Vehicle_condition | 1 | highest slow rate rank | 3 | 3 | MATCH |
| Vehicle_condition | 2 | delivery count | 15,034 | 15,034 | MATCH |
| Vehicle_condition | 2 | slow delivery count | 712 | 712 | MATCH |
| Vehicle_condition | 2 | mean delivery time | 24.45543435 | 24.45543435 | MATCH |
| Vehicle_condition | 2 | median delivery time | 24 | 24 | MATCH |
| Vehicle_condition | 2 | p90 delivery time | 37 | 37 | MATCH |
| Vehicle_condition | 2 | slow delivery rate | 0.04735932 | 0.04735932 | MATCH |
| Vehicle_condition | 2 | fastest mean rank | 2 | 2 | MATCH |
| Vehicle_condition | 2 | slowest mean rank | 3 | 3 | MATCH |
| Vehicle_condition | 2 | fastest median rank | 1 | 1 | MATCH |
| Vehicle_condition | 2 | slowest median rank | 3 | 3 | MATCH |
| Vehicle_condition | 2 | lowest slow rate rank | 1 | 1 | MATCH |
| Vehicle_condition | 2 | highest slow rate rank | 4 | 4 | MATCH |
| Vehicle_condition | 3 | delivery count | 520 | 520 | MATCH |
| Vehicle_condition | 3 | slow delivery count | 45 | 45 | MATCH |
| Vehicle_condition | 3 | mean delivery time | 26.49230769 | 26.49230769 | MATCH |
| Vehicle_condition | 3 | median delivery time | 26 | 26 | MATCH |
| Vehicle_condition | 3 | p90 delivery time | 39 | 39 | MATCH |
| Vehicle_condition | 3 | slow delivery rate | 0.08653846 | 0.08653846 | MATCH |
| Vehicle_condition | 3 | fastest mean rank | 3 | 3 | MATCH |
| Vehicle_condition | 3 | slowest mean rank | 2 | 2 | MATCH |
| Vehicle_condition | 3 | fastest median rank | 3 | 3 | MATCH |
| Vehicle_condition | 3 | slowest median rank | 2 | 2 | MATCH |
| Vehicle_condition | 3 | lowest slow rate rank | 3 | 3 | MATCH |
| Vehicle_condition | 3 | highest slow rate rank | 2 | 2 | MATCH |

Both dimension-specific category counts reconcile to their valid target rows after only the relevant missing dimension values are excluded. Ranking consistency was checked for mean, median, and slow-delivery rate in both directions; groups below the minimum are not ranked.

## Interpretation

The reported metrics and rankings describe observed associations for vehicle type and vehicle condition separately. All rankings are accompanied by delivery counts and distribution metrics. They do not establish that vehicle type or vehicle condition causes faster or slower delivery. Vehicle condition is treated as categorical; no ordered or causal meaning is assigned to its numeric labels.

## Limitations

- This is an observational, unadjusted comparison; other dimensions are not analyzed here.
- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision.
- Missing vehicle type and missing vehicle condition are excluded separately from their own group comparisons and are not inferred.
- Group P90 is descriptive; slow-delivery classification uses the fixed global threshold of > 40 minutes.
- Findings are limited to valid targets in the cleaned training data.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the input schema is unchanged and no derived columns were persisted.
