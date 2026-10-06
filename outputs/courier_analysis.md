# Courier Analysis

## Objective

Describe observed delivery-performance differences across delivery-person ratings, delivery-person age bands, and multiple-delivery categories as separate dimensions. No causal interpretation is made.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only.
- **Target:** `Time_taken(min)`, included only when non-null and numeric.
- **Slow threshold:** fixed at 40 minutes from Step 5.1; slow means strictly `Time_taken(min) > 40`.
- Median, P25, P75, and P90 use continuous linear interpolation at rank `1 + (n - 1) × p`.
- A group must contain at least 30 valid targets to be ranked or substantively compared; smaller groups are descriptive only.
- Total train rows: **45,593**; valid numeric targets: **45,593**; missing/invalid targets: **0**.
- Missing courier values remain in the overall valid-target population and are excluded only from the corresponding grouped comparison.

## Delivery Person Ratings

### Data Quality

- Valid-target records with a missing rating: **1,908**.
- Valid-target records with an out-of-range rating: **53** (outside the expected inclusive 1–5 range).
- Primary in-range comparison population: **43,632**.
- All-ratings sensitivity population, including out-of-range values: **43,685**.
- Primary analysis uses the established `rating_out_of_range` flag and the inclusive 1–5 rule; out-of-range values are excluded, not corrected or recoded.

Exact observed non-missing numeric rating values and their valid-target counts:

| Rating value | Valid-target records |
| --- | --- |
| 1 | 38 |
| 2.5 | 20 |
| 2.6 | 22 |
| 2.7 | 22 |
| 2.8 | 19 |
| 2.9 | 19 |
| 3 | 6 |
| 3.1 | 29 |
| 3.2 | 29 |
| 3.3 | 25 |
| 3.4 | 32 |
| 3.5 | 249 |
| 3.6 | 207 |
| 3.7 | 225 |
| 3.8 | 228 |
| 3.9 | 197 |
| 4 | 1,077 |
| 4.1 | 1,430 |
| 4.2 | 1,418 |
| 4.3 | 1,409 |
| 4.4 | 1,361 |
| 4.5 | 3,303 |
| 4.6 | 6,940 |
| 4.7 | 7,142 |
| 4.8 | 7,148 |
| 4.9 | 7,041 |
| 5 | 3,996 |
| 6 | 53 |

### Primary Results

Only exact numeric rating values within 1–5 are included. Values with fewer than 30 records are listed descriptively and are not ranked.

| Rating | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| 1 | 38 | 26 | 26.5 | 34 | Meets minimum; ranked |
| 2.5 | 20 | 37.3 | 35.5 | 43.1 | Small sample; descriptive only |
| 2.6 | 22 | 38.59090909 | 39 | 43 | Small sample; descriptive only |
| 2.7 | 22 | 35.86363636 | 36.5 | 39.9 | Small sample; descriptive only |
| 2.8 | 19 | 36.63157895 | 37 | 42.2 | Small sample; descriptive only |
| 2.9 | 19 | 38.52631579 | 39 | 43 | Small sample; descriptive only |
| 3 | 6 | 32.66666667 | 32.5 | 34 | Small sample; descriptive only |
| 3.1 | 29 | 36.55172414 | 35 | 43.2 | Small sample; descriptive only |
| 3.2 | 29 | 36.34482759 | 36 | 42.2 | Small sample; descriptive only |
| 3.3 | 25 | 36.04 | 36 | 42 | Small sample; descriptive only |
| 3.4 | 32 | 35.71875 | 34 | 42 | Meets minimum; ranked |
| 3.5 | 249 | 37.0562249 | 36 | 43 | Meets minimum; ranked |
| 3.6 | 207 | 37.28985507 | 37 | 43 | Meets minimum; ranked |
| 3.7 | 225 | 37.36 | 37 | 44 | Meets minimum; ranked |
| 3.8 | 228 | 37.10087719 | 37 | 43 | Meets minimum; ranked |
| 3.9 | 197 | 37.49238579 | 37 | 44 | Meets minimum; ranked |
| 4 | 1,077 | 34.7446611 | 34 | 44 | Meets minimum; ranked |
| 4.1 | 1,430 | 34.53006993 | 34 | 44 | Meets minimum; ranked |
| 4.2 | 1,418 | 34.53244006 | 34 | 44 | Meets minimum; ranked |
| 4.3 | 1,409 | 34.62952449 | 34 | 44 | Meets minimum; ranked |
| 4.4 | 1,361 | 34.83468038 | 35 | 44 | Meets minimum; ranked |
| 4.5 | 3,303 | 23.64517106 | 23 | 33.8 | Meets minimum; ranked |
| 4.6 | 6,940 | 24.56959654 | 24 | 37 | Meets minimum; ranked |
| 4.7 | 7,142 | 24.17054046 | 24 | 36 | Meets minimum; ranked |
| 4.8 | 7,148 | 24.02560157 | 23 | 36 | Meets minimum; ranked |
| 4.9 | 7,041 | 24.12313592 | 23 | 36 | Meets minimum; ranked |
| 5 | 3,996 | 25.53128128 | 25 | 39 | Meets minimum; ranked |
### Rankings

#### Fastest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 4.5 | 3,303 | 23.64517106 |
| 2 | 4.8 | 7,148 | 24.02560157 |
| 3 | 4.9 | 7,041 | 24.12313592 |
| 4 | 4.7 | 7,142 | 24.17054046 |
| 5 | 4.6 | 6,940 | 24.56959654 |
| 6 | 5 | 3,996 | 25.53128128 |
| 7 | 1 | 38 | 26 |
| 8 | 4.1 | 1,430 | 34.53006993 |
| 9 | 4.2 | 1,418 | 34.53244006 |
| 10 | 4.3 | 1,409 | 34.62952449 |
| 11 | 4 | 1,077 | 34.7446611 |
| 12 | 4.4 | 1,361 | 34.83468038 |
| 13 | 3.4 | 32 | 35.71875 |
| 14 | 3.5 | 249 | 37.0562249 |
| 15 | 3.8 | 228 | 37.10087719 |
| 16 | 3.6 | 207 | 37.28985507 |
| 17 | 3.7 | 225 | 37.36 |
| 18 | 3.9 | 197 | 37.49238579 |

#### Slowest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 3.9 | 197 | 37.49238579 |
| 2 | 3.7 | 225 | 37.36 |
| 3 | 3.6 | 207 | 37.28985507 |
| 4 | 3.8 | 228 | 37.10087719 |
| 5 | 3.5 | 249 | 37.0562249 |
| 6 | 3.4 | 32 | 35.71875 |
| 7 | 4.4 | 1,361 | 34.83468038 |
| 8 | 4 | 1,077 | 34.7446611 |
| 9 | 4.3 | 1,409 | 34.62952449 |
| 10 | 4.2 | 1,418 | 34.53244006 |
| 11 | 4.1 | 1,430 | 34.53006993 |
| 12 | 1 | 38 | 26 |
| 13 | 5 | 3,996 | 25.53128128 |
| 14 | 4.6 | 6,940 | 24.56959654 |
| 15 | 4.7 | 7,142 | 24.17054046 |
| 16 | 4.9 | 7,041 | 24.12313592 |
| 17 | 4.8 | 7,148 | 24.02560157 |
| 18 | 4.5 | 3,303 | 23.64517106 |

#### Fastest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 4.5 | 3,303 | 23 |
| 1 | 4.8 | 7,148 | 23 |
| 1 | 4.9 | 7,041 | 23 |
| 4 | 4.6 | 6,940 | 24 |
| 4 | 4.7 | 7,142 | 24 |
| 6 | 5 | 3,996 | 25 |
| 7 | 1 | 38 | 26.5 |
| 8 | 3.4 | 32 | 34 |
| 8 | 4 | 1,077 | 34 |
| 8 | 4.1 | 1,430 | 34 |
| 8 | 4.2 | 1,418 | 34 |
| 8 | 4.3 | 1,409 | 34 |
| 13 | 4.4 | 1,361 | 35 |
| 14 | 3.5 | 249 | 36 |
| 15 | 3.6 | 207 | 37 |
| 15 | 3.7 | 225 | 37 |
| 15 | 3.8 | 228 | 37 |
| 15 | 3.9 | 197 | 37 |

#### Slowest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 3.6 | 207 | 37 |
| 1 | 3.7 | 225 | 37 |
| 1 | 3.8 | 228 | 37 |
| 1 | 3.9 | 197 | 37 |
| 5 | 3.5 | 249 | 36 |
| 6 | 4.4 | 1,361 | 35 |
| 7 | 3.4 | 32 | 34 |
| 7 | 4 | 1,077 | 34 |
| 7 | 4.1 | 1,430 | 34 |
| 7 | 4.2 | 1,418 | 34 |
| 7 | 4.3 | 1,409 | 34 |
| 12 | 1 | 38 | 26.5 |
| 13 | 5 | 3,996 | 25 |
| 14 | 4.6 | 6,940 | 24 |
| 14 | 4.7 | 7,142 | 24 |
| 16 | 4.5 | 3,303 | 23 |
| 16 | 4.8 | 7,148 | 23 |
| 16 | 4.9 | 7,041 | 23 |

#### Lowest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | 1 | 38 | 2.6316% |
| 2 | 4.5 | 3,303 | 4.9046% |
| 3 | 4.8 | 7,148 | 5.7918% |
| 4 | 4.7 | 7,142 | 6.0207% |
| 5 | 4.9 | 7,041 | 6.2065% |
| 6 | 4.6 | 6,940 | 6.3112% |
| 7 | 5 | 3,996 | 8.4334% |
| 8 | 4 | 1,077 | 18.4773% |
| 9 | 4.3 | 1,409 | 18.8786% |
| 10 | 4.1 | 1,430 | 19.0210% |
| 11 | 4.2 | 1,418 | 20.3808% |
| 12 | 4.4 | 1,361 | 20.7935% |
| 13 | 3.8 | 228 | 21.0526% |
| 14 | 3.6 | 207 | 21.7391% |
| 15 | 3.5 | 249 | 22.4900% |
| 16 | 3.9 | 197 | 24.8731% |
| 17 | 3.4 | 32 | 25.0000% |
| 18 | 3.7 | 225 | 26.2222% |

#### Highest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | 3.7 | 225 | 26.2222% |
| 2 | 3.4 | 32 | 25.0000% |
| 3 | 3.9 | 197 | 24.8731% |
| 4 | 3.5 | 249 | 22.4900% |
| 5 | 3.6 | 207 | 21.7391% |
| 6 | 3.8 | 228 | 21.0526% |
| 7 | 4.4 | 1,361 | 20.7935% |
| 8 | 4.2 | 1,418 | 20.3808% |
| 9 | 4.1 | 1,430 | 19.0210% |
| 10 | 4.3 | 1,409 | 18.8786% |
| 11 | 4 | 1,077 | 18.4773% |
| 12 | 5 | 3,996 | 8.4334% |
| 13 | 4.6 | 6,940 | 6.3112% |
| 14 | 4.9 | 7,041 | 6.2065% |
| 15 | 4.7 | 7,142 | 6.0207% |
| 16 | 4.8 | 7,148 | 5.7918% |
| 17 | 4.5 | 3,303 | 4.9046% |
| 18 | 1 | 38 | 2.6316% |

### Slow-Delivery Analysis

Slow rate = slow deliveries in the rating group / all valid deliveries in that rating group. The same strict global threshold (> 40 minutes) is used.

| Rating | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate |
| --- | --- | --- | --- | --- |
| 1 | 1 | 38 | 1 / 38 | 2.6316% |
| 2.5 | 7 | 20 | 7 / 20 | 35.0000% |
| 2.6 | 10 | 22 | 10 / 22 | 45.4545% |
| 2.7 | 2 | 22 | 2 / 22 | 9.0909% |
| 2.8 | 4 | 19 | 4 / 19 | 21.0526% |
| 2.9 | 6 | 19 | 6 / 19 | 31.5789% |
| 3 | 0 | 6 | 0 / 6 | 0.0000% |
| 3.1 | 9 | 29 | 9 / 29 | 31.0345% |
| 3.2 | 7 | 29 | 7 / 29 | 24.1379% |
| 3.3 | 5 | 25 | 5 / 25 | 20.0000% |
| 3.4 | 8 | 32 | 8 / 32 | 25.0000% |
| 3.5 | 56 | 249 | 56 / 249 | 22.4900% |
| 3.6 | 45 | 207 | 45 / 207 | 21.7391% |
| 3.7 | 59 | 225 | 59 / 225 | 26.2222% |
| 3.8 | 48 | 228 | 48 / 228 | 21.0526% |
| 3.9 | 49 | 197 | 49 / 197 | 24.8731% |
| 4 | 199 | 1,077 | 199 / 1,077 | 18.4773% |
| 4.1 | 272 | 1,430 | 272 / 1,430 | 19.0210% |
| 4.2 | 289 | 1,418 | 289 / 1,418 | 20.3808% |
| 4.3 | 266 | 1,409 | 266 / 1,409 | 18.8786% |
| 4.4 | 283 | 1,361 | 283 / 1,361 | 20.7935% |
| 4.5 | 162 | 3,303 | 162 / 3,303 | 4.9046% |
| 4.6 | 438 | 6,940 | 438 / 6,940 | 6.3112% |
| 4.7 | 430 | 7,142 | 430 / 7,142 | 6.0207% |
| 4.8 | 414 | 7,148 | 414 / 7,148 | 5.7918% |
| 4.9 | 437 | 7,041 | 437 / 7,041 | 6.2065% |
| 5 | 337 | 3,996 | 337 / 3,996 | 8.4334% |

### Rating Sensitivity Analysis

The sensitivity scenario includes every non-missing numeric rating, including out-of-range values as their original distinct categories. No value is recoded.

| Scenario | Rated deliveries | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate |
| --- | --- | --- | --- | --- | --- | --- |
| Primary: in-range ratings (1-5) | 43,632 | 26.29187294 | 26 | 40 | 3,843 / 43,632 | 8.8078% |
| Sensitivity: all ratings (non-missing; includes out-of-range) | 43,685 | 26.28902369 | 26 | 40 | 3,845 / 43,685 | 8.8016% |

Out-of-range categories in the all-ratings scenario (descriptive only when below the 30-record minimum):

| Original rating value | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 53 | 23.94339623 | 22 | 35.8 | 2 / 53 | 3.7736% | Meets minimum; sensitivity only |

The 27 shared in-range rating categories have identical group counts and delivery metrics in both scenarios; adding out-of-range ratings changes the rated-population aggregate, not the membership of ratings 1–5.

Aggregate change (all non-missing ratings minus primary in-range population): mean -0.00284924 min; median +0.00000000 min; P90 +0.00000000 min; slow rate -0.006108 percentage points.

## Delivery Person Age

### Data Distribution

Age distribution statistics use valid-target records with a non-missing numeric age. The missing count is within the valid-target population.

| Valid age count | Missing age count | Minimum | Maximum | Median | P25 | P75 |
| --- | --- | --- | --- | --- | --- | --- |
| 43,739 | 1,854 | 15 | 50 | 30 | 25 | 35 |

### Age-Band Results

The predefined bands are Under 20, 20–29, 30–39, 40–49, and 50+. Empty bands are shown with zero records; no additional bands were created.

| Age band | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| Under 20 | 38 | 26 | 26.5 | 34 | Meets minimum; ranked |
| 20-29 | 21,635 | 22.98969263 | 22 | 36 | Meets minimum; ranked |
| 30-39 | 22,013 | 29.53459319 | 29 | 42 | Meets minimum; ranked |
| 40-49 | 0 | — | — | — | No valid records |
| 50+ | 53 | 23.94339623 | 22 | 35.8 | Meets minimum; ranked |
### Rankings

#### Fastest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 20-29 | 21,635 | 22.98969263 |
| 2 | 50+ | 53 | 23.94339623 |
| 3 | Under 20 | 38 | 26 |
| 4 | 30-39 | 22,013 | 29.53459319 |

#### Slowest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 30-39 | 22,013 | 29.53459319 |
| 2 | Under 20 | 38 | 26 |
| 3 | 50+ | 53 | 23.94339623 |
| 4 | 20-29 | 21,635 | 22.98969263 |

#### Fastest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 20-29 | 21,635 | 22 |
| 1 | 50+ | 53 | 22 |
| 3 | Under 20 | 38 | 26.5 |
| 4 | 30-39 | 22,013 | 29 |

#### Slowest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 30-39 | 22,013 | 29 |
| 2 | Under 20 | 38 | 26.5 |
| 3 | 20-29 | 21,635 | 22 |
| 3 | 50+ | 53 | 22 |

#### Lowest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | Under 20 | 38 | 2.6316% |
| 2 | 50+ | 53 | 3.7736% |
| 3 | 20-29 | 21,635 | 4.4188% |
| 4 | 30-39 | 22,013 | 13.1241% |

#### Highest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | 30-39 | 22,013 | 13.1241% |
| 2 | 20-29 | 21,635 | 4.4188% |
| 3 | 50+ | 53 | 3.7736% |
| 4 | Under 20 | 38 | 2.6316% |

### Slow-Delivery Analysis

Slow rate = slow deliveries in the age band / all valid deliveries in that age band; the fixed threshold remains strictly > 40 minutes.

| Age band | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate |
| --- | --- | --- | --- | --- |
| Under 20 | 1 | 38 | 1 / 38 | 2.6316% |
| 20-29 | 956 | 21,635 | 956 / 21,635 | 4.4188% |
| 30-39 | 2,889 | 22,013 | 2,889 / 22,013 | 13.1241% |
| 40-49 | 0 | 0 | Not defined | — |
| 50+ | 2 | 53 | 2 / 53 | 3.7736% |

## Multiple Deliveries

### Category Distribution

Valid-target records with missing `multiple_deliveries`: **993**. Distinct observed non-missing values:

| Category label | Delivery count |
| --- | --- |
| 0 | 14,095 |
| 1 | 28,159 |
| 2 | 1,985 |
| 3 | 361 |

### Results

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Sample-size status |
| --- | --- | --- | --- | --- | --- |
| 0 | 14,095 | 22.87626818 | 22 | 35 | Meets minimum; ranked |
| 1 | 28,159 | 26.85588977 | 26 | 39 | Meets minimum; ranked |
| 2 | 1,985 | 40.45491184 | 40 | 48 | Meets minimum; ranked |
| 3 | 361 | 47.8199446 | 48 | 53 | Meets minimum; ranked |
### Rankings

#### Fastest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 0 | 14,095 | 22.87626818 |
| 2 | 1 | 28,159 | 26.85588977 |
| 3 | 2 | 1,985 | 40.45491184 |
| 4 | 3 | 361 | 47.8199446 |

#### Slowest by mean delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 3 | 361 | 47.8199446 |
| 2 | 2 | 1,985 | 40.45491184 |
| 3 | 1 | 28,159 | 26.85588977 |
| 4 | 0 | 14,095 | 22.87626818 |

#### Fastest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 0 | 14,095 | 22 |
| 2 | 1 | 28,159 | 26 |
| 3 | 2 | 1,985 | 40 |
| 4 | 3 | 361 | 48 |

#### Slowest by median delivery time

| Rank | Category | Delivery count | Minutes |
| --- | --- | --- | --- |
| 1 | 3 | 361 | 48 |
| 2 | 2 | 1,985 | 40 |
| 3 | 1 | 28,159 | 26 |
| 4 | 0 | 14,095 | 22 |

#### Lowest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | 0 | 14,095 | 4.5406% |
| 2 | 1 | 28,159 | 7.4008% |
| 3 | 2 | 1,985 | 45.7431% |
| 4 | 3 | 361 | 100.0000% |

#### Highest slow-delivery rate

| Rank | Category | Delivery count | Rate |
| --- | --- | --- | --- |
| 1 | 3 | 361 | 100.0000% |
| 2 | 2 | 1,985 | 45.7431% |
| 3 | 1 | 28,159 | 7.4008% |
| 4 | 0 | 14,095 | 4.5406% |

### Slow-Delivery Analysis

Slow rate = slow deliveries in the category / all valid deliveries in that category; slow remains strictly > 40 minutes.

| Category | Slow count (numerator) | Delivery count (denominator) | Rate calculation | Slow rate |
| --- | --- | --- | --- | --- |
| 0 | 640 | 14,095 | 640 / 14,095 | 4.5406% |
| 1 | 2,084 | 28,159 | 2,084 / 28,159 | 7.4008% |
| 2 | 908 | 1,985 | 908 / 1,985 | 45.7431% |
| 3 | 361 | 361 | 361 / 361 | 100.0000% |

## SQL vs Python Validation

SQL was executed from `sql/06_courier_analysis.sql` against an in-memory SQLite table (version `3.50.4`). Python independently grouped the same valid-target population with Pandas and NumPy's `percentile(method='linear')`. SQLite's query implements equivalent continuous rank interpolation.

Counts and rankings were compared exactly. Floating-point statistics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`. All category-level metrics, eligible-group ranks, the age distribution summary, and both rating sensitivity populations matched.

| Analysis | Groups / scenarios | Metric checks | Ranking checks | Result |
| --- | --- | --- | --- | --- |
| rating_primary | 27 | 162 | 108 | MATCH |
| rating_all | 28 | 168 | 114 | MATCH |
| age_band | 5 | 26 | 24 | MATCH |
| multiple_deliveries | 4 | 24 | 24 | MATCH |
| rating_sensitivity | 2 | 12 | 0 | MATCH |
| Age distribution | 1 | 7 | 0 | MATCH |
| Shared in-range rating pattern | 27 | 162 | 0 | MATCH |

For rating sensitivity, both the 1–5 primary population and the all-non-missing rating population were independently validated. The out-of-range values were kept as observed and were not recoded. Group counts reconcile to each dimension's eligible population; the two rating sensitivity rows are separate overlapping populations, not additive categories. Missing values are excluded only from their own dimension's comparison.

## Interpretation

The tables describe observed delivery-time differences across rating values, fixed age bands, and multiple-delivery categories separately. Rating values outside 1–5 are excluded from the primary comparison and shown unchanged in the sensitivity scenario. These descriptive associations do not show that ratings, age, or multiple deliveries cause faster or slower deliveries.

## Limitations

- The comparisons are observational and unadjusted; traffic, weather, city, vehicle, distance, and time dimensions are not analyzed here.
- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision; smaller categories remain descriptive only.
- Missing rating, age, and multiple-delivery values are excluded separately from their own comparisons and are not inferred.
- Ratings outside the expected 1–5 range remain anomalous values; sensitivity analysis includes them without assigning a valid-rating meaning.
- The age bands are the fixed descriptive bands requested and do not imply a causal or ordinal model.
- `multiple_deliveries` values are treated as categorical labels; the numeric labels are not interpreted as an ordered scale.
- Findings are limited to valid targets in the cleaned training data.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the input schema is unchanged and no derived columns were persisted.
