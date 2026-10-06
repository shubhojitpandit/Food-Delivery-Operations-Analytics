# Final Business Report: Food Delivery Operations & Delivery Performance Analytics

## 1. Executive Summary

This report summarizes the completed descriptive analytics phase for the food delivery operations dataset. The validated performance population is the cleaned training data, with 45,593 valid numeric `Time_taken(min)` records and a fixed slow-delivery threshold of `Time_taken(min) > 40` minutes. Under that rule, 4,037 deliveries were slow, equal to 8.8544% of the valid-target population. See [V01](../outputs/charts/V01_delivery_time_distribution.png) and [overall_delivery_performance.md](../outputs/overall_delivery_performance.md).

The strongest operational signal is the concentration of slow deliveries in congested conditions. Jam traffic had a slow-delivery rate of 20.0099% (2,830/14,143), compared with 1.3827% in Low traffic (214/15,477). Within the city Ã— traffic dimension, the Metropolitan Ã— Jam cell alone contributed 2,321 slow deliveries out of 4,037 total slow deliveries, or 57.49% of the observed slow-delivery burden; this is the largest single segment in the validated evidence set. See [V02](../outputs/charts/V02_traffic_performance.png), [V11](../outputs/charts/V11_city_traffic.png), and [city_traffic_analysis.md](../outputs/city_traffic_analysis.md).

Workload also shows a strong observed association with slow-delivery risk. Multiple-delivery category 2 had a slow rate of 45.7431% (908/1,985), while category 3 had 100% (361/361). This pattern is visible across traffic and vehicle strata and is operationally relevant for dispatch and resource planning investigations. See [V03](../outputs/charts/V03_multiple_deliveries.png), [V13](../outputs/charts/V13_vehicle_multiple_deliveries.png), [traffic_multiple_delivery_analysis.md](../outputs/traffic_multiple_delivery_analysis.md), and [vehicle_multiple_delivery_analysis.md](../outputs/vehicle_multiple_delivery_analysis.md).

Delivery-time and distance patterns show that longer-distance and evening/late-night conditions carry a materially higher observed slow-delivery burden. In Jam traffic, the 10â€“15 km band had a slow rate of 27.5273% (1,435/5,213) and the 15+ km band 28.7329% (1,093/3,804). Across order-time bands, Evening Jam was 19.7704% (1,722/8,710) and Late Night Jam was 20.1572% (1,026/5,090), while the Morning Low rate was 0.0000% (0/5,949). Similarly, Jam under Fog reached 35.4055% (860/2,429) and under Cloudy 34.9510% (821/2,349), while Low under each weather category remained below 3%. See [V06](../outputs/charts/V06_distance_bands.png), [V07](../outputs/charts/V07_weather_traffic.png), [V08](../outputs/charts/V08_distance_traffic.png), [V12](../outputs/charts/V12_time_traffic.png), [distance_traffic_analysis.md](../outputs/distance_traffic_analysis.md), [weather_traffic_analysis.md](../outputs/weather_traffic_analysis.md), and [time_traffic_analysis.md](../outputs/time_traffic_analysis.md).

Taken together, the evidence indicates that slow deliveries are concentrated in particular operating conditions rather than evenly distributed across the network. The reporting objective is to identify segments that warrant operational investigation, not to claim that any single factor causes delay.

## 2. Business Objective

The business objective of this phase was to complete a validated descriptive diagnostic of delivery performance, using the cleaned dataset to answer a practical operating question: where is the slow-delivery burden concentrated, and which observed segments merit further operational investigation?

This is a descriptive business analysis. It is designed to highlight which combinations of traffic, weather, time, city, distance, and workload are associated with higher observed slow-delivery volume and rates. It does not attempt to determine causation, estimate business impact, or prescribe permanent policy changes based on single-factor comparisons.

## 3. Dataset & Analytical Scope

The analysis used the cleaned training dataset, `data/processed/train_clean.csv`, which contains 45,593 rows with valid numeric `Time_taken(min)` values. The performance population is restricted to valid numeric targets and excludes invalid or missing target rows from target-based comparisons. The fixed slow-delivery rule remained `Time_taken(min) > 40` minutes for all individual and combined-factor comparisons; no subgroup-specific threshold was recalculated.

The project scope covered:

- overall delivery-time distribution
- traffic density
- multiple-delivery workload
- city-level performance
- order-time bands
- distance bands
- weather categories
- vehicle type and vehicle condition
- cross-factor conditions combining the above dimensions

The analysis adhered to the projectâ€™s 30-record minimum rule: groups with fewer than 30 valid records were displayed as descriptive context only and were not used for substantive comparisons or ranking. The dataset was not modified, and no new data was created.

## 4. Analytical Approach

The project followed a fixed reporting framework established in the analytical documentation and validated for consistency across SQL and Python output. The core analytic question was descriptive: which conditions are associated with higher observed slow-delivery rates and volumes among valid deliveries?

The evidence layer for this report is the consolidated findings document, [analysis/findings.md](../analysis/findings.md), which is the primary source for the validated metrics and denominators used here. Supporting project artifacts described the methods and validation logic in [analysis/analytical_framework.md](../analysis/analytical_framework.md), [outputs/overall_delivery_performance.md](../outputs/overall_delivery_performance.md), and the dimension-specific analysis files in [outputs/](../outputs/).

The validated charts used throughout the report are in [outputs/charts/](../outputs/charts/), including [V01](../outputs/charts/V01_delivery_time_distribution.png), [V02](../outputs/charts/V02_traffic_performance.png), [V03](../outputs/charts/V03_multiple_deliveries.png), [V04](../outputs/charts/V04_city_performance.png), [V05](../outputs/charts/V05_order_time_bands.png), [V06](../outputs/charts/V06_distance_bands.png), [V07](../outputs/charts/V07_weather_traffic.png), [V08](../outputs/charts/V08_distance_traffic.png), [V09](../outputs/charts/V09_vehicle_type.png), [V10](../outputs/charts/V10_vehicle_condition.png), [V11](../outputs/charts/V11_city_traffic.png), [V12](../outputs/charts/V12_time_traffic.png), [V13](../outputs/charts/V13_vehicle_multiple_deliveries.png), and [V14](../outputs/charts/V14_pickup_delay_bands.png).

Methodology note: AI tools were used to assist with implementation, SQL/Python querying, validation, documentation, and analysis support. The analytical requirements, validation checks, interpretation, and final conclusions were reviewed by the project owner.

## 5. Overall Delivery Performance

Across the valid training population, the observed delivery-time distribution was centered around 26 minutes but had a meaningful tail beyond the fixed slow threshold. The overall mean was 26.2946 minutes, the median was 26 minutes, and the P90 was 40 minutes. Under the fixed strict rule `Time_taken(min) > 40`, 4,037 of 45,593 valid deliveries were slow, equal to 8.8544% of the valid-target population. This baseline provides the reference point for all within-group comparisons in the descriptive analysis. See [V01](../outputs/charts/V01_delivery_time_distribution.png) and [overall_delivery_performance.md](../outputs/overall_delivery_performance.md).

The baseline is important because it shows that the slow-delivery burden is not evenly spread across the operation; it is concentrated in a smaller set of observed conditions rather than being evenly distributed across all deliveries.

## 6. Key Operational Findings

### Traffic

The standalone traffic comparison shows a clear observed separation between jammed and low-congestion operating conditions. Jam traffic had a slow-delivery rate of 20.0099% (2,830/14,143) with a mean delivery time of 31.1766 minutes, compared with Low traffic at 1.3827% (214/15,477) and a mean of 21.2670 minutes. The High and Medium traffic groups were intermediate at 6.3277% (280/4,425) and 6.0199% (659/10,947), respectively. These are observed associations, not evidence that traffic caused the delays. See [V02](../outputs/charts/V02_traffic_performance.png), [traffic_analysis.md](../outputs/traffic_analysis.md), and [analysis/findings.md](../analysis/findings.md).

Business interpretation: congested traffic is an operational segment of material slow-delivery burden and warrants targeted investigation. This is not a claim that road conditions are the sole cause of delay; it is a description of where the observed slow-delivery concentration sits.

### Multiple Deliveries

The multiple-delivery dimension shows a sharp increase in slow-delivery burden as the workload label increases. Category 0 had a slow rate of 4.5406% (640/14,095), category 1 had 7.4008% (2,084/28,159), category 2 had 45.7431% (908/1,985), and category 3 had 100.0000% (361/361). Mean delivery times rose from 22.8763 minutes in category 0 to 47.8199 minutes in category 3. See [V03](../outputs/charts/V03_multiple_deliveries.png) and [traffic_multiple_delivery_analysis.md](../outputs/traffic_multiple_delivery_analysis.md).

This pattern is operationally important because the slow-delivery burden is highly concentrated in the highest workload categories. The evidence supports investigation of workload-related operating conditions and dispatch patterns, without inferred causal claims.

### City

City differences are pronounced in the standalone summaries. Urban had a mean of 22.9840 minutes and a slow rate of 4.7652% (483/10,136); Metropolitan had a mean of 27.3152 minutes and a slow rate of 9.8349% (3,353/34,093); Semi-Urban had a mean of 49.7317 minutes and a slow rate of 100.0000% (164/164). The Semi-Urban result is notable but must be interpreted alongside its smaller sample and sparse within-city cross-factor coverage. See [V04](../outputs/charts/V04_city_performance.png), [city_analysis.md](../outputs/city_analysis.md), and [city_traffic_analysis.md](../outputs/city_traffic_analysis.md).

The practical implication is that Metropolitan deliveries make up a large share of the total slow-delivery burden, while the highest observed city-level rate sits in the small Semi-Urban segment. This warrants further review of segmented city operating conditions, but not a conclusion about geographic causation.

### Order Time

The order-time bands show a strong pattern in the highest-risk periods. Evening had the highest observed slow-delivery rate at 13.2294% (2,367/17,892) and a mean of 29.2108 minutes; Morning had the lowest at 1.3475% (104/7,718) and a mean of 21.2755 minutes. Late Night also showed a materially elevated slow-delivery rate at 8.9087% (1,227/13,773). See [V05](../outputs/charts/V05_order_time_bands.png), [time_analysis.md](../outputs/time_analysis.md), and [time_traffic_analysis.md](../outputs/time_traffic_analysis.md).

The combined time Ã— traffic descriptive analysis showed that Evening Jam was 19.7704% (1,722/8,710), while Evening Medium was 7.0246% (645/9,182). In Late Night, Jam was 20.1572% (1,026/5,090) versus Low at 2.3149% (201/8,683). This indicates operational relevance in the evening/late-night periods, especially when combined with traffic density. The evidence supports investigation of time-of-day operating conditions, not causation.

### Distance

Distance shows a strong observed association with slow-delivery burden in the descriptive data. The 10â€“15 km band had a slow rate of 16.2096% (1,974/12,178), and the 15+ km band had 16.2934% (1,477/9,065), compared with 3.0445% (371/12,186) in the 5â€“10 km band and 1.8509% (140/7,564) in the 3â€“5 km band. The slow-delivery burden rises materially at longer straight-line distances. See [V06](../outputs/charts/V06_distance_bands.png) and [distance_analysis.md](../outputs/distance_analysis.md).

This is a descriptive association only. The metric is straight-line distance rather than road distance, so it is best interpreted as a segment indicator for operational review rather than a route-performance causal claim.

### Weather

Weather conditions show a distinct pattern in the slow-delivery rates. Fog had the highest observed slow-delivery rate at 15.0379% (1,151/7,654), followed closely by Cloudy at 14.8355% (1,118/7,536). Sunny had the lowest at 4.6266% (337/7,284), while Sandstorms, Stormy, and Windy were between 5.6024% and 6.4134%. See [V07](../outputs/charts/V07_weather_traffic.png) and [weather_analysis.md](../outputs/weather_analysis.md).

Weather is not independently causal in this report, but the observed distribution is operationally relevant because the slow-delivery burden rises meaningfully in foggy and cloudy conditions.

### Vehicle

Vehicle type shows a meaningful difference in observed delivery performance. Motorcycle had the highest slow-delivery rate at 11.7685% (3,111/26,435), while electric_scooter was 4.7457% (181/3,814) and scooter was 4.8507% (741/15,276). Bicycle had a rate of 5.8824% (4/68), but the bicycle sample is small. See [V09](../outputs/charts/V09_vehicle_type.png) and [vehicle_analysis.md](../outputs/vehicle_analysis.md).

### Vehicle Condition

Vehicle-condition category 0 had the highest observed slow rate at 17.0298% (2,556/15,009), while category 1 had 4.8170% (724/15,030), category 2 was 4.7359% (712/15,034), and category 3 was 8.6538% (45/520). The dataset defines these labels categorically; they are not treated as an ordered quality measure in the formal interpretation. See [V10](../outputs/charts/V10_vehicle_condition.png) and [vehicle_analysis.md](../outputs/vehicle_analysis.md).

## 7. Cross-Factor Findings

### Weather Ã— Traffic

The weather Ã— traffic comparison shows that traffic remains the dominant operating signal within most weather strata, and that the weather ordering shifts by traffic condition. The valid combined analysis included 44,977 records with both dimensions present. Under Jam traffic, Fog was 35.4055% (860/2,429) and Cloudy was 34.9510% (821/2,349), both materially above the low-traffic weather cells. Under Low traffic, every observed weather cell remained below 3%: Cloudy 2.7639% (72/2,605), Fog 2.9650% (77/2,597), Sandstorms 0.0000% (0/2,609), Stormy 0.0000% (0/2,699), Sunny 2.6263% (65/2,475), and Windy 0.0000% (0/2,484). See [V07](../outputs/charts/V07_weather_traffic.png) and [weather_traffic_analysis.md](../outputs/weather_traffic_analysis.md).

Interpretation: the combination of traffic congestion and fog/cloudy conditions is an observed high-risk operating segment, while low-congestion conditions remain comparatively low risk across weather categories. This is a descriptive association and not a causal interaction result.

### Distance Ã— Traffic

The distance Ã— traffic comparison shows that the longer-distance burden is especially pronounced under Jam conditions. Within Jam, the 10â€“15 km band had a slow rate of 27.5273% (1,435/5,213), and the 15+ km band had 28.7329% (1,093/3,804). For Low traffic, the 10â€“15 km and 15+ km slow rates were much lower at 3.5463% (121/3,412) and 3.6257% (93/2,565). Medium traffic also showed a meaningful jump at longer distance: 11.6570% (401/3,440) in 10â€“15 km and 10.6086% (258/2,432) in 15+ km, compared with 0.0000% in 5â€“10 km as a valid-count comparison. See [V08](../outputs/charts/V08_distance_traffic.png) and [distance_traffic_analysis.md](../outputs/distance_traffic_analysis.md).

This supports the operational hypothesis that congestion plus longer straight-line distance is a materially higher-risk segment for investigation, while noting that High traffic has no qualifying 10+ km comparison cells under the 30-record rule.

### City Ã— Traffic

The city Ã— traffic comparison reinforces the concentration of slow-delivery burden in Metropolitan and Jam conditions. Metropolitan Ã— Jam had a slow rate of 20.9288% (2,321/11,090), while Urban Ã— Jam had 13.3612% (351/2,627). In Metropolitan, Jam was the highest slow rate within the city; in Urban, Jam was also highest. In every traffic stratum where both Metropolitan and Urban qualified, Metropolitanâ€™s slow rate exceeded Urbanâ€™s: High 6.8648% (231/3,365) vs 3.1746% (30/945), Low 1.7785% (193/10,852) vs 0.4398% (18/4,093), Medium 6.7051% (558/8,322) vs 3.4380% (81/2,356), and Jam 20.9288% vs 13.3612%. At city level, the Metropolitan Ã— Jam cell alone accounted for 57.49% of the observed slow-delivery burden (2,321/4,037). Semi-Urban had one qualifying cell, Jam, with n=135 and a 100.0000% slow rate, but this is a small-stratum result that should be read with caution. See [V11](../outputs/charts/V11_city_traffic.png) and [city_traffic_analysis.md](../outputs/city_traffic_analysis.md).

### Time Ã— Traffic

The time Ã— traffic comparison shows that the higher-risk periods are concentrated in jammed conditions. Evening Jam was 19.7704% (1,722/8,710), Late Night Jam was 20.1572% (1,026/5,090), and Morning High was 5.8790% (104/1,769) while Morning Low was 0.0000% (0/5,949). The pattern is consistent with the standalone evidence that evening and late-night periods are operationally relevant, especially when combined with high congestion. See [V12](../outputs/charts/V12_time_traffic.png) and [time_traffic_analysis.md](../outputs/time_traffic_analysis.md).

The time Ã— traffic comparison also highlights the reporting limitation: there was no full traffic-by-time matrix because some time Ã— traffic cells were below 30 records, and no traffic category had both qualifying Morning and Evening cells. This is important for interpretation and for any future design of a more complete operating view.

### Vehicle Ã— Multiple Deliveries

The vehicle Ã— multiple-delivery comparison shows that the workload pattern remains visible within vehicle types, especially for motorcycles and scooters. Motorcycle slow-delivery rates increased across workload categories from 6.2338% at 0 (480/7,700) to 9.6135% at 1 (1,587/16,508), 50.6980% at 2 (690/1,361), and 100.0000% at 3 (322/322). Scooter showed the same pattern: 2.5230% (129/5,113), 4.3235% (401/9,275), 34.6939% (170/490), and 100.0000% (31/31). Electric_scooter category 2 was 36.1538% (47/130), but category 3 was small-sample descriptive only (n=8). See [V13](../outputs/charts/V13_vehicle_multiple_deliveries.png) and [vehicle_multiple_delivery_analysis.md](../outputs/vehicle_multiple_delivery_analysis.md).

This indicates that a high workload label is associated with materially higher slow-delivery rates across key vehicle types, but it does not establish that workload itself is the cause of delay.

## 8. Operational Implications

The evidence supports several operationally relevant implications, all framed as hypotheses for further investigation rather than accepted conclusions:

- Jam traffic is the most material slow-delivery segment in the observed data and should be treated as a priority area for operational review. The Metropolitan Ã— Jam segment is especially significant and contributes a majority of slow deliveries.
- Longer straight-line distance combined with congestion appears to be a high-risk operating condition, especially in Jam traffic for the 10â€“15 km and 15+ km bands.
- Evening and late-night delivery periods, particularly under Jam conditions, warrant closer review because they are associated with the highest observed slow-delivery rates while still having substantial sample sizes.
- Multiple-delivery workload is a strong operational signal; categories 2 and 3 merit focused review because they are disproportionately represented among slow deliveries.
- Fog and Cloudy conditions are associated with higher slow-delivery rates than Sunny conditions, especially within Jam traffic, suggesting that weather Ã— traffic segmentation should be considered in operational planning and risk review.
- The strongest consistent observed signal is not a single variable but a set of combinations: congestion + longer distance, congestion + evening or late night, and congested metropolitan conditions.

These are preliminary implications based on observational patterns, not proven causal drivers.

## 9. Preliminary Business Recommendations

The following recommendations are deliberately framed as hypotheses or operational areas worth investigating. They are derived from the observed patterns in the descriptive data and should be validated in the next working phase before any operational policy decisions are made.

1. Investigate jam-traffic operations by geography and time period, with particular attention to Metropolitan deliveries during evening and late-night windows. This is the clearest candidate for an operational review because it carries the largest observed slow-delivery burden.
2. Investigate the combination of congestion and longer delivery distances, especially Jam traffic in the 10â€“15 km and 15+ km bands, as a likely high-risk operating segment for route review and dispatch planning.
3. Examine weather-related congestion patterns, especially Fog and Cloudy conditions under Jam traffic, because they consistently show materially higher slow-delivery rates than low-congestion comparisons in the same weather cells.
4. Review high-workload delivery patterns, particularly multiple-delivery categories 2 and 3, with attention to vehicle type, route complexity, and dispatch sequencing. The observed pattern is strong enough to warrant operational investigation.
5. Improve coverage and interpretability where key cross-factor comparisons are sparse, particularly in smaller city, vehicle, and time-band cells below the 30-record threshold. This is a data-coverage recommendation for future analyses, not a policy prescription.

## 10. Data Quality, Coverage & Limitations

The quality and coverage of the analysis are generally sound for the intended descriptive purpose, but several limitations must be retained when interpreting the findings.

- The dataset used is the cleaned training file, and the project did not modify source or processed data files.
- The performance denominator is 45,593 valid numeric `Time_taken(min)` records; the overall slow-delivery rate is based on that population.
- The fixed slow-delivery definition remained `Time_taken(min) > 40` minutes for all segments and combinations. The threshold was not recalculated by group.
- The 30-record minimum rule was applied consistently; groups below 30 valid records were treated as descriptive only and were not ranked or used for substantive comparison.
- Missing values were excluded only from the relevant grouped comparison and reported explicitly in the underlying descriptive outputs.
- Some cross-factor cells were sparse, preventing a full comparison matrix in every stratum. This is especially visible in time Ã— traffic and some city/vehicle combinations.
- This project is descriptive and observational. It does not establish causal relationships, and it does not imply that a segment is the cause of delay without additional evidence.
- The distance metric is approximate straight-line geographic distance; it is not network distance or actual route distance.
- City, weather, traffic, vehicle, order-time, and workload categories are not adjusted for one another in the descriptive framework, so the results must be interpreted as unadjusted observed associations.

## 11. What This Analysis Does Not Establish

This analysis does not establish any of the following:

- that traffic causes slower delivery times;
- that weather causes delay outright;
- that distance or workload are independent drivers of performance;
- that city geography alone determines operational outcomes;
- that any single variable or interaction is statistically significant;
- that a policy change will improve performance without further validation;
- that the observed patterns generalize beyond this cleaned dataset.

The analysis also does not provide a predictive model, feature ranking, or causal inference framework. It is a diagnostic scan of the observed operational landscape, designed to identify areas worth investigating further.

## 12. Next Phase: Predictive Analytics

This descriptive and diagnostic phase is complete. The next phase is a separate predictive analytics effort that will require a modeling-ready dataset built from the cleaned data, with explicit handling of missing data, feature preparation, and a defined target strategy.

Potential future questions for that phase include:

- predicting delivery time as a continuous outcome;
- identifying which observed features have predictive value;
- classifying potential slow deliveries;
- estimating high-risk operational combinations before execution.

These are separate future activities and are not part of the current descriptive reporting. The current analysis should be treated as the evidence base for a later predictive design effort, not as a predictive model itself.

## 13. Conclusion

The descriptive analytics evidence indicates that slow deliveries are not evenly spread across the operation. The most consistently important observed segments are congestion-heavy conditions, especially Jam traffic, and the combinations of congestion with longer distance, evening/late-night periods, and high workload. The Metropolitan Ã— Jam segment is the single strongest observed concentration of slow-delivery burden, contributing 57.49% of all slow deliveries in the valid-target population. The workload pattern is similarly strong, with category 2 and category 3 multiple-delivery conditions carrying much higher slow-delivery rates than category 0 and category 1. See [analysis/findings.md](../analysis/findings.md).

These findings are operationally valuable because they show where the slow-delivery burden is concentrated. They are also intentionally cautious: they identify observed patterns and high-priority investigation areas, without claiming that the observed conditions are proven drivers of delay. The next step is not a causal model; it is a separate predictive analytics phase built on the cleaned data and designed to answer different questions with explicit prediction-oriented methods.
