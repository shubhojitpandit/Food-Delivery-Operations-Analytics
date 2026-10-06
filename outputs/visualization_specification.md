# Visualization Specification

## Purpose and analytical lock

This specification selects charts for the completed Food Delivery Operations & Delivery Performance Analytics project. It uses only validated findings in the completed Step 5 and Step 6 reports and the shared definitions in [`analysis/analytical_framework.md`](../analysis/analytical_framework.md).

- Source for performance visuals: `data/processed/train_clean.csv`; valid targets are non-null numeric `Time_taken(min)`.
- The fixed slow-delivery rule is **strictly greater than 40 minutes**. It is not recalculated by segment.
- Use the established minimum of **30 valid records** as a comparison/ranking guardrail. Show counts, and label below-minimum observations descriptive only.
- Percentiles in the source analyses use continuous linear interpolation. Where displayed, use the already-validated values.
- Comparisons are observational; charts must not imply causation.
- This step specifies charts only. It does not create charts, scripts, or derived data.

## Portfolio narrative and priority sequence

The CORE sequence below moves from the target distribution to the strongest standalone patterns, then to the most informative context-dependent comparisons:

1. **V01** establishes the delivery-time distribution and the fixed 40-minute threshold.
2. **V02–V04** show the strongest standalone traffic, workload-category, and city contrasts.
3. **V05–V06** extend the story to time-of-day and approximate geographic distance.
4. **V07–V08** show how two of the clearest patterns vary by context: weather × traffic and distance × traffic.

SUPPORTING visuals extend the story to vehicle categories and pickup delay, and make the narrower city/time/vehicle interactions available without presenting them as equally conclusive.

## CORE visualizations

### V01 — Overall delivery-time distribution

- **Priority:** CORE
- **Title:** Distribution of Delivery Times
- **Analytical finding:** Among 45,593 valid targets, delivery times range from 10 to 54 minutes; the mean is 26.2946, median 26, P90 40, and 4,037 deliveries (8.8544%) exceed 40 minutes.
- **Source analysis:** Step 5.1, [`outputs/overall_delivery_performance.md`](./overall_delivery_performance.md).
- **Metric:** Record count by exact delivery-time value; reference lines at median 26 and fixed P90/slow threshold 40 minutes.
- **Dimensions:** X-axis: `Time_taken(min)` in minutes, using the existing integer-minute support (10–54); Y-axis: delivery count. Include all valid targets. Use one-minute integer bins, which match the exact observed target values reported in the analysis. Add a clearly labeled vertical reference at 40 minutes; do not imply values at 40 are slow.
- **Recommended chart type:** Histogram with one-minute bins.
- **Why this chart:** The distribution, rather than a single average, shows the central mass, spread, and tail near the project’s fixed slow-delivery threshold.
- **Expected audience takeaway:** Most observed delivery times cluster well below 40 minutes, while a meaningful upper tail crosses the predefined threshold.
- **Caveats:** Descriptive distribution of the cleaned training target only; 40 minutes is the overall P90 and the slow rule is strictly `> 40`. It is not a causal or forecast chart.
- **Portfolio narrative:** Opens with the outcome and establishes the threshold used consistently by every subsequent chart.

### V02 — Slow-delivery rate by traffic category

- **Priority:** CORE
- **Title:** Slow-Delivery Rate Varies Across Traffic Categories
- **Analytical finding:** Jam has the highest standalone mean (31.1766 minutes) and slow rate (20.0099%; 2,830/14,143); Low has the lowest mean (21.2670) and slow rate (1.3827%; 214/15,477).
- **Source analysis:** Step 5.2, [`outputs/traffic_analysis.md`](./traffic_analysis.md).
- **Metric:** Slow-delivery rate, with count and slow numerator shown alongside or as direct labels.
- **Dimensions:** X-axis: rate from 0% to 100%; Y-axis: traffic category. Use the report’s category labels (High, Jam, Low, Medium), not an invented ordinal scale. Show delivery count and `slow count / delivery count` for each bar. Include valid-target rows with a non-missing traffic category only.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** The rate difference is large and readily compared across four short categorical labels; numerator/denominator annotations prevent rate-only reading.
- **Expected audience takeaway:** Slow-delivery rates differ substantially in the observed traffic groups, with Jam highest and Low lowest.
- **Caveats:** Missing traffic on 601 valid-target records is outside the grouped comparison. Observational association only; do not say traffic caused longer delivery times. All groups meet the 30-record guardrail.
- **Portfolio narrative:** Introduces the clearest operational category contrast before exploring how that contrast changes under stratification.

### V03 — Slow-delivery rate by multiple-delivery category

- **Priority:** CORE
- **Title:** Slow-Delivery Rate Rises Across Observed Multiple-Delivery Categories
- **Analytical finding:** Standalone slow rates are 4.5406% (0; 640/14,095), 7.4008% (1; 2,084/28,159), 45.7431% (2; 908/1,985), and 100% (3; 361/361); mean delivery time also increases from 22.8763 to 47.8199 minutes.
- **Source analysis:** Step 5.6, [`outputs/courier_analysis.md`](./courier_analysis.md); supported by Steps 6.1 and 6.5.
- **Metric:** Slow-delivery rate, with delivery count and slow count shown.
- **Dimensions:** X-axis: category label `multiple_deliveries` in the established order 0, 1, 2, 3; Y-axis: rate from 0% to 100%. Labels remain categories; do not fit a continuous trend. Include valid target rows with non-missing category.
- **Recommended chart type:** Bar chart.
- **Why this chart:** It makes the sharp change at categories 2 and 3 visible without obscuring group size.
- **Expected audience takeaway:** The observed delivery-time and slow-rate distributions differ sharply across workload labels, especially categories 2 and 3.
- **Caveats:** The 30-record minimum is met by standalone category groups, but does not guarantee precision. This is not a causal workload effect. Use exact category labels and the fixed `> 40` rule.
- **Portfolio narrative:** Adds an important workload pattern alongside traffic before context-specific views.

### V04 — Slow-delivery rate by city

- **Priority:** CORE
- **Title:** Delivery Performance Differs Across the Three Observed City Categories
- **Analytical finding:** Standalone city rates are Urban 4.7652% (483/10,136), Metropolitan 9.8349% (3,353/34,093), and Semi-Urban 100% (164/164); Semi-Urban mean is 49.7317 minutes.
- **Source analysis:** Step 5.4, [`outputs/city_analysis.md`](./city_analysis.md); contextualized by Step 6.2.
- **Metric:** Slow-delivery rate, with delivery count and slow numerator displayed.
- **Dimensions:** X-axis: rate from 0% to 100%; Y-axis: city category. Use the cleaned category names exactly: Urban, Metropolitan, Semi-Urban. Order by the report’s rate comparison (Urban, Metropolitan, Semi-Urban) and annotate each bar with `slow count / n`. Use non-missing city records only.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** Long category names fit and the extreme Semi-Urban rate remains traceable to its denominator.
- **Expected audience takeaway:** The three observed city groups have different descriptive rates, while the Semi-Urban result is based on a much smaller population than the other two cities.
- **Caveats:** Semi-Urban has n=164 and 164 slow deliveries; the 30-record minimum is only a reporting guardrail. City comparisons are observational, unadjusted, and do not establish a city effect. 1,200 records with missing City are not included.
- **Portfolio narrative:** Brings the geographic/operational dimension into the narrative while foregrounding sample-size context.

### V05 — Slow-delivery rate by order-time band

- **Priority:** CORE
- **Title:** Delivery Performance Is Highest in the Evening Order-Time Band
- **Analytical finding:** In Step 5.7, Evening has mean 29.2108 minutes and slow rate 13.2294% (2,367/17,892); Morning has mean 21.2755 and slow rate 1.3475% (104/7,718).
- **Source analysis:** Step 5.7, [`outputs/time_analysis.md`](./time_analysis.md).
- **Metric:** Slow-delivery rate with count and numerator; mean delivery time may be a separate label or table note, not a second axis.
- **Dimensions:** X-axis: slow-delivery rate from 0% to 100%; Y-axis: order-time band in the fixed Step 5.7 chronological order: Night, Morning, Afternoon, Evening, Late Night. Use valid, strictly parsed `Time_Orderd` values; keep unassigned times out of bands and report their count in accompanying text.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** It communicates the contrast among five established day periods without representing the categories as a continuous time series.
- **Expected audience takeaway:** Delivery-time performance varies descriptively across order-time bands; Evening is highest on mean and slow rate, Morning lowest.
- **Caveats:** 1,731 of 45,593 valid targets have missing/invalid order time. The bands are categorical periods, not equal-width statistical intervals. Observational only.
- **Portfolio narrative:** Adds a temporal pattern before the geographic distance result.

### V06 — Slow-delivery rate by approximate distance band

- **Priority:** CORE
- **Title:** Slow-Delivery Rates Are Higher in the 10 km-and-Above Distance Bands
- **Analytical finding:** Slow rates are 1.6446% (1–2 km), 1.5209% (2–3), 1.8509% (3–5), 3.0445% (5–10), 16.2096% (10–15), and 16.2934% (15+). Mean and median times are also higher in the two bands at or above 10 km.
- **Source analysis:** Step 5.8, [`outputs/distance_analysis.md`](./distance_analysis.md).
- **Metric:** Slow-delivery rate; show band count and slow numerator. Do not substitute Pearson correlation for this validated band comparison.
- **Dimensions:** X-axis: rate from 0% to 100%; Y-axis: fixed half-open bands in Step 5.8 order: 0–1, 1–2, 2–3, 3–5, 5–10, 10–15, 15+ km. Show the empty 0–1 km band as zero/no records or explicitly mark it empty. Use all coordinate-valid targets, retaining 15+ km observations.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** The step change around 10 km is clearer as a categorical rate comparison than as a single linear association coefficient.
- **Expected audience takeaway:** The reported slow-delivery rate rises materially at 10–15 km and remains similarly high at 15+ km in these approximate-distance bands.
- **Caveats:** Distance is Haversine straight-line distance, not road/network distance. The 15+ km band includes extreme distances (maximum 19,692.7 km); they were retained. Pearson correlation was near zero (-0.0025), while Spearman was 0.3138, so do not describe the association as a simple linear effect. Observational only.
- **Portfolio narrative:** Highlights the geographic signal while explicitly exposing the approximation and extreme-value limitation.

### V07 — Weather × traffic slow-rate heatmap

- **Priority:** CORE
- **Title:** Weather-Related Slow-Rate Patterns Vary by Traffic Category
- **Analytical finding:** All 24 observed Weather × Traffic cells meet n≥30. Jam slow rates are high for Cloudy/Fog (34.9510%/35.4055%) and lower for Sunny (6.6405%); in High traffic the within-weather maximum is Sunny (16.3265%) while Cloudy and Fog are 0% in the observed groups. Fog is highest standalone, but its within-traffic position changes.
- **Source analysis:** Step 6.4, [`outputs/weather_traffic_analysis.md`](./weather_traffic_analysis.md), with Step 5.3 standalone context.
- **Metric:** Slow-delivery rate; annotate each cell with rate and delivery count. Do not add another axis for means.
- **Dimensions:** X-axis: traffic categories in reported order High, Jam, Low, Medium. Y-axis: the exact cleaned weather labels in report order: conditions Cloudy, conditions Fog, conditions Sandstorms, conditions Stormy, conditions Sunny, conditions Windy. All valid-target rows with both dimensions available.
- **Recommended chart type:** Heatmap.
- **Why this chart:** It shows the six-by-four context matrix at once and makes the weather ranking changes across traffic strata visible.
- **Expected audience takeaway:** Weather category differences are not uniform across traffic categories; Jam is often high, but not every weather-by-traffic cell follows the standalone weather ordering.
- **Caveats:** All cells meet the 30-record guardrail, but no causal claim is supported. Missing weather/traffic reduce the population to 44,977; the result does not control for other factors.
- **Portfolio narrative:** First context plot; it demonstrates why one-dimensional findings should be interpreted alongside observed operating conditions.

### V08 — Distance × traffic slow-rate heatmap

- **Priority:** CORE
- **Title:** The Distance-Band Signal Remains Visible Within Several Traffic Categories
- **Analytical finding:** In Jam, slow rates are 27.5273% for 10–15 km and 28.7329% for 15+ km, versus 6.0276% at 5–10 km. Medium also has higher rates in the two longest bands (11.6570%, 10.6086%); Low shows a smaller rise (3.5463%, 3.6257%). High has no qualifying 10+ km cells.
- **Source analysis:** Step 6.3, [`outputs/distance_traffic_analysis.md`](./distance_traffic_analysis.md), with Step 5.8 and Step 5.2 context.
- **Metric:** Slow-delivery rate; annotate rate and cell count.
- **Dimensions:** X-axis: traffic categories High, Jam, Low, Medium. Y-axis: Step 5.8 bands, in order 0–1, 1–2, 2–3, 3–5, 5–10, 10–15, 15+ km. Show absent/unqualified cells distinctly; do not color empty cells as 0%. Keep all distance observations, including extreme values, in their established bands.
- **Recommended chart type:** Heatmap with explicit count labels and a separate legend for missing/empty cells.
- **Why this chart:** The matrix reveals which traffic strata preserve the higher rates in the 10+ km bands and where data coverage prevents a comparison.
- **Expected audience takeaway:** The elevated long-distance slow-rate pattern is visible in Jam, Low, and Medium but is not testable in High under the 30-record rule; 15+ and 10–15 km rates are similar within the comparable traffic groups.
- **Caveats:** Straight-line Haversine distance is not actual travel distance. Extreme values were retained; the separate Step 6.3 sensitivity checked only the ten largest records and did not alter affected cell rankings materially. Combinations below 30 are not substantively compared. Observational only.
- **Portfolio narrative:** Closes the core sequence with the clearest validated two-dimensional check of distance and traffic.

## SUPPORTING visualizations

### V09 — Slow-delivery rate by vehicle type

- **Priority:** SUPPORTING
- **Title:** Motorcycle Has the Highest Standalone Slow-Delivery Rate Among Vehicle Types
- **Analytical finding:** Motorcycle slow rate is 11.7685% (3,111/26,435), compared with 4.7457% for electric_scooter, 4.8507% for scooter, and 5.8824% for bicycle.
- **Source analysis:** Step 5.5, [`outputs/vehicle_analysis.md`](./vehicle_analysis.md).
- **Metric:** Slow-delivery rate with `slow count / delivery count`.
- **Dimensions:** X-axis: percentage, 0–100%; Y-axis: `Type_of_vehicle`, preserving the reported category labels. Use non-missing vehicle types.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** Clear four-category comparison that can support the vehicle section without treating vehicle type as a numeric scale.
- **Expected audience takeaway:** Observed rates differ by vehicle type; motorcycle is notably higher in this dataset.
- **Caveats:** Counts differ greatly (bicycle n=68 versus motorcycle n=26,435); all exceed 30 but the minimum does not guarantee precision. Observational and unadjusted; no inherent vehicle effect is established.

### V10 — Slow-delivery rate by vehicle condition

- **Priority:** SUPPORTING
- **Title:** Vehicle-Condition Categories Show Different Observed Slow Rates
- **Analytical finding:** Condition category 0 has a 17.0298% slow rate (2,556/15,009), versus 4.8170% (724/15,030) for category 1, 4.7359% (712/15,034) for category 2, and 8.6538% (45/520) for category 3.
- **Source analysis:** Step 5.5, [`outputs/vehicle_analysis.md`](./vehicle_analysis.md).
- **Metric:** Slow-delivery rate and count.
- **Dimensions:** X-axis: rate, 0–100%; Y-axis: observed condition categories in report order 0, 1, 2, 3. Treat these as categorical labels; no numeric/ordinal scale or quality meaning.
- **Recommended chart type:** Bar chart.
- **Why this chart:** It isolates the difference across the four category labels while avoiding an unsupported trend line.
- **Expected audience takeaway:** Delivery outcomes vary across the recorded condition categories in this unadjusted comparison.
- **Caveats:** Observational association only; category labels are not an explanation of why performance differs. Category 3 has n=520, lower than other categories; 30 is not a precision guarantee.

### V11 — City × traffic mean-delivery heatmap

- **Priority:** SUPPORTING
- **Title:** City and Traffic Comparisons Are Not Equally Covered
- **Analytical finding:** In Metropolitan and Urban, Jam has the highest within-city mean and Low the lowest; Semi-Urban has only one qualifying traffic cell (Jam, n=135, mean 49.8889, slow rate 100%). Semi-Urban High and Medium cells are below 30; no Semi-Urban Low cell is present.
- **Source analysis:** Step 6.2, [`outputs/city_traffic_analysis.md`](./city_traffic_analysis.md).
- **Metric:** Mean delivery time (minutes), with count printed in each cell. Keep rates in the report table rather than adding a dual axis.
- **Dimensions:** X-axis: traffic High, Jam, Low, Medium. Y-axis: Metropolitan, Semi-Urban, Urban. Display all observed cells; blank/unobserved and subminimum cells must be distinguished visually from valid zeros.
- **Recommended chart type:** Heatmap.
- **Why this chart:** It shows the consistent traffic ordering in the two broadly covered cities while making sparse Semi-Urban comparison coverage explicit.
- **Expected audience takeaway:** Traffic patterns are visible within Urban and Metropolitan; the extreme Semi-Urban result is supported by a qualifying Jam cell only and does not provide a complete within-city comparison.
- **Caveats:** 30-record cell minimum applies. Semi-Urban standalone n=164 and one qualifying cross-cell do not justify broad generalization. Observational; no city/traffic causation.

### V12 — Time × traffic cell coverage and slow rate

- **Priority:** SUPPORTING
- **Title:** Time × Traffic Comparisons Have Limited Category Overlap
- **Analytical finding:** Only nine of 20 cells have qualifying observations: Night has Low only; Morning has High and Low; Afternoon has High and Medium; Evening has Jam and Medium; Late Night has Jam and Low. No traffic category has qualifying cells in both Morning and Evening.
- **Source analysis:** Step 6.7, [`outputs/time_traffic_analysis.md`](./time_traffic_analysis.md).
- **Metric:** Cell delivery count as the primary matrix value; slow rate as a clearly separate annotation or companion matrix using the same grid (not a second axis).
- **Dimensions:** X-axis: time bands Night, Morning, Afternoon, Evening, Late Night in inherited Step 5.7 order. Y-axis: traffic categories High, Jam, Low, Medium. All five Step 5.7 order-time bands and observed traffic categories.
- **Recommended chart type:** Two-panel heatmap (delivery count; slow-delivery rate), with count labels and distinct blanks for empty cells.
- **Why this chart:** Coverage is itself an important result; the paired matrices prevent missing combinations from being mistaken for zero rates and contextualize the limited overlap.
- **Expected audience takeaway:** Time and traffic categories are unevenly represented together; some apparent comparisons cannot be made within common strata.
- **Caveats:** Strict `HH:MM:SS` order-time parsing and exact Step 5.7 bands only. 1,731 order times are missing/invalid; cells with fewer than 30 records are not ranked. No common Morning/Evening traffic stratum exists, so the strongest standalone time contrast cannot be checked within traffic.

### V13 — Vehicle × multiple-delivery slow-rate heatmap

- **Priority:** SUPPORTING
- **Title:** Multiple-Delivery Patterns Are Visible in Several Vehicle Strata
- **Analytical finding:** Slow rates rise across qualifying categories 0–3 for motorcycle (6.2338%, 9.6135%, 50.6980%, 100%) and scooter (2.5230%, 4.3235%, 34.6939%, 100%). Electric_scooter is increasing through categories 0–2; category 3 has only n=8. Bicycle cells are mostly small.
- **Source analysis:** Step 6.5, [`outputs/vehicle_multiple_delivery_analysis.md`](./vehicle_multiple_delivery_analysis.md).
- **Metric:** Slow-delivery rate, with cell count labeled.
- **Dimensions:** X-axis: observed `multiple_deliveries` labels 0, 1, 2, 3; Y-axis: vehicle types bicycle, electric_scooter, motorcycle, scooter in report order. Use all cell results but flag n<30 cells as descriptive and keep them visually distinct.
- **Recommended chart type:** Heatmap.
- **Why this chart:** It communicates the within-vehicle workload-category progression compactly while retaining the small-cell warning.
- **Expected audience takeaway:** The standalone workload pattern remains visible in several vehicle strata, but some vehicle/category combinations do not support a substantive comparison.
- **Caveats:** `multiple_deliveries` remains categorical. Do not label a vehicle type as better/worse. Cells below 30 are not substantively compared; scooter category 3 has only n=31, electric_scooter category 3 n=8, and bicycle has sparse coverage. Observational only.

### V14 — Non-negative order-to-pickup delay by existing delay band

- **Priority:** SUPPORTING
- **Title:** Valid Non-Negative Order-to-Pickup Times Cluster Between 5 and 15 Minutes
- **Analytical finding:** Among 43,031 valid paired clocks with non-negative direct same-day difference, delay ranges from 5 to 15 minutes; median is 10, P90 is 15, and mean is 9.9553. Validated existing delay-band counts are 14,564 (0–5), 14,288 (>5–10), and 14,179 (>10–15); the remaining defined bands have zero records.
- **Source analysis:** Step 5.7, [`outputs/time_analysis.md`](./time_analysis.md).
- **Metric:** Record count by the already-established pickup-delay band.
- **Dimensions:** X-axis: delivery count; Y-axis: existing band order 0–5 minutes, 6–10 minutes, 11–15 minutes, 16–20 minutes, 21–30 minutes, 31+ minutes. Show the zero-count bands explicitly or mark them as empty. Do not introduce new intervals.
- **Recommended chart type:** Horizontal bar chart.
- **Why this chart:** The fixed delay bands are the report’s validated representation of a concentrated distribution; custom histogram edges would add an unvalidated binning decision.
- **Expected audience takeaway:** The analyzed non-negative direct clock differences are concentrated in the three 0–15-minute bands.
- **Caveats:** 831 negative same-day clock differences are ambiguous and omitted from this delay summary; no midnight rollover is assumed. 1,731 order-time records are missing/invalid. This is pickup-delay context only, not a new grouping or a causal analysis.

## Deliberately not visualized

- **Courier × multiple-delivery courier-level rankings:** Step 6.6 found 1,320 couriers, but no courier has two or more courier × category cells meeting the 30-record minimum. A ranking chart would overstate stability; the analysis explicitly is not a good/bad courier leaderboard.
- **Courier ID performance leaderboard:** The standalone courier report covers ratings, age, and workload categories, but individual IDs are identifiers and the combined analysis cannot make stable within-courier category comparisons under the specified guardrails. Do not plot individual couriers as quality rankings.
- **Distance-versus-time scatter plot as a CORE chart:** Pearson correlation is -0.0025 while Spearman is 0.3138, and straight-line distances include extreme values up to 19,692.7 km. The prevalidated distance-band comparison communicates the documented pattern more clearly without making the extreme tail dominate the story. The scatter could be explored later only with those caveats clearly surfaced.
- **Separate weather standalone rate chart:** The CORE Weather × Traffic heatmap already includes every validated weather category and provides the stronger contextual view. Avoid duplicating essentially the same category contrast; cite the standalone Fog/Sunny results in text.
- **Separate mean, median, and P90 chart for every dimension:** The project reports these validated metrics in tables; graphing all of them would create redundancy. Use rates/counts for the chosen category comparisons and retain distribution statistics in the reports.
- **Pickup-time-of-day chart:** It is not necessary for this focused visualization story; order-time bands are the temporal dimension used in Step 6.7. Pickup-delay context is represented only by V14, without adding it as a grouping variable.
- **Daily trend line, weekday, or month charts:** The time report notes only three calendar months and no full-year seasonal coverage. These visuals are not prioritized over the fixed order-time-band comparison.
- **A chart for every combined analysis:** Only Weather × Traffic, Distance × Traffic, City × Traffic, Time × Traffic, and Vehicle × Multiple Deliveries are selected. Traffic × Multiple Deliveries is not given a separate chart because its headline workload signal is already shown in V03, and the remaining combined views are less central or coverage-limited.
- **Pie, 3D, dual-axis, and decorative charts:** These add no value to the validated comparisons and may obscure scale or group-size interpretation.

## Count summary

| Priority | Count |
|---|---:|
| CORE | 8 |
| SUPPORTING | 6 |
| OPTIONAL | 0 |
| **Total proposed** | **14** |

The chart list prioritizes the strongest validated patterns and includes no speculative chart whose metric, categories, or group definitions are absent from the completed reports.
