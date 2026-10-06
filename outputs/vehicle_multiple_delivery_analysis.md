# Vehicle × Multiple Deliveries Analysis

## Objective

Describe whether observed vehicle-type differences in delivery performance remain visible within multiple-delivery categories, and whether the multiple-delivery pattern remains visible within vehicle types. This is observational analysis only.

## Analytical Context

The standalone vehicle analysis reported the highest slow-delivery rate for motorcycle (11.7685%; 3,111/26,435) and the lowest for electric_scooter (4.7457%; 181/3,814). The standalone multiple-delivery analysis reported increasing mean delivery time and slow-delivery rate over categorical labels 0–3; label 3 had a 100% slow rate (361/361). Both findings motivate this focused two-variable comparison.

Standalone vehicle results:

| Vehicle type | Count | Mean (min) | Slow rate | Slow count / n |
| --- | --- | --- | --- | --- |
| bicycle | 68 | 26.42647059 | 5.88235294% | 4 / 68 |
| electric_scooter | 3,814 | 24.47011012 | 4.74567383% | 181 / 3,814 |
| motorcycle | 26,435 | 27.6056743 | 11.76848875% | 3,111 / 26,435 |
| scooter | 15,276 | 24.48075412 | 4.85074627% | 741 / 15,276 |

Standalone multiple-delivery results:

| multiple_deliveries label | Count | Mean (min) | Slow rate | Slow count / n |
| --- | --- | --- | --- | --- |
| 0 | 14,095 | 22.87626818 | 4.5406% | 640 / 14,095 |
| 1 | 28,159 | 26.85588977 | 7.4008% | 2,084 / 28,159 |
| 2 | 1,985 | 40.45491184 | 45.7431% | 908 / 1,985 |
| 3 | 361 | 47.8199446 | 100.0000% | 361 / 361 |

## Data Coverage

- Total valid-target records: **45,593** of 45,593 training records.
- Valid-target records with missing vehicle type: **0**.
- Valid-target records with missing multiple-delivery category: **993**.
- Records with both dimensions available: **44,600**.
- Records missing either dimension (union): **993**; the separate missing counts may overlap.
Missing dimensions remain in the valid-target population and are excluded only from this two-way comparison.

## Two-Way Analysis

Slow delivery uses the fixed global definition `Time_taken(min) > 40`; no threshold was recalculated. Both dimensions are categorical. Multiple-delivery labels are presented as observed and are only numerically ordered for the explicitly requested descriptive label-pattern check; they are not treated as a continuous variable.

Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Every observed vehicle × multiple-delivery pair is shown; cells with fewer than 30 records remain descriptive and are not ranked or used for substantive comparisons.

### Vehicle × Multiple Deliveries Results

| Vehicle type | multiple_deliveries | Count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow count / n | Slow rate | Eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bicycle | 0 | 20 | 22.05 | 22 | 31 | 0 | 0 / 20 | 0.0000% | Small sample; descriptive only |
| bicycle | 1 | 43 | 27.11627907 | 26 | 39 | 3 | 3 / 43 | 6.9767% | Qualifies |
| bicycle | 2 | 4 | 38.25 | 37.5 | 41.8 | 1 | 1 / 4 | 25.0000% | Small sample; descriptive only |
| bicycle | 3 | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| electric_scooter | 0 | 1,262 | 21.4889065 | 20 | 33 | 31 | 31 / 1,262 | 2.4564% | Qualifies |
| electric_scooter | 1 | 2,333 | 25.24389198 | 25 | 36 | 93 | 93 / 2,333 | 3.9863% | Qualifies |
| electric_scooter | 2 | 130 | 39.36153846 | 39 | 44 | 47 | 47 / 130 | 36.1538% | Qualifies |
| electric_scooter | 3 | 8 | 46.125 | 44.5 | 50.2 | 8 | 8 / 8 | 100.0000% | Small sample; descriptive only |
| motorcycle | 0 | 7,700 | 24.01246753 | 23 | 37 | 480 | 480 / 7,700 | 6.2338% | Qualifies |
| motorcycle | 1 | 16,508 | 27.8851466 | 27 | 40 | 1,587 | 1,587 / 16,508 | 9.6135% | Qualifies |
| motorcycle | 2 | 1,361 | 41.06318883 | 41 | 48 | 690 | 690 / 1,361 | 50.6980% | Qualifies |
| motorcycle | 3 | 322 | 48.10559006 | 48 | 53 | 322 | 322 / 322 | 100.0000% | Qualifies |
| scooter | 0 | 5,113 | 21.51085468 | 19 | 33 | 129 | 129 / 5,113 | 2.5230% | Qualifies |
| scooter | 1 | 9,275 | 25.42824798 | 25 | 37 | 401 | 401 / 9,275 | 4.3235% | Qualifies |
| scooter | 2 | 490 | 39.07346939 | 39 | 44 | 170 | 170 / 490 | 34.6939% | Qualifies |
| scooter | 3 | 31 | 45.29032258 | 44 | 49 | 31 | 31 / 31 | 100.0000% | Qualifies |

## Within-Vehicle Multiple-Delivery Comparison

The extrema below use only qualifying cells. The detailed rows show count, mean, median, P90, slow numerator/denominator, slow rate, and within-vehicle ranks. Numeric labels are sorted only to inspect descriptive successive-category patterns.

| Vehicle | Observed category cells (counts) | Qualifying cells | Lowest mean category | Highest mean category | Lowest slow-rate category | Highest slow-rate category |
| --- | --- | --- | --- | --- | --- | --- |
| bicycle | 0 (n=20); 1 (n=43); 2 (n=4); 3 (n=0) | 1 | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) |
| electric_scooter | 0 (n=1,262); 1 (n=2,333); 2 (n=130); 3 (n=8) | 3 | 0 (n=1,262; 21.4889065 min; median 20; P90 33) | 2 (n=130; 39.36153846 min; median 39; P90 44) | 0 (n=1,262; 2.4564%; median 20; P90 33) | 2 (n=130; 36.1538%; median 39; P90 44) |
| motorcycle | 0 (n=7,700); 1 (n=16,508); 2 (n=1,361); 3 (n=322) | 4 | 0 (n=7,700; 24.01246753 min; median 23; P90 37) | 3 (n=322; 48.10559006 min; median 48; P90 53) | 0 (n=7,700; 6.2338%; median 23; P90 37) | 3 (n=322; 100.0000%; median 48; P90 53) |
| scooter | 0 (n=5,113); 1 (n=9,275); 2 (n=490); 3 (n=31) | 4 | 0 (n=5,113; 21.51085468 min; median 19; P90 33) | 3 (n=31; 45.29032258 min; median 44; P90 49) | 0 (n=5,113; 2.5230%; median 19; P90 33) | 3 (n=31; 100.0000%; median 44; P90 49) |

Qualifying category-level comparison details:

| Vehicle | multiple_deliveries category | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bicycle |   category 1 | 43 | 27.11627907 | 26 | 39 | 3 / 43 | 6.9767% | 1 | 1 |
| electric_scooter |   category 0 | 1,262 | 21.4889065 | 20 | 33 | 31 / 1,262 | 2.4564% | 1 | 1 |
| electric_scooter |   category 1 | 2,333 | 25.24389198 | 25 | 36 | 93 / 2,333 | 3.9863% | 2 | 2 |
| electric_scooter |   category 2 | 130 | 39.36153846 | 39 | 44 | 47 / 130 | 36.1538% | 3 | 3 |
| motorcycle |   category 0 | 7,700 | 24.01246753 | 23 | 37 | 480 / 7,700 | 6.2338% | 1 | 1 |
| motorcycle |   category 1 | 16,508 | 27.8851466 | 27 | 40 | 1,587 / 16,508 | 9.6135% | 2 | 2 |
| motorcycle |   category 2 | 1,361 | 41.06318883 | 41 | 48 | 690 / 1,361 | 50.6980% | 3 | 3 |
| motorcycle |   category 3 | 322 | 48.10559006 | 48 | 53 | 322 / 322 | 100.0000% | 4 | 4 |
| scooter |   category 0 | 5,113 | 21.51085468 | 19 | 33 | 129 / 5,113 | 2.5230% | 1 | 1 |
| scooter |   category 1 | 9,275 | 25.42824798 | 25 | 37 | 401 / 9,275 | 4.3235% | 2 | 2 |
| scooter |   category 2 | 490 | 39.07346939 | 39 | 44 | 170 / 490 | 34.6939% | 3 | 3 |
| scooter |   category 3 | 31 | 45.29032258 | 44 | 49 | 31 / 31 | 100.0000% | 4 | 4 |

Descriptive sequences across observed numeric category labels:

| Vehicle | Qualifying categories | Mean pattern | Slow-rate pattern |
| --- | --- | --- | --- |
| bicycle | 1 | Insufficient qualifying categories | Insufficient qualifying categories |
| electric_scooter | 3 | increasing | increasing |
| motorcycle | 4 | increasing | increasing |
| scooter | 4 | increasing | increasing |

## Within-Multiple-Delivery Vehicle Comparison

Only vehicle cells with at least 30 records for each multiple-delivery category are ranked or compared. Rank 1 is the lowest mean/rate; ties share ranks.

| multiple_deliveries | Vehicle | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | electric_scooter | 1,262 | 21.4889065 | 20 | 33 | 31 / 1,262 | 2.4564% | 1 | 1 |
| 0 | scooter | 5,113 | 21.51085468 | 19 | 33 | 129 / 5,113 | 2.5230% | 2 | 2 |
| 0 | motorcycle | 7,700 | 24.01246753 | 23 | 37 | 480 / 7,700 | 6.2338% | 3 | 3 |
| 1 | electric_scooter | 2,333 | 25.24389198 | 25 | 36 | 93 / 2,333 | 3.9863% | 1 | 1 |
| 1 | scooter | 9,275 | 25.42824798 | 25 | 37 | 401 / 9,275 | 4.3235% | 2 | 2 |
| 1 | bicycle | 43 | 27.11627907 | 26 | 39 | 3 / 43 | 6.9767% | 3 | 3 |
| 1 | motorcycle | 16,508 | 27.8851466 | 27 | 40 | 1,587 / 16,508 | 9.6135% | 4 | 4 |
| 2 | scooter | 490 | 39.07346939 | 39 | 44 | 170 / 490 | 34.6939% | 1 | 1 |
| 2 | electric_scooter | 130 | 39.36153846 | 39 | 44 | 47 / 130 | 36.1538% | 2 | 2 |
| 2 | motorcycle | 1,361 | 41.06318883 | 41 | 48 | 690 / 1,361 | 50.6980% | 3 | 3 |
| 3 | scooter | 31 | 45.29032258 | 44 | 49 | 31 / 31 | 100.0000% | 1 | 1 |
| 3 | motorcycle | 322 | 48.10559006 | 48 | 53 | 322 / 322 | 100.0000% | 2 | 1 |

Vehicle orders, highest to lowest, within each qualifying multiple-delivery category:

| multiple_deliveries | Qualifying vehicle types | Mean order | Slow-rate order |
| --- | --- | --- | --- |
| 0 | 3 | motorcycle > scooter > electric_scooter | motorcycle > scooter > electric_scooter |
| 1 | 4 | motorcycle > bicycle > scooter > electric_scooter | motorcycle > bicycle > scooter > electric_scooter |
| 2 | 3 | motorcycle > electric_scooter > scooter | motorcycle > electric_scooter > scooter |
| 3 | 2 | motorcycle > scooter | motorcycle > scooter |

## Vehicle Signal Check

The standalone highest-rate vehicle was **motorcycle**; the lowest was **electric_scooter**. Among 4 multiple-delivery categories where motorcycle had a qualifying cell, it had the highest or tied-highest vehicle slow rate in 4. Vehicle slow-rate order changed across 3 successive multiple-delivery category comparisons where at least two vehicle types qualified.

| multiple_deliveries | Highest slow-rate vehicle(s) | Standalone-high vehicle rate | Qualifying vehicle slow-rate spread | Vehicle mean range |
| --- | --- | --- | --- | --- |
| 0 | motorcycle (n=7,700) | motorcycle rate 6.2338% | Rate range 2.4564–6.2338% (3.7773 pp) | Mean range 21.4889–24.0125 min; high standalone vehicle rank 1 |
| 1 | motorcycle (n=16,508) | motorcycle rate 9.6135% | Rate range 3.9863–9.6135% (5.6272 pp) | Mean range 25.2439–27.8851 min; high standalone vehicle rank 1 |
| 2 | motorcycle (n=1,361) | motorcycle rate 50.6980% | Rate range 34.6939–50.6980% (16.0041 pp) | Mean range 39.0735–41.0632 min; high standalone vehicle rank 1 |
| 3 | motorcycle (n=322); scooter (n=31) | motorcycle rate 100.0000% | Rate range 100.0000–100.0000% (0.0000 pp) | Mean range 45.2903–48.1056 min; high standalone vehicle rank 1 |

The ranges and within-category ranks indicate where observed vehicle differences remain separated, narrow, tie, or change order; no difference is declared to have disappeared using an arbitrary cutoff.

## Multiple-Delivery Signal Check

Standalone mean endpoints were labels 0 and 3 (difference 24.9437 minutes); slow-rate endpoints were labels 0 and 3 (difference 95.4594 percentage points). The comparisons below use those endpoint categories only where both vehicle-specific cells meet n ≥ 30.

| Vehicle | Qualifying multiple-delivery cells | Counts: low / high slow-rate endpoint | Means: low mean / high mean endpoint (min) | Slow rates: low / high endpoint | Endpoint change and category pattern |
| --- | --- | --- | --- | --- | --- |
| bicycle | 1 | Not comparable | Not comparable | Not comparable | Highest/lowest standalone slow-rate endpoint missing or below minimum |
| electric_scooter | 3 | Not comparable | Not comparable | Not comparable | Highest/lowest standalone slow-rate endpoint missing or below minimum |
| motorcycle | 4 | 7,700 / 322 | 24.0125 → 48.1056 | 6.2338% → 100.0000% | Endpoint mean delta +24.0931 min; rate delta +93.7662 pp; category sequences: mean increasing, rate increasing |
| scooter | 4 | 5,113 / 31 | 21.5109 → 45.2903 | 2.5230% → 100.0000% | Endpoint mean delta +23.7795 min; rate delta +97.4770 pp; category sequences: mean increasing, rate increasing |

Among 2 vehicle types comparable at both slow-rate endpoints, the high-minus-low endpoint mean gap was smaller than standalone in 2, larger in 0, and reversed in 0; the slow-rate gap was smaller in 1, larger in 1, and reversed in 0. Increasing labels are not modeled as a continuous predictor.

Subminimum cells with the highest observed slow rates (descriptive only):

| Vehicle | multiple_deliveries | Count | Slow count | Slow rate | Status |
| --- | --- | --- | --- | --- | --- |
| electric_scooter | 3 | 8 | 8 | 100.0000% | Descriptive only; below n=30 |
| bicycle | 2 | 4 | 1 | 25.0000% | Descriptive only; below n=30 |
| bicycle | 0 | 20 | 0 | 0.0000% | Descriptive only; below n=30 |

## Slow-Delivery Contribution

Across all valid targets, **4,037** are slow. Of these, **3,984** occur in qualifying cells, **9** in subminimum cells, and **44** in records with at least one missing dimension. The five qualifying cells with the largest slow counts account for **3,480 (86.20%)** of all slow deliveries.

| Vehicle | multiple_deliveries | Count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| motorcycle | 1 | 16,508 | 1,587 | 9.6135% | 27.8851466 | 27 | 40 | 1,587 / 4,037 (39.31%) |
| motorcycle | 2 | 1,361 | 690 | 50.6980% | 41.06318883 | 41 | 48 | 690 / 4,037 (17.09%) |
| motorcycle | 0 | 7,700 | 480 | 6.2338% | 24.01246753 | 23 | 37 | 480 / 4,037 (11.89%) |
| scooter | 1 | 9,275 | 401 | 4.3235% | 25.42824798 | 25 | 37 | 401 / 4,037 (9.93%) |
| motorcycle | 3 | 322 | 322 | 100.0000% | 48.10559006 | 48 | 53 | 322 / 4,037 (7.98%) |

## SQL vs Python Validation

SQL from `sql/13_vehicle_multiple_delivery_analysis.sql` ran against an in-memory SQLite 3.50.4 table. Python independently grouped the same valid-target records with Pandas and NumPy linear interpolation. Counts and ranks were compared exactly; floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Two-way cell metrics, standalone references, and population counts | 228 | MATCH |
| Within-vehicle and within-multiple-delivery rankings | 96 | MATCH |
| Vehicle signal comparisons | 4 | MATCH |
| Multiple-delivery endpoint comparisons | 2 | MATCH |
| Slow-delivery population reconciliation | all | MATCH |

## Key Observations

- The standalone highest-rate vehicle (motorcycle) was highest or tied-highest in 4/4 qualifying multiple-delivery strata in which it was comparable; rankings otherwise vary as listed.
- Mean delivery time increased across qualifying successive multiple-delivery labels in 3 vehicle types; slow rate increased in 3. Other strata were mixed, tied, or insufficiently comparable.
- Standalone high-to-low multiple-delivery endpoint differences in mean and slow rate were reduced in 2/2 and 1/2 comparable vehicle types, respectively; direction changes are reported separately.
- The five largest qualifying slow-delivery contributors account for 3,480 of 4,037 slow records (86.20%).

## Interpretation

The two-way descriptive results assess whether the standalone vehicle and multiple-delivery patterns remain visible within the other dimension. Patterns are not uniform where rankings, ranges, or successive category summaries differ. Small cells are shown but do not support substantive comparison. These observed associations do not show that vehicle type or multiple deliveries cause delivery-time differences.

## Limitations

- This is observational analysis; no causal relationship is established.
- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.
- Vehicle type and multiple deliveries may be related to other operational factors.
- This analysis does not control for city, distance, weather, traffic, courier, or time.
- No regression, machine learning, or formal interaction model was fitted.
- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.
- `multiple_deliveries` is treated as categorical, not continuous.
- Missing categories are not inferred; records are excluded only from the two-way cells requiring both dimensions.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; its schema is unchanged.
