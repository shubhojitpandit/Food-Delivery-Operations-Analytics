# Food Delivery Data Quality Assessment

This assessment investigates potential issues in raw `train.csv` and `test.csv`. It does not clean, overwrite, or create replacement data, and it does not perform business analysis. All diagnostic parsing uses temporary in-memory values only.

Pandas default CSV parsing is used to match the Step 1 inspection. Consequently, pandas-recognized nulls and null-like strings (including padded or embedded markers) are reported separately.

## 1. Missing values

Actual missing means pandas parsed the cell as null. Missing-like text remains a literal string in the source and is counted separately. Percentages use all rows in that file as the denominator.

| File | Column | Actual missing | Missing-like text | Exact marker text |
| --- | --- | --- | --- | --- |
| train.csv | `Delivery_person_Age` | 0 (0.00%) | 1,854 (4.07%) | 'NaN ' |
| train.csv | `Delivery_person_Ratings` | 0 (0.00%) | 1,908 (4.18%) | 'NaN ' |
| train.csv | `Time_Orderd` | 0 (0.00%) | 1,731 (3.80%) | 'NaN ' |
| train.csv | `Weatherconditions` | 0 (0.00%) | 616 (1.35%) | 'conditions NaN' |
| train.csv | `Road_traffic_density` | 0 (0.00%) | 601 (1.32%) | 'NaN ' |
| train.csv | `multiple_deliveries` | 0 (0.00%) | 993 (2.18%) | 'NaN ' |
| train.csv | `Festival` | 0 (0.00%) | 228 (0.50%) | 'NaN ' |
| train.csv | `City` | 0 (0.00%) | 1,200 (2.63%) | 'NaN ' |
| test.csv | `Delivery_person_Age` | 0 (0.00%) | 491 (4.31%) | 'NaN ' |
| test.csv | `Delivery_person_Ratings` | 0 (0.00%) | 507 (4.45%) | 'NaN ' |
| test.csv | `Time_Orderd` | 0 (0.00%) | 444 (3.90%) | 'NaN ' |
| test.csv | `Weatherconditions` | 0 (0.00%) | 158 (1.39%) | 'conditions NaN' |
| test.csv | `Road_traffic_density` | 0 (0.00%) | 154 (1.35%) | 'NaN ' |
| test.csv | `multiple_deliveries` | 0 (0.00%) | 238 (2.09%) | 'NaN ' |
| test.csv | `Festival` | 0 (0.00%) | 65 (0.57%) | 'NaN ' |
| test.csv | `City` | 0 (0.00%) | 324 (2.84%) | 'NaN ' |

## 2. Leading/trailing whitespace

Counts are rows whose string value starts or ends with whitespace; raw values are not stripped. Exact whitespace-bearing values are shown (up to 20 per cell).

| File | Column | Rows affected | Percent | Raw values |
| --- | --- | --- | --- | --- |
| train.csv | `ID` | 45,593 | 100.00% | '0x4607 ', '0xb379 ', '0x5d6d ', '0x7a6a ', '0x70a2 ', '0x9bb4 ', '0x95b4 ', '0x9eb2 ', '0x1102 ', '0xcdcd ', '0xd987 ', '0x2784 ', '0xc8b6 ', '0xdb64 ', '0x3af3 ', '0x3aab ', '0x689b ', '0x6f67 ', '0xc9cf ', '0x36b8 ', ... (45573 more) |
| train.csv | `Delivery_person_ID` | 45,593 | 100.00% | 'INDORES13DEL02 ', 'BANGRES18DEL02 ', 'BANGRES19DEL01 ', 'COIMBRES13DEL02 ', 'CHENRES12DEL01 ', 'HYDRES09DEL03 ', 'RANCHIRES15DEL01 ', 'MYSRES15DEL02 ', 'HYDRES05DEL02 ', 'DEHRES17DEL01 ', 'KOCRES16DEL01 ', 'PUNERES13DEL03 ', 'LUDHRES15DEL02 ', 'KNPRES14DEL02 ', 'MUMRES15DEL03 ', 'MYSRES01DEL01 ', 'PUNERES20DEL01 ', 'HYDRES14DEL01 ', 'KOLRES15DEL03 ', 'PUNERES19DEL02 ', ... (1300 more) |
| train.csv | `Delivery_person_Age` | 1,854 | 4.07% | 'NaN ' |
| train.csv | `Delivery_person_Ratings` | 1,908 | 4.18% | 'NaN ' |
| train.csv | `Time_Orderd` | 1,731 | 3.80% | 'NaN ' |
| train.csv | `Road_traffic_density` | 45,593 | 100.00% | 'High ', 'Jam ', 'Low ', 'Medium ', 'NaN ' |
| train.csv | `Type_of_order` | 45,593 | 100.00% | 'Snack ', 'Drinks ', 'Buffet ', 'Meal ' |
| train.csv | `Type_of_vehicle` | 45,593 | 100.00% | 'motorcycle ', 'scooter ', 'electric_scooter ', 'bicycle ' |
| train.csv | `multiple_deliveries` | 993 | 2.18% | 'NaN ' |
| train.csv | `Festival` | 45,593 | 100.00% | 'No ', 'Yes ', 'NaN ' |
| train.csv | `City` | 45,593 | 100.00% | 'Urban ', 'Metropolitian ', 'Semi-Urban ', 'NaN ' |
| test.csv | `ID` | 11,399 | 100.00% | '0x2318 ', '0x3474 ', '0x9420 ', '0x72ee ', '0xa759 ', '0xc4af ', '0x3b9d ', '0xdd42 ', '0x872b ', '0x6001 ', '0xd845 ', '0x4946 ', '0x4598 ', '0xbd51 ', '0x73ec ', '0x5ca7 ', '0x9fa6 ', '0x914e ', '0x36e5 ', '0xd82e ', ... (11379 more) |
| test.csv | `Delivery_person_ID` | 11,399 | 100.00% | 'COIMBRES13DEL01 ', 'BANGRES15DEL01 ', 'JAPRES09DEL03 ', 'JAPRES07DEL03 ', 'CHENRES19DEL01 ', 'GOARES04DEL01 ', 'BANGRES19DEL02 ', 'KOLRES06DEL02 ', 'MYSRES05DEL03 ', 'HYDRES04DEL03 ', 'KOCRES09DEL01 ', 'VADRES04DEL01 ', 'RANCHIRES14DEL03 ', 'BANGRES11DEL01 ', 'RANCHIRES010DEL03 ', 'HYDRES19DEL03 ', 'COIMBRES03DEL03 ', 'HYDRES12DEL02 ', 'CHENRES20DEL03 ', 'KOCRES09DEL02 ', ... (1277 more) |
| test.csv | `Delivery_person_Age` | 491 | 4.31% | 'NaN ' |
| test.csv | `Delivery_person_Ratings` | 507 | 4.45% | 'NaN ' |
| test.csv | `Time_Orderd` | 444 | 3.90% | 'NaN ' |
| test.csv | `Road_traffic_density` | 11,399 | 100.00% | 'NaN ', 'Jam ', 'Medium ', 'Low ', 'High ' |
| test.csv | `Type_of_order` | 11,399 | 100.00% | 'Drinks ', 'Snack ', 'Meal ', 'Buffet ' |
| test.csv | `Type_of_vehicle` | 11,399 | 100.00% | 'electric_scooter ', 'motorcycle ', 'scooter ', 'bicycle ' |
| test.csv | `multiple_deliveries` | 238 | 2.09% | 'NaN ' |
| test.csv | `Festival` | 11,399 | 100.00% | 'No ', 'Yes ', 'NaN ' |
| test.csv | `City` | 11,399 | 100.00% | 'Metropolitian ', 'Urban ', 'NaN ', 'Semi-Urban ' |

## 3. String columns with date, time, or numeric-looking content

Parsing below is temporary diagnostic inspection only; source columns are unchanged. Numeric candidates list how many non-null, non-marker cells parsed.

| File | Column | Current dtype | Content type | Inspection | Unparsed |
| --- | --- | --- | --- | --- | --- |
| train.csv | `Delivery_person_Age` | `str` | Numeric-looking string | 43,739 parsed; range 15 to 50 | 0 |
| train.csv | `Delivery_person_Ratings` | `str` | Numeric-looking string | 43,685 parsed; range 1.0 to 6.0 | 0 |
| train.csv | `Order_Date` | `str` | Date string | 2022-02-11 to 2022-04-06 | 0 |
| train.csv | `Time_Orderd` | `str` | Clock-time string | 00:00:00 to 23:55:00 | 0 |
| train.csv | `Time_Order_picked` | `str` | Clock-time string | 00:00:00 to 23:55:00 | 0 |
| train.csv | `multiple_deliveries` | `str` | Numeric-looking string | 44,600 parsed; range 0 to 3 | 0 |
| train.csv | `Time_taken(min)` | `str` | Target with `(min)` prefix | prefix values: 45,593; numeric range: 10 to 54 | 0 |
| test.csv | `Delivery_person_Age` | `str` | Numeric-looking string | 10,908 parsed; range 15 to 50 | 0 |
| test.csv | `Delivery_person_Ratings` | `str` | Numeric-looking string | 10,892 parsed; range 1.0 to 6.0 | 0 |
| test.csv | `Order_Date` | `str` | Date string | 2022-02-11 to 2022-04-06 | 0 |
| test.csv | `Time_Orderd` | `str` | Clock-time string | 00:00:00 to 23:55:00 | 0 |
| test.csv | `Time_Order_picked` | `str` | Clock-time string | 00:00:00 to 23:55:00 | 0 |
| test.csv | `multiple_deliveries` | `str` | Numeric-looking string | 11,161 parsed; range 0 to 3 | 0 |

## 4. Delivery person ratings

Exact numeric values are parsed from non-missing, non-marker rating strings for comparison only. The raw data is not corrected or filtered.

| File | Distinct numeric-looking values | Below 1 | Above 5 | Equal to 6 |
| --- | --- | --- | --- | --- |
| train.csv | 1, 2.5, 2.6, 2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5, 6 | 0 | 53 | 53 |
| test.csv | 1, 2.5, 2.6, 2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5, 6 | 0 | 10 | 10 |

- **Equal to 6 across train/test:** 63; occurs in train.csv, test.csv.
- **Exact distinct numeric-looking values across both files:** 1, 2.5, 2.6, 2.7, 2.8, 2.9, 3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 5, 6.

## 5. Geographic coordinates

Geographic bounds are checked against the universal latitude/longitude limits. The value `0.01` is counted exactly as stored. Because datasets may span multiple regions, a globally valid coordinate is not by itself evidence of correctness.

| File | Coordinate | dtype | Min / max | Count = 0.01 | Count = 0 | Count < 0 | Outside global bounds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train.csv | `Restaurant_latitude` | float64 | -30.905562 / 30.914057 | 0 | 3,640 | 431 | 0 |
| train.csv | `Restaurant_longitude` | float64 | -88.366217 / 88.433452 | 0 | 3,640 | 162 | 0 |
| train.csv | `Delivery_location_latitude` | float64 | 0.01 / 31.054057 | 327 | 0 | 0 | 0 |
| train.csv | `Delivery_location_longitude` | float64 | 0.01 / 88.563452 | 327 | 0 | 0 | 0 |
| test.csv | `Restaurant_latitude` | float64 | -30.902872 / 30.914057 | 0 | 870 | 114 | 0 |
| test.csv | `Restaurant_longitude` | float64 | -88.400467 / 88.433452 | 0 | 870 | 47 | 0 |
| test.csv | `Delivery_location_latitude` | float64 | 0.01 / 31.054057 | 83 | 0 | 0 | 0 |
| test.csv | `Delivery_location_longitude` | float64 | 0.01 / 88.563452 | 83 | 0 | 0 | 0 |

### Restaurant/delivery coordinate pairing

| File | Complete coordinate rows | Exact same restaurant/delivery pair | Rows with any coordinate = 0.01 | All four coordinates = 0.01 | All four coordinates = 0 | Negative restaurant latitudes | Negative restaurant longitudes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train.csv | 45,593 | 0 | 327 | 0 | 0 | 431 | 162 |
| test.csv | 11,399 | 0 | 83 | 0 | 0 | 114 | 47 |

This pairing check compares row-wise values only. Non-identical location pairs are not treated as errors; source locations or a geographic reference would be needed to validate actual places.

## 6. Date and time quality

Order/pickup comparisons use clock-time values on the same 24-hour clock because the files provide no pickup date. A pickup time earlier than an order time is therefore reported as a possible midnight crossing, not a proven chronology error.

### train.csv order/pickup clock comparison

- Rows with both valid clock values: 43,862.
- Pickup earlier than order by same-day clock comparison: 831 (possible midnight-crossing records).
- Of those, order at/after 18:00 and pickup at/before 06:00: 831 (more plausible overnight-clock pattern).
- Order and pickup comparisons that are not earlier: 43,031.

### test.csv order/pickup clock comparison

- Rows with both valid clock values: 10,955.
- Pickup earlier than order by same-day clock comparison: 202 (possible midnight-crossing records).
- Of those, order at/after 18:00 and pickup at/before 06:00: 202 (more plausible overnight-clock pattern).
- Order and pickup comparisons that are not earlier: 10,753.

| File | Column | dtype | Actual missing | Missing-like text | Malformed non-marker values | Valid range |
| --- | --- | --- | --- | --- | --- | --- |
| train.csv | `Order_Date` | str | 0 | 0 | 0 | 2022-02-11 to 2022-04-06 |
| train.csv | `Time_Orderd` | str | 0 | 1,731 | 0 | 00:00:00 to 23:55:00 |
| train.csv | `Time_Order_picked` | str | 0 | 0 | 0 | 00:00:00 to 23:55:00 |
| test.csv | `Order_Date` | str | 0 | 0 | 0 | 2022-02-11 to 2022-04-06 |
| test.csv | `Time_Orderd` | str | 0 | 444 | 0 | 00:00:00 to 23:55:00 |
| test.csv | `Time_Order_picked` | str | 0 | 0 | 0 | 00:00:00 to 23:55:00 |

## 7. Categorical consistency

Category labels and counts are displayed exactly as read, including padding. Whitespace-normalized groups are diagnostic comparisons only. The known `Metropolitian` label is called out for verification against an authoritative category spelling; no correction is applied.

### `Weatherconditions`

- **train.csv raw valid categories:** 'conditions Fog' (7,654), 'conditions Stormy' (7,586), 'conditions Cloudy' (7,536), 'conditions Sandstorms' (7,495), 'conditions Windy' (7,422), 'conditions Sunny' (7,284)
- **train.csv missing-like categories:** 'conditions NaN' (616)
- **train.csv categories with leading/trailing whitespace:** none
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'conditions Sunny' (1,975), 'conditions Windy' (1,948), 'conditions Sandstorms' (1,878), 'conditions Cloudy' (1,861), 'conditions Stormy' (1,811), 'conditions Fog' (1,768)
- **test.csv missing-like categories:** 'conditions NaN' (158)
- **test.csv categories with leading/trailing whitespace:** none
- **test.csv labels that collapse after whitespace/case normalization:** none

### `Road_traffic_density`

- **train.csv raw valid categories:** 'Low ' (15,477), 'Jam ' (14,143), 'Medium ' (10,947), 'High ' (4,425)
- **train.csv missing-like categories:** 'NaN ' (601)
- **train.csv categories with leading/trailing whitespace:** 'High ', 'Jam ', 'Low ', 'Medium '
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'Low ' (3,881), 'Jam ' (3,503), 'Medium ' (2,751), 'High ' (1,110)
- **test.csv missing-like categories:** 'NaN ' (154)
- **test.csv categories with leading/trailing whitespace:** 'High ', 'Jam ', 'Low ', 'Medium '
- **test.csv labels that collapse after whitespace/case normalization:** none

### `Type_of_order`

- **train.csv raw valid categories:** 'Snack ' (11,533), 'Meal ' (11,458), 'Drinks ' (11,322), 'Buffet ' (11,280)
- **train.csv missing-like categories:** (none)
- **train.csv categories with leading/trailing whitespace:** 'Buffet ', 'Drinks ', 'Meal ', 'Snack '
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'Drinks ' (2,920), 'Buffet ' (2,870), 'Snack ' (2,815), 'Meal ' (2,794)
- **test.csv missing-like categories:** (none)
- **test.csv categories with leading/trailing whitespace:** 'Buffet ', 'Drinks ', 'Meal ', 'Snack '
- **test.csv labels that collapse after whitespace/case normalization:** none

### `Type_of_vehicle`

- **train.csv raw valid categories:** 'motorcycle ' (26,435), 'scooter ' (15,276), 'electric_scooter ' (3,814), 'bicycle ' (68)
- **train.csv missing-like categories:** (none)
- **train.csv categories with leading/trailing whitespace:** 'bicycle ', 'electric_scooter ', 'motorcycle ', 'scooter '
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'motorcycle ' (6,609), 'scooter ' (3,817), 'electric_scooter ' (950), 'bicycle ' (23)
- **test.csv missing-like categories:** (none)
- **test.csv categories with leading/trailing whitespace:** 'bicycle ', 'electric_scooter ', 'motorcycle ', 'scooter '
- **test.csv labels that collapse after whitespace/case normalization:** none

### `multiple_deliveries`

- **train.csv raw valid categories:** '1' (28,159), '0' (14,095), '2' (1,985), '3' (361)
- **train.csv missing-like categories:** 'NaN ' (993)
- **train.csv categories with leading/trailing whitespace:** none
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** '1' (7,065), '0' (3,491), '2' (513), '3' (92)
- **test.csv missing-like categories:** 'NaN ' (238)
- **test.csv categories with leading/trailing whitespace:** none
- **test.csv labels that collapse after whitespace/case normalization:** none

### `Festival`

- **train.csv raw valid categories:** 'No ' (44,469), 'Yes ' (896)
- **train.csv missing-like categories:** 'NaN ' (228)
- **train.csv categories with leading/trailing whitespace:** 'No ', 'Yes '
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'No ' (11,131), 'Yes ' (203)
- **test.csv missing-like categories:** 'NaN ' (65)
- **test.csv categories with leading/trailing whitespace:** 'No ', 'Yes '
- **test.csv labels that collapse after whitespace/case normalization:** none

### `City`

- **train.csv raw valid categories:** 'Metropolitian ' (34,093), 'Urban ' (10,136), 'Semi-Urban ' (164)
- **train.csv missing-like categories:** 'NaN ' (1,200)
- **train.csv categories with leading/trailing whitespace:** 'Metropolitian ', 'Semi-Urban ', 'Urban '
- **train.csv labels that collapse after whitespace/case normalization:** none
- **test.csv raw valid categories:** 'Metropolitian ' (8,497), 'Urban ' (2,533), 'Semi-Urban ' (45)
- **test.csv missing-like categories:** 'NaN ' (324)
- **test.csv categories with leading/trailing whitespace:** 'Metropolitian ', 'Semi-Urban ', 'Urban '
- **test.csv labels that collapse after whitespace/case normalization:** none
- **Possible spelling issue:** `Metropolitian` occurs in the raw categories and resembles the standard spelling `Metropolitan`; verify the intended label before any standardization.

## 8. Duplicates

Complete duplicates count rows identical across all columns. Duplicate-ID rows count every row whose order ID appears more than once, not just extra occurrences. Repeated delivery-person IDs are reported separately because a person may be associated with multiple records.

| File | Completely duplicated rows | Unique IDs | Rows with repeated ID | Repeated ID occurrences after first | Unique delivery-person IDs | Rows with repeated delivery-person ID |
| --- | --- | --- | --- | --- | --- | --- |
| train.csv | 0 | 45,593 | 0 | 0 | 1,320 | 45,593 |
| test.csv | 0 | 11,399 | 0 | 0 | 1,297 | 11,316 |

- **IDs shared between train and test:** 0.
- **IDs unique to train:** 45,593; **unique to test:** 11,399.

## 9. Train/test consistency

- **Shared columns:** `ID`, `Delivery_person_ID`, `Delivery_person_Age`, `Delivery_person_Ratings`, `Restaurant_latitude`, `Restaurant_longitude`, `Delivery_location_latitude`, `Delivery_location_longitude`, `Order_Date`, `Time_Orderd`, `Time_Order_picked`, `Weatherconditions`, `Road_traffic_density`, `Vehicle_condition`, `Type_of_order`, `Type_of_vehicle`, `multiple_deliveries`, `Festival`, `City`.
- **Train-only columns:** `Time_taken(min)`.
- **Test-only columns:** (none).

### Shared-column dtype comparison

| Column | Train dtype | Test dtype | Match |
| --- | --- | --- | --- |
| `ID` | str | str | Yes |
| `Delivery_person_ID` | str | str | Yes |
| `Delivery_person_Age` | str | str | Yes |
| `Delivery_person_Ratings` | str | str | Yes |
| `Restaurant_latitude` | float64 | float64 | Yes |
| `Restaurant_longitude` | float64 | float64 | Yes |
| `Delivery_location_latitude` | float64 | float64 | Yes |
| `Delivery_location_longitude` | float64 | float64 | Yes |
| `Order_Date` | str | str | Yes |
| `Time_Orderd` | str | str | Yes |
| `Time_Order_picked` | str | str | Yes |
| `Weatherconditions` | str | str | Yes |
| `Road_traffic_density` | str | str | Yes |
| `Vehicle_condition` | int64 | int64 | Yes |
| `Type_of_order` | str | str | Yes |
| `Type_of_vehicle` | str | str | Yes |
| `multiple_deliveries` | str | str | Yes |
| `Festival` | str | str | Yes |
| `City` | str | str | Yes |

### Category/value-pattern comparison

| Column | Train raw categories | Test raw categories | Test-only categories | Train-only categories | Missing-like markers |
| --- | --- | --- | --- | --- | --- |
| `Weatherconditions` | 7 | 7 | (none) | (none) | 'conditions NaN' |
| `Road_traffic_density` | 5 | 5 | (none) | (none) | 'NaN ' |
| `Type_of_order` | 4 | 4 | (none) | (none) | (none) |
| `Type_of_vehicle` | 4 | 4 | (none) | (none) | (none) |
| `multiple_deliveries` | 5 | 5 | (none) | (none) | 'NaN ' |
| `Festival` | 3 | 3 | (none) | (none) | 'NaN ' |
| `City` | 4 | 4 | (none) | (none) | 'NaN ' |

### Numeric-like range comparison

| Column | Train range | Test range | Parsed valid cells (train / test) |
| --- | --- | --- | --- |
| `Delivery_person_Age` | 15 to 50 | 15 to 50 | 43,739 / 10,908 |
| `Delivery_person_Ratings` | 1.0 to 6.0 | 1.0 to 6.0 | 43,685 / 10,892 |
| `multiple_deliveries` | 0 to 3 | 0 to 3 | 44,600 / 11,161 |
| `Restaurant_latitude` | -30.905562 to 30.914057 | -30.902872 to 30.914057 | 45,593 / 11,399 |
| `Restaurant_longitude` | -88.366217 to 88.433452 | -88.400467 to 88.433452 | 45,593 / 11,399 |
| `Delivery_location_latitude` | 0.01 to 31.054057 | 0.01 to 31.054057 | 45,593 / 11,399 |
| `Delivery_location_longitude` | 0.01 to 88.563452 | 0.01 to 88.563452 | 45,593 / 11,399 |

The train-only `Time_taken(min)` field is the target candidate identified by structure. It contains text-prefixed minute values in this file and is absent from test. Category-set differences are shown exactly, including text markers where relevant; they are not automatically treated as schema errors.

## 10. Recommended Data Treatment

These are decision-support recommendations only. No treatment below has been applied to the raw files.

| Issue | Recommendation | Reason |
| --- | --- | --- |
| Text missing markers | Convert to NULL | Literal `NaN`, `NaN `, and embedded forms such as `conditions NaN` represent missing-like text, not pandas nulls; confirm marker rules per column first. |
| Leading/trailing whitespace | normalize/strip | Padding appears in identifiers and categories and can create false category differences. Preserve a raw copy and validate identifiers before matching. |
| Numeric-looking string columns | convert type | Age, ratings, and multiple_deliveries parse numerically after excluding missing-like text; check invalid values and expected domains before conversion. |
| Order_Date | convert type | The observed date strings parse with day-first format; retain malformed values for review rather than silently coercing them. |
| Order/pickup clock columns | convert type | Valid cells parse as `%H:%M:%S`; preserve missing markers and consider midnight semantics before later timeline calculations. |
| Time_taken(min) | convert type | Remove the `(min)` prefix only as an explicit parsed representation in a later cleaning step; preserve the raw target and validate all conversions. |
| Ratings outside 1–5, including 6 | investigate further | Out-of-range ratings are observed. Confirm the source convention before correcting or excluding them; do not infer a replacement. |
| Coordinate values equal to 0.01, negative values, and extreme patterns | investigate further | Counts flag potential sentinel or geographic anomalies, but raw locations cannot be verified without authoritative geography/source metadata. |
| Categorical spelling `Metropolitian` | correct/standardize | It resembles `Metropolitan`, but confirm the intended canonical label and apply consistently across train and test only after validation. |
| Other categorical differences | retain | Keep distinct values unless they are confirmed missing markers or verified spelling/format variants; report unseen labels during later validation. |
| Repeated IDs / complete duplicates | exclude only if justified | Do not discard automatically. Establish ID-key semantics and investigate whether repeated records are legitimate before exclusion. |
| Pandas-recognized nulls | retain | Keep missingness explicit during assessment; choose any imputation or exclusion policy only after the intended downstream use is defined. |
| Pickup clock earlier than order clock | investigate further | Some records may cross midnight, but no pickup date is supplied to establish the correct chronology. Validate source semantics before deriving elapsed time. |

Assessment evidence includes 0 complete train duplicates and 0 complete test duplicates. ID duplicate-row counts are reported in Section 8. The target `Time_taken(min)` is present in train: yes; present in test: no.
