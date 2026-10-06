-- Approximate straight-line geographic distance using the Haversine formula.
-- The Python validator loads the unchanged training rows as train_clean. SQL
-- independently recalculates Haversine distance for row-level verification.
-- Earth radius is fixed at 6,371.0088 km (mean Earth radius).
-- Coordinates must be numeric and within latitude [-90, 90] and longitude
-- [-180, 180]. Missing and implausible rows receive no derived distance.
-- SQLite has no built-in PERCENTILE_CONT; percentiles use continuous linear
-- interpolation at rank 1 + (n - 1) * p.

CREATE TEMP VIEW distance_analysis AS
WITH coordinate_values AS (
    SELECT
        rowid AS source_row_id,
        "ID" AS order_id,
        "Time_taken(min)" AS delivery_time,
        "Restaurant_latitude" AS restaurant_latitude_raw,
        "Restaurant_longitude" AS restaurant_longitude_raw,
        "Delivery_location_latitude" AS delivery_latitude_raw,
        "Delivery_location_longitude" AS delivery_longitude_raw,
        "City" AS city,
        "Road_traffic_density" AS road_traffic_density,
        "Weatherconditions" AS weather_conditions,
        "Type_of_vehicle" AS vehicle_type,
        typeof("Time_taken(min)") IN ('integer', 'real') AS target_numeric,
        typeof("Restaurant_latitude") IN ('integer', 'real')
            AS restaurant_latitude_numeric,
        typeof("Restaurant_longitude") IN ('integer', 'real')
            AS restaurant_longitude_numeric,
        typeof("Delivery_location_latitude") IN ('integer', 'real')
            AS delivery_latitude_numeric,
        typeof("Delivery_location_longitude") IN ('integer', 'real')
            AS delivery_longitude_numeric,
        CASE WHEN "Restaurant_latitude" IS NULL THEN 1 ELSE 0 END
            AS restaurant_latitude_missing,
        CASE WHEN "Restaurant_longitude" IS NULL THEN 1 ELSE 0 END
            AS restaurant_longitude_missing,
        CASE WHEN "Delivery_location_latitude" IS NULL THEN 1 ELSE 0 END
            AS delivery_latitude_missing,
        CASE WHEN "Delivery_location_longitude" IS NULL THEN 1 ELSE 0 END
            AS delivery_longitude_missing
    FROM train_clean
),
numeric_coordinates AS (
    SELECT
        *,
        CASE WHEN restaurant_latitude_numeric
             THEN CAST(restaurant_latitude_raw AS REAL) END
            AS restaurant_latitude,
        CASE WHEN restaurant_longitude_numeric
             THEN CAST(restaurant_longitude_raw AS REAL) END
            AS restaurant_longitude,
        CASE WHEN delivery_latitude_numeric
             THEN CAST(delivery_latitude_raw AS REAL) END
            AS delivery_latitude,
        CASE WHEN delivery_longitude_numeric
             THEN CAST(delivery_longitude_raw AS REAL) END
            AS delivery_longitude
    FROM coordinate_values
),
coordinate_status AS (
    SELECT
        *,
        CASE
            WHEN restaurant_latitude_numeric
             AND restaurant_longitude_numeric
             AND delivery_latitude_numeric
             AND delivery_longitude_numeric
             AND restaurant_latitude BETWEEN -90 AND 90
             AND delivery_latitude BETWEEN -90 AND 90
             AND restaurant_longitude BETWEEN -180 AND 180
             AND delivery_longitude BETWEEN -180 AND 180
            THEN 1 ELSE 0
        END AS coordinates_valid,
        CASE
            WHEN restaurant_latitude_missing
              OR restaurant_longitude_missing
              OR delivery_latitude_missing
              OR delivery_longitude_missing
            THEN 1 ELSE 0
        END AS coordinates_missing,
        CASE
            WHEN (restaurant_latitude_raw IS NOT NULL
                  AND NOT restaurant_latitude_numeric)
              OR (restaurant_longitude_raw IS NOT NULL
                  AND NOT restaurant_longitude_numeric)
              OR (delivery_latitude_raw IS NOT NULL
                  AND NOT delivery_latitude_numeric)
              OR (delivery_longitude_raw IS NOT NULL
                  AND NOT delivery_longitude_numeric)
            THEN 1 ELSE 0
        END AS coordinates_non_numeric,
        CASE
            WHEN (restaurant_latitude_numeric
                  AND restaurant_latitude NOT BETWEEN -90 AND 90)
              OR (delivery_latitude_numeric
                  AND delivery_latitude NOT BETWEEN -90 AND 90)
              OR (restaurant_longitude_numeric
                  AND restaurant_longitude NOT BETWEEN -180 AND 180)
              OR (delivery_longitude_numeric
                  AND delivery_longitude NOT BETWEEN -180 AND 180)
            THEN 1 ELSE 0
        END AS coordinates_out_of_range
    FROM numeric_coordinates
),
haversine_components AS (
    SELECT
        *,
        sin(radians(delivery_latitude - restaurant_latitude) / 2.0)
            * sin(radians(delivery_latitude - restaurant_latitude) / 2.0)
        + cos(radians(restaurant_latitude))
            * cos(radians(delivery_latitude))
            * sin(radians(delivery_longitude - restaurant_longitude) / 2.0)
            * sin(radians(delivery_longitude - restaurant_longitude) / 2.0)
            AS haversine_a
    FROM coordinate_status
    WHERE coordinates_valid = 1
)
SELECT
    *,
    6371.0088 * 2.0 * asin(
        sqrt(
            CASE
                WHEN haversine_a < 0 THEN 0
                WHEN haversine_a > 1 THEN 1
                ELSE haversine_a
            END
        )
    ) AS distance_km
FROM haversine_components;

SELECT
    COUNT(*) AS total_train_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL THEN 1 ELSE 0 END)
        AS valid_target_rows,
    SUM(CASE WHEN coordinates_valid = 1 THEN 1 ELSE 0 END)
        AS valid_coordinate_count,
    SUM(CASE WHEN coordinates_missing = 1 THEN 1 ELSE 0 END)
        AS rows_with_missing_coordinates,
    SUM(CASE WHEN coordinates_non_numeric = 1 THEN 1 ELSE 0 END)
        AS rows_with_non_numeric_coordinates,
    SUM(CASE WHEN coordinates_out_of_range = 1 THEN 1 ELSE 0 END)
        AS rows_with_out_of_range_coordinates,
    SUM(CASE WHEN coordinates_non_numeric = 1
                  OR coordinates_out_of_range = 1 THEN 1 ELSE 0 END)
        AS rows_with_invalid_coordinates,
    SUM(CASE WHEN coordinates_valid = 0 THEN 1 ELSE 0 END)
        AS rows_excluded_for_invalid_or_missing_coordinates,
    SUM(CASE WHEN restaurant_latitude_missing = 1 THEN 1 ELSE 0 END)
        AS missing_restaurant_latitude,
    SUM(CASE WHEN restaurant_longitude_missing = 1 THEN 1 ELSE 0 END)
        AS missing_restaurant_longitude,
    SUM(CASE WHEN delivery_latitude_missing = 1 THEN 1 ELSE 0 END)
        AS missing_delivery_latitude,
    SUM(CASE WHEN delivery_longitude_missing = 1 THEN 1 ELSE 0 END)
        AS missing_delivery_longitude,
    SUM(CASE WHEN restaurant_latitude_numeric = 0
                  AND restaurant_latitude_raw IS NOT NULL THEN 1 ELSE 0 END)
        AS non_numeric_restaurant_latitude,
    SUM(CASE WHEN restaurant_longitude_numeric = 0
                  AND restaurant_longitude_raw IS NOT NULL THEN 1 ELSE 0 END)
        AS non_numeric_restaurant_longitude,
    SUM(CASE WHEN delivery_latitude_numeric = 0
                  AND delivery_latitude_raw IS NOT NULL THEN 1 ELSE 0 END)
        AS non_numeric_delivery_latitude,
    SUM(CASE WHEN delivery_longitude_numeric = 0
                  AND delivery_longitude_raw IS NOT NULL THEN 1 ELSE 0 END)
        AS non_numeric_delivery_longitude,
    MIN(restaurant_latitude) AS min_restaurant_latitude,
    MAX(restaurant_latitude) AS max_restaurant_latitude,
    MIN(delivery_latitude) AS min_delivery_latitude,
    MAX(delivery_latitude) AS max_delivery_latitude,
    MIN(restaurant_longitude) AS min_restaurant_longitude,
    MAX(restaurant_longitude) AS max_restaurant_longitude,
    MIN(delivery_longitude) AS min_delivery_longitude,
    MAX(delivery_longitude) AS max_delivery_longitude,
    SUM(CASE WHEN restaurant_latitude_raw = 0.01 THEN 1 ELSE 0 END)
        AS restaurant_latitude_0_01_count,
    SUM(CASE WHEN restaurant_longitude_raw = 0.01 THEN 1 ELSE 0 END)
        AS restaurant_longitude_0_01_count,
    SUM(CASE WHEN delivery_latitude_raw = 0.01 THEN 1 ELSE 0 END)
        AS delivery_latitude_0_01_count,
    SUM(CASE WHEN delivery_longitude_raw = 0.01 THEN 1 ELSE 0 END)
        AS delivery_longitude_0_01_count,
    SUM(CASE WHEN restaurant_latitude_numeric = 1
                  AND restaurant_latitude NOT BETWEEN -90 AND 90
             THEN 1 ELSE 0 END) AS invalid_restaurant_latitude_range,
    SUM(CASE WHEN restaurant_longitude_numeric = 1
                  AND restaurant_longitude NOT BETWEEN -180 AND 180
             THEN 1 ELSE 0 END) AS invalid_restaurant_longitude_range,
    SUM(CASE WHEN delivery_latitude_numeric = 1
                  AND delivery_latitude NOT BETWEEN -90 AND 90
             THEN 1 ELSE 0 END) AS invalid_delivery_latitude_range,
    SUM(CASE WHEN delivery_longitude_numeric = 1
                  AND delivery_longitude NOT BETWEEN -180 AND 180
             THEN 1 ELSE 0 END) AS invalid_delivery_longitude_range
FROM distance_analysis;

WITH ordered_distances AS (
    SELECT
        distance_km,
        ROW_NUMBER() OVER (ORDER BY distance_km) AS row_number,
        COUNT(*) OVER () AS distance_count
    FROM distance_analysis
    WHERE target_numeric = 1
      AND delivery_time IS NOT NULL
      AND distance_km IS NOT NULL
),
percentile_positions AS (
    SELECT DISTINCT
        distance_count,
        1.0 + (distance_count - 1) * 0.25 AS p25_rank,
        1.0 + (distance_count - 1) * 0.50 AS median_rank,
        1.0 + (distance_count - 1) * 0.75 AS p75_rank,
        1.0 + (distance_count - 1) * 0.90 AS p90_rank
    FROM ordered_distances
),
percentile_values AS (
    SELECT
        p25_lower.distance_km
            + (p25_upper.distance_km - p25_lower.distance_km)
            * (positions.p25_rank - CAST(positions.p25_rank AS INTEGER))
            AS p25_distance_km,
        median_lower.distance_km
            + (median_upper.distance_km - median_lower.distance_km)
            * (positions.median_rank - CAST(positions.median_rank AS INTEGER))
            AS median_distance_km,
        p75_lower.distance_km
            + (p75_upper.distance_km - p75_lower.distance_km)
            * (positions.p75_rank - CAST(positions.p75_rank AS INTEGER))
            AS p75_distance_km,
        p90_lower.distance_km
            + (p90_upper.distance_km - p90_lower.distance_km)
            * (positions.p90_rank - CAST(positions.p90_rank AS INTEGER))
            AS p90_distance_km
    FROM percentile_positions AS positions
    JOIN ordered_distances AS p25_lower
      ON p25_lower.row_number = CAST(positions.p25_rank AS INTEGER)
    JOIN ordered_distances AS p25_upper
      ON p25_upper.row_number = CAST(positions.p25_rank AS INTEGER)
         + CASE WHEN positions.p25_rank > CAST(positions.p25_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_distances AS median_lower
      ON median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_distances AS median_upper
      ON median_upper.row_number = CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_distances AS p75_lower
      ON p75_lower.row_number = CAST(positions.p75_rank AS INTEGER)
    JOIN ordered_distances AS p75_upper
      ON p75_upper.row_number = CAST(positions.p75_rank AS INTEGER)
         + CASE WHEN positions.p75_rank > CAST(positions.p75_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_distances AS p90_lower
      ON p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_distances AS p90_upper
      ON p90_upper.row_number = CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
)
SELECT
    COUNT(distance_km) AS distance_count,
    MIN(distance_km) AS minimum_distance_km,
    (SELECT p25_distance_km FROM percentile_values) AS p25_distance_km,
    (SELECT median_distance_km FROM percentile_values) AS median_distance_km,
    (SELECT p75_distance_km FROM percentile_values) AS p75_distance_km,
    (SELECT p90_distance_km FROM percentile_values) AS p90_distance_km,
    MAX(distance_km) AS maximum_distance_km,
    AVG(distance_km) AS mean_distance_km,
    SUM(CASE WHEN distance_km = 0 THEN 1 ELSE 0 END) AS zero_distance_count,
    SUM(CASE WHEN distance_km < 0 THEN 1 ELSE 0 END) AS negative_distance_count,
    SUM(CASE WHEN distance_km > 15 THEN 1 ELSE 0 END)
        AS distance_over_15_km_count,
    SUM(CASE WHEN distance_km > 15
                  AND (delivery_latitude_raw = 0.01
                       OR delivery_longitude_raw = 0.01)
             THEN 1 ELSE 0 END)
        AS distance_over_15_with_delivery_0_01_count,
    SUM(CASE WHEN distance_km IS NULL THEN 1 ELSE 0 END)
        AS missing_derived_distance_count
FROM distance_analysis
WHERE target_numeric = 1
  AND delivery_time IS NOT NULL;

WITH bands(category, sort_order) AS (
    VALUES
        ('0-1 km', 1), ('1-2 km', 2), ('2-3 km', 3),
        ('3-5 km', 4), ('5-10 km', 5), ('10-15 km', 6), ('15+ km', 7)
),
classified AS (
    SELECT
        CASE
            WHEN distance_km < 1 THEN '0-1 km'
            WHEN distance_km < 2 THEN '1-2 km'
            WHEN distance_km < 3 THEN '2-3 km'
            WHEN distance_km < 5 THEN '3-5 km'
            WHEN distance_km < 10 THEN '5-10 km'
            WHEN distance_km < 15 THEN '10-15 km'
            ELSE '15+ km'
        END AS category,
        delivery_time
    FROM distance_analysis
    WHERE target_numeric = 1
      AND delivery_time IS NOT NULL
      AND distance_km IS NOT NULL
),
group_counts AS (
    SELECT
        category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM classified
    GROUP BY category
),
ordered_times AS (
    SELECT
        category,
        delivery_time,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY delivery_time)
            AS row_number,
        COUNT(*) OVER (PARTITION BY category) AS delivery_count
    FROM classified
),
percentile_positions AS (
    SELECT DISTINCT
        category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_times
),
percentile_values AS (
    SELECT
        positions.category,
        median_lower.delivery_time
            + (median_upper.delivery_time - median_lower.delivery_time)
            * (positions.median_rank - CAST(positions.median_rank AS INTEGER))
            AS median_delivery_time,
        p90_lower.delivery_time
            + (p90_upper.delivery_time - p90_lower.delivery_time)
            * (positions.p90_rank - CAST(positions.p90_rank AS INTEGER))
            AS p90_delivery_time
    FROM percentile_positions AS positions
    JOIN ordered_times AS median_lower
      ON median_lower.category = positions.category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_times AS median_upper
      ON median_upper.category = positions.category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_times AS p90_lower
      ON p90_lower.category = positions.category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_times AS p90_upper
      ON p90_upper.category = positions.category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
metrics AS (
    SELECT
        bands.category,
        bands.sort_order,
        COALESCE(group_counts.delivery_count, 0) AS delivery_count,
        group_counts.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        COALESCE(group_counts.slow_delivery_count, 0) AS slow_delivery_count,
        CASE WHEN group_counts.delivery_count IS NULL THEN NULL
             ELSE 1.0 * group_counts.slow_delivery_count
                  / group_counts.delivery_count END AS slow_delivery_rate
    FROM bands
    LEFT JOIN group_counts USING (category)
    LEFT JOIN percentile_values USING (category)
),
ranks AS (
    SELECT
        category,
        RANK() OVER (ORDER BY mean_delivery_time ASC) AS fastest_mean_rank,
        RANK() OVER (ORDER BY mean_delivery_time DESC) AS slowest_mean_rank,
        RANK() OVER (ORDER BY median_delivery_time ASC) AS fastest_median_rank,
        RANK() OVER (ORDER BY median_delivery_time DESC) AS slowest_median_rank,
        RANK() OVER (ORDER BY slow_delivery_rate ASC) AS lowest_slow_rate_rank,
        RANK() OVER (ORDER BY slow_delivery_rate DESC) AS highest_slow_rate_rank
    FROM metrics
    WHERE delivery_count >= 30
)
SELECT
    metrics.*,
    CASE WHEN metrics.delivery_count >= 30 THEN 'qualifies'
         ELSE 'small_sample' END AS sample_size_status,
    ranks.fastest_mean_rank,
    ranks.slowest_mean_rank,
    ranks.fastest_median_rank,
    ranks.slowest_median_rank,
    ranks.lowest_slow_rate_rank,
    ranks.highest_slow_rate_rank
FROM metrics
LEFT JOIN ranks USING (category)
ORDER BY metrics.sort_order;

SELECT
    order_id AS "ID",
    source_row_id,
    distance_km,
    delivery_time AS "Time_taken(min)",
    city AS "City",
    road_traffic_density AS "Road_traffic_density",
    weather_conditions AS "Weatherconditions",
    vehicle_type AS "Type_of_vehicle"
FROM distance_analysis
WHERE target_numeric = 1
  AND delivery_time IS NOT NULL
  AND distance_km IS NOT NULL
ORDER BY distance_km DESC, source_row_id
LIMIT 10;

WITH ranked_pairs AS (
    SELECT
        distance_km,
        delivery_time,
        RANK() OVER (ORDER BY distance_km)
            + (COUNT(*) OVER (PARTITION BY distance_km) - 1) / 2.0
            AS distance_rank,
        RANK() OVER (ORDER BY delivery_time)
            + (COUNT(*) OVER (PARTITION BY delivery_time) - 1) / 2.0
            AS delivery_time_rank
    FROM distance_analysis
    WHERE target_numeric = 1
      AND delivery_time IS NOT NULL
      AND distance_km IS NOT NULL
),
means AS (
    SELECT
        AVG(distance_km) AS mean_distance,
        AVG(delivery_time) AS mean_delivery_time,
        AVG(distance_rank) AS mean_distance_rank,
        AVG(delivery_time_rank) AS mean_delivery_time_rank
    FROM ranked_pairs
),
centered AS (
    SELECT
        ranked_pairs.*,
        ranked_pairs.distance_km - means.mean_distance AS centered_distance,
        ranked_pairs.delivery_time - means.mean_delivery_time AS centered_time,
        ranked_pairs.distance_rank - means.mean_distance_rank AS centered_distance_rank,
        ranked_pairs.delivery_time_rank - means.mean_delivery_time_rank
            AS centered_time_rank
    FROM ranked_pairs
    CROSS JOIN means
)
SELECT
    COUNT(*) AS correlation_pair_count,
    SUM(centered_distance * centered_time)
        / sqrt(SUM(centered_distance * centered_distance)
               * SUM(centered_time * centered_time)) AS pearson_correlation,
    SUM(centered_distance_rank * centered_time_rank)
        / sqrt(SUM(centered_distance_rank * centered_distance_rank)
               * SUM(centered_time_rank * centered_time_rank))
        AS spearman_correlation
FROM centered;

SELECT
    COUNT(*) AS sql_haversine_count,
    COUNT(reference.python_distance_km) AS python_haversine_count,
    MAX(ABS(distance_analysis.distance_km - reference.python_distance_km))
        AS maximum_absolute_distance_difference_km,
    SUM(
        CASE
            WHEN ABS(distance_analysis.distance_km - reference.python_distance_km)
                 > 1e-9 + 1e-12 * ABS(distance_analysis.distance_km)
            THEN 1 ELSE 0
        END
    ) AS distance_calculation_mismatch_count
FROM distance_analysis
JOIN python_distance_reference AS reference
  ON reference.source_row_id = distance_analysis.source_row_id
WHERE distance_analysis.coordinates_valid = 1;
