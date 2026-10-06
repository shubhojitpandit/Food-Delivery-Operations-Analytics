-- Type_of_vehicle x multiple_deliveries descriptive analysis.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- The multiple_deliveries values are categories, not a continuous measure.
-- Missing dimensions are excluded from two-way cells and reported separately.
-- Slow delivery uses the fixed Step 5.1 rule: Time_taken(min) > 40.
-- SQLite has no built-in PERCENTILE_CONT; median/P90 use linear interpolation
-- at rank 1 + (n - 1) * p. Ranks are assigned only when cell count >= 30.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        "Type_of_vehicle" AS vehicle_category,
        CASE
            WHEN "multiple_deliveries" IS NULL THEN NULL
            ELSE printf('%g', CAST("multiple_deliveries" AS REAL))
        END AS multiple_category
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
categorized_targets AS (
    SELECT *
    FROM valid_targets
    WHERE vehicle_category IS NOT NULL
      AND multiple_category IS NOT NULL
),
vehicle_categories AS (
    SELECT DISTINCT vehicle_category
    FROM valid_targets
    WHERE vehicle_category IS NOT NULL
),
multiple_categories AS (
    SELECT DISTINCT multiple_category
    FROM valid_targets
    WHERE multiple_category IS NOT NULL
),
category_grid AS (
    SELECT vehicle_category, multiple_category
    FROM vehicle_categories CROSS JOIN multiple_categories
),
group_metrics AS (
    SELECT
        vehicle_category,
        multiple_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY vehicle_category, multiple_category
),
ordered_targets AS (
    SELECT
        vehicle_category,
        multiple_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY vehicle_category, multiple_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY vehicle_category, multiple_category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        vehicle_category,
        multiple_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.vehicle_category,
        positions.multiple_category,
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
      ON median_lower.vehicle_category = positions.vehicle_category
     AND median_lower.multiple_category = positions.multiple_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.vehicle_category = positions.vehicle_category
     AND median_upper.multiple_category = positions.multiple_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.vehicle_category = positions.vehicle_category
     AND p90_lower.multiple_category = positions.multiple_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.vehicle_category = positions.vehicle_category
     AND p90_upper.multiple_category = positions.multiple_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
metrics AS (
    SELECT
        category_grid.vehicle_category,
        category_grid.multiple_category,
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
    FROM category_grid
    LEFT JOIN group_metrics
      USING (vehicle_category, multiple_category)
    LEFT JOIN percentile_values
      USING (vehicle_category, multiple_category)
),
qualifying AS (
    SELECT *
    FROM metrics
    WHERE delivery_count >= 30
),
within_vehicle_ranks AS (
    SELECT
        vehicle_category,
        multiple_category,
        RANK() OVER (
            PARTITION BY vehicle_category ORDER BY mean_delivery_time
        ) AS mean_rank_within_vehicle,
        RANK() OVER (
            PARTITION BY vehicle_category ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_vehicle,
        RANK() OVER (
            PARTITION BY vehicle_category ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_vehicle,
        RANK() OVER (
            PARTITION BY vehicle_category ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_vehicle
    FROM qualifying
),
within_multiple_ranks AS (
    SELECT
        vehicle_category,
        multiple_category,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY mean_delivery_time
        ) AS mean_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_multiple
    FROM qualifying
),
standalone_vehicle AS (
    SELECT
        vehicle_category,
        COUNT(*) AS standalone_vehicle_count,
        AVG(delivery_time) AS standalone_vehicle_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_vehicle_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_vehicle_slow_rate
    FROM valid_targets
    WHERE vehicle_category IS NOT NULL
    GROUP BY vehicle_category
),
standalone_multiple AS (
    SELECT
        multiple_category,
        COUNT(*) AS standalone_multiple_count,
        AVG(delivery_time) AS standalone_multiple_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_multiple_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_multiple_slow_rate
    FROM valid_targets
    WHERE multiple_category IS NOT NULL
    GROUP BY multiple_category
),
population AS (
    SELECT
        COUNT(*) AS total_train_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END) AS valid_target_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Type_of_vehicle" IS NULL
                 THEN 1 ELSE 0 END) AS missing_vehicle_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "multiple_deliveries" IS NULL
                 THEN 1 ELSE 0 END) AS missing_multiple_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Type_of_vehicle" IS NULL
                           OR "multiple_deliveries" IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_for_missing_either_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Time_taken(min)" > 40
                 THEN 1 ELSE 0 END) AS all_slow_delivery_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Type_of_vehicle" IS NULL
                           OR "multiple_deliveries" IS NULL)
                      AND "Time_taken(min)" > 40
                 THEN 1 ELSE 0 END) AS excluded_slow_delivery_count
    FROM train_clean
),
two_way_population AS (
    SELECT COUNT(*) AS eligible_combination_population
    FROM categorized_targets
)
SELECT
    metrics.*,
    within_vehicle_ranks.mean_rank_within_vehicle,
    within_vehicle_ranks.highest_mean_rank_within_vehicle,
    within_vehicle_ranks.slow_rate_rank_within_vehicle,
    within_vehicle_ranks.highest_slow_rate_rank_within_vehicle,
    within_multiple_ranks.mean_rank_within_multiple,
    within_multiple_ranks.highest_mean_rank_within_multiple,
    within_multiple_ranks.slow_rate_rank_within_multiple,
    within_multiple_ranks.highest_slow_rate_rank_within_multiple,
    standalone_vehicle.standalone_vehicle_count,
    standalone_vehicle.standalone_vehicle_mean,
    standalone_vehicle.standalone_vehicle_slow_count,
    standalone_vehicle.standalone_vehicle_slow_rate,
    standalone_multiple.standalone_multiple_count,
    standalone_multiple.standalone_multiple_mean,
    standalone_multiple.standalone_multiple_slow_count,
    standalone_multiple.standalone_multiple_slow_rate,
    population.*,
    two_way_population.eligible_combination_population
FROM metrics
LEFT JOIN within_vehicle_ranks
  USING (vehicle_category, multiple_category)
LEFT JOIN within_multiple_ranks
  USING (vehicle_category, multiple_category)
JOIN standalone_vehicle USING (vehicle_category)
JOIN standalone_multiple USING (multiple_category)
CROSS JOIN population
CROSS JOIN two_way_population
ORDER BY metrics.vehicle_category, CAST(metrics.multiple_category AS REAL);
