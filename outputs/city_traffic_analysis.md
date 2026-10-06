# City × Traffic Analysis

## Objective

Describe whether observed city-level delivery-time differences remain visible within traffic categories, and whether traffic differences remain visible within cities. This is observational; it does not establish causality.

## Analytical Context

The standalone City analysis reported means of 22.9840 minutes for Urban (n=10,136), 27.3152 for Metropolitan (n=34,093), and 49.7317 for Semi-Urban (n=164); Semi-Urban's slow-delivery rate was 100% (164/164). Standalone traffic results ranged from a 21.2670-minute mean and 1.3827% slow rate in Low traffic to a 31.1766-minute mean and 20.0099% slow rate in Jam. This step stratifies only by City × `Road_traffic_density`.

## Two-Way Analysis

- Source: `data/processed/train_clean.csv`; 45,593 rows and 45,593 valid numeric targets.
- Fixed slow rule: `Time_taken(min) > 40`; no group-specific threshold was calculated.
- 1,200 valid targets have missing City; 601 have missing traffic; 1,780 are excluded from the two-way cells because either dimension is missing.
- Every observed City × traffic cell is shown. Cells with fewer than 30 targets remain visible as descriptive results but are not ranked or used for substantive comparisons.

### City × Traffic Results

Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow rate is slow count / delivery count.

| City | Traffic | Count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow rate (numerator / denominator) | Eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Metropolitan | High | 3,365 | 28.10846954 | 28 | 38 | 231 | 231 / 3,365 (6.8648%) | Qualifies |
| Metropolitan | Jam | 11,090 | 31.91009919 | 32 | 44 | 2,321 | 2,321 / 11,090 (20.9288%) | Qualifies |
| Metropolitan | Low | 10,852 | 22.12965352 | 22 | 30 | 193 | 193 / 10,852 (1.7785%) | Qualifies |
| Metropolitan | Medium | 8,322 | 27.611031 | 27 | 39 | 558 | 558 / 8,322 (6.7051%) | Qualifies |
| Semi-Urban | High | 17 | 50.05882353 | 49 | 53.4 | 17 | 17 / 17 (100.0000%) | Small sample; descriptive only |
| Semi-Urban | Jam | 135 | 49.88888889 | 49 | 54 | 135 | 135 / 135 (100.0000%) | Qualifies |
| Semi-Urban | Medium | 11 | 47.45454545 | 48 | 49 | 11 | 11 / 11 (100.0000%) | Small sample; descriptive only |
| Urban | High | 945 | 24.12592593 | 24 | 34 | 30 | 30 / 945 (3.1746%) | Qualifies |
| Urban | Jam | 2,627 | 27.74343357 | 27 | 42 | 351 | 351 / 2,627 (13.3612%) | Qualifies |
| Urban | Low | 4,093 | 19.24407525 | 18 | 28 | 18 | 18 / 4,093 (0.4398%) | Qualifies |
| Urban | Medium | 2,356 | 23.73089983 | 23 | 35 | 81 | 81 / 2,356 (3.4380%) | Qualifies |

## Within-City Traffic Comparison

Extremes use only qualifying traffic cells within each city; counts are included, and ties are retained.

| City | Observed cells (counts) | Qualifying traffic categories | Lowest mean traffic | Highest mean traffic | Lowest slow-rate traffic | Highest slow-rate traffic |
| --- | --- | --- | --- | --- | --- | --- |
| Metropolitan | High (n=3,365); Jam (n=11,090); Low (n=10,852); Medium (n=8,322) | 4 | Low (n=10,852; 22.12965352 min) | Jam (n=11,090; 31.91009919 min) | Low (n=10,852; 1.7785%) | Jam (n=11,090; 20.9288%) |
| Semi-Urban | High (n=17); Jam (n=135); Medium (n=11) | 1 | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) | Not comparable (fewer than 2 qualifying groups) |
| Urban | High (n=945); Jam (n=2,627); Low (n=4,093); Medium (n=2,356) | 4 | Low (n=4,093; 19.24407525 min) | Jam (n=2,627; 27.74343357 min) | Low (n=4,093; 0.4398%) | Jam (n=2,627; 13.3612%) |

Traffic category rankings by mean and slow rate within each city:

| City | Qualifying cells | Mean order (highest to lowest) | Slow-rate order (highest to lowest) |
| --- | --- | --- | --- |
| Metropolitan | 4 | Jam > High > Medium > Low | Jam > High > Medium > Low |
| Urban | 4 | Jam > High > Medium > Low | Jam > Medium > High > Low |

## Within-Traffic City Comparison

Only cells with n ≥ 30 are shown in this comparison. Mean rank and slow-rate rank use 1 for the lowest value; ties share ranks.

| Traffic | City | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | Urban | 945 | 24.12592593 | 24 | 34 | 30 / 945 | 3.1746% | 1 | 1 |
| High | Metropolitan | 3,365 | 28.10846954 | 28 | 38 | 231 / 3,365 | 6.8648% | 2 | 2 |
| Jam | Urban | 2,627 | 27.74343357 | 27 | 42 | 351 / 2,627 | 13.3612% | 1 | 1 |
| Jam | Metropolitan | 11,090 | 31.91009919 | 32 | 44 | 2,321 / 11,090 | 20.9288% | 2 | 2 |
| Jam | Semi-Urban | 135 | 49.88888889 | 49 | 54 | 135 / 135 | 100.0000% | 3 | 3 |
| Low | Urban | 4,093 | 19.24407525 | 18 | 28 | 18 / 4,093 | 0.4398% | 1 | 1 |
| Low | Metropolitan | 10,852 | 22.12965352 | 22 | 30 | 193 / 10,852 | 1.7785% | 2 | 2 |
| Medium | Urban | 2,356 | 23.73089983 | 23 | 35 | 81 / 2,356 | 3.4380% | 1 | 1 |
| Medium | Metropolitan | 8,322 | 27.611031 | 27 | 39 | 558 / 8,322 | 6.7051% | 2 | 2 |

City category rankings by mean and slow rate within each traffic category:

| Traffic | Qualifying cities | Mean order (highest to lowest) | Slow-rate order (highest to lowest) |
| --- | --- | --- | --- |
| High | 2 | Metropolitan > Urban | Metropolitan > Urban |
| Jam | 3 | Semi-Urban > Metropolitan > Urban | Semi-Urban > Metropolitan > Urban |
| Low | 2 | Metropolitan > Urban | Metropolitan > Urban |
| Medium | 2 | Metropolitan > Urban | Metropolitan > Urban |

## Semi-Urban Signal Check

Standalone Semi-Urban differences versus the highest standalone non-Semi-Urban city were 22.4165 minutes in mean delivery time and 90.1651 percentage points in slow rate (mean peer: Metropolitan; slow-rate peer: Metropolitan).

| Traffic | Semi-Urban sample | Semi mean (min) | Semi slow rate | Mean gap vs highest other qualifying city | Slow-rate gap vs highest other qualifying city | Within-stratum position |
| --- | --- | --- | --- | --- | --- | --- |
| High | 17 (below 30) | Not comparable | Not comparable | Not comparable | Not comparable | Semi-Urban cell below 30; not comparable with peer cities |
| Jam | 135 (qualifies) | 49.88888889 | 100.0000% | +17.9788 min vs highest non-Semi-Urban mean | +79.0712 pp vs highest non-Semi-Urban rate | highest mean; highest rate |
| Low | No | Not comparable | Not comparable | Not comparable | Not comparable | No Semi-Urban cell; not comparable |
| Medium | 11 (below 30) | Not comparable | Not comparable | Not comparable | Not comparable | Semi-Urban cell below 30; not comparable with peer cities |

Semi-Urban is comparable to at least one other qualifying city in 1 traffic categories: Jam. Across those comparisons, the mean gap narrowed in 1, widened in 0, and reversed in 0; the slow-rate gap narrowed in 1, widened in 0, and reversed in 0. A stratum without a qualifying Semi-Urban cell or qualifying peer is explicitly not compared.

## Slow-Delivery Contribution

Across all valid targets, 4,037 deliveries meet the fixed slow rule. Of these, 3,918 occur in qualifying cells, 28 occur in subminimum cells, and 91 have at least one missing grouping dimension. The five qualifying cells with the largest slow counts account for 3,654 (90.51%) of all slow deliveries.

| City | Traffic | Count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Metropolitan | Jam | 11,090 | 2,321 | 20.9288% | 31.91009919 | 32 | 44 | 2,321 / 4,037 (57.49%) |
| Metropolitan | Medium | 8,322 | 558 | 6.7051% | 27.611031 | 27 | 39 | 558 / 4,037 (13.82%) |
| Urban | Jam | 2,627 | 351 | 13.3612% | 27.74343357 | 27 | 42 | 351 / 4,037 (8.69%) |
| Metropolitan | High | 3,365 | 231 | 6.8648% | 28.10846954 | 28 | 38 | 231 / 4,037 (5.72%) |
| Metropolitan | Low | 10,852 | 193 | 1.7785% | 22.12965352 | 22 | 30 | 193 / 4,037 (4.78%) |

## SQL vs Python Validation

SQL from `sql/10_city_traffic_analysis.sql` ran in in-memory SQLite 3.50.4; Pandas independently grouped the cleaned source. SQLite percentile values use the same continuous linear interpolation as NumPy. Counts and ranks were compared exactly; floating metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Cell metrics, standalone references, and population counts | 162 | MATCH |
| Within-city and within-traffic rankings | 72 | MATCH |
| Cell eligibility and slow-count reconciliation | all | MATCH |
| Semi-Urban qualifying-cell comparisons | 1 | MATCH |

## Key Observations

- Across 4 traffic strata where both Metropolitan and Urban qualify, Metropolitan has a higher mean in 4 and a higher slow rate in 4; Semi-Urban is comparable to other cities only in Jam traffic stratum.
- Among 2 cities with at least two qualifying traffic categories, the highest/lowest mean traffic labels are Jam / Low; the highest/lowest slow-rate labels are Jam / Low. Consistency is 2/2 and 2/2 for highest and lowest mean, and 2/2 and 2/2 for highest and lowest slow rate. Full per-city orders appear above.
- The qualifying coverage is 9 of 11 observed cells. Read every ranking alongside its count; single-group city strata are not labeled as within-city comparisons.
- Standalone Semi-Urban had a 22.4165-minute mean gap and a 90.1651-percentage-point slow-rate gap versus the highest other standalone city. The within-traffic comparisons show those gaps narrowed in 1/1 and 1/1 comparable traffic categories respectively; direction changes are counted separately.
- The five largest qualifying slow-delivery contributors account for 3,654 of 4,037 slow deliveries; contribution depends on both group volume and its slow rate.

## Interpretation

The two-way tables show whether the standalone city and traffic differences remain visible within observed strata. Semi-Urban's position is assessed only where both the Semi-Urban cell and another city cell meet the 30-record rule; no value is imputed or comparison manufactured for nonqualifying cells. All differences are descriptive associations and do not show that city or traffic causes delivery-time differences.

## Limitations

- This is observational analysis; no causal relationship is established.
- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings; all observed cells and counts remain displayed.
- City and traffic may be related to other operational factors.
- This analysis does not control for distance, weather, vehicle, courier, multiple deliveries, or time.
- No regression, machine learning, or formal interaction model was fitted.
- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision.
- Missing City/traffic values are excluded only from the two-way grouping and reported above; no observations are silently removed from the source.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the source schema is unchanged.
