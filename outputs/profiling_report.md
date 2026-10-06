# Food Delivery Dataset Profiling Report

This report describes the supplied raw CSV files only. It does not clean, overwrite, or add columns to the source data, and it contains no business analysis or derived variables.

Pandas-missing percentages use the number of rows in the corresponding file. Null-like words read as literal text are reported separately. Unique counts exclude pandas-recognized missing values. Numeric-looking statistics use temporary diagnostic parsing only; source values are not changed. The 3×IQR screening is a potential outlier check, not a data-validity conclusion.

## train.csv

- **Rows:** 45,593
- **Columns:** 20
- **Completely duplicated rows:** 0

### Column-by-column profile

#### `ID`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 45,593
- **Distinct values:** '0x4607 ', '0xb379 ', '0x5d6d ', '0x7a6a ', '0x70a2 ', '0x9bb4 ', '0x95b4 ', '0x9eb2 ', '0x1102 ', '0xcdcd ', '0xd987 ', '0x2784 ', '0xc8b6 ', '0xdb64 ', '0x3af3 ', '0x3aab ', '0x689b ', '0x6f67 ', '0xc9cf ', '0x36b8 ', ... (45573 more)

#### `Delivery_person_ID`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 1,320
- **Distinct values:** 'INDORES13DEL02 ', 'BANGRES18DEL02 ', 'BANGRES19DEL01 ', 'COIMBRES13DEL02 ', 'CHENRES12DEL01 ', 'HYDRES09DEL03 ', 'RANCHIRES15DEL01 ', 'MYSRES15DEL02 ', 'HYDRES05DEL02 ', 'DEHRES17DEL01 ', 'KOCRES16DEL01 ', 'PUNERES13DEL03 ', 'LUDHRES15DEL02 ', 'KNPRES14DEL02 ', 'MUMRES15DEL03 ', 'MYSRES01DEL01 ', 'PUNERES20DEL01 ', 'HYDRES14DEL01 ', 'KOLRES15DEL03 ', 'PUNERES19DEL02 ', ... (1300 more)

#### `Delivery_person_Age`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 23
- **Missing-like text markers (not parsed as missing):** 1,854 (4.07%)
- **Distinct values:** '37', '34', '23', '38', '32', '22', '33', '35', '36', '21', '24', '29', '25', '31', '27', '26', '20', 'NaN ', '28', '39', ... (3 more)
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    43739.000000
  mean        29.567137
  std          5.815155
  min         15.000000
  25%         25.000000
  50%         30.000000
  75%         35.000000
  max         50.000000
  ```
- **Numeric-looking minimum / maximum:** 15 / 50

#### `Delivery_person_Ratings`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 29
- **Missing-like text markers (not parsed as missing):** 1,908 (4.18%)
- **Distinct values:** '4.9', '4.5', '4.4', '4.7', '4.6', '4.8', '4.2', '4.3', '4', '4.1', '5', '3.5', 'NaN ', '3.8', '3.9', '3.7', '2.6', '2.5', '3.6', '3.1', ... (9 more)
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    43685.000000
  mean         4.633780
  std          0.334716
  min          1.000000
  25%          4.500000
  50%          4.700000
  75%          4.900000
  max          6.000000
  ```
- **Numeric-looking minimum / maximum:** 1.0 / 6.0

#### `Restaurant_latitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 657
- **Numerical statistics:**

  ```text
count    45593.000000
  mean        17.017729
  std          8.185109
  min        -30.905562
  25%         12.933284
  50%         18.546947
  75%         22.728163
  max         30.914057
  ```
- **Minimum / maximum:** -30.905562 / 30.914057
- **Coordinate bound check:** all numeric values are within [-90, 90].

#### `Restaurant_longitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 518
- **Numerical statistics:**

  ```text
count    45593.000000
  mean        70.231332
  std         22.883647
  min        -88.366217
  25%         73.170000
  50%         75.898497
  75%         78.044095
  max         88.433452
  ```
- **Minimum / maximum:** -88.366217 / 88.433452
- **Coordinate bound check:** all numeric values are within [-180, 180].

#### `Delivery_location_latitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4,373
- **Numerical statistics:**

  ```text
count    45593.000000
  mean        17.465186
  std          7.335122
  min          0.010000
  25%         12.988453
  50%         18.633934
  75%         22.785049
  max         31.054057
  ```
- **Minimum / maximum:** 0.01 / 31.054057
- **Coordinate bound check:** all numeric values are within [-90, 90].

#### `Delivery_location_longitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4,373
- **Numerical statistics:**

  ```text
count    45593.000000
  mean        70.845702
  std         21.118812
  min          0.010000
  25%         73.280000
  50%         76.002574
  75%         78.107044
  max         88.563452
  ```
- **Minimum / maximum:** 0.01 / 88.563452
- **Coordinate bound check:** all numeric values are within [-180, 180].

#### `Order_Date`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 44
- **Distinct values:** '19-03-2022', '25-03-2022', '05-04-2022', '26-03-2022', '11-03-2022', '04-03-2022', '14-03-2022', '20-03-2022', '12-02-2022', '13-02-2022', '14-02-2022', '02-04-2022', '01-03-2022', '16-03-2022', '15-02-2022', '10-03-2022', '27-03-2022', '12-03-2022', '01-04-2022', '05-03-2022', ... (24 more)
- **Parsed date range:** 2022-02-11 to 2022-04-06

#### `Time_Orderd`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 177
- **Missing-like text markers (not parsed as missing):** 1,731 (3.80%)
- **Distinct values:** '11:30:00', '19:45:00', '08:30:00', '18:00:00', '13:30:00', '21:20:00', '19:15:00', '17:25:00', '20:55:00', '21:55:00', '14:55:00', '17:30:00', '09:20:00', '19:50:00', '20:25:00', '20:30:00', '20:40:00', '21:15:00', '20:20:00', '22:30:00', ... (157 more)
- **Time-related inspection:** 43,862 non-missing value(s); sample '11:30:00', '19:45:00', '08:30:00', '18:00:00', '13:30:00'
- **Clock-time range:** 00:00:00 to 23:55:00

#### `Time_Order_picked`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 193
- **Distinct values:** '11:45:00', '19:50:00', '08:45:00', '18:10:00', '13:45:00', '21:30:00', '19:30:00', '17:30:00', '21:05:00', '22:10:00', '15:05:00', '17:40:00', '09:30:00', '20:05:00', '20:35:00', '15:10:00', '20:40:00', '20:50:00', '20:25:00', '22:45:00', ... (173 more)
- **Time-related inspection:** 45,593 non-missing value(s); sample '11:45:00', '19:50:00', '08:45:00', '18:10:00', '13:45:00'
- **Clock-time range:** 00:00:00 to 23:55:00

#### `Weatherconditions`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 7
- **Missing-like text markers (not parsed as missing):** 616 (1.35%)
- **Distinct values:** 'conditions Sunny', 'conditions Stormy', 'conditions Sandstorms', 'conditions Cloudy', 'conditions Fog', 'conditions Windy', 'conditions NaN'

#### `Road_traffic_density`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 5
- **Missing-like text markers (not parsed as missing):** 601 (1.32%)
- **Distinct values:** 'High ', 'Jam ', 'Low ', 'Medium ', 'NaN '

#### `Vehicle_condition`

- **Pandas dtype:** `int64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Numerical statistics:**

  ```text
count    45593.000000
  mean         1.023359
  std          0.839065
  min          0.000000
  25%          0.000000
  50%          1.000000
  75%          2.000000
  max          3.000000
  ```
- **Minimum / maximum:** 0 / 3

#### `Type_of_order`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Distinct values:** 'Snack ', 'Drinks ', 'Buffet ', 'Meal '

#### `Type_of_vehicle`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Distinct values:** 'motorcycle ', 'scooter ', 'electric_scooter ', 'bicycle '

#### `multiple_deliveries`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 5
- **Missing-like text markers (not parsed as missing):** 993 (2.18%)
- **Distinct values:** '0', '1', '3', 'NaN ', '2'
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    44600.000000
  mean         0.744664
  std          0.572473
  min          0.000000
  25%          0.000000
  50%          1.000000
  75%          1.000000
  max          3.000000
  ```
- **Numeric-looking minimum / maximum:** 0 / 3

#### `Festival`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 3
- **Missing-like text markers (not parsed as missing):** 228 (0.50%)
- **Distinct values:** 'No ', 'Yes ', 'NaN '

#### `City`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Missing-like text markers (not parsed as missing):** 1,200 (2.63%)
- **Distinct values:** 'Urban ', 'Metropolitian ', 'Semi-Urban ', 'NaN '

#### `Time_taken(min)`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 45
- **Distinct values:** '(min) 24', '(min) 33', '(min) 26', '(min) 21', '(min) 30', '(min) 40', '(min) 32', '(min) 34', '(min) 46', '(min) 23', '(min) 20', '(min) 41', '(min) 15', '(min) 36', '(min) 39', '(min) 18', '(min) 38', '(min) 47', '(min) 12', '(min) 22', ... (25 more)
- **Numeric-looking duration statistics (diagnostic only):**

  ```text
count    45593.000000
  mean        26.294607
  std          9.383806
  min         10.000000
  25%         19.000000
  50%         26.000000
  75%         32.000000
  max         54.000000
  ```
- **Numeric-looking minimum / maximum:** 10 / 54
- **Time-related inspection:** 45,593 non-missing value(s); sample '(min) 24', '(min) 33', '(min) 26', '(min) 21', '(min) 30'
- Treated as a duration-like field for inspection; no conversion or derived duration was created.

### Potential data-quality issues

- `ID` has leading/trailing whitespace in categorical value(s), for example '0x4607 ', '0xb379 ', '0x5d6d ', '0x7a6a ', '0x70a2 ', ... (45588 more).
- `Delivery_person_ID` has leading/trailing whitespace in categorical value(s), for example 'INDORES13DEL02 ', 'BANGRES18DEL02 ', 'BANGRES19DEL01 ', 'COIMBRES13DEL02 ', 'CHENRES12DEL01 ', ... (1315 more).
- `Delivery_person_Age` contains 1,854 literal text value(s) that look like missing markers: 'NaN '.
- `Delivery_person_Age` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Delivery_person_Age` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Delivery_person_Ratings` contains 1,908 literal text value(s) that look like missing markers: 'NaN '.
- `Delivery_person_Ratings` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Delivery_person_Ratings` has 204 value(s) beyond a 3×IQR screening fence; these are candidates for review, not confirmed errors.
- `Delivery_person_Ratings` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Order_Date` appears date-related but is stored as `str`.
- `Time_Orderd` contains 1,731 literal text value(s) that look like missing markers: 'NaN '.
- `Time_Orderd` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Weatherconditions` contains 616 literal text value(s) that look like missing markers: 'conditions NaN'.
- `Road_traffic_density` contains 601 literal text value(s) that look like missing markers: 'NaN '.
- `Road_traffic_density` has leading/trailing whitespace in categorical value(s), for example 'High ', 'Jam ', 'Low ', 'Medium ', 'NaN '.
- `Type_of_order` has leading/trailing whitespace in categorical value(s), for example 'Snack ', 'Drinks ', 'Buffet ', 'Meal '.
- `Type_of_vehicle` has leading/trailing whitespace in categorical value(s), for example 'motorcycle ', 'scooter ', 'electric_scooter ', 'bicycle '.
- `multiple_deliveries` contains 993 literal text value(s) that look like missing markers: 'NaN '.
- `multiple_deliveries` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `multiple_deliveries` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Festival` contains 228 literal text value(s) that look like missing markers: 'NaN '.
- `Festival` has leading/trailing whitespace in categorical value(s), for example 'No ', 'Yes ', 'NaN '.
- `City` contains 1,200 literal text value(s) that look like missing markers: 'NaN '.
- `City` has leading/trailing whitespace in categorical value(s), for example 'Urban ', 'Metropolitian ', 'Semi-Urban ', 'NaN '.
- `Time_taken(min)` is stored as `str` using text values with a unit prefix rather than a numeric dtype.

## test.csv

- **Rows:** 11,399
- **Columns:** 19
- **Completely duplicated rows:** 0

### Column-by-column profile

#### `ID`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 11,399
- **Distinct values:** '0x2318 ', '0x3474 ', '0x9420 ', '0x72ee ', '0xa759 ', '0xc4af ', '0x3b9d ', '0xdd42 ', '0x872b ', '0x6001 ', '0xd845 ', '0x4946 ', '0x4598 ', '0xbd51 ', '0x73ec ', '0x5ca7 ', '0x9fa6 ', '0x914e ', '0x36e5 ', '0xd82e ', ... (11379 more)

#### `Delivery_person_ID`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 1,297
- **Distinct values:** 'COIMBRES13DEL01 ', 'BANGRES15DEL01 ', 'JAPRES09DEL03 ', 'JAPRES07DEL03 ', 'CHENRES19DEL01 ', 'GOARES04DEL01 ', 'BANGRES19DEL02 ', 'KOLRES06DEL02 ', 'MYSRES05DEL03 ', 'HYDRES04DEL03 ', 'KOCRES09DEL01 ', 'VADRES04DEL01 ', 'RANCHIRES14DEL03 ', 'BANGRES11DEL01 ', 'RANCHIRES010DEL03 ', 'HYDRES19DEL03 ', 'COIMBRES03DEL03 ', 'HYDRES12DEL02 ', 'CHENRES20DEL03 ', 'KOCRES09DEL02 ', ... (1277 more)

#### `Delivery_person_Age`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 23
- **Missing-like text markers (not parsed as missing):** 491 (4.31%)
- **Distinct values:** 'NaN ', '28', '23', '21', '31', '26', '35', '24', '22', '33', '36', '34', '38', '37', '30', '29', '20', '39', '27', '25', ... (3 more)
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    10908.000000
  mean        29.517235
  std          5.797077
  min         15.000000
  25%         25.000000
  50%         30.000000
  75%         34.000000
  max         50.000000
  ```
- **Numeric-looking minimum / maximum:** 15 / 50

#### `Delivery_person_Ratings`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 29
- **Missing-like text markers (not parsed as missing):** 507 (4.45%)
- **Distinct values:** 'NaN ', '4.6', '4.5', '4.8', '4.7', '4.9', '4.2', '2.7', '5', '4.3', '3.8', '4.1', '4.4', '3.9', '4', '3.7', '3.5', '2.8', '3.3', '3.4', ... (9 more)
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    10892.000000
  mean         4.632786
  std          0.344081
  min          1.000000
  25%          4.500000
  50%          4.700000
  75%          4.900000
  max          6.000000
  ```
- **Numeric-looking minimum / maximum:** 1.0 / 6.0

#### `Restaurant_latitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 492
- **Numerical statistics:**

  ```text
count    11399.000000
  mean        17.099934
  std          8.193510
  min        -30.902872
  25%         12.933284
  50%         18.551440
  75%         22.732225
  max         30.914057
  ```
- **Minimum / maximum:** -30.902872 / 30.914057
- **Coordinate bound check:** all numeric values are within [-90, 90].

#### `Restaurant_longitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 434
- **Numerical statistics:**

  ```text
count    11399.000000
  mean        70.399259
  std         22.773144
  min        -88.400467
  25%         73.170937
  50%         75.897429
  75%         78.045732
  max         88.433452
  ```
- **Minimum / maximum:** -88.400467 / 88.433452
- **Coordinate bound check:** all numeric values are within [-180, 180].

#### `Delivery_location_latitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 3,572
- **Numerical statistics:**

  ```text
count    11399.000000
  mean        17.569497
  std          7.287440
  min          0.010000
  25%         12.992532
  50%         18.643481
  75%         22.791226
  max         31.054057
  ```
- **Minimum / maximum:** 0.01 / 31.054057
- **Coordinate bound check:** all numeric values are within [-90, 90].

#### `Delivery_location_longitude`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 3,572
- **Numerical statistics:**

  ```text
count    11399.000000
  mean        71.102187
  std         20.693782
  min          0.010000
  25%         73.771081
  50%         75.996959
  75%         78.109004
  max         88.563452
  ```
- **Minimum / maximum:** 0.01 / 88.563452
- **Coordinate bound check:** all numeric values are within [-180, 180].

#### `Order_Date`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 44
- **Distinct values:** '30-03-2022', '29-03-2022', '10-03-2022', '02-04-2022', '27-03-2022', '15-02-2022', '01-04-2022', '13-02-2022', '02-03-2022', '05-04-2022', '17-02-2022', '08-03-2022', '16-03-2022', '17-03-2022', '15-03-2022', '14-03-2022', '24-03-2022', '16-02-2022', '04-03-2022', '09-03-2022', ... (24 more)
- **Parsed date range:** 2022-02-11 to 2022-04-06

#### `Time_Orderd`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 177
- **Missing-like text markers (not parsed as missing):** 444 (3.90%)
- **Distinct values:** 'NaN ', '20:30:00', '19:35:00', '17:15:00', '18:25:00', '09:45:00', '10:00:00', '18:00:00', '21:30:00', '20:45:00', '14:35:00', '23:40:00', '22:15:00', '20:35:00', '21:55:00', '18:35:00', '21:20:00', '22:10:00', '20:20:00', '12:00:00', ... (157 more)
- **Time-related inspection:** 10,955 non-missing value(s); sample '20:30:00', '19:35:00', '17:15:00', '18:25:00', '09:45:00'
- **Clock-time range:** 00:00:00 to 23:55:00

#### `Time_Order_picked`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 193
- **Distinct values:** '15:05:00', '20:35:00', '19:45:00', '17:20:00', '18:40:00', '09:55:00', '10:05:00', '18:05:00', '21:45:00', '20:55:00', '14:40:00', '23:50:00', '22:25:00', '23:55:00', '21:40:00', '20:50:00', '22:10:00', '18:50:00', '21:25:00', '22:20:00', ... (173 more)
- **Time-related inspection:** 11,399 non-missing value(s); sample '15:05:00', '20:35:00', '19:45:00', '17:20:00', '18:40:00'
- **Clock-time range:** 00:00:00 to 23:55:00

#### `Weatherconditions`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 7
- **Missing-like text markers (not parsed as missing):** 158 (1.39%)
- **Distinct values:** 'conditions NaN', 'conditions Windy', 'conditions Stormy', 'conditions Fog', 'conditions Sunny', 'conditions Cloudy', 'conditions Sandstorms'

#### `Road_traffic_density`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 5
- **Missing-like text markers (not parsed as missing):** 154 (1.35%)
- **Distinct values:** 'NaN ', 'Jam ', 'Medium ', 'Low ', 'High '

#### `Vehicle_condition`

- **Pandas dtype:** `int64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Numerical statistics:**

  ```text
count    11399.000000
  mean         1.031406
  std          0.839599
  min          0.000000
  25%          0.000000
  50%          1.000000
  75%          2.000000
  max          3.000000
  ```
- **Minimum / maximum:** 0 / 3

#### `Type_of_order`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Distinct values:** 'Drinks ', 'Snack ', 'Meal ', 'Buffet '

#### `Type_of_vehicle`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Distinct values:** 'electric_scooter ', 'motorcycle ', 'scooter ', 'bicycle '

#### `multiple_deliveries`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 5
- **Missing-like text markers (not parsed as missing):** 238 (2.09%)
- **Distinct values:** '1', '0', 'NaN ', '2', '3'
- **Numeric-looking text statistics (diagnostic only):**

  ```text
count    11161.000000
  mean         0.749664
  std          0.573657
  min          0.000000
  25%          0.000000
  50%          1.000000
  75%          1.000000
  max          3.000000
  ```
- **Numeric-looking minimum / maximum:** 0 / 3

#### `Festival`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 3
- **Missing-like text markers (not parsed as missing):** 65 (0.57%)
- **Distinct values:** 'No ', 'Yes ', 'NaN '

#### `City`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 4
- **Missing-like text markers (not parsed as missing):** 324 (2.84%)
- **Distinct values:** 'Metropolitian ', 'Urban ', 'NaN ', 'Semi-Urban '

### Potential data-quality issues

- `ID` has leading/trailing whitespace in categorical value(s), for example '0x2318 ', '0x3474 ', '0x9420 ', '0x72ee ', '0xa759 ', ... (11394 more).
- `Delivery_person_ID` has leading/trailing whitespace in categorical value(s), for example 'COIMBRES13DEL01 ', 'BANGRES15DEL01 ', 'JAPRES09DEL03 ', 'JAPRES07DEL03 ', 'CHENRES19DEL01 ', ... (1292 more).
- `Delivery_person_Age` contains 491 literal text value(s) that look like missing markers: 'NaN '.
- `Delivery_person_Age` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Delivery_person_Age` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Delivery_person_Ratings` contains 507 literal text value(s) that look like missing markers: 'NaN '.
- `Delivery_person_Ratings` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Delivery_person_Ratings` has 63 value(s) beyond a 3×IQR screening fence; these are candidates for review, not confirmed errors.
- `Delivery_person_Ratings` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Order_Date` appears date-related but is stored as `str`.
- `Time_Orderd` contains 444 literal text value(s) that look like missing markers: 'NaN '.
- `Time_Orderd` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `Weatherconditions` contains 158 literal text value(s) that look like missing markers: 'conditions NaN'.
- `Road_traffic_density` contains 154 literal text value(s) that look like missing markers: 'NaN '.
- `Road_traffic_density` has leading/trailing whitespace in categorical value(s), for example 'NaN ', 'Jam ', 'Medium ', 'Low ', 'High '.
- `Type_of_order` has leading/trailing whitespace in categorical value(s), for example 'Drinks ', 'Snack ', 'Meal ', 'Buffet '.
- `Type_of_vehicle` has leading/trailing whitespace in categorical value(s), for example 'electric_scooter ', 'motorcycle ', 'scooter ', 'bicycle '.
- `multiple_deliveries` contains 238 literal text value(s) that look like missing markers: 'NaN '.
- `multiple_deliveries` has leading/trailing whitespace in categorical value(s), for example 'NaN '.
- `multiple_deliveries` is stored as `str` although every non-missing, non-marker value can be parsed as numeric.
- `Festival` contains 65 literal text value(s) that look like missing markers: 'NaN '.
- `Festival` has leading/trailing whitespace in categorical value(s), for example 'No ', 'Yes ', 'NaN '.
- `City` contains 324 literal text value(s) that look like missing markers: 'NaN '.
- `City` has leading/trailing whitespace in categorical value(s), for example 'Metropolitian ', 'Urban ', 'NaN ', 'Semi-Urban '.

## Sample_Submission.csv

- **Rows:** 11,399
- **Columns:** 2
- **Completely duplicated rows:** 0

### Column-by-column profile

#### `ID`

- **Pandas dtype:** `str`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 11,399
- **Distinct values:** '0x2318 ', '0x3474 ', '0x9420 ', '0x72ee ', '0xa759 ', '0xc4af ', '0x3b9d ', '0xdd42 ', '0x872b ', '0x6001 ', '0xd845 ', '0x4946 ', '0x4598 ', '0xbd51 ', '0x73ec ', '0x5ca7 ', '0x9fa6 ', '0x914e ', '0x36e5 ', '0xd82e ', ... (11379 more)

#### `Time_taken (min)`

- **Pandas dtype:** `float64`
- **Pandas missing values:** 0 (0.00%)
- **Unique non-missing values:** 9,694
- **Numerical statistics:**

  ```text
count    11399.000000
  mean        26.234647
  std          8.408526
  min         10.394167
  25%         20.143333
  50%         24.527500
  75%         32.139583
  max         52.315833
  ```
- **Minimum / maximum:** 10.394166666666669 / 52.31583333333333
- **Time-related inspection:** 11,399 non-missing value(s); sample '25.668333333333333', '27.881666666666668', '27.023333333333333', '28.15333333333333', '21.01833333333333'
- Treated as a duration-like field for inspection; no conversion or derived duration was created.

### Potential data-quality issues

- `ID` has leading/trailing whitespace in categorical value(s), for example '0x2318 ', '0x3474 ', '0x9420 ', '0x72ee ', '0xa759 ', ... (11394 more).

## Train / test structure comparison

- **Columns in train but not test:** 'Time_taken(min)'
- **Columns in test but not train:** (none)

### Shared-column pandas dtypes

| Column | train.csv dtype | test.csv dtype | Match |
|---|---|---|---|
| `ID` | `str` | `str` | Yes |
| `Delivery_person_ID` | `str` | `str` | Yes |
| `Delivery_person_Age` | `str` | `str` | Yes |
| `Delivery_person_Ratings` | `str` | `str` | Yes |
| `Restaurant_latitude` | `float64` | `float64` | Yes |
| `Restaurant_longitude` | `float64` | `float64` | Yes |
| `Delivery_location_latitude` | `float64` | `float64` | Yes |
| `Delivery_location_longitude` | `float64` | `float64` | Yes |
| `Order_Date` | `str` | `str` | Yes |
| `Time_Orderd` | `str` | `str` | Yes |
| `Time_Order_picked` | `str` | `str` | Yes |
| `Weatherconditions` | `str` | `str` | Yes |
| `Road_traffic_density` | `str` | `str` | Yes |
| `Vehicle_condition` | `int64` | `int64` | Yes |
| `Type_of_order` | `str` | `str` | Yes |
| `Type_of_vehicle` | `str` | `str` | Yes |
| `multiple_deliveries` | `str` | `str` | Yes |
| `Festival` | `str` | `str` | Yes |
| `City` | `str` | `str` | Yes |

### Target-column presence

- Train-only column(s), and therefore target candidate(s) based on structure: 'Time_taken(min)'.
- `Time_taken(min)` exists in train.csv and is absent in test.csv.
