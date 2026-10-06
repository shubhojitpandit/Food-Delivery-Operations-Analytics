-- Traffic x multiple_deliveries two-way summary.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Targets must be non-NULL numeric values. Missing either grouping dimension is
-- excluded from these combinations only and remains in the overall target pool.
-- The fixed Step 5.1 slow rule is delivery_time > 40 minutes.
--
-- SQLite has no built-in PERCENTILE_CONT. Median/P90 use continuous linear
-- interpolation at rank 1 + (n - 1) * p. Comparison ranks are populated only
-- for combinations with at least 30 valid target records.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        "Road_traffic_density" AS traffic_category,
        CASE
            WHEN "multiple_deliveries" IS NULL THEN NULL
            ELSE printf('%g', CAST("multiple_deliveries" AS REAL))
        END AS multiple_deliveries_category
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
categorized_targets AS (
    SELECT *
    FROM valid_targets
    WHERE traffic_category IS NOT NULL
      AND multiple_deliveries_category IS NOT NULL
),
group_metrics AS (
    SELECT
        traffic_category,
        multiple_deliveries_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY traffic_category, multiple_deliveries_category
),
ordered_targets AS (
    SELECT
        traffic_category,
        multiple_deliveries_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY traffic_category, multiple_deliveries_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY traffic_category, multiple_deliveries_category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        traffic_category,
        multiple_deliveries_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.traffic_category,
        positions.multiple_deliveries_category,
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
      ON median_lower.traffic_category = positions.traffic_category
     AND median_lower.multiple_deliveries_category =
         positions.multiple_deliveries_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.traffic_category = positions.traffic_category
     AND median_upper.multiple_deliveries_category =
         positions.multiple_deliveries_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE
             WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
             THEN 1 ELSE 0
           END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.traffic_category = positions.traffic_category
     AND p90_lower.multiple_deliveries_category =
         positions.multiple_deliveries_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.traffic_category = positions.traffic_category
     AND p90_upper.multiple_deliveries_category =
         positions.multiple_deliveries_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE
             WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
             THEN 1 ELSE 0
           END
),
metrics AS (
    SELECT
        group_metrics.traffic_category,
        group_metrics.multiple_deliveries_category,
        group_metrics.delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        group_metrics.slow_delivery_count,
        1.0 * group_metrics.slow_delivery_count / group_metrics.delivery_count
            AS slow_delivery_rate,
        CASE WHEN group_metrics.delivery_count >= 30
             THEN 'qualifies' ELSE 'small_sample' END AS sample_size_status
    FROM group_metrics
    JOIN percentile_values
      USING (traffic_category, multiple_deliveries_category)
),
qualifying AS (
    SELECT *
    FROM metrics
    WHERE delivery_count >= 30
),
within_traffic_ranks AS (
    SELECT
        traffic_category,
        multiple_deliveries_category,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY mean_delivery_time ASC
        ) AS mean_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY mean_delivery_time DESC
        ) AS slowest_mean_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY slow_delivery_rate ASC
        ) AS slow_rate_rank_within_traffic,
        RANK() OVER (
            PARTITION BY traffic_category ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_traffic
    FROM qualifying
),
within_multiple_ranks AS (
    SELECT
        traffic_category,
        multiple_deliveries_category,
        RANK() OVER (
            PARTITION BY multiple_deliveries_category
            ORDER BY mean_delivery_time ASC
        ) AS mean_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_deliveries_category
            ORDER BY mean_delivery_time DESC
        ) AS slowest_mean_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_deliveries_category
            ORDER BY slow_delivery_rate ASC
        ) AS slow_rate_rank_within_multiple,
        RANK() OVER (
            PARTITION BY multiple_deliveries_category
            ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_multiple
    FROM qualifying
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
standalone_multiple AS (
    SELECT
        multiple_deliveries_category,
        COUNT(*) AS standalone_multiple_count,
        AVG(delivery_time) AS standalone_multiple_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_multiple_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_multiple_slow_rate
    FROM valid_targets
    WHERE multiple_deliveries_category IS NOT NULL
    GROUP BY multiple_deliveries_category
),
population AS (
    SELECT
        COUNT(*) AS total_train_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END) AS valid_target_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Road_traffic_density" IS NULL
                 THEN 1 ELSE 0 END) AS missing_traffic_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "multiple_deliveries" IS NULL
                 THEN 1 ELSE 0 END) AS missing_multiple_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Road_traffic_density" IS NULL
                           OR "multiple_deliveries" IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_for_missing_either_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Time_taken(min)" > 40
                 THEN 1 ELSE 0 END) AS all_slow_delivery_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Road_traffic_density" IS NULL
                           OR "multiple_deliveries" IS NULL)
                      AND "Time_taken(min)" > 40
                 THEN 1 ELSE 0 END) AS excluded_slow_delivery_count
    FROM train_clean
),
combination_coverage AS (
    SELECT COUNT(*) AS eligible_combination_population
    FROM categorized_targets
)
SELECT
    metrics.*,
    within_traffic_ranks.mean_rank_within_traffic,
    within_traffic_ranks.slowest_mean_rank_within_traffic,
    within_traffic_ranks.slow_rate_rank_within_traffic,
    within_traffic_ranks.highest_slow_rate_rank_within_traffic,
    within_multiple_ranks.mean_rank_within_multiple,
    within_multiple_ranks.slowest_mean_rank_within_multiple,
    within_multiple_ranks.slow_rate_rank_within_multiple,
    within_multiple_ranks.highest_slow_rate_rank_within_multiple,
    standalone_traffic.standalone_traffic_count,
    standalone_traffic.standalone_traffic_mean,
    standalone_traffic.standalone_traffic_slow_count,
    standalone_traffic.standalone_traffic_slow_rate,
    standalone_multiple.standalone_multiple_count,
    standalone_multiple.standalone_multiple_mean,
    standalone_multiple.standalone_multiple_slow_count,
    standalone_multiple.standalone_multiple_slow_rate,
    population.*,
    combination_coverage.eligible_combination_population
FROM metrics
LEFT JOIN within_traffic_ranks
  USING (traffic_category, multiple_deliveries_category)
LEFT JOIN within_multiple_ranks
  USING (traffic_category, multiple_deliveries_category)
JOIN standalone_traffic USING (traffic_category)
JOIN standalone_multiple USING (multiple_deliveries_category)
CROSS JOIN population
CROSS JOIN combination_coverage
ORDER BY metrics.traffic_category, CAST(metrics.multiple_deliveries_category AS REAL);
