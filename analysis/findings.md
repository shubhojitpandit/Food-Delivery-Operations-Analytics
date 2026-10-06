# Validated Analytical Findings

## Evidence and interpretation conventions

This document consolidates findings from the completed standalone and combined analyses. Its performance population is the cleaned training dataset, [`train_clean.csv`](../data/processed/train_clean.csv), restricted to the **45,593 valid numeric `Time_taken(min)` targets**. It does not add analyses or recommendations.

- Slow delivery always means `Time_taken(min) > 40` minutes. The threshold is the overall continuous P90 established in Step 5.1; it is not recalculated by group.
- A group must have at least **30 valid records** to support comparative interpretation or ranking. Smaller groups may be named as descriptive context only.
- Results are descriptive observational findings. They do not establish causation or statistical significance.
- Where appropriate, visualization IDs link to the generated charts in [`outputs/charts/`](../outputs/charts/). The chart calculations are recorded in [`outputs/visualization_validation.md`](../outputs/visualization_validation.md).

## 1. Executive Findings

1. Across 45,593 valid deliveries, mean delivery time was **26.2946 minutes**, median **26**, and P90 **40**. Under the fixed strict `>40` rule, **4,037 deliveries (8.8544%)** were slow. See [V01](../outputs/charts/V01_delivery_time_distribution.png) and [Step 5.1](../outputs/overall_delivery_performance.md).
2. Standalone slow-delivery rates varied materially by traffic: **Jam 20.0099%** (2,830/14,143) versus **Low 1.3827%** (214/15,477). In every observed Jam × multiple-delivery category with qualifying counts, Jam had the highest mean; Jam/Low differences also remained visible across all six weather categories where both traffic cells qualified. These are associations, not effects. See [V02](../outputs/charts/V02_traffic_performance.png), [Step 6.1](../outputs/traffic_multiple_delivery_analysis.md), and [Step 6.4](../outputs/weather_traffic_analysis.md).
3. Multiple-delivery categories 2 and 3 had markedly higher standalone slow rates than categories 0 and 1: **45.7431%** (908/1,985) and **100%** (361/361), versus **4.5406%** (640/14,095) and **7.4008%** (2,084/28,159). The increasing pattern was also present across the qualifying successive categories within each traffic stratum; the labels remain categorical and no causal workload effect is inferred. See [V03](../outputs/charts/V03_multiple_deliveries.png) and [Step 6.1](../outputs/traffic_multiple_delivery_analysis.md).
4. City differences are pronounced in the standalone summaries, but coverage is uneven. Urban had a **4.7652%** slow rate (483/10,136), Metropolitan **9.8349%** (3,353/34,093), and Semi-Urban **100%** (164/164). In City × Traffic, Semi-Urban has only one qualifying cell (Jam, n=135); its other observed traffic cells are below 30. See [V04](../outputs/charts/V04_city_performance.png) and [V11](../outputs/charts/V11_city_traffic.png).
5. Time-band, weather, and distance summaries show meaningful differences, but combined comparisons reveal context and coverage constraints. In particular, Evening has the highest standalone order-time slow rate (**13.2294%**, n=17,892), while Step 6.7 has no traffic group qualifying in both Morning and Evening. The higher rates in the longer distance bands remain visible within Jam, Low, and Medium traffic, but not High. See [V05](../outputs/charts/V05_order_time_bands.png), [V06](../outputs/charts/V06_distance_bands.png), [V08](../outputs/charts/V08_distance_traffic.png), and [V12](../outputs/charts/V12_time_traffic.png).
6. The strongest validated analyses do not isolate causal drivers. City, weather, traffic, time, approximate distance, vehicle, and workload categories are unadjusted for other operational factors; all conclusions should retain that limitation.

## 2. Overall Delivery Performance

**Descriptive finding.** All **45,593** training rows had a valid numeric target. Delivery time ranged from **10 to 54 minutes**; mean was **26.2946**, median **26**, P75 **32**, and P90 **40**. The fixed threshold is strictly greater than 40 minutes, so values exactly at 40 are not slow. There were **4,037 slow deliveries**, or **8.8544%** of valid targets.

**Interpretation.** The histogram shows a broad distribution with a tail beyond the fixed P90 threshold; the threshold is an analytical convention, not a naturally occurring boundary. See [V01](../outputs/charts/V01_delivery_time_distribution.png) and [Step 5.1](../outputs/overall_delivery_performance.md).

## 3. Traffic Analysis

**Descriptive finding.** All four traffic groups meet the 30-record guardrail. Jam recorded mean **31.1766 minutes** and a **20.0099%** slow rate (2,830/14,143); High, mean **27.24** and rate **6.3277%** (280/4,425); Medium, mean **26.6996** and rate **6.0199%** (659/10,947); Low, mean **21.2670** and rate **1.3827%** (214/15,477). Traffic was missing for **601** valid-target records.

**Interpretation.** The observed group summaries show higher delivery times and slow rates in Jam than Low; the analysis does not establish traffic as the cause. See [V02](../outputs/charts/V02_traffic_performance.png) and [Step 5.2](../outputs/traffic_analysis.md).

## 4. Multiple-Delivery Analysis

**Descriptive finding.** The observed `multiple_deliveries` categories and slow-delivery rates were:

| Category | Delivery count | Mean (min) | Slow count / n | Slow rate |
|---:|---:|---:|---:|---:|
| 0 | 14,095 | 22.8763 | 640 / 14,095 | 4.5406% |
| 1 | 28,159 | 26.8559 | 2,084 / 28,159 | 7.4008% |
| 2 | 1,985 | 40.4549 | 908 / 1,985 | 45.7431% |
| 3 | 361 | 47.8199 | 361 / 361 | 100.0000% |

All four categories meet the minimum. Multiple-delivery category was missing for **993** valid-target records.

**Interpretation.** The observed means and slow rates increase across the displayed labels, especially between categories 1 and 2. The labels were analyzed as categories; this pattern does not show that workload causes longer delivery time. See [V03](../outputs/charts/V03_multiple_deliveries.png) and [Step 5.6](../outputs/courier_analysis.md).

## 5. City Analysis

**Descriptive finding.** Urban had mean **22.9840 minutes** and slow rate **4.7652%** (483/10,136); Metropolitan, mean **27.3152** and rate **9.8349%** (3,353/34,093); Semi-Urban, mean **49.7317** and rate **100%** (164/164). All standalone city groups exceed 30 records, but Semi-Urban’s n is much smaller. City was missing for **1,200** valid-target records.

**Interpretation.** The standalone results distinguish these observed city categories, but cannot explain the differences. Semi-Urban’s particularly high rate should be read together with its denominator and the sparse City × Traffic coverage. See [V04](../outputs/charts/V04_city_performance.png), [Step 5.4](../outputs/city_analysis.md), and [Step 6.2](../outputs/city_traffic_analysis.md).

## 6. Order-Time Analysis

**Descriptive finding.** Using the validated strict `HH:MM:SS` parsing and fixed bands—Night, Morning, Afternoon, Evening, Late Night—Evening had the highest mean (**29.2108 minutes**) and slow rate (**13.2294%**, 2,367/17,892). Morning had the lowest mean (**21.2755**) and rate (**1.3475%**, 104/7,718). All five bands meet the 30-record minimum. **43,862** of 45,593 targets had valid order times; **1,731** were missing or invalid.

**Interpretation.** The Evening/Morning contrast is visible in the standalone bands, but is not fully testable within traffic strata: Step 6.7 contains no traffic category with qualifying cells in both Morning and Evening. See [V05](../outputs/charts/V05_order_time_bands.png), [V12](../outputs/charts/V12_time_traffic.png), [Step 5.7](../outputs/time_analysis.md), and [Step 6.7](../outputs/time_traffic_analysis.md).

## 7. Distance Analysis

**Descriptive finding.** Step 5.8 calculated Haversine straight-line distance using Earth radius 6,371.0088 km and the fixed half-open bands. The slow rate was **3.0445%** in 5–10 km (371/12,186), **16.2096%** in 10–15 km (1,974/12,178), and **16.2934%** in 15+ km (1,477/9,065). Mean delivery time was 24.3694, 29.8658, and 29.6531 minutes for these bands, respectively. The 0–1 km band had no records; all nonempty bands exceed 30 records. The 15+ km band, including extreme distances, was retained.

Pearson distance/time correlation was **-0.00250807**; Spearman rank correlation was **0.31378161**.

**Interpretation.** The banded summaries show higher slow rates in the two longest bands, while the differing correlation measures do not support describing the relationship as a simple linear association. Distance is straight-line separation, not road or traveled distance; maximum computed distance was approximately **19,692.7 km**. See [V06](../outputs/charts/V06_distance_bands.png), [V08](../outputs/charts/V08_distance_traffic.png), and [Step 5.8](../outputs/distance_analysis.md).

## 8. Weather Analysis

**Descriptive finding.** Fog had the highest standalone slow rate: **15.0379%** (1,151/7,654; mean 28.9161 minutes). Cloudy was similar, **14.8355%** (1,118/7,536; mean 28.9173). Sunny had the lowest rate, **4.6266%** (337/7,284; mean 21.8569). All six observed weather categories meet the minimum. Weather was missing for **616** valid-target records.

**Interpretation.** Standalone weather differences are visible, but their ordering changes across traffic strata; Fog remains highest for slow rate in only two of four traffic categories with qualifying weather cells. See [V07](../outputs/charts/V07_weather_traffic.png), [Step 5.3](../outputs/weather_analysis.md), and [Step 6.4](../outputs/weather_traffic_analysis.md).

## 9. Vehicle Analysis

**Descriptive finding.** Motorcycle had the highest vehicle-type mean (**27.6057 minutes**) and slow rate (**11.7685%**, 3,111/26,435). Electric_scooter had a **4.7457%** rate (181/3,814), scooter **4.8507%** (741/15,276), and bicycle **5.8824%** (4/68). Every standalone category meets n≥30, although bicycle has substantially fewer observations.

**Interpretation.** These are differences among the recorded vehicle categories, not evidence of an inherent vehicle effect. See [V09](../outputs/charts/V09_vehicle_type.png) and [Step 5.5](../outputs/vehicle_analysis.md).

## 10. Vehicle Condition Analysis

**Descriptive finding.** Vehicle-condition category 0 had mean **30.0722 minutes** and the highest slow rate, **17.0298%** (2,556/15,009). Category 1 had a **4.8170%** rate (724/15,030), category 2 **4.7359%** (712/15,034), and category 3 **8.6538%** (45/520). Every category meets the comparison minimum.

**Interpretation.** The recorded labels are categorical; the analysis assigns them no ordinal quality meaning and does not establish a condition-related cause. See [V10](../outputs/charts/V10_vehicle_condition.png) and [Step 5.5](../outputs/vehicle_analysis.md).

## 11. Interaction Analysis

### Weather × Traffic

**Descriptive finding.** The combined population contained **44,977** valid-target records with both dimensions available; 616 had missing weather (601 of those also had missing traffic). All **24** observed Weather × Traffic cells met n≥30. Jam slow rate was highest among traffic groups for five of six weather categories; Sunny is the exception, with High at **16.3265%** (120/735) and Jam at **6.6405%** (152/2,289). Under Jam, Fog was **35.4055%** (860/2,429) and Cloudy **34.9510%** (821/2,349); under Low, all observed weather rates were below 3%.

Within traffic categories, Fog was highest for slow rate in Jam (**35.4055%**) and Low (**2.9650%**), but not High (Sunny, **16.3265%**) or Medium (Cloudy, **12.2416%**). Thus, the standalone Fog-high/Sunny-low comparison is not preserved uniformly.

**Interpretation.** Traffic-related differences remain visible within most weather categories, and weather ordering varies with traffic. This is descriptive stratification, not evidence of interaction or causation. See [V07](../outputs/charts/V07_weather_traffic.png) and [Step 6.4](../outputs/weather_traffic_analysis.md).

### Distance × Traffic

**Descriptive finding.** Within Jam, the slow rate was **6.0276%** in 5–10 km (210/3,484), **27.5273%** in 10–15 km (1,435/5,213), and **28.7329%** in 15+ km (1,093/3,804). Within Medium, it was **0%** in 5–10 km (n=3,890), **11.6570%** in 10–15 km (401/3,440), and **10.6086%** in 15+ km (258/2,432). Within Low, the 10–15 and 15+ km rates were **3.5463%** (121/3,412) and **3.6257%** (93/2,565). High has no qualifying 10+ km comparison cells: 10–15 km n=0, 15+ km n=25.

**Interpretation.** The higher slow rates at longer approximate distances remain visible in Jam, Low, and Medium. No conclusion for High at 10+ km is supported by the comparison rule. Extreme straight-line distances were retained. See [V08](../outputs/charts/V08_distance_traffic.png) and [Step 6.3](../outputs/distance_traffic_analysis.md).

### City × Traffic

**Descriptive finding.** Metropolitan and Urban each have four qualifying traffic cells. Jam had their highest within-city mean and slow rate; Low their lowest. In every traffic stratum where both cities qualify, Metropolitan’s slow rate exceeded Urban’s: Jam **20.9288%** (2,321/11,090) versus **13.3612%** (351/2,627); Low **1.7785%** (193/10,852) versus **0.4398%** (18/4,093); High **6.8648%** (231/3,365) versus **3.1746%** (30/945); Medium **6.7051%** (558/8,322) versus **3.4380%** (81/2,356).

Semi-Urban has one qualifying cell: Jam, n=135, mean **49.8889 minutes**, slow rate **100%**. Its High (n=17) and Medium (n=11) cells are below 30, and no Low cell was observed; comparisons to other cities are not made in those strata.

**Interpretation.** Metropolitan/Urban differences and Jam/Low ordering are visible within their qualifying strata. Semi-Urban’s standalone high rate does not translate into a complete within-city comparison because only its Jam cell qualifies. See [V11](../outputs/charts/V11_city_traffic.png) and [Step 6.2](../outputs/city_traffic_analysis.md).

### Time × Traffic

**Descriptive finding.** The combined analysis used **43,862** valid order-time and traffic records and had **9 qualifying cells out of 20**. Only Low qualified at Night (n=430); Morning had High and Low; Afternoon had High and Medium; Evening had Jam and Medium; Late Night had Jam and Low. Jam and Low are jointly comparable only in Late Night. No traffic category has qualifying cells in both Morning and Evening.

Among the qualifying cells, Evening Jam had a **19.7704%** slow rate (1,722/8,710), Evening Medium **7.0246%** (645/9,182); Late Night Jam **20.1572%** (1,026/5,090), Late Night Low **2.3149%** (201/8,683). At Morning, High was **5.8790%** (104/1,769) and Low **0%** (0/5,949). These are distinct observed cells and not a full-factor ranking.

**Interpretation.** Traffic ordering is consistent in the pairwise comparisons that can be made, but sparse category overlap prevents a full within-traffic comparison of the standalone time pattern. See [V12](../outputs/charts/V12_time_traffic.png) and [Step 6.7](../outputs/time_traffic_analysis.md).

### Vehicle × Multiple Deliveries

**Descriptive finding.** Motorcycle’s slow rate increased across all four qualifying workload categories: **6.2338%** at 0 (480/7,700), **9.6135%** at 1 (1,587/16,508), **50.6980%** at 2 (690/1,361), and **100%** at 3 (322/322). Scooter also increased across its four qualifying cells: **2.5230%** (129/5,113), **4.3235%** (401/9,275), **34.6939%** (170/490), and **100%** (31/31). Electric_scooter category 3 has n=8 and is descriptive only; bicycle has just one qualifying cell (category 1, n=43).

Motorcycle had the highest or tied-highest vehicle slow rate in all four workload categories where it was comparable. In category 3, motorcycle and scooter both have a 100% slow rate, but scooter’s n is only 31.

**Interpretation.** The standalone workload pattern remains visible for motorcycle and scooter in the observed strata, with incomplete vehicle coverage in some cells. Multiple-delivery labels and vehicle types are categorical; no causal effect is established. See [V13](../outputs/charts/V13_vehicle_multiple_deliveries.png) and [Step 6.5](../outputs/vehicle_multiple_delivery_analysis.md).

## 12. Pickup-Delay Analysis

**Descriptive finding.** Among **43,862** valid paired order/pickup clock values, **831 (1.8946%)** had a negative direct same-day difference and were treated as ambiguous, not as confirmed midnight crossings. The primary delay distribution contains **43,031** non-negative records: mean **9.9553 minutes**, median **10**, P90 **15**, and range **5–15 minutes**. The established bands contain 14,564 records at 0–5 minutes, 14,288 at >5–10, and 14,179 at >10–15; the three higher bands contain no records.

**Interpretation.** The clock-only distribution is concentrated in the existing 0–15-minute bands. It excludes ambiguous negative differences and does not confirm elapsed times across midnight. See [V14](../outputs/charts/V14_pickup_delay_bands.png) and [Step 5.7](../outputs/time_analysis.md).

## 13. Cross-Factor Findings

- **Traffic is a recurring stratified contrast, with exceptions.** Jam was highest within five weather categories and in qualifying City × Traffic comparisons for Metropolitan and Urban. In Weather × Traffic, Sunny reverses the Jam-high order; Time × Traffic lacks broad common coverage. Sources: Steps 6.1, 6.2, 6.4, and 6.7.
- **Higher distance-band rates persist within multiple traffic categories, but not all.** The 10–15 and 15+ km rates exceed the shorter-band reference for Jam, Low, and Medium; High lacks qualifying long-distance cells. The distance dimension remains approximate straight-line Haversine. Source: Step 6.3.
- **Standalone city and weather extremes are context-dependent.** Semi-Urban is comparable to other cities only under Jam traffic; Fog’s standalone top slow-rate position is not retained in every traffic stratum. Sources: Steps 6.2 and 6.4.
- **The workload pattern is visible within several observed strata, not as a causal relationship.** Slow rate increases over qualifying multiple-delivery labels within each traffic category, and for motorcycle and scooter within vehicle strata; some vehicle cells are below minimum. Sources: Steps 6.1 and 6.5.
- **Coverage limits are findings.** Time × Traffic has only nine qualifying cells of 20; no category supports both Morning and Evening comparison. Courier × Multiple Deliveries has **zero couriers with two qualifying workload cells**, so within-courier workload changes or stable courier rankings cannot be assessed. Sources: Steps 6.6 and 6.7.

These comparisons are descriptive consistency checks. No regression, machine learning, or formal interaction model was fitted.

## 14. Key Operational Findings

The following are evidence-backed observations for subsequent reporting, not recommendations:

1. **Slow-delivery burden is concentrated in a few high-volume or high-rate cells.** Metropolitan × Jam contributes **2,321 of 4,037 slow deliveries (57.49%)** in City × Traffic. The five largest qualifying City × Traffic cells account for 3,654 (90.51%) of all slow deliveries. This is contribution by volume and rate, not an estimate of avoidable delays. Source: Step 6.2.
2. **Jam × longer distance cells are substantial contributors.** Distance 10–15 km × Jam contains 1,435 slow deliveries (35.55% of all slow deliveries); 15+ km × Jam contains 1,093 (27.07%). The five largest qualifying Distance × Traffic cells account for 3,397 (84.15%). Source: Step 6.3.
3. **Jam × Fog/Cloudy cells combine high rates with large counts.** Fog × Jam contributes 860 slow deliveries (21.30% of all slow deliveries), and Cloudy × Jam 821 (20.34%); together, 41.64%. These cells’ slow rates are 35.4055% and 34.9510%, respectively. Source: Step 6.4.
4. **The Evening and Late Night time/traffic cells contribute many slow deliveries, but their coverage does not enable a full traffic comparison across all day periods.** Evening Jam contains 1,722 slow deliveries and Late Night Jam 1,026; each figure is tied to its own cell denominator and should not be interpreted as a controlled time effect. Source: Step 6.7.
5. **High standalone rates in small groups require denominator context.** Semi-Urban n=164 is above the formal minimum, but is much smaller than Urban and Metropolitan; Semi-Urban × Jam n=135 is its only qualifying traffic cell. Category 3 multiple deliveries has n=361 standalone, while some conditional cells are near the minimum (e.g., Scooter × 3 n=31). Sources: Steps 5.4, 6.2, and 6.5.

## 15. Limitations and Data Coverage

- All performance analyses use **45,593 valid target records**. Grouped analyses exclude a missing dimension only from the corresponding comparison and report the affected population; no source rows are silently removed.
- The fixed slow-delivery threshold is **strictly `>40` minutes**, based on the overall continuous P90. Every grouped comparison uses the same threshold.
- The **30-record minimum** is a reporting guardrail, not a guarantee of statistical precision. Subminimum groups/cells are descriptive only and are not used to support rankings or comparisons.
- Standalone missing dimensions include: traffic **601**, weather **616**, City **1,200**, multiple-delivery category **993**, and order time **1,731**. Combined-population exclusions and overlaps vary by analysis; use each report’s own counts rather than summing missing fields.
- Combined coverage is uneven: City × Traffic has 9/11 qualifying observed cells; Time × Traffic has 9/20; Distance × Traffic has no qualifying 10–15 km High cell and only 25 records in 15+ km High; Vehicle × Multiple Deliveries includes subminimum cells.
- The courier interaction has no courier with two qualifying workload-category cells, which prevents within-courier category comparisons. It is not suitable for an individual courier ranking.
- Distance is Haversine straight-line separation, not road/network distance; 9,065 observations are in 15+ km, including extreme values. The two distance/time correlations differ substantially (Pearson -0.0025; Spearman 0.3138), so the evidence does not support a simple linear summary.
- Pickup-delay interpretation is limited to valid clocks and non-negative direct same-day differences. The 831 negative differences are ambiguous without a pickup date and are not confirmed midnight crossings.
- Analyses are observational and unadjusted. Combined reports do not control for all other recorded factors; no regression, machine learning, or formal interaction model was fitted.
- **Method-text discrepancy:** an earlier time-band paragraph in [`analytical_framework.md`](./analytical_framework.md) describes four broad clock periods. The completed, independently validated Step 5.7 and Step 6.7 analyses use the five explicit bands Night, Morning, Afternoon, Evening, and Late Night. This findings document follows those validated reports and their generated visualizations.
- SQL and Pandas validation results are documented per analysis. The generated chart-validation register marks all **8 CORE** and **6 SUPPORTING** visuals `VALIDATED`; see [`visualization_validation.md`](../outputs/visualization_validation.md).
