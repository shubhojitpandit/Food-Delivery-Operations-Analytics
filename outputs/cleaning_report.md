# Food Delivery Cleaning Report

## Scope and files

- **Input files:** `data/raw/train.csv`, `data/raw/test.csv`.
- **Reference file not transformed:** `data/raw/Sample_Submission.csv`.
- **Output files:** `data/processed/train_clean.csv`, `data/processed/test_clean.csv`.
- **Script:** `python/03_clean.py`.
- No business analysis was performed. The raw input files were read-only.

## Transformations applied

- Converted only the confirmed, column-specific missing markers listed below to pandas missing values.
- Stripped leading/trailing whitespace from string values; internal spaces were preserved.
- Converted `Delivery_person_Age`, `Delivery_person_Ratings`, and `multiple_deliveries` to numeric values.
- Parsed `Time_taken(min)` in train by removing its literal `(min)` prefix and converting only the numeric delivery-time value; retained its column name.
- Parsed `Order_Date` strictly as day-first dates in memory. CSV files serialize the dates as ISO `YYYY-MM-DD` strings.
- Parsed clock columns strictly as 24-hour times in memory and serialized them as `HH:MM:SS` strings; missing values remain blank/null.
- Standardized `City` value `Metropolitian` to `Metropolitan` in both datasets.
- Preserved all numeric ratings, including 6; did not modify negative restaurant coordinates or `0.01` delivery coordinates.
- Did not remove complete rows, repeated order/person IDs, or records with missing order time. No pickup duration was calculated.

### Confirmed missing-marker conversions

Counts show marker strings converted per file; pandas-recognized nulls remain missing. `conditions NaN` was handled only in `Weatherconditions`; generic null tokens were handled only in the columns confirmed by Step 2.

| File | Column | Text markers converted |
| --- | --- | --- |
| train.csv | `Delivery_person_Age` | 1,854 |
| train.csv | `Delivery_person_Ratings` | 1,908 |
| train.csv | `Time_Orderd` | 1,731 |
| train.csv | `Road_traffic_density` | 601 |
| train.csv | `multiple_deliveries` | 993 |
| train.csv | `Festival` | 228 |
| train.csv | `City` | 1,200 |
| train.csv | `Weatherconditions` | 616 |
| test.csv | `Delivery_person_Age` | 491 |
| test.csv | `Delivery_person_Ratings` | 507 |
| test.csv | `Time_Orderd` | 444 |
| test.csv | `Road_traffic_density` | 154 |
| test.csv | `multiple_deliveries` | 238 |
| test.csv | `Festival` | 65 |
| test.csv | `City` | 324 |
| test.csv | `Weatherconditions` | 158 |

### City spelling standardization

| File | City values standardized |
| --- | --- |
| train.csv | 34093 |
| test.csv | 8497 |

### Quality flags created

`rating_out_of_range` is 1 when a non-null rating is outside [1, 5]. `suspicious_delivery_coordinates` is 1 when either delivery coordinate equals 0.01. `possible_midnight_crossing` is 1 when both clock values are present and pickup time is earlier than order time; this does not assert actual chronology across dates.

| File | Rows with rating_out_of_range | Rows with suspicious_delivery_coordinates | Rows with possible_midnight_crossing |
| --- | --- | --- | --- |
| train.csv | 53 | 327 | 831 |
| test.csv | 10 | 83 | 202 |

## Rows and schema

| File | Rows before | Rows retained | Rows removed | Complete duplicates before | Complete duplicates after |
| --- | --- | --- | --- | --- | --- |
| train.csv | 45,593 | 45,593 | 0 | 0 | 0 |
| test.csv | 11,399 | 11,399 | 0 | 0 | 0 |

### Before/after dtype and missing-value counts

The cleaned in-memory date dtype is `datetime64[ns]`; time values are Python `datetime.time` objects with missing values preserved. CSV has no native date or time dtype, so those fields are serialized in the documented ISO/clock formats. Before counts distinguish actual pandas nulls from approved text markers; after counts are nulls in the cleaned in-memory values.

| File | Column | Before dtype | After in-memory dtype | Before missing count | After missing count |
| --- | --- | --- | --- | --- | --- |
| train.csv | `ID` | str | str | 0 actual + 0 markers | 0 |
| train.csv | `Delivery_person_ID` | str | str | 0 actual + 0 markers | 0 |
| train.csv | `Delivery_person_Age` | str | float64 | 0 actual + 1,854 markers | 1,854 |
| train.csv | `Delivery_person_Ratings` | str | float64 | 0 actual + 1,908 markers | 1,908 |
| train.csv | `Restaurant_latitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| train.csv | `Restaurant_longitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| train.csv | `Delivery_location_latitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| train.csv | `Delivery_location_longitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| train.csv | `Order_Date` | str | datetime64[us] | 0 actual + 0 markers | 0 |
| train.csv | `Time_Orderd` | str | object | 0 actual + 1,731 markers | 1,731 |
| train.csv | `Time_Order_picked` | str | object | 0 actual + 0 markers | 0 |
| train.csv | `Weatherconditions` | str | str | 0 actual + 616 markers | 616 |
| train.csv | `Road_traffic_density` | str | str | 0 actual + 601 markers | 601 |
| train.csv | `Vehicle_condition` | int64 | int64 | 0 actual + 0 markers | 0 |
| train.csv | `Type_of_order` | str | str | 0 actual + 0 markers | 0 |
| train.csv | `Type_of_vehicle` | str | str | 0 actual + 0 markers | 0 |
| train.csv | `multiple_deliveries` | str | float64 | 0 actual + 993 markers | 993 |
| train.csv | `Festival` | str | str | 0 actual + 228 markers | 228 |
| train.csv | `City` | str | str | 0 actual + 1,200 markers | 1,200 |
| train.csv | `Time_taken(min)` | str | Int64 | 0 actual + 0 markers | 0 |
| train.csv | `rating_out_of_range` (added) | (not present) | int8 | — | 0 |
| train.csv | `suspicious_delivery_coordinates` (added) | (not present) | int8 | — | 0 |
| train.csv | `possible_midnight_crossing` (added) | (not present) | int8 | — | 0 |
| test.csv | `ID` | str | str | 0 actual + 0 markers | 0 |
| test.csv | `Delivery_person_ID` | str | str | 0 actual + 0 markers | 0 |
| test.csv | `Delivery_person_Age` | str | float64 | 0 actual + 491 markers | 491 |
| test.csv | `Delivery_person_Ratings` | str | float64 | 0 actual + 507 markers | 507 |
| test.csv | `Restaurant_latitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| test.csv | `Restaurant_longitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| test.csv | `Delivery_location_latitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| test.csv | `Delivery_location_longitude` | float64 | float64 | 0 actual + 0 markers | 0 |
| test.csv | `Order_Date` | str | datetime64[us] | 0 actual + 0 markers | 0 |
| test.csv | `Time_Orderd` | str | object | 0 actual + 444 markers | 444 |
| test.csv | `Time_Order_picked` | str | object | 0 actual + 0 markers | 0 |
| test.csv | `Weatherconditions` | str | str | 0 actual + 158 markers | 158 |
| test.csv | `Road_traffic_density` | str | str | 0 actual + 154 markers | 154 |
| test.csv | `Vehicle_condition` | int64 | int64 | 0 actual + 0 markers | 0 |
| test.csv | `Type_of_order` | str | str | 0 actual + 0 markers | 0 |
| test.csv | `Type_of_vehicle` | str | str | 0 actual + 0 markers | 0 |
| test.csv | `multiple_deliveries` | str | float64 | 0 actual + 238 markers | 238 |
| test.csv | `Festival` | str | str | 0 actual + 65 markers | 65 |
| test.csv | `City` | str | str | 0 actual + 324 markers | 324 |
| test.csv | `rating_out_of_range` (added) | (not present) | int8 | — | 0 |
| test.csv | `suspicious_delivery_coordinates` (added) | (not present) | int8 | — | 0 |
| test.csv | `possible_midnight_crossing` (added) | (not present) | int8 | — | 0 |

## Validation checks performed

- Train row count preserved: 45,593.
- Test row count preserved: 11,399.
- Target is present in train only.
- Required numeric columns and training target have numeric dtypes.
- Order_Date is datetime; clock columns contain time values or missing values.
- No leading/trailing whitespace remains in string values.
- City spelling standardization is consistent in train and test.
- All quality flags contain only 0/1.
- No complete duplicate rows were introduced.
- Only the three documented quality flags were added.
- SHA-256 checks confirm all raw input files are unchanged.
- Saved CSVs re-read successfully with expected rows, schema, types, formats, and flag values.
- Target `Time_taken(min)` is present only in train; it is not added to test.
- Processed CSV outputs were re-read to confirm headers, row counts, numeric columns, ISO dates, clock format, and binary flags.

## Unresolved data-quality limitations

- A clock comparison cannot determine whether an earlier pickup time truly crossed midnight because no pickup date is supplied; the flag is deliberately named `possible_midnight_crossing`.
- `0.01` delivery coordinate values are preserved and flagged; the cleaning does not establish their geographic correctness.
- Ratings equal to 6 are retained and flagged as out of range, not corrected.
- CSV serialization stores date/time columns as formatted text; consumers should parse the documented formats when loading the files.
- Missing values remain missing; no imputation or row exclusion was performed.
