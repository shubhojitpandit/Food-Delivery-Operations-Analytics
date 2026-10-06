# Visualization Validation

Charts are generated from `data/processed/train_clean.csv` with Pandas and Matplotlib. The fixed slow rule is `Time_taken(min) > 40`; the established minimum is 30 records.

| Visualization ID | Chart filename | Source analysis | Metric used | Validation status | Caveat |
|---|---|---|---|---|---|
| V01 | V01_delivery_time_distribution.png | Step 5.1 overall | Delivery-time count distribution | VALIDATED | 45,593 targets; 10–54 min; fixed line at 40; slow is strictly >40. |
| V02 | V02_traffic_performance.png | Step 5.2 traffic | Slow rate; slow count / n | VALIDATED | 601 valid targets have missing traffic. |
| V03 | V03_multiple_deliveries.png | Step 5.6 courier / multiple deliveries | Slow rate; slow count / n | VALIDATED | Category labels are categorical; no continuous trend is fitted. |
| V04 | V04_city_performance.png | Step 5.4 city | Slow rate; slow count / n | VALIDATED | Semi-Urban has n=164; all included city groups meet n>=30. |
| V05 | V05_order_time_bands.png | Step 5.7 time | Slow rate; slow count / n | VALIDATED | Strict HH:MM:SS parsing; 1,731 order times are missing or invalid. |
| V06 | V06_distance_bands.png | Step 5.8 distance | Slow rate; slow count / n | VALIDATED | Haversine straight-line distance; extreme 15+ km records are retained. |
| V07 | V07_weather_traffic.png | Step 6.4 Weather × Traffic | Slow-delivery rate by observed cell | VALIDATED | All 24 cells meet n>=30; observational association, not causation. |
| V08 | V08_distance_traffic.png | Step 6.3 Distance × Traffic | Slow-delivery rate by qualifying cell | VALIDATED | Cells below n=30 are uncolored; distance is Haversine straight-line and observational. |
| V09 | V09_vehicle_type.png | Step 5.5 vehicle | Slow rate; slow count / n | VALIDATED | Bicycle n=68; all standalone vehicle categories meet n>=30. |
| V10 | V10_vehicle_condition.png | Step 5.5 vehicle condition | Slow rate; slow count / n | VALIDATED | Vehicle-condition labels are categorical, not a quality scale. |
| V11 | V11_city_traffic.png | Step 6.2 City × Traffic | Mean delivery time in qualifying cells | VALIDATED | Only cells with n>=30 are shaded; subminimum Semi-Urban cells are not compared. |
| V12 | V12_time_traffic.png | Step 6.7 Time × Traffic | Cell count and qualifying-cell slow rate | VALIDATED | Exact Step 5.7 time bands; empty combinations are shown as zero, not inferred categories. |
| V13 | V13_vehicle_multiple_deliveries.png | Step 6.5 Vehicle × Multiple Deliveries | Slow rate for cells meeting n>=30 | VALIDATED | Subminimum cells are shown only as counts, not rate comparisons; category labels remain categorical. |
| V14 | V14_pickup_delay_bands.png | Step 5.7 pickup delay | Delivery count by established delay band | VALIDATED | Only valid non-negative direct same-day differences; 831 ambiguous negative differences excluded. |
