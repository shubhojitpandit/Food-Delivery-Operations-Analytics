-- Traffic-group delivery metrics using the fixed Step 5.1 threshold of 40 minutes.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- The valid-target rule is non-NULL numeric Time_taken(min). Rows with a NULL
-- traffic category remain part of the valid target population but are excluded
-- from category groups, consistent with the analytical framework.
--
-- Standard SQLite has no built-in PERCENTILE_CONT. Group P90 is calculated by
-- continuous linear interpolation at rank 1 + (n - 1) * 0.90.

WITH valid_targets AS (
    SELECT
        "Road_traffic_density" AS traffic_category,
        CAST("Time_taken(min)" AS REAL) AS delivery_time
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
population_counts AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        COUNT(*) AS valid_target_rows,
        SUM(CASE WHEN traffic_category IS NULL THEN 1 ELSE 0 END)
            AS valid_targets_with_missing_traffic
    FROM valid_targets
),
categorized_targets AS (
    SELECT traffic_category, delivery_time
    FROM valid_targets
    WHERE traffic_category IS NOT NULL
),
ordered_targets AS (
    SELECT
        traffic_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY traffic_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (PARTITION BY traffic_category) AS delivery_count
    FROM categorized_targets
),
p90_positions AS (
    SELECT DISTINCT
        traffic_category,
        1.0 + (delivery_count - 1) * 0.90 AS rank_position
    FROM ordered_targets
),
p90_values AS (
    SELECT
        positions.traffic_category,
        lower_value.delivery_time
            + (upper_value.delivery_time - lower_value.delivery_time)
            * (positions.rank_position - CAST(positions.rank_position AS INTEGER))
            AS p90_delivery_time
    FROM p90_positions AS positions
    JOIN ordered_targets AS lower_value
      ON lower_value.traffic_category = positions.traffic_category
     AND lower_value.row_number = CAST(positions.rank_position AS INTEGER)
    JOIN ordered_targets AS upper_value
      ON upper_value.traffic_category = positions.traffic_category
     AND upper_value.row_number =
         CAST(positions.rank_position AS INTEGER)
         + CASE
             WHEN positions.rank_position > CAST(positions.rank_position AS INTEGER)
             THEN 1
             ELSE 0
           END
),
group_metrics AS (
    SELECT
        traffic_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        MIN(delivery_time) AS minimum_delivery_time,
        MAX(delivery_time) AS maximum_delivery_time
    FROM categorized_targets
    GROUP BY traffic_category
),
slow_metrics AS (
    SELECT
        traffic_category,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY traffic_category
)
SELECT
    group_metrics.traffic_category AS "Road_traffic_density",
    group_metrics.delivery_count,
    group_metrics.mean_delivery_time,
    median_values.percentile_value AS median_delivery_time,
    p90_values.p90_delivery_time,
    group_metrics.minimum_delivery_time,
    group_metrics.maximum_delivery_time,
    slow_metrics.slow_delivery_count,
    1.0 * slow_metrics.slow_delivery_count / group_metrics.delivery_count
        AS slow_delivery_rate,
    population_counts.total_train_rows,
    population_counts.valid_target_rows,
    population_counts.valid_target_rows
        - population_counts.valid_targets_with_missing_traffic
        AS valid_targets_with_traffic_category,
    population_counts.valid_targets_with_missing_traffic
        AS valid_targets_excluded_for_missing_traffic
FROM group_metrics
JOIN slow_metrics USING (traffic_category)
JOIN p90_values USING (traffic_category)
JOIN population_counts
LEFT JOIN (
    SELECT
        positions.traffic_category,
        lower_value.delivery_time
            + (upper_value.delivery_time - lower_value.delivery_time)
            * (positions.rank_position - CAST(positions.rank_position AS INTEGER))
            AS percentile_value
    FROM (
        SELECT DISTINCT
            traffic_category,
            1.0 + (delivery_count - 1) * 0.50 AS rank_position
        FROM ordered_targets
    ) AS positions
    JOIN ordered_targets AS lower_value
      ON lower_value.traffic_category = positions.traffic_category
     AND lower_value.row_number = CAST(positions.rank_position AS INTEGER)
    JOIN ordered_targets AS upper_value
      ON upper_value.traffic_category = positions.traffic_category
     AND upper_value.row_number =
         CAST(positions.rank_position AS INTEGER)
         + CASE
             WHEN positions.rank_position > CAST(positions.rank_position AS INTEGER)
             THEN 1
             ELSE 0
           END
) AS median_values USING (traffic_category)
ORDER BY group_metrics.traffic_category;
