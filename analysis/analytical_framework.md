# Food Delivery Operations & Delivery Performance Analytics

## Purpose and scope

> The dataset already exists. We are not building or fabricating a dataset. We are applying defined analytical parameters to the available data to discover and validate meaningful patterns.

This document defines questions and methods before running the SQL or Python analyses. It contains no calculated findings or business recommendations. Use `data/processed/train_clean.csv` for delivery-time performance analysis because it contains the target. Use `data/processed/test_clean.csv` only for checks that do not require an observed delivery time; never invent a target for test.

The cleaned CSVs serialize `Order_Date` as `YYYY-MM-DD` and clock times as `HH:MM:SS`. Interpret these formats on read. The target is `Time_taken(min)`. The Step 3 quality flags are `rating_out_of_range`, `suspicious_delivery_coordinates`, and `possible_midnight_crossing`.

## Shared definitions and analysis parameters

| Parameter | Definition to apply |
|---|---|
| Valid delivery record | A train row with a non-null, numeric `Time_taken(min)`. Report this count for every performance output. Do not remove a row just because a dimension or quality flag is missing/set; exclude it only from a calculation that requires that field, and report the applicable denominator. |
| Core delivery-time metrics | Count of valid targets, mean, median, P75, P90, minimum, and maximum in minutes. Compute percentiles using continuous linear interpolation in Python and the database's equivalent continuous percentile function where available. Record the SQL engine/function used. |
| Slow-delivery threshold | Define once from the valid target distribution in the cleaned training data: the overall continuous P90 delivery time. A record is slow only when `Time_taken(min)` is **strictly greater than** this threshold. Report the numerical threshold, percentile method, target population, and number/rate of slow rows. Use this same fixed threshold for every segment and combined-factor comparison; do not recalculate within groups. Ties at P90 are not classified as slow. |
| Slow-delivery rate | `count(valid target > fixed threshold) / count(valid targets in that group)`. Show numerator and denominator, not only the percentage. |
| Minimum group size | Use **30 valid target records** as the minimum for interpreting a group or ranking it. Smaller groups may be shown with counts and descriptive statistics, but label them small-sample/descriptive and do not rank or draw comparative conclusions from them. This is a reporting guardrail, not a guarantee of statistical precision. |
| Missing dimensions | Exclude null dimension values only from the corresponding grouped comparison. Report the number excluded for that dimension so group counts reconcile to the eligible target population. Do not treat nulls as categories unless a separately labeled missingness comparison is explicitly asked. |
| Comparison language | Describe observed differences and associations only. Avoid causal statements, explanations not measured by the data, and claims of statistical significance unless a suitable test and assumptions are documented. |

For every comparison, show group count and at least mean, median, P90, and slow-delivery rate; show P75, minimum, and maximum where useful. Include group sample sizes and use the minimum-size rule above. Means alone are insufficient.

## Analytical question framework

The table follows **Question → Metric → Dimension → Method → Validation → Interpretation**. “Metric” refers to the shared definitions above unless otherwise stated.

| Area | Question | Metric | Dimension | Method | Validation | Interpretation |
|---|---|---|---|---|---|---|
| Overall delivery performance | What does normal delivery performance look like across the dataset? | Valid-record count, mean, median, P75, P90, minimum, maximum, slow count/rate | None | Summarize valid cleaned training targets; define the single P90 slow threshold from this distribution | Reconcile valid count to target null counts; compare SQL aggregates/percentiles with Python; verify percentile convention and strict `>` slow rule | Describe the observed distribution only; do not assume a “normal” level or conclude a cause |
| Traffic | How is delivery time associated with road traffic density? | Group count, mean, median, P90, slow rate | `Road_traffic_density` | Aggregate valid targets by cleaned category; report unknown/missing dimension count separately | Reconcile group counts; compare SQL and Python aggregates; apply minimum group size | Association only, not evidence that traffic caused the observed delivery times |
| Weather | How does delivery performance vary across weather conditions? | Same core group metrics | `Weatherconditions` | Aggregate valid targets by cleaned weather category | Reconcile counts, category values, and null exclusions; cross-validate metrics | Describe observed variation without attributing causality |
| City | How does delivery performance differ between cities? | Record volume, mean, median, P90, slow rate | `City` | Aggregate by standardized city; show all counts; only compare/rank groups meeting the 30-record rule | Verify `Metropolitian` standardization to `Metropolitan`; reconcile counts and SQL/Python metrics | Do not rank a group below minimum sample size; no causal/geographic explanation without evidence |
| Vehicle | Does performance differ by vehicle type or condition? | Same core group metrics | `Type_of_vehicle`; `Vehicle_condition` | Run separate grouped comparisons; treat vehicle condition as a categorical level unless a later question justifies an ordered model | Reconcile category counts, nulls, and SQL/Python metrics | Observational differences do not establish that vehicle type/condition caused performance |
| Courier | Are rating, age, or multiple deliveries associated with delivery time? | Same core group metrics; include group counts | `Delivery_person_Ratings`, `Delivery_person_Age`, `multiple_deliveries` | Rating: primary association uses only ratings with `rating_out_of_range = 0`; separately compare valid and flagged rating records as sensitivity. Age and multiple-delivery count: show discrete categories or predeclared bins; do not invent unmotivated cutoffs. | Confirm rating flag matches [1, 5] rule, and explicitly report excluded/flagged/missing rating counts; check counts and metrics against Python | Keep out-of-range ratings unchanged; do not silently treat 6 as 5 or mix flagged ratings into the in-range rating trend |
| Date and time | Does performance vary by date, month, weekday, or order-time period? | Same core group metrics; date-level count | `Order_Date`; month, day, weekday, and justified order-time period | Derive calendar date, month, and weekday from `Order_Date` only for these questions. For order-time period use four fixed clock bands: 00:00–05:59, 06:00–11:59, 12:00–17:59, and 18:00–23:59. Missing order time remains missing and is counted separately. Do not create other time dimensions absent a question. | Check date parsing and weekday convention (document Monday=0 or Monday name); verify time-band boundaries are exhaustive/non-overlapping and counts reconcile | Describe temporal patterns, not trends beyond the observed date coverage or causal effects |
| Pickup / operational delay | How much time appears between order placement and pickup? | Valid paired-clock count; clock-difference minutes; count/rate of possible crossings | `Time_Orderd`, `Time_Order_picked`, optionally date for grouping | Primary elapsed-time summary: calculate only for valid paired times where pickup clock is equal to or later than order clock; report excluded possible-crossing and missing-time counts, do not delete those records from other analyses. Separate sensitivity: if explicitly labeled as an assumption, add 24 hours to negative differences and compare results. Do not present assumed rollover as confirmed duration without pickup date/source validation. | Reconcile valid pairs, negative same-clock comparisons, null order/pickup counts, and sensitivity totals to the Step 3 flag; test example boundary times | Because pickup date is absent, same-day vs overnight chronology is unknowable. Treat rollover results as sensitivity only and never discard crossing records from the dataset |
| Geographic distance | Is approximate delivery distance associated with delivery time? | Haversine distance in km; distance-target association and core metrics by distance group | Restaurant/delivery coordinates; predeclared distance groups | Calculate great-circle distance using Haversine and mean Earth radius 6,371.0088 km. Exclude `suspicious_delivery_coordinates = 1` from the primary distance analysis, preserve those rows elsewhere, and report excluded count. For sensitivity, show flagged rows separately; do not interpret their distance as reliable. Use training-data quartile cut points for distance bands, freeze them across comparisons, and report cut points/ties. | Check coordinate nulls/ranges, Haversine outputs are finite/nonnegative, test known identical points yield zero, compare sample distances with an independent Python implementation; report flagged/null counts | Straight-line distance is not road distance, travel distance, or travel time; association does not imply causation |
| Combined factors | Do combinations add interpretable context beyond single dimensions? | Core group metrics and cell counts | Candidate pairs: traffic × city; traffic × weather; distance × traffic; distance × vehicle condition; multiple deliveries × traffic; city × traffic; distance × city | Treat combinations as candidates, not a required full grid. Produce a combination only when its question is clear and cells are interpretable. Apply the 30-valid-target minimum per cell; show sparse cells without ranking, or omit with a documented reason. | Reconcile cell counts to eligible rows; check for empty/sparse cells and compare selected SQL results with Python | Retain only interpretable, sufficiently supported comparisons; do not imply interaction or cause from a cross-tab alone |
| Slow delivery | Which observed conditions are most represented among deliveries above the fixed threshold? | Slow count/rate, eligible group count, share of all slow records (clearly distinguished from within-group rate) | Traffic, city, weather, vehicle type/condition, multiple deliveries, distance bands, and selected combinations | Use the single overall training P90 threshold and strict greater-than rule from Shared definitions. Report both within-group slow rate and group share among slow records to avoid confusing denominators. Apply minimum group size for comparisons. | Validate threshold and slow-row count against the overall target distribution; reconcile each group numerator/denominator to the slow total; reproduce in SQL and Python | Representation is descriptive; do not imply that overrepresented factors cause a slow delivery |
| Data-quality sensitivity | Do flags materially change relevant comparisons? | Recomputed core metrics and differences from the primary population | `rating_out_of_range`, `suspicious_delivery_coordinates`, `possible_midnight_crossing`, applied only where relevant | Rating analyses: compare in-range primary results with a version that includes flagged ratings and a flagged-only summary. Distance: compare primary unflagged-coordinate analysis with flagged rows summarized separately. Pickup-clock analysis: compare primary non-crossing calculations with the explicitly assumed rollover sensitivity. For unrelated analyses do not filter on irrelevant flags. | Show inclusion/exclusion counts and exactly which flag filter was applied; use the same target definition, threshold, group rules, and percentile method in each comparison | Call changes sensitivity, not proof that records are wrong; report whether conclusions are stable or differ without silently choosing the preferred version |

## Specific methodology notes

### Rating handling

`rating_out_of_range = 1` identifies numeric ratings outside the expected 1–5 range. Do not alter the underlying rating. Use in-range ratings for the primary rating-specific association, report flagged and missing rating counts, and provide the include-flagged sensitivity comparison. In other analyses, do not drop a record merely because its rating flag is set.

### Pickup-time ambiguity

`possible_midnight_crossing = 1` means the pickup clock is earlier than the order clock when compared without dates; it does not prove midnight crossing. The primary clock-difference summary is restricted to nonnegative same-clock differences, with crossing rows explicitly counted and retained in the source analysis population. A next-day adjustment may be reported only as a separately labeled sensitivity scenario (`24 hours - order time + pickup time`). Do not publish it as the actual delay without a pickup date or confirmation from the data owner.

### Geographic distance

Convert degrees to radians before applying Haversine. For latitudes \(\phi_1,\phi_2\), longitude difference \(\Delta\lambda\), and latitude difference \(\Delta\phi\):

\[
a = \sin^2(\Delta\phi/2) + \cos(\phi_1)\cos(\phi_2)\sin^2(\Delta\lambda/2)
\]
\[
d = 2R\arcsin(\sqrt{a}), \quad R=6{,}371.0088\text{ km}
\]

Clamp the computed \(a\) to [0, 1] for floating-point safety. Keep full precision for calculations and round only for presentation. The `suspicious_delivery_coordinates` flag marks a delivery latitude or longitude equal to 0.01; it is a screening signal, not an assertion that every flagged coordinate is wrong.

### Distribution-aware grouping and interpretation

- Report exact group counts with all segment summaries. Do not use rankings for groups with fewer than 30 valid targets.
- Distance quartile cut points are computed from valid, unflagged training distances, then held fixed for all related comparisons; if ties produce fewer than four distinct bands, report the actual cut points and resulting bands instead of forcing balanced bins.
- Do not select candidate combinations based on whether they appear to show a desirable result. Record the question and inclusion criteria before reviewing metrics; document omitted combinations and the reason (for example, sparse or not interpretable).
- If uncertainty intervals or formal tests are added later, specify the procedure, assumptions, multiple-comparison handling, and practical effect-size interpretation before treating them as evidence.

## Reproducibility, validation, and analytical principles

1. Preserve `data/raw/`; use only the cleaned processed files for analysis. Do not change the cleaned datasets as part of the analytical queries.
2. Keep transformations used only for analysis (weekday, order-time bands, Haversine distance, distance bands, slow indicator) explicit in SQL/Python code; do not persist unrequested derived columns in the source files.
3. For every result, record input file, target eligibility, filters, dimension null handling, group-size rule, threshold, percentile method, and numerator/denominator.
4. Cross-validate important SQL counts and statistics in Python where practical. Match the percentile definition, null behavior, inclusion filters, and rounding before comparing.
5. Validate total eligible counts, segment count reconciliation, flag counts, and date/time parsing before interpreting a result.
6. The dataset is observational. Association does not establish causation.
7. Use central tendency and distribution metrics together; consider sample size and avoid conclusions based on extremely small groups.
8. Preserve raw data. Use cleaned data only for analysis.
9. Important findings must be supported by calculated evidence and reproducible through SQL or Python. This framework itself reports no findings.

## Intended division of analytical work

| Tool | Intended use |
|---|---|
| SQL | Aggregations, `GROUP BY`, filtering, segmentation, comparisons, CTEs, subqueries, and window functions where useful. SQL is the primary route for repeatable tabular summaries. |
| Python | Input/type handling for analysis, Haversine calculation, statistical checks, visualizations, and analyses that are awkward or inefficient in SQL. Python also cross-validates key SQL outputs where practical. |

No analysis queries, calculated findings, or business recommendations are part of Step 4.
