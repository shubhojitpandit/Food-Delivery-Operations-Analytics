-- Weather-group delivery metrics using the fixed Step 5.1 threshold of 40 minutes.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Valid targets are non-NULL numeric Time_taken(min) values. Missing weather
-- values stay in the overall valid-target population but are excluded from
-- weather-category groups.
--
-- Standard SQLite has no built-in PERCENTILE_CONT. Median and P90 use
-- continuous linear interpolation at rank 1 + (n - 1) * p.

WITH valid_targets AS (
    SELECT
        "Weatherconditions" AS weather_category,
        CAST("Time_taken(min)" AS REAL) AS delivery_time
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
population_counts AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        COUNT(*) AS valid_target_rows,
        SUM(CASE WHEN weather_category IS NULL THEN 1 ELSE 0 END)
            AS valid_targets_with_missing_weather
    FROM valid_targets
),
categorized_targets AS (
    SELECT weather_category, delivery_time
    FROM valid_targets
    WHERE weather_category IS NOT NULL
),
ordered_targets AS (
    SELECT
        weather_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY weather_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (PARTITION BY weather_category) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        weather_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.weather_category,
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
      ON median_lower.weather_category = positions.weather_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.weather_category = positions.weather_category
     AND median_upper.row_number = CAST(positions.median_rank AS INTEGER)
         + CASE
             WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
             THEN 1
             ELSE 0
           END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.weather_category = positions.weather_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.weather_category = positions.weather_category
     AND p90_upper.row_number = CAST(positions.p90_rank AS INTEGER)
         + CASE
             WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
             THEN 1
             ELSE 0
           END
),
group_metrics AS (
    SELECT
        weather_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time
    FROM categorized_targets
    GROUP BY weather_category
),
slow_metrics AS (
    SELECT
        weather_category,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY weather_category
)
SELECT
    group_metrics.weather_category AS "Weatherconditions",
    group_metrics.delivery_count,
    group_metrics.mean_delivery_time,
    percentile_values.median_delivery_time,
    percentile_values.p90_delivery_time,
    slow_metrics.slow_delivery_count,
    1.0 * slow_metrics.slow_delivery_count / group_metrics.delivery_count
        AS slow_delivery_rate,
    population_counts.total_train_rows,
    population_counts.valid_target_rows,
    population_counts.valid_target_rows
        - population_counts.valid_targets_with_missing_weather
        AS valid_targets_with_weather_category,
    population_counts.valid_targets_with_missing_weather
        AS valid_targets_excluded_for_missing_weather
FROM group_metrics
JOIN slow_metrics USING (weather_category)
JOIN percentile_values USING (weather_category)
CROSS JOIN population_counts
ORDER BY group_metrics.weather_category;
