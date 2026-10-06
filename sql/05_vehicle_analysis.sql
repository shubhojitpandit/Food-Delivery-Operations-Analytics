-- Separate vehicle-type and vehicle-condition summaries using the fixed
-- Step 5.1 slow-delivery threshold of 40 minutes.
-- Load data/processed/train_clean.csv into SQLite as train_clean.
-- Valid targets are non-NULL numeric Time_taken(min). Missing dimension values
-- are excluded only from the corresponding grouped comparison.
--
-- Standard SQLite has no built-in PERCENTILE_CONT. Median and P90 use
-- continuous linear interpolation at rank 1 + (n - 1) * p.
-- Ranks are populated only for groups with at least 30 valid records.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        "Type_of_vehicle" AS vehicle_type,
        CAST("Vehicle_condition" AS TEXT) AS vehicle_condition
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
dimension_targets AS (
    SELECT 'Type_of_vehicle' AS dimension_name,
           vehicle_type AS category,
           delivery_time
    FROM valid_targets
    UNION ALL
    SELECT 'Vehicle_condition' AS dimension_name,
           vehicle_condition AS category,
           delivery_time
    FROM valid_targets
),
population_counts AS (
    SELECT
        'Type_of_vehicle' AS dimension_name,
        COUNT(*) AS total_train_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END) AS valid_target_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Type_of_vehicle" IS NULL
                 THEN 1 ELSE 0 END) AS valid_targets_missing_dimension
    FROM train_clean
    UNION ALL
    SELECT
        'Vehicle_condition',
        COUNT(*),
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END),
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Vehicle_condition" IS NULL
                 THEN 1 ELSE 0 END)
    FROM train_clean
),
categorized_targets AS (
    SELECT dimension_name, category, delivery_time
    FROM dimension_targets
    WHERE category IS NOT NULL
),
ordered_targets AS (
    SELECT
        dimension_name,
        category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY dimension_name, category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY dimension_name, category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        dimension_name,
        category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.dimension_name,
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
    JOIN ordered_targets AS median_lower
      ON median_lower.dimension_name = positions.dimension_name
     AND median_lower.category = positions.category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.dimension_name = positions.dimension_name
     AND median_upper.category = positions.category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.dimension_name = positions.dimension_name
     AND p90_lower.category = positions.category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.dimension_name = positions.dimension_name
     AND p90_upper.category = positions.category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
group_metrics AS (
    SELECT
        dimension_name,
        category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time
    FROM categorized_targets
    GROUP BY dimension_name, category
),
slow_metrics AS (
    SELECT
        dimension_name,
        category,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY dimension_name, category
),
metrics AS (
    SELECT
        group_metrics.dimension_name,
        group_metrics.category,
        group_metrics.delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        slow_metrics.slow_delivery_count,
        1.0 * slow_metrics.slow_delivery_count / group_metrics.delivery_count
            AS slow_delivery_rate
    FROM group_metrics
    JOIN percentile_values USING (dimension_name, category)
    JOIN slow_metrics USING (dimension_name, category)
),
qualifying_ranks AS (
    SELECT
        dimension_name,
        category,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY mean_delivery_time ASC
        ) AS fastest_mean_rank,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY mean_delivery_time DESC
        ) AS slowest_mean_rank,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY median_delivery_time ASC
        ) AS fastest_median_rank,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY median_delivery_time DESC
        ) AS slowest_median_rank,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY slow_delivery_rate ASC
        ) AS lowest_slow_rate_rank,
        RANK() OVER (
            PARTITION BY dimension_name ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank
    FROM metrics
    WHERE delivery_count >= 30
)
SELECT
    metrics.dimension_name,
    metrics.category,
    metrics.delivery_count,
    metrics.mean_delivery_time,
    metrics.median_delivery_time,
    metrics.p90_delivery_time,
    metrics.slow_delivery_count,
    metrics.slow_delivery_rate,
    CASE WHEN metrics.delivery_count >= 30 THEN 'qualifies' ELSE 'small_sample' END
        AS sample_size_status,
    qualifying_ranks.fastest_mean_rank,
    qualifying_ranks.slowest_mean_rank,
    qualifying_ranks.fastest_median_rank,
    qualifying_ranks.slowest_median_rank,
    qualifying_ranks.lowest_slow_rate_rank,
    qualifying_ranks.highest_slow_rate_rank,
    population_counts.total_train_rows,
    population_counts.valid_target_rows,
    population_counts.valid_target_rows
        - population_counts.valid_targets_missing_dimension AS valid_targets_with_dimension,
    population_counts.valid_targets_missing_dimension
        AS valid_targets_excluded_for_missing_dimension
FROM metrics
JOIN population_counts USING (dimension_name)
LEFT JOIN qualifying_ranks USING (dimension_name, category)
ORDER BY metrics.dimension_name, metrics.category;
