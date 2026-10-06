# Weather × Traffic Analysis

## Objective

Describe whether observed weather-related delivery-performance differences remain visible within traffic categories, and whether traffic-related differences remain visible within weather categories. This is an observational analysis, not a causal analysis.

## Analytical Context

The standalone Weather Analysis found the highest slow-delivery rate in **conditions Fog** (15.0379%) and the lowest in **conditions Sunny** (4.6266%). By mean delivery time, the highest category was conditions Cloudy (28.9173 minutes) and the lowest was conditions Sunny (21.8569 minutes). The standalone Traffic Analysis found the highest slow rate in Jam (20.0099%) and lowest in Low (1.3827%).

Standalone weather metrics used for context:

| Weather category | Count | Mean (min) | Slow count / n | Slow rate |
| --- | --- | --- | --- | --- |
| conditions Cloudy | 7,536 | 28.91733015 | 1,118 / 7,536 | 14.8355% |
| conditions Fog | 7,654 | 28.91612229 | 1,151 / 7,654 | 15.0379% |
| conditions Sandstorms | 7,495 | 25.87551701 | 474 / 7,495 | 6.3242% |
| conditions Stormy | 7,586 | 25.87081466 | 425 / 7,586 | 5.6024% |
| conditions Sunny | 7,284 | 21.85694673 | 337 / 7,284 | 4.6266% |
| conditions Windy | 7,422 | 26.11883589 | 476 / 7,422 | 6.4134% |

Standalone traffic metrics used for context:

| Traffic category | Count | Mean (min) | Slow count / n | Slow rate |
| --- | --- | --- | --- | --- |
| High | 4,425 | 27.24 | 280 / 4,425 | 6.3277% |
| Jam | 14,143 | 31.17662448 | 2,830 / 14,143 | 20.0099% |
| Low | 15,477 | 21.2669768 | 214 / 15,477 | 1.3827% |
| Medium | 10,947 | 26.69964374 | 659 / 10,947 | 6.0199% |

## Data Coverage

- Total valid-target records: **45,593** of 45,593 training rows.
- Valid-target records with missing weather: **616**.
- Valid-target records with missing traffic: **601**.
- Records with both dimensions available for the combined analysis: **44,977**.
- Records missing either dimension (union; includes 601 missing both): **616**. Missing weather and traffic counts overlap only for records missing both.
Missing-dimension records remain in the valid-target population and are excluded only from the two-way grouped comparison. No source rows were modified.

## Two-Way Analysis

The fixed slow rule is `Time_taken(min) > 40` minutes. Every observed weather × traffic pair is shown, including empty or subminimum cells. Cells with fewer than 30 records are descriptive only and are not ranked or used for substantive comparison.

### Weather × Traffic Results

Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow-delivery rate is slow count / delivery count.

| Weather | Traffic | Count | Mean (min) | Median (min) | P90 (min) | Slow count | Slow count / n | Slow rate | Eligibility |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| conditions Cloudy | High | 744 | 28.94086022 | 29 | 35 | 0 | 0 / 744 | 0.0000% | Qualifies |
| conditions Cloudy | Jam | 2,349 | 36.68965517 | 37 | 47 | 821 | 821 / 2,349 | 34.9510% | Qualifies |
| conditions Cloudy | Low | 2,605 | 22.2084453 | 20 | 35 | 72 | 72 / 2,605 | 2.7639% | Qualifies |
| conditions Cloudy | Medium | 1,838 | 28.48313384 | 30 | 42 | 225 | 225 / 1,838 | 12.2416% | Qualifies |
| conditions Fog | High | 776 | 28.42654639 | 28 | 35 | 0 | 0 / 776 | 0.0000% | Qualifies |
| conditions Fog | Jam | 2,429 | 36.80691643 | 37 | 47 | 860 | 860 / 2,429 | 35.4055% | Qualifies |
| conditions Fog | Low | 2,597 | 22.30342703 | 20 | 36 | 77 | 77 / 2,597 | 2.9650% | Qualifies |
| conditions Fog | Medium | 1,852 | 28.04481641 | 29 | 41 | 214 | 214 / 1,852 | 11.5551% | Qualifies |
| conditions Sandstorms | High | 701 | 27.71184023 | 28 | 38 | 57 | 57 / 701 | 8.1312% | Qualifies |
| conditions Sandstorms | Jam | 2,399 | 30.01875782 | 29 | 42 | 339 | 339 / 2,399 | 14.1309% | Qualifies |
| conditions Sandstorms | Low | 2,609 | 20.29704868 | 20 | 28 | 0 | 0 / 2,609 | 0.0000% | Qualifies |
| conditions Sandstorms | Medium | 1,786 | 27.73852184 | 27 | 37 | 78 | 78 / 1,786 | 4.3673% | Qualifies |
| conditions Stormy | High | 733 | 27.84583902 | 28 | 38 | 52 | 52 / 733 | 7.0941% | Qualifies |
| conditions Stormy | Jam | 2,323 | 29.85019372 | 29 | 42 | 306 | 306 / 2,323 | 13.1726% | Qualifies |
| conditions Stormy | Low | 2,699 | 20.68173398 | 21 | 28 | 0 | 0 / 2,699 | 0.0000% | Qualifies |
| conditions Stormy | Medium | 1,831 | 27.68050246 | 27 | 37 | 67 | 67 / 1,831 | 3.6592% | Qualifies |
| conditions Sunny | High | 735 | 23.44897959 | 20 | 45 | 120 | 120 / 735 | 16.3265% | Qualifies |
| conditions Sunny | Jam | 2,289 | 23.08213194 | 21 | 34 | 152 | 152 / 2,289 | 6.6405% | Qualifies |
| conditions Sunny | Low | 2,475 | 21.44929293 | 20 | 31 | 65 | 65 / 2,475 | 2.6263% | Qualifies |
| conditions Sunny | Medium | 1,785 | 20.19551821 | 19 | 29 | 0 | 0 / 1,785 | 0.0000% | Qualifies |
| conditions Windy | High | 735 | 26.97278912 | 27 | 38 | 50 | 50 / 735 | 6.8027% | Qualifies |
| conditions Windy | Jam | 2,351 | 30.21905572 | 29 | 43 | 351 | 351 / 2,351 | 14.9298% | Qualifies |
| conditions Windy | Low | 2,484 | 20.66586151 | 21 | 28 | 0 | 0 / 2,484 | 0.0000% | Qualifies |
| conditions Windy | Medium | 1,852 | 27.8887689 | 27 | 37 | 75 | 75 / 1,852 | 4.0497% | Qualifies |

## Within-Weather Traffic Comparison

Extremes compare only qualifying traffic cells within each weather category; counts, medians, and P90 accompany values. Where fewer than two traffic cells qualify, the category is not compared.

| Weather | Observed traffic cells (counts) | Qualifying traffic cells | Lowest mean traffic | Highest mean traffic | Lowest slow-rate traffic | Highest slow-rate traffic |
| --- | --- | --- | --- | --- | --- | --- |
| conditions Cloudy | High (n=744); Jam (n=2,349); Low (n=2,605); Medium (n=1,838) | 4 | Low (n=2,605; 22.2084453 min; median 20; P90 35) | Jam (n=2,349; 36.68965517 min; median 37; P90 47) | High (n=744; 0.0000%; median 29; P90 35) | Jam (n=2,349; 34.9510%; median 37; P90 47) |
| conditions Fog | High (n=776); Jam (n=2,429); Low (n=2,597); Medium (n=1,852) | 4 | Low (n=2,597; 22.30342703 min; median 20; P90 36) | Jam (n=2,429; 36.80691643 min; median 37; P90 47) | High (n=776; 0.0000%; median 28; P90 35) | Jam (n=2,429; 35.4055%; median 37; P90 47) |
| conditions Sandstorms | High (n=701); Jam (n=2,399); Low (n=2,609); Medium (n=1,786) | 4 | Low (n=2,609; 20.29704868 min; median 20; P90 28) | Jam (n=2,399; 30.01875782 min; median 29; P90 42) | Low (n=2,609; 0.0000%; median 20; P90 28) | Jam (n=2,399; 14.1309%; median 29; P90 42) |
| conditions Stormy | High (n=733); Jam (n=2,323); Low (n=2,699); Medium (n=1,831) | 4 | Low (n=2,699; 20.68173398 min; median 21; P90 28) | Jam (n=2,323; 29.85019372 min; median 29; P90 42) | Low (n=2,699; 0.0000%; median 21; P90 28) | Jam (n=2,323; 13.1726%; median 29; P90 42) |
| conditions Sunny | High (n=735); Jam (n=2,289); Low (n=2,475); Medium (n=1,785) | 4 | Medium (n=1,785; 20.19551821 min; median 19; P90 29) | High (n=735; 23.44897959 min; median 20; P90 45) | Medium (n=1,785; 0.0000%; median 19; P90 29) | High (n=735; 16.3265%; median 20; P90 45) |
| conditions Windy | High (n=735); Jam (n=2,351); Low (n=2,484); Medium (n=1,852) | 4 | Low (n=2,484; 20.66586151 min; median 21; P90 28) | Jam (n=2,351; 30.21905572 min; median 29; P90 43) | Low (n=2,484; 0.0000%; median 21; P90 28) | Jam (n=2,351; 14.9298%; median 29; P90 43) |

Traffic orders within each weather category, highest to lowest:

| Weather | Qualifying traffic cells | Mean order | Slow-rate order |
| --- | --- | --- | --- |
| conditions Cloudy | 4 | Jam > High > Medium > Low | Jam > Medium > Low > High |
| conditions Fog | 4 | Jam > High > Medium > Low | Jam > Medium > Low > High |
| conditions Sandstorms | 4 | Jam > Medium > High > Low | Jam > High > Medium > Low |
| conditions Stormy | 4 | Jam > High > Medium > Low | Jam > High > Medium > Low |
| conditions Sunny | 4 | High > Jam > Low > Medium | High > Jam > Low > Medium |
| conditions Windy | 4 | Jam > Medium > High > Low | Jam > High > Medium > Low |

## Within-Traffic Weather Comparison

Only weather × traffic cells with n ≥ 30 are ranked and compared. Rank 1 is the lowest mean or slow rate; ties share ranks.

| Traffic | Weather | Count | Mean (min) | Median (min) | P90 (min) | Slow count / n | Slow rate | Mean rank | Slow-rate rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| High | conditions Sunny | 735 | 23.44897959 | 20 | 45 | 120 / 735 | 16.3265% | 1 | 6 |
| High | conditions Windy | 735 | 26.97278912 | 27 | 38 | 50 / 735 | 6.8027% | 2 | 3 |
| High | conditions Sandstorms | 701 | 27.71184023 | 28 | 38 | 57 / 701 | 8.1312% | 3 | 5 |
| High | conditions Stormy | 733 | 27.84583902 | 28 | 38 | 52 / 733 | 7.0941% | 4 | 4 |
| High | conditions Fog | 776 | 28.42654639 | 28 | 35 | 0 / 776 | 0.0000% | 5 | 1 |
| High | conditions Cloudy | 744 | 28.94086022 | 29 | 35 | 0 / 744 | 0.0000% | 6 | 1 |
| Jam | conditions Sunny | 2,289 | 23.08213194 | 21 | 34 | 152 / 2,289 | 6.6405% | 1 | 1 |
| Jam | conditions Stormy | 2,323 | 29.85019372 | 29 | 42 | 306 / 2,323 | 13.1726% | 2 | 2 |
| Jam | conditions Sandstorms | 2,399 | 30.01875782 | 29 | 42 | 339 / 2,399 | 14.1309% | 3 | 3 |
| Jam | conditions Windy | 2,351 | 30.21905572 | 29 | 43 | 351 / 2,351 | 14.9298% | 4 | 4 |
| Jam | conditions Cloudy | 2,349 | 36.68965517 | 37 | 47 | 821 / 2,349 | 34.9510% | 5 | 5 |
| Jam | conditions Fog | 2,429 | 36.80691643 | 37 | 47 | 860 / 2,429 | 35.4055% | 6 | 6 |
| Low | conditions Sandstorms | 2,609 | 20.29704868 | 20 | 28 | 0 / 2,609 | 0.0000% | 1 | 1 |
| Low | conditions Windy | 2,484 | 20.66586151 | 21 | 28 | 0 / 2,484 | 0.0000% | 2 | 1 |
| Low | conditions Stormy | 2,699 | 20.68173398 | 21 | 28 | 0 / 2,699 | 0.0000% | 3 | 1 |
| Low | conditions Sunny | 2,475 | 21.44929293 | 20 | 31 | 65 / 2,475 | 2.6263% | 4 | 4 |
| Low | conditions Cloudy | 2,605 | 22.2084453 | 20 | 35 | 72 / 2,605 | 2.7639% | 5 | 5 |
| Low | conditions Fog | 2,597 | 22.30342703 | 20 | 36 | 77 / 2,597 | 2.9650% | 6 | 6 |
| Medium | conditions Sunny | 1,785 | 20.19551821 | 19 | 29 | 0 / 1,785 | 0.0000% | 1 | 1 |
| Medium | conditions Stormy | 1,831 | 27.68050246 | 27 | 37 | 67 / 1,831 | 3.6592% | 2 | 2 |
| Medium | conditions Sandstorms | 1,786 | 27.73852184 | 27 | 37 | 78 / 1,786 | 4.3673% | 3 | 4 |
| Medium | conditions Windy | 1,852 | 27.8887689 | 27 | 37 | 75 / 1,852 | 4.0497% | 4 | 3 |
| Medium | conditions Fog | 1,852 | 28.04481641 | 29 | 41 | 214 / 1,852 | 11.5551% | 5 | 5 |
| Medium | conditions Cloudy | 1,838 | 28.48313384 | 30 | 42 | 225 / 1,838 | 12.2416% | 6 | 6 |

Weather orders within each traffic category, highest to lowest:

| Traffic | Qualifying weather categories | Mean order | Slow-rate order |
| --- | --- | --- | --- |
| High | 6 | conditions Cloudy > conditions Fog > conditions Stormy > conditions Sandstorms > conditions Windy > conditions Sunny | conditions Sunny > conditions Sandstorms > conditions Stormy > conditions Windy > conditions Fog > conditions Cloudy |
| Jam | 6 | conditions Fog > conditions Cloudy > conditions Windy > conditions Sandstorms > conditions Stormy > conditions Sunny | conditions Fog > conditions Cloudy > conditions Windy > conditions Sandstorms > conditions Stormy > conditions Sunny |
| Low | 6 | conditions Fog > conditions Cloudy > conditions Sunny > conditions Stormy > conditions Windy > conditions Sandstorms | conditions Fog > conditions Cloudy > conditions Sunny > conditions Sandstorms > conditions Stormy > conditions Windy |
| Medium | 6 | conditions Cloudy > conditions Fog > conditions Windy > conditions Sandstorms > conditions Stormy > conditions Sunny | conditions Cloudy > conditions Fog > conditions Sandstorms > conditions Windy > conditions Stormy > conditions Sunny |

## Weather Signal Check

Standalone slow-rate endpoints: highest conditions Fog (15.0379%) and lowest conditions Sunny (4.6266%), a difference of 10.4113 percentage points. Standalone mean endpoints are conditions Cloudy and conditions Sunny, a difference of 7.0604 minutes.

| Traffic | Counts: highest-rate weather / lowest-rate weather | Slow rates: highest / lowest weather | Within-traffic slow-rate gap | Within-traffic mean gap | Assessment / within-traffic ranks |
| --- | --- | --- | --- | --- | --- |
| High | 776 / 735 | 0.0000% / 16.3265% | -16.3265 pp | +4.9776 min | reversed; conditions Fog rank 5, conditions Sunny rank 1 |
| Jam | 2,429 / 2,289 | 35.4055% / 6.6405% | +28.7651 pp | +13.7248 min | increased; conditions Fog rank 1, conditions Sunny rank 6 |
| Low | 2,597 / 2,475 | 2.9650% / 2.6263% | +0.3387 pp | +0.8541 min | reduced; conditions Fog rank 1, conditions Sunny rank 3 |
| Medium | 1,852 / 1,785 | 11.5551% / 0.0000% | +11.5551 pp | +7.8493 min | increased; conditions Fog rank 2, conditions Sunny rank 6 |

The standalone highest slow-rate category conditions Fog remains the highest slow-rate category within 2 of 4 traffic strata where both weather endpoints qualify; conditions Sunny remains lowest within 2. Endpoint ranking differs from the standalone order in 3 comparable strata (including ties/rank shifts).

Strongest standalone traffic signal across weather categories (Jam vs Low):

The standalone Jam-minus-Low slow-rate difference was 18.6272 percentage points.

| Weather | Counts: Jam / Low | Slow rates: Jam / Low | Conditional gap vs standalone; mean difference |
| --- | --- | --- | --- |
| conditions Cloudy | 2,349 / 2,605 | 34.9510% / 2.7639% | Jam−Low: +32.1871 pp; +0.1356 pp vs standalone gap; mean +14.4812 min |
| conditions Fog | 2,429 / 2,597 | 35.4055% / 2.9650% | Jam−Low: +32.4406 pp; +0.1381 pp vs standalone gap; mean +14.5035 min |
| conditions Sandstorms | 2,399 / 2,609 | 14.1309% / 0.0000% | Jam−Low: +14.1309 pp; -0.0450 pp vs standalone gap; mean +9.7217 min |
| conditions Stormy | 2,323 / 2,699 | 13.1726% / 0.0000% | Jam−Low: +13.1726 pp; -0.0545 pp vs standalone gap; mean +9.1685 min |
| conditions Sunny | 2,289 / 2,475 | 6.6405% / 2.6263% | Jam−Low: +4.0142 pp; -0.1461 pp vs standalone gap; mean +1.6328 min |
| conditions Windy | 2,351 / 2,484 | 14.9298% / 0.0000% | Jam−Low: +14.9298 pp; -0.0370 pp vs standalone gap; mean +9.5532 min |

Across the 6 weather strata where both Jam and Low qualify, the Jam–Low slow-rate gap was reduced in 4, increased in 2, and reversed in 0. Jam has the highest within-weather slow rate in 5 categories and the highest mean in 5 categories where its cell qualifies.

Subminimum cells whose observed slow rate exceeds the maximum slow rate among qualifying cells (high rates remain descriptive only):

| Weather | Traffic | Count | Slow count | Slow rate | Comparison |
| --- | --- | --- | --- | --- | --- |
| None | — | — | — | — | No subminimum cell exceeds the qualifying-cell maximum |

## Slow-Delivery Contribution

Across all valid targets, **4,037** meet the fixed slow rule. Of these, **3,981** occur in qualifying weather × traffic cells, **0** in subminimum cells, and **56** in records with at least one missing dimension. The five qualifying cells with the largest slow counts account for **2,677 (66.31%)** of all slow deliveries.

| Weather | Traffic | Count | Slow count | Slow rate | Mean (min) | Median (min) | P90 (min) | Share of all slow deliveries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| conditions Fog | Jam | 2,429 | 860 | 35.4055% | 36.80691643 | 37 | 47 | 860 / 4,037 (21.30%) |
| conditions Cloudy | Jam | 2,349 | 821 | 34.9510% | 36.68965517 | 37 | 47 | 821 / 4,037 (20.34%) |
| conditions Windy | Jam | 2,351 | 351 | 14.9298% | 30.21905572 | 29 | 43 | 351 / 4,037 (8.69%) |
| conditions Sandstorms | Jam | 2,399 | 339 | 14.1309% | 30.01875782 | 29 | 42 | 339 / 4,037 (8.40%) |
| conditions Stormy | Jam | 2,323 | 306 | 13.1726% | 29.85019372 | 29 | 42 | 306 / 4,037 (7.58%) |

## SQL vs Python Validation

SQL from `sql/12_weather_traffic_analysis.sql` ran against an in-memory SQLite 3.50.4 table. Pandas independently grouped the same valid-target records. Counts and ranks were compared exactly; floating-point metrics use `numpy.isclose` with absolute tolerance `1e-09` and relative tolerance `1e-12`.

| Validation | Checks | Result |
| --- | --- | --- |
| Weather × traffic cell metrics and standalone references | 344 | MATCH |
| Within-weather and within-traffic ranks | 192 | MATCH |
| Missing-dimension populations and cell-count reconciliation | all | MATCH |

## Key Observations

- The highest standalone slow-rate category, conditions Fog, remains the highest within-traffic endpoint in 2/4 comparable strata; the lowest standalone category, conditions Sunny, remains lowest in 2/4.
- Weather slow-rate endpoint differences were reduced in 1 comparable traffic category, increased in 2, and reversed in 1; only strata where both endpoint cells qualify are included.
- Jam-versus-Low slow-rate differences are directly comparable in 6 of 6 weather categories; the conditional gap is smaller than the standalone gap in 4, larger in 2, and reversed in 0. Jam has the highest within-weather slow rate in 5 categories and highest mean in 5.
- 0 subminimum cell(s) have a slow rate above the largest qualifying-cell rate; each is explicitly labeled descriptive only.

## Interpretation

The two-way results show observed weather differences within traffic categories and observed traffic differences within weather categories. Standalone category rankings may shift after stratification, and comparisons are limited to cells meeting the 30-record minimum. This analysis does not establish that weather or traffic causes delivery-time differences.

## Limitations

- This is observational analysis; no causal relationship is established.
- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.
- Weather and traffic may be related to other operational factors.
- Missing weather/traffic dimensions reduce the combined-analysis population; their counts are reported separately and the union is reported without double-counting.
- This analysis does not control for city, distance, vehicle, courier, multiple deliveries, or time.
- No regression, machine learning, or formal interaction model was fitted.
- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.
- Missing categories were not imputed, and no rows or raw categories were altered.

Read-only validation: `data/processed/train_clean.csv` SHA-256 is `c6c14b001e89c372152ed603ca45bd08464beba191f4862f87f0878e1502089c` before and after; its schema is unchanged.
