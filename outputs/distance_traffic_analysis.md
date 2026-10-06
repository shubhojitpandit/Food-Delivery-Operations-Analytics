# Distance × Traffic Analysis

## Objective

Describe whether the association between approximate straight-line geographic distance and delivery performance remains visible across traffic categories, and whether traffic differences remain visible across distance bands. This is observational analysis only.

## Analytical Context

Step 5.8 reported slow-delivery rates of 16.2096% in 10–15 km and 16.2934% in 15+ km, compared with 3.0445% in 5–10 km. Its Pearson correlation was -0.00250807 and Spearman correlation was 0.31378161. Step 5.2 reported traffic-category slow rates from 1.3827% (Low) to 20.0099% (Jam). This step considers only exact distance bands × `Road_traffic_density` categories.

## Distance Method

Approximate straight-line geographic distance was recalculated from the four cleaned coordinate fields with the Step 5.8 Haversine implementation: `a = sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)`, and distance `= 2R asin(√a)`. Earth radius is **6,371.0088 km**. Both Python and SQLite calculate it independently.

The exact Step 5.8 half-open bands are `[0,1)`, `[1,2)`, `[2,3)`, `[3,5)`, `[5,10)`, `[10,15)`, and `[15,∞)` km. Boundary values enter the band beginning at that value. Distance is straight-line geographic separation, not actual road/network, driving, or travelled distance.

- Source: `data/processed/train_clean.csv`; 45,593 total rows and 45,593 valid numeric delivery-time targets.
- Coordinate-valid target rows: 45,593; rows excluded for missing/invalid coordinates: 0.
- Missing-coordinate rows: 0; non-numeric-coordinate rows: 0; out-of-range-coordinate rows: 0.
- All valid-target records were assigned to a distance band; 9,065 are in the 15+ km band and remain in the primary analysis.

Distance distribution among valid targets with plausible numeric coordinates:

| Count | Minimum (km) | P25 (km) | Median (km) | P75 (km) | P90 (km) | Maximum (km) | Mean (km) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 45,593 | 1.46506943 | 4.66349958 | 9.26429378 | 13.76399624 | 19.3958335 | 19692.70180715 | 99.30404798 |

Zero distances: 0; negative distances: 0; missing derived distances among coordinate-valid targets: 0.

## Two-Way Analysis

The fixed slow-delivery definition is `Time_taken(min) > 40`; it was not recalculated. Cells with fewer than 30 records remain displayed but are excluded from substantive comparisons and rankings.

### Distance × Traffic Results

Median/P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow rate is slow count / delivery count.

| Distance band | Traffic | Count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow count / n | Slow rate | Eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0-1 km | High | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 0-1 km | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 0-1 km | Low | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 0-1 km | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 1-2 km | High | 972 | 27.38168724 | 27.5 | 38 | 67 | 67 / 972 | 6.8930% | Qualifies |
| 1-2 km | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 1-2 km | Low | 3,058 | 19.56213211 | 19 | 27 | 0 | 0 / 3,058 | 0.0000% | Qualifies |
| 1-2 km | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 2-3 km | High | 128 | 27.0546875 | 27.5 | 35.6 | 8 | 8 / 128 | 6.2500% | Qualifies |
| 2-3 km | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 2-3 km | Low | 396 | 19.60606061 | 19 | 28 | 0 | 0 / 396 | 0.0000% | Qualifies |
| 2-3 km | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 3-5 km | High | 885 | 26.87457627 | 27 | 37 | 47 | 47 / 885 | 5.3107% | Qualifies |
| 3-5 km | Jam | 1,642 | 27.02984166 | 27 | 37 | 92 | 92 / 1,642 | 5.6029% | Qualifies |
| 3-5 km | Low | 3,773 | 19.50649351 | 19 | 27 | 0 | 0 / 3,773 | 0.0000% | Qualifies |
| 3-5 km | Medium | 1,185 | 22.91223629 | 23 | 32 | 0 | 0 / 1,185 | 0.0000% | Qualifies |
| 5-10 km | High | 2,415 | 27.30186335 | 27 | 38 | 155 | 155 / 2,415 | 6.4182% | Qualifies |
| 5-10 km | Jam | 3,484 | 27.17738232 | 27 | 37 | 210 | 210 / 3,484 | 6.0276% | Qualifies |
| 5-10 km | Low | 2,273 | 19.41399032 | 19 | 27 | 0 | 0 / 2,273 | 0.0000% | Qualifies |
| 5-10 km | Medium | 3,890 | 22.91748072 | 23 | 32 | 0 | 0 / 3,890 | 0.0000% | Qualifies |
| 10-15 km | High | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| 10-15 km | Jam | 5,213 | 33.5142912 | 35 | 46 | 1,435 | 1,435 / 5,213 | 27.5273% | Qualifies |
| 10-15 km | Low | 3,412 | 24.08704572 | 23 | 36 | 121 | 121 / 3,412 | 3.5463% | Qualifies |
| 10-15 km | Medium | 3,440 | 30.05436047 | 30 | 41.1 | 401 | 401 / 3,440 | 11.6570% | Qualifies |
| 15+ km | High | 25 | 29.64 | 28 | 41.8 | 3 | 3 / 25 | 12.0000% | Small sample; descriptive only |
| 15+ km | Jam | 3,804 | 33.42586751 | 35 | 46 | 1,093 | 1,093 / 3,804 | 28.7329% | Qualifies |
| 15+ km | Low | 2,565 | 24.03625731 | 23 | 36 | 93 | 93 / 2,565 | 3.6257% | Qualifies |
| 15+ km | Medium | 2,432 | 29.84950658 | 30 | 41 | 258 | 258 / 2,432 | 10.6086% | Qualifies |

## Within-Traffic Distance Comparison

All cells meeting n ≥ 30 are listed. Ranks use 1 for the lowest mean/rate; ties share ranks. Min/max labels include count, median, and P90.

| Traffic | Distance band | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | 1-2 km | 972 | 27.38168724 | 27.5 | 38 | 67 / 972 | 6.8930% | 4 | 4 |
| High | 2-3 km | 128 | 27.0546875 | 27.5 | 35.6 | 8 / 128 | 6.2500% | 2 | 2 |
| High | 3-5 km | 885 | 26.87457627 | 27 | 37 | 47 / 885 | 5.3107% | 1 | 1 |
| High | 5-10 km | 2,415 | 27.30186335 | 27 | 38 | 155 / 2,415 | 6.4182% | 3 | 3 |
| Jam | 3-5 km | 1,642 | 27.02984166 | 27 | 37 | 92 / 1,642 | 5.6029% | 1 | 1 |
| Jam | 5-10 km | 3,484 | 27.17738232 | 27 | 37 | 210 / 3,484 | 6.0276% | 2 | 2 |
| Jam | 10-15 km | 5,213 | 33.5142912 | 35 | 46 | 1,435 / 5,213 | 27.5273% | 4 | 3 |
| Jam | 15+ km | 3,804 | 33.42586751 | 35 | 46 | 1,093 / 3,804 | 28.7329% | 3 | 4 |
| Low | 1-2 km | 3,058 | 19.56213211 | 19 | 27 | 0 / 3,058 | 0.0000% | 3 | 1 |
| Low | 2-3 km | 396 | 19.60606061 | 19 | 28 | 0 / 396 | 0.0000% | 4 | 1 |
| Low | 3-5 km | 3,773 | 19.50649351 | 19 | 27 | 0 / 3,773 | 0.0000% | 2 | 1 |
| Low | 5-10 km | 2,273 | 19.41399032 | 19 | 27 | 0 / 2,273 | 0.0000% | 1 | 1 |
| Low | 10-15 km | 3,412 | 24.08704572 | 23 | 36 | 121 / 3,412 | 3.5463% | 6 | 5 |
| Low | 15+ km | 2,565 | 24.03625731 | 23 | 36 | 93 / 2,565 | 3.6257% | 5 | 6 |
| Medium | 3-5 km | 1,185 | 22.91223629 | 23 | 32 | 0 / 1,185 | 0.0000% | 1 | 1 |
| Medium | 5-10 km | 3,890 | 22.91748072 | 23 | 32 | 0 / 3,890 | 0.0000% | 2 | 1 |
| Medium | 10-15 km | 3,440 | 30.05436047 | 30 | 41.1 | 401 / 3,440 | 11.6570% | 4 | 4 |
| Medium | 15+ km | 2,432 | 29.84950658 | 30 | 41 | 258 / 2,432 | 10.6086% | 3 | 3 |

| Traffic | Qualifying distance bands | Lowest mean | Highest mean | Lowest slow rate | Highest slow rate |
| --- | --- | --- | --- | --- | --- |
| High | 4 | 3-5 km (n=885; 26.87457627 min; median 27; P90 37) | 1-2 km (n=972; 27.38168724 min; median 27.5; P90 38) | 3-5 km (n=885; 5.3107%; median 27; P90 37) | 1-2 km (n=972; 6.8930%; median 27.5; P90 38) |
| Jam | 4 | 3-5 km (n=1,642; 27.02984166 min; median 27; P90 37) | 10-15 km (n=5,213; 33.5142912 min; median 35; P90 46) | 3-5 km (n=1,642; 5.6029%; median 27; P90 37) | 15+ km (n=3,804; 28.7329%; median 35; P90 46) |
| Low | 6 | 5-10 km (n=2,273; 19.41399032 min; median 19; P90 27) | 10-15 km (n=3,412; 24.08704572 min; median 23; P90 36) | 1-2 km (n=3,058; 0.0000%; median 19; P90 27); 2-3 km (n=396; 0.0000%; median 19; P90 28); 3-5 km (n=3,773; 0.0000%; median 19; P90 27); 5-10 km (n=2,273; 0.0000%; median 19; P90 27) | 15+ km (n=2,565; 3.6257%; median 23; P90 36) |
| Medium | 4 | 3-5 km (n=1,185; 22.91223629 min; median 23; P90 32) | 10-15 km (n=3,440; 30.05436047 min; median 30; P90 41.1) | 3-5 km (n=1,185; 0.0000%; median 23; P90 32); 5-10 km (n=3,890; 0.0000%; median 23; P90 32) | 10-15 km (n=3,440; 11.6570%; median 30; P90 41.1) |

Observed sequences across qualifying bands (ordered by increasing distance; no monotonicity is assumed):

| Traffic | Qualifying bands | Mean sequence | Slow-rate sequence |
| --- | --- | --- | --- |
| High | 4 | mixed / ties | mixed / ties |
| Jam | 4 | mixed / ties | increasing |
| Low | 6 | mixed / ties | mixed / ties |
| Medium | 4 | mixed / ties | mixed / ties |

## Within-Distance Traffic Comparison

Only traffic cells with at least 30 records in a given distance band are ranked or compared.

| Distance band | Traffic | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1-2 km | Low | 3,058 | 19.56213211 | 19 | 27 | 0 / 3,058 | 0.0000% | 1 | 1 |
| 1-2 km | High | 972 | 27.38168724 | 27.5 | 38 | 67 / 972 | 6.8930% | 2 | 2 |
| 2-3 km | Low | 396 | 19.60606061 | 19 | 28 | 0 / 396 | 0.0000% | 1 | 1 |
| 2-3 km | High | 128 | 27.0546875 | 27.5 | 35.6 | 8 / 128 | 6.2500% | 2 | 2 |
| 3-5 km | Low | 3,773 | 19.50649351 | 19 | 27 | 0 / 3,773 | 0.0000% | 1 | 1 |
| 3-5 km | Medium | 1,185 | 22.91223629 | 23 | 32 | 0 / 1,185 | 0.0000% | 2 | 1 |
| 3-5 km | High | 885 | 26.87457627 | 27 | 37 | 47 / 885 | 5.3107% | 3 | 3 |
| 3-5 km | Jam | 1,642 | 27.02984166 | 27 | 37 | 92 / 1,642 | 5.6029% | 4 | 4 |
| 5-10 km | Low | 2,273 | 19.41399032 | 19 | 27 | 0 / 2,273 | 0.0000% | 1 | 1 |
| 5-10 km | Medium | 3,890 | 22.91748072 | 23 | 32 | 0 / 3,890 | 0.0000% | 2 | 1 |
| 5-10 km | Jam | 3,484 | 27.17738232 | 27 | 37 | 210 / 3,484 | 6.0276% | 3 | 3 |
| 5-10 km | High | 2,415 | 27.30186335 | 27 | 38 | 155 / 2,415 | 6.4182% | 4 | 4 |
| 10-15 km | Low | 3,412 | 24.08704572 | 23 | 36 | 121 / 3,412 | 3.5463% | 1 | 1 |
| 10-15 km | Medium | 3,440 | 30.05436047 | 30 | 41.1 | 401 / 3,440 | 11.6570% | 2 | 2 |
| 10-15 km | Jam | 5,213 | 33.5142912 | 35 | 46 | 1,435 / 5,213 | 27.5273% | 3 | 3 |
| 15+ km | Low | 2,565 | 24.03625731 | 23 | 36 | 93 / 2,565 | 3.6257% | 1 | 1 |
| 15+ km | Medium | 2,432 | 29.84950658 | 30 | 41 | 258 / 2,432 | 10.6086% | 2 | 2 |
| 15+ km | Jam | 3,804 | 33.42586751 | 35 | 46 | 1,093 / 3,804 | 28.7329% | 3 | 3 |

Traffic-category orders (highest to lowest) where at least two traffic cells qualify:

| Distance band | Qualifying traffic categories | Mean order | Slow-rate order |
| --- | --- | --- | --- |
| 1-2 km | 2 | High > Low | High > Low |
| 2-3 km | 2 | High > Low | High > Low |
| 3-5 km | 4 | Jam > High > Medium > Low | Jam > High > Low > Medium |
| 5-10 km | 4 | High > Jam > Medium > Low | High > Jam > Low > Medium |
| 10-15 km | 3 | Jam > Medium > Low | Jam > Medium > Low |
| 15+ km | 3 | Jam > Medium > Low | Jam > Medium > Low |

## 10 km Signal Check

The comparison reference within each traffic category is the highest slow-delivery rate among qualifying bands below 10 km. The exact 10–15 km and 15+ km bands are compared separately; no additional distance category is created. Every entry uses n ≥ 30 cells.

| Traffic | Band / comparison | Count(s) | Slow rate(s) | Below-10 km reference | Difference / assessment |
| --- | --- | --- | --- | --- | --- |
| Standalone all-traffic comparison | 5-10 km | 12,186 | 3.0445% maximum among qualifying <10 km bands | — | 10-15: 16.2096%; 15+: 16.2934% |
| High | 10-15 km | Not comparable | Not comparable | Not comparable | No qualifying short-distance reference or long-distance cell |
| High | 15+ km | Not comparable | Not comparable | Not comparable | No qualifying short-distance reference or long-distance cell |
| High | 15+ vs 10-15 comparison | Not comparable | Not comparable | Not comparable | One or both long-band cells do not meet n ≥ 30 |
| Jam | 10-15 km | 5,213 | 27.5273% | 6.0276% | +21.4998 pp; elevated |
| Jam | 15+ km | 3,804 | 28.7329% | 6.0276% | +22.7054 pp; elevated |
| Jam | 15+ vs 10-15 comparison | 3,804 vs 5,213 | 28.7329% vs 27.5273% | — | Slow-rate delta +1.2056 pp; mean delta -0.0884 min |
| Low | 10-15 km | 3,412 | 3.5463% | 0.0000% | +3.5463 pp; elevated |
| Low | 15+ km | 2,565 | 3.6257% | 0.0000% | +3.6257 pp; elevated |
| Low | 15+ vs 10-15 comparison | 2,565 vs 3,412 | 3.6257% vs 3.5463% | — | Slow-rate delta +0.0794 pp; mean delta -0.0508 min |
| Medium | 10-15 km | 3,440 | 11.6570% | 0.0000% | +11.6570 pp; elevated |
| Medium | 15+ km | 2,432 | 10.6086% | 0.0000% | +10.6086 pp; elevated |
| Medium | 15+ vs 10-15 comparison | 2,432 vs 3,440 | 10.6086% vs 11.6570% | — | Slow-rate delta -1.0484 pp; mean delta -0.2049 min |

Across traffic strata with qualifying reference and long-band cells, the 10–15 km rate is above the within-traffic <10 km reference in 3 categories; the 15+ km rate is above it in 3 categories. These counts describe consistency, not causation.

## Extreme Distance Check

All 9,065 records in the 15+ km band, including the exact ten largest records below, are retained in primary results. Their extreme values are the same rows inspected in Step 5.8.

| ID | Approx. straight-line distance (km) | Time_taken(min) | Traffic category | Distance band |
| --- | --- | --- | --- | --- |
| 0xbf01 | 19692.70180715 | 28 | NULL | 15+ km |
| 0xc014 | 19688.02848227 | 46 | Jam | 15+ km |
| 0xbf10 | 19683.71474898 | 22 | Jam | 15+ km |
| 0xc012 | 19677.2077312 | 15 | Low | 15+ km |
| 0x3ef | 19070.43445074 | 32 | NULL | 15+ km |
| 0x462 | 19070.36418053 | 15 | NULL | 15+ km |
| 0x509 | 19069.1852858 | 29 | NULL | 15+ km |
| 0x3ed | 19068.27330049 | 44 | NULL | 15+ km |
| 0x481 | 19067.15488338 | 29 | NULL | 15+ km |
| 0x4d7 | 19066.17707742 | 21 | Jam | 15+ km |

A separate sensitivity recalculates affected cells after omitting only these ten rows; the primary results above include them. Of these ten records, 4 have a traffic category and 6 have missing traffic, so only the former enter two-way sensitivity cells. Across 2 qualifying affected cells, the maximum absolute mean change is 0.003524 minutes and the maximum absolute slow-rate change is 0.0036 percentage points. Considering all qualifying traffic categories in affected distance bands, traffic mean order changed in 0 band(s) and slow-rate order in 0 band(s). This measures the influence of the ten largest-distance records only; the 15+ km group as a whole is not excluded.

| Band | Traffic | Top-10 records | Primary n | Sensitivity n | Primary mean | Without top 10 mean | Mean delta | Primary slow rate | Without top 10 rate | Rate delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15+ km | Jam | 3 | 3,804 | 3,801 | 33.42586751 | 33.42883452 | +0.002967 | 28.7329% | 28.7293% | -0.0036 pp |
| 15+ km | Low | 1 | 2,565 | 2,564 | 24.03625731 | 24.03978159 | +0.003524 | 3.6257% | 3.6271% | +0.0014 pp |

## Slow-Delivery Contribution

Across all valid targets, 4,037 deliveries are slow. Of these, 3,980 occur in qualifying Distance × traffic cells, 3 in subminimum cells, 54 have missing traffic among coordinate-valid targets, and 0 are excluded for coordinate issues. The five qualifying cells with the largest slow counts contribute 3,397 (84.15%) of all slow deliveries.

| Distance band | Traffic | Count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10-15 km | Jam | 5,213 | 1,435 | 27.5273% | 33.5142912 | 35 | 46 | 1,435 / 4,037 (35.55%) |
| 15+ km | Jam | 3,804 | 1,093 | 28.7329% | 33.42586751 | 35 | 46 | 1,093 / 4,037 (27.07%) |
| 10-15 km | Medium | 3,440 | 401 | 11.6570% | 30.05436047 | 30 | 41.1 | 401 / 4,037 (9.93%) |
| 15+ km | Medium | 2,432 | 258 | 10.6086% | 29.84950658 | 30 | 41 | 258 / 4,037 (6.39%) |
| 5-10 km | Jam | 3,484 | 210 | 6.0276% | 27.17738232 | 27 | 37 | 210 / 4,037 (5.20%) |

## SQL vs Python Validation

SQL from `sql/11_distance_traffic_analysis.sql` ran in in-memory SQLite 3.50.4. Python independently calculated Haversine distance, band assignments, cell metrics, and rankings. Counts/ranks matched exactly; floating values use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Population and coordinate-validity counts | 12 | MATCH |
| Haversine row values and band assignments | 45,593 rows; max absolute difference 5.46e-11 km | MATCH |
| Distance × traffic cell metrics and ranks | 91,368 metric/population checks; 144 rank checks | MATCH |
| Top-10 extreme record identities/order | 10 | MATCH |
| Distance-band assignment coverage | 45,593 / 45,593 | MATCH |

## Key Observations

- Within-traffic mean delivery time increased across all observed qualifying distance bands in 0 of 4 comparable traffic categories; slow rate increased monotonically in 1. At least one metric was mixed or tied in 4 categories. Jam's sequence is mixed for mean but increasing for slow rate; High, Low, and Medium have mixed/tied sequences for at least one measure.
- Standalone, the 10–15 km and 15+ km slow rates (16.2096% and 16.2934%) exceeded the highest qualifying below-10 km rate (3.0445%). Within traffic, they exceed the short-band reference in 3 and 3 comparable strata respectively.
- Among comparable traffic categories, the largest 10+ km excess over the <10 km slow-rate reference occurs in Jam; the excess is smaller in Medium and Low. High has no qualifying 10+ km cell, so its pattern is not comparable under the minimum-size rule. For Jam, Low, and Medium, 15+ km slow rates are close to their 10–15 km rates, with category-specific differences shown above.
- The ten largest geographic distances are retained. Removing those ten only in the labeled sensitivity changed affected cell mean by at most 0.003524 minutes and slow rate by at most 0.0036 percentage points; see affected cells above.
- Traffic comparisons within distance bands vary by band; consult the qualifying counts and full rankings rather than generalizing from one category.

## Interpretation

The tables describe observed delivery-time patterns across distance bands within traffic categories, and traffic patterns within distance bands. The elevated standalone 10+ km slow rates are assessed against qualifying shorter bands separately for each traffic category. Straight-line geographic distance is only an approximation of actual travel conditions and does not establish a causal explanation. Extreme observations remain included in the primary results.

## Limitations

- This is observational analysis; no causal relationship is established.
- Haversine distance is approximate straight-line geographic separation, not actual road/network distance.
- Combinations with fewer than 30 records are excluded from substantive comparison and ranking, while their counts remain displayed.
- Extreme geographic values were retained in the primary analysis; the top-ten-excluded calculation is clearly labeled as sensitivity only.
- Traffic and distance may be related to other operational factors.
- No regression, machine learning, or formal interaction model was fitted.
- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.
- This analysis does not add weather, city, vehicle, courier, multiple deliveries, or time.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; the source schema is unchanged and no distance column was persisted.
