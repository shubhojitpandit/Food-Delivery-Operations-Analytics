# Time Analysis

## Objective

Describe observed delivery-performance patterns by order date, weekday, month, order-time band, pickup-time band, and valid non-negative order-to-pickup delay. These are separate unadjusted temporal comparisons.

## Data Scope

- **Source:** `data/processed/train_clean.csv` only; no test targets are used.
- **Target:** `Time_taken(min)`, included only when non-null and numeric.
- **Fixed slow threshold:** 40 minutes; slow means strictly `Time_taken(min) > 40`.
- **Percentiles:** continuous linear interpolation at rank `1 + (n - 1) × p`.
- **Minimum group size:** 30; smaller groups are shown descriptively and not substantively compared.
- Dates are parsed strictly as `YYYY-MM-DD`; clock values are parsed strictly as `HH:MM:SS`. SQLite uses explicit date/time parsing and minute-of-day conversion.

Total train rows: **45,593**; valid numeric targets: **45,593**.

## Order Date Coverage

- Minimum valid date: **2022-02-11**.
- Maximum valid date: **2022-04-06**.
- Valid dates among valid targets: **45,593**.
- Missing/invalid dates among valid targets: **0**.
- Observed calendar-month coverage: **3 month(s)**.

Delivery performance by calendar date:

| Order date | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022-02-11 | 970 | 23.42061856 | 23 | 33 | 28 / 970 | 2.8866% | Meets minimum |
| 2022-02-12 | 864 | 30.06365741 | 29 | 44 | 156 / 864 | 18.0556% | Meets minimum |
| 2022-02-13 | 957 | 23.35632184 | 23 | 33 | 18 / 957 | 1.8809% | Meets minimum |
| 2022-02-14 | 851 | 30.06110458 | 29 | 44 | 144 / 851 | 16.9213% | Meets minimum |
| 2022-02-15 | 945 | 23.29417989 | 23 | 33 | 23 / 945 | 2.4339% | Meets minimum |
| 2022-02-16 | 861 | 30.29500581 | 30 | 43 | 146 / 861 | 16.9570% | Meets minimum |
| 2022-02-17 | 939 | 23.49520767 | 24 | 33 | 20 / 939 | 2.1299% | Meets minimum |
| 2022-02-18 | 855 | 29.66900585 | 29 | 42 | 127 / 855 | 14.8538% | Meets minimum |
| 2022-03-01 | 1,140 | 23.22631579 | 23 | 33 | 26 / 1,140 | 2.2807% | Meets minimum |
| 2022-03-02 | 1,012 | 29.50790514 | 29 | 43 | 156 / 1,012 | 15.4150% | Meets minimum |
| 2022-03-03 | 1,150 | 23.05478261 | 22.5 | 33 | 29 / 1,150 | 2.5217% | Meets minimum |
| 2022-03-04 | 981 | 29.57798165 | 29 | 43 | 166 / 981 | 16.9215% | Meets minimum |
| 2022-03-05 | 1,154 | 23.08058925 | 23 | 33 | 25 / 1,154 | 2.1664% | Meets minimum |
| 2022-03-06 | 986 | 30.06896552 | 29 | 43 | 160 / 986 | 16.2272% | Meets minimum |
| 2022-03-07 | 1,153 | 23.00173461 | 23 | 33 | 22 / 1,153 | 1.9081% | Meets minimum |
| 2022-03-08 | 964 | 29.86307054 | 29 | 43 | 142 / 964 | 14.7303% | Meets minimum |
| 2022-03-09 | 1,159 | 23.41328732 | 24 | 33 | 28 / 1,159 | 2.4159% | Meets minimum |
| 2022-03-10 | 996 | 30.21385542 | 29 | 43.5 | 164 / 996 | 16.4659% | Meets minimum |
| 2022-03-11 | 1,149 | 23.31418625 | 23 | 33 | 27 / 1,149 | 2.3499% | Meets minimum |
| 2022-03-12 | 964 | 29.55912863 | 29 | 42 | 128 / 964 | 13.2780% | Meets minimum |
| 2022-03-13 | 1,169 | 23.35414885 | 23 | 33 | 32 / 1,169 | 2.7374% | Meets minimum |
| 2022-03-14 | 974 | 30.18377823 | 29 | 43.7 | 179 / 974 | 18.3778% | Meets minimum |
| 2022-03-15 | 1,192 | 23.40520134 | 23 | 33 | 35 / 1,192 | 2.9362% | Meets minimum |
| 2022-03-16 | 995 | 29.8201005 | 29 | 43 | 163 / 995 | 16.3819% | Meets minimum |
| 2022-03-17 | 1,134 | 23.19400353 | 23 | 33 | 27 / 1,134 | 2.3810% | Meets minimum |
| 2022-03-18 | 968 | 30.25309917 | 30 | 43 | 169 / 968 | 17.4587% | Meets minimum |
| 2022-03-19 | 1,150 | 23.12782609 | 23 | 33 | 29 / 1,150 | 2.5217% | Meets minimum |
| 2022-03-20 | 994 | 30.13682093 | 29 | 44 | 185 / 994 | 18.6117% | Meets minimum |
| 2022-03-21 | 1,149 | 23.62489121 | 24 | 33 | 26 / 1,149 | 2.2628% | Meets minimum |
| 2022-03-23 | 964 | 30.10788382 | 29 | 44 | 163 / 964 | 16.9087% | Meets minimum |
| 2022-03-24 | 1,162 | 22.883821 | 23 | 33 | 24 / 1,162 | 2.0654% | Meets minimum |
| 2022-03-25 | 975 | 29.64205128 | 29 | 43 | 154 / 975 | 15.7949% | Meets minimum |
| 2022-03-26 | 1,166 | 23.1432247 | 23 | 33 | 25 / 1,166 | 2.1441% | Meets minimum |
| 2022-03-27 | 965 | 29.5761658 | 29 | 43 | 150 / 965 | 15.5440% | Meets minimum |
| 2022-03-28 | 1,139 | 23.41000878 | 23 | 33.2 | 29 / 1,139 | 2.5461% | Meets minimum |
| 2022-03-29 | 977 | 30.07881269 | 29 | 44 | 175 / 977 | 17.9120% | Meets minimum |
| 2022-03-30 | 1,141 | 23.34268186 | 23 | 33 | 37 / 1,141 | 3.2428% | Meets minimum |
| 2022-03-31 | 967 | 29.26783868 | 28 | 43 | 151 / 967 | 15.6153% | Meets minimum |
| 2022-04-01 | 1,133 | 23.36981465 | 23 | 33 | 28 / 1,133 | 2.4713% | Meets minimum |
| 2022-04-02 | 992 | 29.71875 | 29 | 43 | 159 / 992 | 16.0282% | Meets minimum |
| 2022-04-03 | 1,178 | 23.07470289 | 23 | 33 | 29 / 1,178 | 2.4618% | Meets minimum |
| 2022-04-04 | 941 | 29.38150903 | 28 | 42 | 148 / 941 | 15.7279% | Meets minimum |
| 2022-04-05 | 1,157 | 23.21866897 | 23 | 33 | 25 / 1,157 | 2.1608% | Meets minimum |
| 2022-04-06 | 961 | 29.64308012 | 29 | 43 | 160 / 961 | 16.6493% | Meets minimum |

Highest-volume dates (descriptive counts):

| Date | Valid deliveries |
| --- | --- |
| 2022-03-15 | 1,192 |
| 2022-04-03 | 1,178 |
| 2022-03-13 | 1,169 |
| 2022-03-26 | 1,166 |
| 2022-03-24 | 1,162 |

Lowest-volume dates (descriptive counts):

| Date | Valid deliveries |
| --- | --- |
| 2022-02-14 | 851 |
| 2022-02-18 | 855 |
| 2022-02-16 | 861 |
| 2022-02-12 | 864 |
| 2022-02-17 | 939 |
## Day-of-Week Analysis

Weekday is derived from valid Order_Date. Order is chronological, Monday through Sunday (Python weekday convention Monday=0); every category meets the same 30-record reporting rule.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Monday | 6,207 | 26.25406799 | 25 | 39 | 548 / 6,207 | 8.8287% | Meets minimum |
| Tuesday | 6,375 | 25.32219608 | 25 | 38 | 426 / 6,375 | 6.6824% | Meets minimum |
| Wednesday | 7,093 | 27.75948118 | 27 | 42 | 853 / 7,093 | 12.0259% | Meets minimum |
| Thursday | 6,348 | 25.18320731 | 25 | 38 | 415 / 6,348 | 6.5375% | Meets minimum |
| Friday | 7,031 | 26.81738017 | 26 | 40 | 699 / 7,031 | 9.9417% | Meets minimum |
| Saturday | 6,290 | 26.09984102 | 25.5 | 39 | 522 / 6,290 | 8.2989% | Meets minimum |
| Sunday | 6,249 | 26.40102416 | 25 | 40 | 574 / 6,249 | 9.1855% | Meets minimum |

## Monthly Analysis

Months are ordered by calendar month number. The observed training data covers 3 calendar month(s), from 2022-02-11 to 2022-04-06; this is not a full-year seasonal sample.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 02 — February | 7,242 | 26.53314002 | 26 | 40 | 662 / 7,242 | 9.1411% | Meets minimum |
| 03 — March | 31,989 | 26.27643878 | 26 | 40 | 2,826 / 31,989 | 8.8343% | Meets minimum |
| 04 — April | 6,362 | 26.11442942 | 25 | 39 | 549 / 6,362 | 8.6294% | Meets minimum |

## Order-Time Analysis

Valid order times are converted from HH:MM:SS into minutes after midnight, then classified into the fixed bands: Night (00:00–05:59), Morning (06:00–11:59), Afternoon (12:00–16:59), Evening (17:00–20:59), and Late Night (21:00–23:59). Missing/invalid order times among valid targets: **1,731**; valid parsed order times: **43,862**.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Night | 430 | 22.16976744 | 21 | 30 | 11 / 430 | 2.5581% | Meets minimum |
| Morning | 7,718 | 21.27545996 | 20 | 30 | 104 / 7,718 | 1.3475% | Meets minimum |
| Afternoon | 4,049 | 25.64015806 | 26 | 35 | 164 / 4,049 | 4.0504% | Meets minimum |
| Evening | 17,892 | 29.21082048 | 29 | 42 | 2,367 / 17,892 | 13.2294% | Meets minimum |
| Late Night | 13,773 | 25.63755173 | 24 | 40 | 1,227 / 13,773 | 8.9087% | Meets minimum |

## Pickup-Time Analysis

Pickup time is analyzed separately using the same fixed bands: Night (00:00–05:59), Morning (06:00–11:59), Afternoon (12:00–16:59), Evening (17:00–20:59), and Late Night (21:00–23:59). Missing/invalid pickup times among valid targets: **0**; valid parsed pickup times: **45,593**.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Night | 1,320 | 22.3780303 | 21 | 33 | 39 / 1,320 | 2.9545% | Meets minimum |
| Morning | 7,643 | 20.9502813 | 20 | 29 | 82 / 7,643 | 1.0729% | Meets minimum |
| Afternoon | 4,466 | 25.92454098 | 26 | 36 | 206 / 4,466 | 4.6126% | Meets minimum |
| Evening | 17,873 | 29.0611537 | 29 | 42 | 2,293 / 17,873 | 12.8294% | Meets minimum |
| Late Night | 14,291 | 26.17024701 | 25 | 40 | 1,417 / 14,291 | 9.9153% | Meets minimum |

## Order-to-Pickup Delay

### Time Parsing

Valid clock strings were parsed strictly as HH:MM:SS and converted to fractional minutes after midnight. The direct same-day difference is `pickup time − order time`; it was not made positive or adjusted by 24 hours.
- Valid paired order/pickup clocks: **43,862**.
- Missing/invalid order times among valid targets: **1,731**.
- Missing/invalid pickup times among valid targets: **0**.

### Negative/Ambiguous Differences

- Negative same-day differences treated as ambiguous: **831**.
- Denominator (valid paired clocks): **43,862**.
- Negative/ambiguous proportion: **1.8946%**.
- Non-negative differences retained for the primary delay distribution: **43,031**.
- Negative cases are excluded from the primary delay distribution because the available dates do not establish whether midnight was crossed.

### Valid Pickup Delay Distribution

Statistics below include only valid paired clocks with a non-negative direct same-day difference. Percentiles use continuous linear interpolation.

| Count | Minimum (min) | P25 (min) | Median (min) | P75 (min) | P90 (min) | Maximum (min) | Mean (min) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 43,031 | 5 | 5 | 10 | 15 | 15 | 15 | 9.95526481 |
### Pickup Delay Band Analysis

Bands use direct same-day delay minutes: 0–5, >5–10, >10–15, >15–20, >20–30, and >30 minutes. Negative and unpaired clock records are excluded. Exact fractional-minute values are retained for summary statistics.

| Category | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0-5 minutes | 14,564 | 26.37963472 | 26 | 40 | 1,338 / 14,564 | 9.1870% | Meets minimum |
| 6-10 minutes | 14,288 | 26.44771837 | 26 | 40 | 1,284 / 14,288 | 8.9866% | Meets minimum |
| 11-15 minutes | 14,179 | 26.28020312 | 26 | 39 | 1,227 / 14,179 | 8.6536% | Meets minimum |
| 16-20 minutes | 0 | — | — | — | 0 / 0 | — | No records |
| 21-30 minutes | 0 | — | — | — | 0 / 0 | — | No records |
| 31+ minutes | 0 | — | — | — | 0 / 0 | — | No records |

## SQL vs Python Validation

SQL statements in `sql/07_time_analysis.sql` were executed against an in-memory SQLite table (version `3.50.4`). Python independently parsed the source strings and calculated groups and continuous percentiles with Pandas/NumPy. SQLite has no built-in PERCENTILE_CONT; SQL implements continuous linear interpolation.

Counts, classifications, and category ordering were checked exactly. Floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Analysis | Groups | Validated fields | Result |
| --- | --- | --- | --- |
| order_date | 44 | 264 | MATCH |
| day_of_week | 7 | 42 | MATCH |
| month | 3 | 18 | MATCH |
| order_time | 5 | 30 | MATCH |
| pickup_time | 5 | 30 | MATCH |
| pickup_delay_band | 6 | 24 | MATCH |
| Coverage and delay distribution | 1 | 21 | MATCH |
| Weekday/month/time/delay band order and classification | 4 dimensions | category sets, counts, labels, and order checked | MATCH |

All SQL/Python checks passed: **429 metric/count checks** across grouped results and coverage/delay summaries. Weekday and month ordering, fixed clock bands, and pickup-delay band classifications matched.

## Interpretation

The tables describe observed delivery-time variation across calendar dates, weekdays, months, order-time bands, pickup-time bands, and non-negative same-day pickup delays. These temporal associations do not establish that a date, weekday, month, time band, or pickup delay causes delivery-time differences.

## Limitations

- The data spans 3 calendar month(s), so it cannot establish annual seasonality or a full-year temporal pattern.
- Daily performance can be sensitive to per-date sample size; dates below 30 valid targets are descriptive only.
- Clock-only negative differences are ambiguous; no midnight rollover is assumed without a pickup date.
- Order-to-pickup elapsed-time metrics omit negative and unpaired clock records from the primary distribution.
- Comparisons are observational and unadjusted; other explanatory dimensions are not combined or analyzed in this step.
- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the input schema is unchanged and no derived columns were persisted.
