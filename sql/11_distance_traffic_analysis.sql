-- Approximate straight-line geographic distance x road traffic density.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Haversine and distance bands match Step 5.8 exactly; extreme observations
-- remain in the primary analysis.
-- Earth radius: 6,371.0088 km. Bands are [0,1), [1,2), [2,3), [3,5),
-- [5,10), [10,15), and [15, infinity) km.
-- SQLite has no built-in PERCENTILE_CONT; median/P90 use continuous linear
-- interpolation at rank 1 + (n - 1) * p. Ranks require at least 30 records.

CREATE TEMP VIEW distance_traffic_analysis AS
WITH coordinate_values AS (
    SELECT
        rowid AS source_row_id,
        "ID" AS order_id,
        "Time_taken(min)" AS delivery_time_raw,
        "Road_traffic_density" AS traffic_category,
        "Restaurant_latitude" AS restaurant_latitude_raw,
        "Restaurant_longitude" AS restaurant_longitude_raw,
        "Delivery_location_latitude" AS delivery_latitude_raw,
        "Delivery_location_longitude" AS delivery_longitude_raw,
        typeof("Time_taken(min)") IN ('integer', 'real') AS target_numeric,
        typeof("Restaurant_latitude") IN ('integer', 'real')
            AS restaurant_latitude_numeric,
        typeof("Restaurant_longitude") IN ('integer', 'real')
            AS restaurant_longitude_numeric,
        typeof("Delivery_location_latitude") IN ('integer', 'real')
            AS delivery_latitude_numeric,
        typeof("Delivery_location_longitude") IN ('integer', 'real')
            AS delivery_longitude_numeric
    FROM train_clean
),
numeric_values AS (
    SELECT
        *,
        CASE WHEN target_numeric THEN CAST(delivery_time_raw AS REAL) END
            AS delivery_time,
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
            WHEN restaurant_latitude_raw IS NULL
              OR restaurant_longitude_raw IS NULL
              OR delivery_latitude_raw IS NULL
              OR delivery_longitude_raw IS NULL
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
    FROM numeric_values
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
),
distances AS (
    SELECT
        *,
        CASE WHEN coordinates_valid = 1 THEN 6371.0088 * 2.0 * asin(
            sqrt(
                CASE
                    WHEN haversine_a < 0 THEN 0
                    WHEN haversine_a > 1 THEN 1
                    ELSE haversine_a
                END
            )
        ) END AS distance_km
    FROM haversine_components
)
SELECT
    *,
    CASE
        WHEN distance_km IS NULL THEN NULL
        WHEN distance_km < 1 THEN '0-1 km'
        WHEN distance_km < 2 THEN '1-2 km'
        WHEN distance_km < 3 THEN '2-3 km'
        WHEN distance_km < 5 THEN '3-5 km'
        WHEN distance_km < 10 THEN '5-10 km'
        WHEN distance_km < 15 THEN '10-15 km'
        ELSE '15+ km'
    END AS distance_band
FROM distances;

-- Target population, coordinate validity, missing traffic, and slow-count
-- reconciliation components.
SELECT
    COUNT(*) AS total_train_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
             THEN 1 ELSE 0 END) AS valid_target_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND coordinates_valid = 1 THEN 1 ELSE 0 END)
        AS valid_target_coordinate_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND coordinates_valid = 0 THEN 1 ELSE 0 END)
        AS target_rows_excluded_for_coordinates,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND coordinates_valid = 1 AND traffic_category IS NULL
             THEN 1 ELSE 0 END) AS target_rows_missing_traffic,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND coordinates_valid = 1 AND traffic_category IS NOT NULL
             THEN 1 ELSE 0 END) AS categorized_target_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND delivery_time > 40 THEN 1 ELSE 0 END)
        AS all_slow_target_rows,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND delivery_time > 40 AND coordinates_valid = 0
             THEN 1 ELSE 0 END) AS slow_rows_excluded_for_coordinates,
    SUM(CASE WHEN target_numeric = 1 AND delivery_time IS NOT NULL
                  AND delivery_time > 40 AND coordinates_valid = 1
                  AND traffic_category IS NULL
             THEN 1 ELSE 0 END) AS slow_rows_missing_traffic,
    SUM(CASE WHEN coordinates_missing = 1 THEN 1 ELSE 0 END)
        AS rows_with_missing_coordinates,
    SUM(CASE WHEN coordinates_non_numeric = 1 THEN 1 ELSE 0 END)
        AS rows_with_non_numeric_coordinates,
    SUM(CASE WHEN coordinates_out_of_range = 1 THEN 1 ELSE 0 END)
        AS rows_with_out_of_range_coordinates
FROM distance_traffic_analysis;

-- Row-level SQL distances allow independent Python Haversine and band checks.
SELECT
    source_row_id,
    order_id,
    delivery_time,
    traffic_category,
    distance_km,
    distance_band
FROM distance_traffic_analysis
WHERE target_numeric = 1
  AND delivery_time IS NOT NULL
  AND coordinates_valid = 1
ORDER BY source_row_id;

-- All seven exact bands crossed with the traffic categories observed in data.
WITH bands(category, sort_order) AS (
    VALUES
        ('0-1 km', 1), ('1-2 km', 2), ('2-3 km', 3),
        ('3-5 km', 4), ('5-10 km', 5), ('10-15 km', 6), ('15+ km', 7)
),
traffic_categories AS (
    SELECT DISTINCT traffic_category
    FROM distance_traffic_analysis
    WHERE target_numeric = 1
      AND delivery_time IS NOT NULL
      AND coordinates_valid = 1
      AND traffic_category IS NOT NULL
),
categorized AS (
    SELECT
        distance_band,
        traffic_category,
        delivery_time
    FROM distance_traffic_analysis
    WHERE target_numeric = 1
      AND delivery_time IS NOT NULL
      AND coordinates_valid = 1
      AND traffic_category IS NOT NULL
),
group_metrics AS (
    SELECT
        distance_band,
        traffic_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized
    GROUP BY distance_band, traffic_category
),
ordered_targets AS (
    SELECT
        distance_band,
        traffic_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY distance_band, traffic_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY distance_band, traffic_category
        ) AS delivery_count
    FROM categorized
),
percentile_positions AS (
    SELECT DISTINCT
        distance_band,
        traffic_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.distance_band,
        positions.traffic_category,
        median_lower.delivery_time
            + (median_upper.delivery_time - median_lower.delivery_time)
            * (positions.median_rank - CAST(positions.median_rank AS INTEGER))
            AS median_delivery_time,
        p90_lower.delivery_time
            + (p90_upper.delivery_time - p90_lower.delivery_time)
            * (positions.p90_rank - CAST(positions.p90_rank AS INTEGER))
            AS p90_delivery_time
    FROM percentile_positions AS positions
    JOIN ordered_targets AS median_lower
      ON median_lower.distance_band = positions.distance_band
     AND median_lower.traffic_category = positions.traffic_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.distance_band = positions.distance_band
     AND median_upper.traffic_category = positions.traffic_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.distance_band = positions.distance_band
     AND p90_lower.traffic_category = positions.traffic_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.distance_band = positions.distance_band
     AND p90_upper.traffic_category = positions.traffic_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
grid AS (
    SELECT bands.category AS distance_band,
           bands.sort_order,
           traffic_categories.traffic_category
    FROM bands CROSS JOIN traffic_categories
),
metrics AS (
    SELECT
        grid.distance_band,
        grid.sort_order,
        grid.traffic_category,
        COALESCE(group_metrics.delivery_count, 0) AS delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        COALESCE(group_metrics.slow_delivery_count, 0) AS slow_delivery_count,
        CASE WHEN group_metrics.delivery_count IS NULL THEN NULL
             ELSE 1.0 * group_metrics.slow_delivery_count
                  / group_metrics.delivery_count END AS slow_delivery_rate,
        CASE WHEN COALESCE(group_metrics.delivery_count, 0) >= 30
             THEN 'qualifies' ELSE 'small_sample' END AS sample_size_status
    FROM grid
    LEFT JOIN group_metrics
      ON group_metrics.distance_band = grid.distance_band
     AND group_metrics.traffic_category = grid.traffic_category
    LEFT JOIN percentile_values
      ON percentile_values.distance_band = grid.distance_band
     AND percentile_values.traffic_category = grid.traffic_category
),
qualifying AS (
    SELECT *
    FROM metrics
    WHERE delivery_count >= 30
),
within_traffic_ranks AS (
    SELECT
        distance_band,
        traffic_category,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY mean_delivery_time
        ) AS mean_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_traffic
    FROM qualifying
),
within_distance_ranks AS (
    SELECT
        distance_band,
        traffic_category,
        RANK() OVER (
            PARTITION BY distance_band ORDER BY mean_delivery_time
        ) AS mean_rank_within_distance,
        RANK() OVER (
            PARTITION BY distance_band ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_distance,
        RANK() OVER (
            PARTITION BY distance_band ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_distance,
        RANK() OVER (
            PARTITION BY distance_band ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_distance
    FROM qualifying
)
SELECT
    metrics.*,
    within_traffic_ranks.mean_rank_within_traffic,
    within_traffic_ranks.highest_mean_rank_within_traffic,
    within_traffic_ranks.slow_rate_rank_within_traffic,
    within_traffic_ranks.highest_slow_rate_rank_within_traffic,
    within_distance_ranks.mean_rank_within_distance,
    within_distance_ranks.highest_mean_rank_within_distance,
    within_distance_ranks.slow_rate_rank_within_distance,
    within_distance_ranks.highest_slow_rate_rank_within_distance
FROM metrics
LEFT JOIN within_traffic_ranks
  USING (distance_band, traffic_category)
LEFT JOIN within_distance_ranks
  USING (distance_band, traffic_category)
ORDER BY metrics.sort_order, metrics.traffic_category;

-- Ten largest exact-distance rows, matching the Step 5.8 extreme check.
SELECT
    order_id AS "ID",
    source_row_id,
    distance_km,
    delivery_time AS "Time_taken(min)",
    traffic_category AS "Road_traffic_density",
    distance_band
FROM distance_traffic_analysis
WHERE target_numeric = 1
  AND delivery_time IS NOT NULL
  AND coordinates_valid = 1
ORDER BY distance_km DESC, source_row_id
LIMIT 10;
