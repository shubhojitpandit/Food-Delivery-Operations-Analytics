-- Overall baseline for the cleaned training target.
-- The caller must load data/processed/train_clean.csv into a SQLite relation
-- named train_clean, preserving Time_taken(min) as a numeric column.
--
-- SQLite does not provide a built-in PERCENTILE_CONT aggregate in its standard
-- build. The query below implements continuous linear interpolation using the
-- 1-based rank: 1 + (n - 1) * p, interpolating between adjacent ordered values.
-- It returns one row and uses the overall P90 as the fixed slow threshold.

WITH valid_targets AS (
    SELECT CAST("Time_taken(min)" AS REAL) AS delivery_time
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
population_counts AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        COUNT(*) AS valid_target_rows
    FROM valid_targets
),
ordered_targets AS (
    SELECT
        delivery_time,
        ROW_NUMBER() OVER (ORDER BY delivery_time) AS row_number,
        COUNT(*) OVER () AS valid_target_rows
    FROM valid_targets
),
percentile_points AS (
    SELECT 0.50 AS percentile
    UNION ALL SELECT 0.75
    UNION ALL SELECT 0.90
),
percentile_positions AS (
    SELECT
        percentile,
        1.0 + (valid_target_rows - 1) * percentile AS rank_position
    FROM percentile_points
    CROSS JOIN population_counts
),
percentile_values AS (
    SELECT
        positions.percentile,
        lower_value.delivery_time
            + (upper_value.delivery_time - lower_value.delivery_time)
            * (positions.rank_position - CAST(positions.rank_position AS INTEGER))
            AS percentile_value
    FROM percentile_positions AS positions
    JOIN ordered_targets AS lower_value
      ON lower_value.row_number = CAST(positions.rank_position AS INTEGER)
    JOIN ordered_targets AS upper_value
      ON upper_value.row_number =
         CAST(positions.rank_position AS INTEGER)
         + CASE
             WHEN positions.rank_position > CAST(positions.rank_position AS INTEGER)
             THEN 1
             ELSE 0
           END
),
overall_metrics AS (
    SELECT
        COUNT(*) AS valid_record_count,
        AVG(delivery_time) AS mean_delivery_time,
        MIN(delivery_time) AS minimum_delivery_time,
        MAX(delivery_time) AS maximum_delivery_time
    FROM valid_targets
),
percentile_metrics AS (
    SELECT
        MAX(CASE WHEN percentile = 0.50 THEN percentile_value END) AS median_delivery_time,
        MAX(CASE WHEN percentile = 0.75 THEN percentile_value END) AS p75_delivery_time,
        MAX(CASE WHEN percentile = 0.90 THEN percentile_value END) AS p90_delivery_time
    FROM percentile_values
),
slow_metrics AS (
    SELECT
        SUM(CASE WHEN delivery_time > percentile_metrics.p90_delivery_time THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM valid_targets
    CROSS JOIN percentile_metrics
)
SELECT
    population_counts.total_train_rows,
    population_counts.valid_target_rows,
    population_counts.total_train_rows - population_counts.valid_target_rows
        AS missing_or_invalid_target_rows,
    100.0 * population_counts.valid_target_rows / population_counts.total_train_rows
        AS valid_target_percentage,
    overall_metrics.valid_record_count,
    overall_metrics.mean_delivery_time,
    percentile_metrics.median_delivery_time,
    percentile_metrics.p75_delivery_time,
    percentile_metrics.p90_delivery_time,
    overall_metrics.minimum_delivery_time,
    overall_metrics.maximum_delivery_time,
    slow_metrics.slow_delivery_count,
    1.0 * slow_metrics.slow_delivery_count / overall_metrics.valid_record_count
        AS slow_delivery_rate
FROM population_counts
CROSS JOIN overall_metrics
CROSS JOIN percentile_metrics
CROSS JOIN slow_metrics;
