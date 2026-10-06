# Traffic × Multiple Deliveries Analysis

## Objective

Examine descriptively whether multiple-delivery-category differences in delivery performance are visible across traffic categories, and whether traffic-category differences remain visible within multiple-delivery categories. This is not a causal analysis.

## Analytical Context

The standalone multiple-delivery analysis reported increasing mean delivery time across labels 0–3 (22.8763, 26.8559, 40.4549, and 47.8199 minutes) and increasing slow-delivery rates (4.5406%, 7.4008%, 45.7431%, and 100.0000%). Standalone traffic metrics also varied: Jam had the highest mean (31.1766 minutes) and slow rate (20.0099%), while Low had the lowest mean (21.2670 minutes) and slow rate (1.3827%). These Step 5 findings motivate the two-way descriptive check below.

## Two-Way Analysis

- Source: `data/processed/train_clean.csv`; valid numeric targets: **45,593**.
- Slow delivery remains strictly `Time_taken(min) > 40` minutes.
- Categories are preserved as stored; the 30-record comparison minimum is applied to individual combinations.
- Valid targets with both dimensions present: **44,010**.
- Excluded only from this two-way grouping because at least one dimension is missing: **1,583** (missing traffic: 601; missing multiple_deliveries: 993).

### Traffic × Multiple Deliveries Results

| Traffic | multiple_deliveries | Delivery count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow count / denominator | Slow rate | Sample-size status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | 0 | 1,240 | 23.98064516 | 24 | 34 | 42 | 42 / 1,240 | 3.3871% | Qualifies |
| High | 1 | 2,886 | 27.73007623 | 28 | 36 | 136 | 136 / 2,886 | 4.7124% | Qualifies |
| High | 2 | 175 | 39.76 | 39 | 49 | 66 | 66 / 175 | 37.7143% | Qualifies |
| High | 3 | 35 | 47.82857143 | 48 | 53 | 35 | 35 / 35 | 100.0000% | Qualifies |
| Jam | 0 | 3,617 | 27.53884435 | 27 | 42 | 453 | 453 / 3,617 | 12.5242% | Qualifies |
| Jam | 1 | 8,848 | 30.94450723 | 30 | 43 | 1,449 | 1,449 / 8,848 | 16.3766% | Qualifies |
| Jam | 2 | 1,155 | 41.46493506 | 41 | 48 | 634 | 634 / 1,155 | 54.8918% | Qualifies |
| Jam | 3 | 264 | 48.18560606 | 48 | 53 | 264 | 264 / 264 | 100.0000% | Qualifies |
| Low | 0 | 5,774 | 19.24194666 | 18 | 28 | 27 | 27 / 5,774 | 0.4676% | Qualifies |
| Low | 1 | 9,111 | 22.29766217 | 22 | 29 | 124 | 124 / 9,111 | 1.3610% | Qualifies |
| Low | 2 | 173 | 38.65317919 | 39 | 43 | 54 | 54 / 173 | 31.2139% | Qualifies |
| Low | 3 | 5 | 43.6 | 44 | 44 | 5 | 5 / 5 | 100.0000% | Small sample; descriptive only |
| Medium | 0 | 3,276 | 23.69261294 | 23 | 35 | 112 | 112 / 3,276 | 3.4188% | Qualifies |
| Medium | 1 | 6,947 | 27.26846121 | 27 | 38 | 347 | 347 / 6,947 | 4.9950% | Qualifies |
| Medium | 2 | 454 | 38.86343612 | 38 | 44 | 142 | 142 / 454 | 31.2775% | Qualifies |
| Medium | 3 | 50 | 46.18 | 47 | 49 | 50 | 50 / 50 | 100.0000% | Qualifies |

Combination counts sum to **44,010** eligible records; each row appears in exactly one observed category pair. Combination-level ranks are only populated for groups meeting the minimum size.

## Within-Traffic Comparison

Within each traffic category, only combinations with at least 30 records are used to identify the lowest/highest mean and slow-delivery rate. Counts are shown with each identified category.

| Traffic | Lowest mean category (n; mean) | Highest mean category (n; mean) | Lowest slow-rate category (n; rate) | Highest slow-rate category (n; rate) |
| --- | --- | --- | --- | --- |
| High | 0 (1,240; 23.98064516 min) | 3 (35; 47.82857143 min) | 0 (1,240; 3.3871%) | 3 (35; 100.0000%) |
| Jam | 0 (3,617; 27.53884435 min) | 3 (264; 48.18560606 min) | 0 (3,617; 12.5242%) | 3 (264; 100.0000%) |
| Low | 0 (5,774; 19.24194666 min) | 2 (173; 38.65317919 min) | 0 (5,774; 0.4676%) | 2 (173; 31.2139%) |
| Medium | 0 (3,276; 23.69261294 min) | 3 (50; 46.18 min) | 0 (3,276; 3.4188%) | 3 (50; 100.0000%) |

Within-traffic comparison across successive numeric category labels (labels remain categorical; missing or subminimum combinations are not inferred):

| Traffic category | Qualifying multiple-delivery categories | Direction across successive represented labels |
| --- | --- | --- |
| High | 4 | Mean: increasing; slow rate: increasing |
| Jam | 4 | Mean: increasing; slow rate: increasing |
| Low | 3 | Mean: increasing; slow rate: increasing |
| Medium | 4 | Mean: increasing; slow rate: increasing |

## Within-Multiple-Delivery Comparison

For each multiple-delivery category, traffic categories are compared only when the pair contains at least 30 records. Traffic values are treated as distinct category labels, not placed on a numeric or causal scale.

| multiple_deliveries | Lowest mean traffic (n; mean) | Highest mean traffic (n; mean) | Lowest slow-rate traffic (n; rate) | Highest slow-rate traffic (n; rate) |
| --- | --- | --- | --- | --- |
| 0 | Low (5,774; 19.24194666 min) | Jam (3,617; 27.53884435 min) | Low (5,774; 0.4676%) | Jam (3,617; 12.5242%) |
| 1 | Low (9,111; 22.29766217 min) | Jam (8,848; 30.94450723 min) | Low (9,111; 1.3610%) | Jam (8,848; 16.3766%) |
| 2 | Low (173; 38.65317919 min) | Jam (1,155; 41.46493506 min) | Low (173; 31.2139%) | Jam (1,155; 54.8918%) |
| 3 | Medium (50; 46.18 min) | Jam (264; 48.18560606 min) | High (35; 100.0000%); Jam (264; 100.0000%); Medium (50; 100.0000%) | High (35; 100.0000%); Jam (264; 100.0000%); Medium (50; 100.0000%) |

Highest- and lowest-mean traffic categories within each multiple-delivery category:

| multiple_deliveries | Qualifying traffic categories | Observed mean extremes |
| --- | --- | --- |
| 0 | 4 | Jam highest mean (27.53884435 min); Low lowest (19.24194666 min) |
| 1 | 4 | Jam highest mean (30.94450723 min); Low lowest (22.29766217 min) |
| 2 | 4 | Jam highest mean (41.46493506 min); Low lowest (38.65317919 min) |
| 3 | 3 | Jam highest mean (48.18560606 min); Medium lowest (46.18 min) |

## Slow-Delivery Contribution

Across all valid targets, **4,037** deliveries meet the fixed slow rule. Of these, **3,935 (97.47%)** occur in qualifying (n ≥ 30) combinations; **5** occur in subminimum combinations and remain descriptive only; **97** slow records have at least one missing grouping dimension and are not assigned to a combination.
The five qualifying combinations with the largest slow-delivery counts account for **3,147 (77.95%)** of all slow deliveries.

| Traffic | multiple_deliveries | Delivery count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Jam | 1 | 8,848 | 1,449 | 16.3766% | 30.94450723 | 30 | 43 | 1,449 / 4,037 (35.89%) |
| Jam | 2 | 1,155 | 634 | 54.8918% | 41.46493506 | 41 | 48 | 634 / 4,037 (15.70%) |
| Jam | 0 | 3,617 | 453 | 12.5242% | 27.53884435 | 27 | 42 | 453 / 4,037 (11.22%) |
| Medium | 1 | 6,947 | 347 | 4.9950% | 27.26846121 | 27 | 38 | 347 / 4,037 (8.60%) |
| Jam | 3 | 264 | 264 | 100.0000% | 48.18560606 | 48 | 53 | 264 / 4,037 (6.54%) |

## SQL vs Python Validation

SQL from `sql/09_traffic_multiple_delivery_analysis.sql` was run against an in-memory SQLite table (version `3.50.4`). Python independently grouped the same valid-target rows with Pandas and calculated median/P90 using NumPy `percentile(method='linear')`. SQLite implements the same continuous linear interpolation at rank `1 + (n - 1) × p`.

Counts and ranks were compared exactly; floating-point values use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Combination metrics and standalone reference metrics | 232 | MATCH |
| Within-traffic/within-multiple ranks | 120 | MATCH |
| Combination eligibility and slow-count reconciliation | all | MATCH |

## Key Observations

- Across the 4 traffic strata with at least two qualifying multiple-delivery categories, mean delivery time increases at every successive observed numeric multiple-delivery label.
- Slow-delivery rate also increases consistently at each successive observed numeric multiple-delivery label within those strata.
- Among 4 multiple-delivery categories with at least two qualifying traffic comparisons, Jam has the highest mean delivery time in every category.
- Jam has the highest or tied-highest slow-delivery rate in every multiple-delivery category with at least two qualifying traffic comparisons.
- Highest slow-rate ties occur in 1 of the 4 comparable multiple-delivery categories.
- In the standalone analysis, the mean endpoint difference between multiple-delivery labels 0 and 3 was 24.9437 minutes, and the slow-rate difference was 95.4594 percentage points. Conditional endpoint spans are listed below where both endpoints meet the minimum.
- Across 3 traffic categories where both multiple-delivery endpoint groups qualify, the mean endpoint span is smaller than standalone in 3 categories; the slow-rate span is smaller in 1 and larger in 2.

Multiple-delivery endpoint spans within traffic strata (category labels remain categorical; endpoint subtraction is descriptive only):

| Traffic | Mean difference: label 3 − label 0 (min) | Slow-rate difference | Mean span vs standalone | Slow-rate span vs standalone |
| --- | --- | --- | --- | --- |
| High | 23.84792627 | +96.6129 percentage points | smaller mean endpoint span than standalone | larger slow-rate endpoint span than standalone |
| Jam | 20.64676171 | +87.4758 percentage points | smaller mean endpoint span than standalone | smaller slow-rate endpoint span than standalone |
| Low | Not comparable | Not comparable | Not comparable | Not comparable |
| Medium | 22.48738706 | +96.5812 percentage points | smaller mean endpoint span than standalone | larger slow-rate endpoint span than standalone |

## Interpretation

This descriptive two-way analysis checks whether the standalone multiple-delivery and traffic patterns remain visible within categories of the other variable. It does not establish that traffic causes or modifies a multiple-delivery association, nor that multiple deliveries cause delays. Any directional differences are observed associations and may reflect other operational factors.

## Limitations

- This is observational analysis; no causal relationship is established.
- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings, though their counts and metrics remain visible in the two-way table.
- Traffic and multiple-delivery categories may themselves be related to other operational factors.
- This analysis does not control for city, distance, weather, vehicle, courier, or time.
- No regression, machine learning, or formal statistical interaction model was fitted.
- Missing values are not fabricated or silently dropped from the overall valid-target population; they are excluded only from the relevant two-way grouping and reported explicitly.
- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the input schema is unchanged.
