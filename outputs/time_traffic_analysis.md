# Time × Traffic Analysis

## Objective

Describe whether traffic-related delivery-performance differences remain visible across the established order-time bands, and whether time-of-day patterns remain visible within traffic categories. This is observational analysis only.

## Analytical Context

The standalone Traffic analysis found the longest observed delivery times and highest slow-delivery rate in Jam, while Low had the shortest times and lowest slow rate. The standalone Time analysis found higher order-time means and slow rates in Evening than Morning. This combined analysis checks those descriptive patterns within the second dimension.

Standalone traffic results:

| Traffic category | Count | Mean (min) | Slow rate |
| --- | --- | --- | --- |
| High | 4,425 | 27.24 | 6.3277% |
| Jam | 14,143 | 31.176624 | 20.0099% |
| Low | 15,477 | 21.266977 | 1.3827% |
| Medium | 10,947 | 26.699644 | 6.0199% |

Standalone order-time results:

| Time band | Count | Mean (min) | Slow rate |
| --- | --- | --- | --- |
| Night | 430 | 22.169767 | 2.5581% |
| Morning | 7,718 | 21.27546 | 1.3475% |
| Afternoon | 4,049 | 25.640158 | 4.0504% |
| Evening | 17,892 | 29.21082 | 13.2294% |
| Late Night | 13,773 | 25.637552 | 8.9087% |

## Data Coverage

- Total valid-target records: **45,593** of 45,593.
- Valid order times: **43,862**.
- Missing/invalid order times: **1,731**.
- Valid-target records with missing traffic: **601**.
- Valid time but missing traffic: **0**; invalid time but valid traffic: **1,130**.
- Records with both a valid time band and traffic category: **43,862**.
- Records excluded from the two-way grouping due to at least one missing/invalid dimension: **1,731**.
Missing and invalid dimensions are reported rather than assigned a fabricated band or traffic category; no source rows are modified.

## Time-Band Method

`Time_Orderd` is parsed strictly as `HH:MM:SS`, then converted to minutes after midnight. The classification is inherited unchanged from Step 5.7: Night (00:00–05:59), Morning (06:00–11:59), Afternoon (12:00–16:59), Evening (17:00–20:59), and Late Night (21:00–23:59). Values that are missing, malformed, or outside a valid clock time are not classified and are counted separately.

## Two-Way Analysis

Slow delivery is the fixed global condition `Time_taken(min) > 40`. Medians and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (`numpy.percentile(method='linear')`). All five established time bands crossed with each observed non-missing traffic category are shown. Cells with fewer than 30 records are descriptive only and excluded from substantive comparisons and rankings.

### Time × Traffic Results

| Time band | Traffic | Count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow count / n | Slow rate | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Night | High | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Night | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Night | Low | 430 | 22.169767 | 21 | 30 | 11 | 11 / 430 | 2.5581% | Qualifies |
| Night | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Morning | High | 1,769 | 27.163369 | 27 | 37 | 104 | 104 / 1,769 | 5.8790% | Qualifies |
| Morning | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Morning | Low | 5,949 | 19.524626 | 19 | 27 | 0 | 0 / 5,949 | 0.0000% | Qualifies |
| Morning | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Afternoon | High | 2,553 | 27.239718 | 27 | 38 | 164 | 164 / 2,553 | 6.4238% | Qualifies |
| Afternoon | Jam | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Afternoon | Low | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Afternoon | Medium | 1,496 | 22.910428 | 23 | 32 | 0 | 0 / 1,496 | 0.0000% | Qualifies |
| Evening | High | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Evening | Jam | 8,710 | 31.184845 | 31 | 44 | 1,722 | 1,722 / 8,710 | 19.7704% | Qualifies |
| Evening | Low | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Evening | Medium | 9,182 | 27.338271 | 27 | 39 | 645 | 645 / 9,182 | 7.0246% | Qualifies |
| Late Night | High | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |
| Late Night | Jam | 5,090 | 31.102161 | 31 | 44 | 1,026 | 1,026 / 5,090 | 20.1572% | Qualifies |
| Late Night | Low | 8,683 | 22.434182 | 22 | 32 | 201 | 201 / 8,683 | 2.3149% | Qualifies |
| Late Night | Medium | 0 | — | — | — | 0 | 0 / 0 | — | Small sample; descriptive only |

## Within-Time Traffic Comparison

For each time band, extrema are selected only among cells with at least 30 records. Counts, means, medians, P90, and slow rates are included in the extrema descriptions; the complete cell metrics are available above.

| Time band | Qualifying traffic categories | Traffic extrema by mean and slow rate |
| --- | --- | --- |
| Night | 1 | Lowest/highest mean: Low (n=430; 22.1698 min; median 21; P90 30) / Low (n=430; 22.1698 min; median 21; P90 30); lowest/highest slow rate: Low (n=430; 2.5581%; median 21; P90 30) / Low (n=430; 2.5581%; median 21; P90 30) |
| Morning | 2 | Lowest/highest mean: Low (n=5,949; 19.5246 min; median 19; P90 27) / High (n=1,769; 27.1634 min; median 27; P90 37); lowest/highest slow rate: Low (n=5,949; 0.0000%; median 19; P90 27) / High (n=1,769; 5.8790%; median 27; P90 37) |
| Afternoon | 2 | Lowest/highest mean: Medium (n=1,496; 22.9104 min; median 23; P90 32) / High (n=2,553; 27.2397 min; median 27; P90 38); lowest/highest slow rate: Medium (n=1,496; 0.0000%; median 23; P90 32) / High (n=2,553; 6.4238%; median 27; P90 38) |
| Evening | 2 | Lowest/highest mean: Medium (n=9,182; 27.3383 min; median 27; P90 39) / Jam (n=8,710; 31.1848 min; median 31; P90 44); lowest/highest slow rate: Medium (n=9,182; 7.0246%; median 27; P90 39) / Jam (n=8,710; 19.7704%; median 31; P90 44) |
| Late Night | 2 | Lowest/highest mean: Low (n=8,683; 22.4342 min; median 22; P90 32) / Jam (n=5,090; 31.1022 min; median 31; P90 44); lowest/highest slow rate: Low (n=8,683; 2.3149%; median 22; P90 32) / Jam (n=5,090; 20.1572%; median 31; P90 44) |

Qualifying traffic-category detail by time band:

| Time band | Qualifying traffic categories | Category metrics |
| --- | --- | --- |
| Night | 1 | Low (n=430; mean 22.169767; median 21; P90 30; slow 11/430 (2.5581%)) |
| Morning | 2 | High (n=1,769; mean 27.163369; median 27; P90 37; slow 104/1,769 (5.8790%)); Low (n=5,949; mean 19.524626; median 19; P90 27; slow 0/5,949 (0.0000%)) |
| Afternoon | 2 | High (n=2,553; mean 27.239718; median 27; P90 38; slow 164/2,553 (6.4238%)); Medium (n=1,496; mean 22.910428; median 23; P90 32; slow 0/1,496 (0.0000%)) |
| Evening | 2 | Jam (n=8,710; mean 31.184845; median 31; P90 44; slow 1,722/8,710 (19.7704%)); Medium (n=9,182; mean 27.338271; median 27; P90 39; slow 645/9,182 (7.0246%)) |
| Late Night | 2 | Jam (n=5,090; mean 31.102161; median 31; P90 44; slow 1,026/5,090 (20.1572%)); Low (n=8,683; mean 22.434182; median 22; P90 32; slow 201/8,683 (2.3149%)) |

Qualifying traffic categories ordered from highest to lowest within each time band:

| Time band | Mean order | Slow-rate order | Qualifying cells |
| --- | --- | --- | --- |
| Night | Low | Low | 1 |
| Morning | High → Low | High → Low | 2 |
| Afternoon | High → Medium | High → Medium | 2 |
| Evening | Jam → Medium | Jam → Medium | 2 |
| Late Night | Jam → Low | Jam → Low | 2 |

## Within-Traffic Time Comparison

Only time bands with at least 30 records for a given traffic category are compared. The detailed table includes the category-level count, mean, median, P90, and slow-delivery rate.

| Traffic category | Qualifying time bands | Time-band metrics |
| --- | --- | --- |
| High | 2 | Afternoon (n=2,553; mean 27.239718; median 27; P90 38; slow 164/2,553 (6.4238%)); Morning (n=1,769; mean 27.163369; median 27; P90 37; slow 104/1,769 (5.8790%)) |
| Jam | 2 | Evening (n=8,710; mean 31.184845; median 31; P90 44; slow 1,722/8,710 (19.7704%)); Late Night (n=5,090; mean 31.102161; median 31; P90 44; slow 1,026/5,090 (20.1572%)) |
| Low | 3 | Late Night (n=8,683; mean 22.434182; median 22; P90 32; slow 201/8,683 (2.3149%)); Morning (n=5,949; mean 19.524626; median 19; P90 27; slow 0/5,949 (0.0000%)); Night (n=430; mean 22.169767; median 21; P90 30; slow 11/430 (2.5581%)) |
| Medium | 2 | Afternoon (n=1,496; mean 22.910428; median 23; P90 32; slow 0/1,496 (0.0000%)); Evening (n=9,182; mean 27.338271; median 27; P90 39; slow 645/9,182 (7.0246%)) |

For each traffic category, lowest/highest mean and slow-rate time-band extrema:

| Traffic category | Qualifying time bands | Extrema with count, median, and P90 |
| --- | --- | --- |
| High | 2 | Lowest/highest mean: Morning (n=1,769; 27.1634 min; median 27; P90 37) / Afternoon (n=2,553; 27.2397 min; median 27; P90 38); lowest/highest slow rate: Morning (n=1,769; 5.8790%; median 27; P90 37) / Afternoon (n=2,553; 6.4238%; median 27; P90 38) |
| Jam | 2 | Lowest/highest mean: Late Night (n=5,090; 31.1022 min; median 31; P90 44) / Evening (n=8,710; 31.1848 min; median 31; P90 44); lowest/highest slow rate: Evening (n=8,710; 19.7704%; median 31; P90 44) / Late Night (n=5,090; 20.1572%; median 31; P90 44) |
| Low | 3 | Lowest/highest mean: Morning (n=5,949; 19.5246 min; median 19; P90 27) / Late Night (n=8,683; 22.4342 min; median 22; P90 32); lowest/highest slow rate: Morning (n=5,949; 0.0000%; median 19; P90 27) / Night (n=430; 2.5581%; median 21; P90 30) |
| Medium | 2 | Lowest/highest mean: Afternoon (n=1,496; 22.9104 min; median 23; P90 32) / Evening (n=9,182; 27.3383 min; median 27; P90 39); lowest/highest slow rate: Afternoon (n=1,496; 0.0000%; median 23; P90 32) / Evening (n=9,182; 7.0246%; median 27; P90 39) |

## Traffic Signal Check

The standalone traffic mean order (highest to lowest) is `Jam > High > Medium > Low`; its slow-rate order is `Jam > High > Medium > Low`. No time band has qualifying cells for all four traffic categories, so a full four-category order comparison is unavailable. Among qualifying pairwise category comparisons, 4/4 mean-order pairs and 4/4 slow-rate-order pairs preserve their standalone pairwise order. These partial comparisons do not establish complete rank stability.

| Time band | Metric | Within-band order, high to low | Agreement with standalone order |
| --- | --- | --- | --- |
| Night | mean delivery time | Low | Not enough qualifying categories |
| Night | slow delivery rate | Low | Not enough qualifying categories |
| Morning | mean delivery time | High > Low | 1/1 pair orders preserved |
| Morning | slow delivery rate | High > Low | 1/1 pair orders preserved |
| Afternoon | mean delivery time | High > Medium | 1/1 pair orders preserved |
| Afternoon | slow delivery rate | High > Medium | 1/1 pair orders preserved |
| Evening | mean delivery time | Jam > Medium | 1/1 pair orders preserved |
| Evening | slow delivery rate | Jam > Medium | 1/1 pair orders preserved |
| Late Night | mean delivery time | Jam > Low | 1/1 pair orders preserved |
| Late Night | slow delivery rate | Jam > Low | 1/1 pair orders preserved |

Jam versus Low mean/slow-rate gaps, where both cells qualify:

| Time band | Jam − Low mean difference | Jam − Low slow-rate difference |
| --- | --- | --- |
| Late Night | 8.667979 min | +17.8423 pp |

Jam versus Low is the strongest standalone contrast: the mean gap is 9.9096 minutes and the slow-rate gap is 18.6272 percentage points. They both have qualifying cells together in 1 time band(s); those within-band gaps are shown above.

## Time Signal Check

The standalone time-band mean order (highest to lowest) is `Evening > Afternoon > Late Night > Night > Morning`; its slow-rate order is `Evening > Late Night > Afternoon > Night > Morning`. No traffic category has qualifying cells in both Morning and Evening (shared categories: none), so the standalone strongest-versus-weakest time-band contrast cannot be evaluated within a common traffic stratum. Other within-traffic band orders and qualifying counts are shown below; missing strata do not establish that a temporal pattern disappears.

| Traffic category | Qualifying time bands | Mean order (high to low) | Slow-rate order (high to low) |
| --- | --- | --- | --- |
| High | 2 | Afternoon → Morning | Afternoon → Morning |
| Jam | 2 | Evening → Late Night | Late Night → Evening |
| Low | 3 | Late Night → Night → Morning | Night → Late Night → Morning |
| Medium | 2 | Evening → Afternoon | Evening → Afternoon |

Within-traffic time-band rank-order agreement with the standalone time order:

| Traffic category | Metric | Within-traffic time order | Agreement with standalone order |
| --- | --- | --- | --- |
| High | mean delivery time | Afternoon > Morning | 1/1 pair orders preserved |
| High | slow delivery rate | Afternoon > Morning | 1/1 pair orders preserved |
| Jam | mean delivery time | Evening > Late Night | 1/1 pair orders preserved |
| Jam | slow delivery rate | Late Night > Evening | 0/1 pair orders preserved |
| Low | mean delivery time | Late Night > Night > Morning | 3/3 pair orders preserved |
| Low | slow delivery rate | Night > Late Night > Morning | 2/3 pair orders preserved |
| Medium | mean delivery time | Evening > Afternoon | 1/1 pair orders preserved |
| Medium | slow delivery rate | Evening > Afternoon | 1/1 pair orders preserved |

Across strata with at least two qualifying bands, mean ranges vary from 0.076349 to 4.427843 minutes; slow-rate ranges vary from 0.3868 to 7.0246 percentage points.

## Slow-Delivery Contribution

Across all valid targets, **4,037** deliveries are slow. **3,873** occur in qualifying cells, **0** in subminimum cells, and **164** in records with at least one missing/invalid dimension. The five qualifying combinations with the largest slow counts account for **3,758 (93.09%)** of all slow deliveries.

| Time band | Traffic | Count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evening | Jam | 8,710 | 1,722 | 19.7704% | 31.184845 | 31 | 44 | 1,722 / 4,037 (42.66%) |
| Late Night | Jam | 5,090 | 1,026 | 20.1572% | 31.102161 | 31 | 44 | 1,026 / 4,037 (25.41%) |
| Evening | Medium | 9,182 | 645 | 7.0246% | 27.338271 | 27 | 39 | 645 / 4,037 (15.98%) |
| Late Night | Low | 8,683 | 201 | 2.3149% | 22.434182 | 22 | 32 | 201 / 4,037 (4.98%) |
| Afternoon | High | 2,553 | 164 | 6.4238% | 27.239718 | 27 | 38 | 164 / 4,037 (4.06%) |

Subminimum nonempty cells, shown descriptively and excluded from rankings:

| Time band | Traffic | Count | Slow count | Slow rate |
| --- | --- | --- | --- | --- |
| None | — | — | — | No nonempty subminimum cells |

## SQL vs Python Validation

SQL from `sql/15_time_traffic_analysis.sql` ran against an in-memory SQLite 3.50.4 table. Python independently parsed `Time_Orderd`, applied the Step 5.7 time-band boundaries, and grouped the same target records. Counts, categories, and ranks were checked exactly; floating-point metrics use absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Cell metrics, standalone references, time-band order, and population counts | 290 | MATCH |
| Within-time traffic rankings | 36 | MATCH |
| Within-traffic time rankings | 36 | MATCH |
| All established time bands × observed traffic categories | 20 / 20 | MATCH |
| Slow-delivery population reconciliation | all slow target records | MATCH |

## Key Observations

- The combined analysis includes 43,862 of 45,593 valid-target records; 1,731 lack a valid order time, while 601 lack traffic.
- No time band supports a full four-category traffic comparison. Of qualifying pairwise comparisons, 4/4 mean and 4/4 slow-rate orders match the standalone pairwise ordering.
- The standalone time-band mean order is Evening > Afternoon > Late Night > Night > Morning; within-traffic orders and coverage are shown in the signal-check table.
- Jam and Low are jointly comparable in 1 time band(s), and no traffic category has qualifying Morning and Evening cells to assess the strongest standalone time contrast within that traffic stratum.
- The five largest qualifying cells represent 3,758/4,037 slow deliveries (93.09%).
- Small groups remain visible in the main table but are not used as if equally reliable in rankings or substantive comparisons.

## Interpretation

The stratified results indicate whether the standalone traffic and time-of-day patterns remain visible in the observed qualifying cells. Changes in ordering, ranges, or missing qualifying cells show where those patterns are not uniform. These descriptive comparisons do not establish that traffic or time of day causes delivery-time differences.

Pickup-time context from Step 5.7: pickup-time bands also showed time-related differences, and the prior order-to-pickup delay distribution was concentrated in non-negative 0–15 minute intervals. Pickup delay is not regrouped or analyzed in this step and is not part of the Time × Traffic comparison.

## Limitations

- This is observational analysis; no causal relationship is established.
- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.
- Time-of-day and traffic may be related to other operational factors.
- Missing/invalid order-time values reduce the combined-analysis population.
- This analysis does not control for city, distance, weather, vehicle, courier, or multiple deliveries.
- No regression, machine learning, or formal interaction model was fitted.
- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.
- Invalid or missing order times were not assigned time bands.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; its schema is unchanged.
