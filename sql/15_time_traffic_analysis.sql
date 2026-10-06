-- Time-of-day x Road_traffic_density descriptive analysis.
-- Load data/processed/train_clean.csv into a SQLite table named train_clean.
-- Reuses the strict HH:MM:SS parser and fixed Step 5.7 order-time bands:
-- Night 00:00-05:59, Morning 06:00-11:59, Afternoon 12:00-16:59,
-- Evening 17:00-20:59, and Late Night 21:00-23:59.
-- Invalid order times are not assigned a band.
-- Slow delivery uses the fixed Step 5.1 rule: Time_taken(min) > 40.
-- SQLite has no built-in PERCENTILE_CONT; median/P90 use linear interpolation
-- at rank 1 + (n - 1) * p. Rankings require at least 30 records per cell.

WITH
time_bands(time_band, sort_order) AS (
    VALUES
        ('Night', 1),
        ('Morning', 2),
        ('Afternoon', 3),
        ('Evening', 4),
        ('Late Night', 5)
),
valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        CASE
            WHEN "Time_Orderd" GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
             AND CAST(substr("Time_Orderd", 1, 2) AS INTEGER)
                 BETWEEN 0 AND 23
             AND time("Time_Orderd") IS NOT NULL
            THEN CAST(substr("Time_Orderd", 1, 2) AS INTEGER) * 60
                 + CAST(substr("Time_Orderd", 4, 2) AS INTEGER)
                 + CAST(substr("Time_Orderd", 7, 2) AS REAL) / 60.0
        END AS order_minutes,
        "Road_traffic_density" AS traffic_category
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
classified_targets AS (
    SELECT
        delivery_time,
        order_minutes,
        CASE
            WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 0 AND 5
                THEN 'Night'
            WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 6 AND 11
                THEN 'Morning'
            WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 12 AND 16
                THEN 'Afternoon'
            WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 17 AND 20
                THEN 'Evening'
            WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 21 AND 23
                THEN 'Late Night'
        END AS time_band,
        traffic_category
    FROM valid_targets
),
categorized_targets AS (
    SELECT *
    FROM classified_targets
    WHERE time_band IS NOT NULL
      AND traffic_category IS NOT NULL
),
traffic_categories AS (
    SELECT DISTINCT traffic_category
    FROM valid_targets
    WHERE traffic_category IS NOT NULL
),
category_grid AS (
    SELECT time_bands.time_band, traffic_categories.traffic_category,
           time_bands.sort_order
    FROM time_bands
    CROSS JOIN traffic_categories
),
group_metrics AS (
    SELECT
        time_band,
        traffic_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY time_band, traffic_category
),
ordered_targets AS (
    SELECT
        time_band,
        traffic_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY time_band, traffic_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY time_band, traffic_category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        time_band,
        traffic_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.time_band,
        positions.traffic_category,
        median_lower.delivery_time
            + (median_upper.delivery_time - median_lower.delivery_time)
            * (positions.median_rank
               - CAST(positions.median_rank AS INTEGER))
            AS median_delivery_time,
        p90_lower.delivery_time
            + (p90_upper.delivery_time - p90_lower.delivery_time)
            * (positions.p90_rank - CAST(positions.p90_rank AS INTEGER))
            AS p90_delivery_time
    FROM percentile_positions AS positions
    JOIN ordered_targets AS median_lower
      ON median_lower.time_band = positions.time_band
     AND median_lower.traffic_category = positions.traffic_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.time_band = positions.time_band
     AND median_upper.traffic_category = positions.traffic_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE
               WHEN positions.median_rank
                    > CAST(positions.median_rank AS INTEGER)
               THEN 1 ELSE 0
           END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.time_band = positions.time_band
     AND p90_lower.traffic_category = positions.traffic_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.time_band = positions.time_band
     AND p90_upper.traffic_category = positions.traffic_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE
               WHEN positions.p90_rank
                    > CAST(positions.p90_rank AS INTEGER)
               THEN 1 ELSE 0
           END
),
metrics AS (
    SELECT
        category_grid.time_band,
        category_grid.sort_order,
        category_grid.traffic_category,
        COALESCE(group_metrics.delivery_count, 0) AS delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        COALESCE(group_metrics.slow_delivery_count, 0)
            AS slow_delivery_count,
        CASE WHEN group_metrics.delivery_count IS NULL THEN NULL
             ELSE 1.0 * group_metrics.slow_delivery_count
                  / group_metrics.delivery_count
        END AS slow_delivery_rate,
        CASE WHEN COALESCE(group_metrics.delivery_count, 0) >= 30
             THEN 'qualifies' ELSE 'small_sample'
        END AS sample_size_status
    FROM category_grid
    LEFT JOIN group_metrics
      USING (time_band, traffic_category)
    LEFT JOIN percentile_values
      USING (time_band, traffic_category)
),
qualifying AS (
    SELECT *
    FROM metrics
    WHERE delivery_count >= 30
),
within_time_ranks AS (
    SELECT
        time_band,
        traffic_category,
        RANK() OVER (
            PARTITION BY time_band ORDER BY mean_delivery_time
        ) AS mean_rank_within_time,
        RANK() OVER (
            PARTITION BY time_band ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_time,
        RANK() OVER (
            PARTITION BY time_band ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_time,
        RANK() OVER (
            PARTITION BY time_band ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_time
    FROM qualifying
),
within_traffic_ranks AS (
    SELECT
        time_band,
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
population AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        SUM(CASE WHEN delivery_time IS NOT NULL THEN 1 ELSE 0 END)
            AS valid_target_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND order_minutes IS NOT NULL
                 THEN 1 ELSE 0 END) AS valid_order_time_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND order_minutes IS NULL
                 THEN 1 ELSE 0 END) AS missing_invalid_order_time_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND traffic_category IS NOT NULL
                 THEN 1 ELSE 0 END) AS valid_traffic_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND traffic_category IS NULL
                 THEN 1 ELSE 0 END) AS missing_traffic_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND order_minutes IS NOT NULL
                      AND traffic_category IS NULL
                 THEN 1 ELSE 0 END) AS valid_time_missing_traffic_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND order_minutes IS NULL
                      AND traffic_category IS NOT NULL
                 THEN 1 ELSE 0 END) AS invalid_time_valid_traffic_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND (order_minutes IS NULL
                           OR traffic_category IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_for_missing_either_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND delivery_time > 40
                 THEN 1 ELSE 0 END) AS all_slow_delivery_count,
        SUM(CASE WHEN delivery_time IS NOT NULL
                      AND delivery_time > 40
                      AND (order_minutes IS NULL
                           OR traffic_category IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_slow_delivery_count,
        (SELECT COUNT(*) FROM categorized_targets)
            AS combined_analysis_record_count,
        (SELECT SUM(slow_delivery_count) FROM qualifying)
            AS slow_delivery_count_in_qualifying_cells,
        (SELECT SUM(slow_delivery_count) FROM metrics
         WHERE delivery_count < 30)
            AS slow_delivery_count_in_subminimum_cells
    FROM valid_targets
),
standalone_traffic AS (
    SELECT
        traffic_category,
        COUNT(*) AS standalone_traffic_count,
        AVG(delivery_time) AS standalone_traffic_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_traffic_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_traffic_slow_rate
    FROM valid_targets
    WHERE traffic_category IS NOT NULL
    GROUP BY traffic_category
),
standalone_time AS (
    SELECT
        time_band,
        COUNT(*) AS standalone_time_count,
        AVG(delivery_time) AS standalone_time_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_time_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_time_slow_rate
    FROM classified_targets
    WHERE time_band IS NOT NULL
    GROUP BY time_band
)
SELECT
    metrics.time_band,
    metrics.sort_order,
    metrics.traffic_category,
    metrics.delivery_count,
    metrics.mean_delivery_time,
    metrics.median_delivery_time,
    metrics.p90_delivery_time,
    metrics.slow_delivery_count,
    metrics.slow_delivery_rate,
    metrics.sample_size_status,
    within_time_ranks.mean_rank_within_time,
    within_time_ranks.highest_mean_rank_within_time,
    within_time_ranks.slow_rate_rank_within_time,
    within_time_ranks.highest_slow_rate_rank_within_time,
    within_traffic_ranks.mean_rank_within_traffic,
    within_traffic_ranks.highest_mean_rank_within_traffic,
    within_traffic_ranks.slow_rate_rank_within_traffic,
    within_traffic_ranks.highest_slow_rate_rank_within_traffic,
    standalone_traffic.standalone_traffic_count,
    standalone_traffic.standalone_traffic_mean,
    standalone_traffic.standalone_traffic_slow_count,
    standalone_traffic.standalone_traffic_slow_rate,
    standalone_time.standalone_time_count,
    standalone_time.standalone_time_mean,
    standalone_time.standalone_time_slow_count,
    standalone_time.standalone_time_slow_rate,
    population.*
FROM metrics
LEFT JOIN within_time_ranks
  USING (time_band, traffic_category)
LEFT JOIN within_traffic_ranks
  USING (time_band, traffic_category)
JOIN standalone_traffic USING (traffic_category)
LEFT JOIN standalone_time USING (time_band)
CROSS JOIN population
ORDER BY metrics.sort_order, metrics.traffic_category;
