-- City-level delivery metrics using the fixed Step 5.1 slow threshold of 40 minutes.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Valid target rows have non-NULL numeric Time_taken(min). Missing City values
-- stay in the valid-target population but are excluded from city comparisons.
--
-- Standard SQLite has no built-in PERCENTILE_CONT. Median and P90 use
-- continuous linear interpolation at rank 1 + (n - 1) * p.
-- Rankings are calculated only for cities with at least 30 valid deliveries.

WITH valid_targets AS (
    SELECT
        "City" AS city,
        CAST("Time_taken(min)" AS REAL) AS delivery_time
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
population_counts AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        COUNT(*) AS valid_target_rows,
        SUM(CASE WHEN city IS NULL THEN 1 ELSE 0 END)
            AS valid_targets_with_missing_city
    FROM valid_targets
),
categorized_targets AS (
    SELECT city, delivery_time
    FROM valid_targets
    WHERE city IS NOT NULL
),
ordered_targets AS (
    SELECT
        city,
        delivery_time,
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY delivery_time) AS row_number,
        COUNT(*) OVER (PARTITION BY city) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        city,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.city,
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
      ON median_lower.city = positions.city
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.city = positions.city
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE
             WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
             THEN 1
             ELSE 0
           END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.city = positions.city
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.city = positions.city
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE
             WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
             THEN 1
             ELSE 0
           END
),
group_metrics AS (
    SELECT
        city,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time
    FROM categorized_targets
    GROUP BY city
),
slow_metrics AS (
    SELECT
        city,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY city
),
city_results AS (
    SELECT
        group_metrics.city,
        group_metrics.delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        slow_metrics.slow_delivery_count,
        1.0 * slow_metrics.slow_delivery_count / group_metrics.delivery_count
            AS slow_delivery_rate
    FROM group_metrics
    JOIN slow_metrics USING (city)
    JOIN percentile_values USING (city)
),
qualifying_city_ranks AS (
    SELECT
        city,
        RANK() OVER (ORDER BY mean_delivery_time ASC) AS fastest_mean_rank,
        RANK() OVER (ORDER BY mean_delivery_time DESC) AS slowest_mean_rank,
        RANK() OVER (ORDER BY median_delivery_time ASC) AS fastest_median_rank,
        RANK() OVER (ORDER BY median_delivery_time DESC) AS slowest_median_rank,
        RANK() OVER (ORDER BY slow_delivery_rate ASC) AS lowest_slow_rate_rank,
        RANK() OVER (ORDER BY slow_delivery_rate DESC) AS highest_slow_rate_rank
    FROM city_results
    WHERE delivery_count >= 30
)
SELECT
    city_results.city AS "City",
    city_results.delivery_count,
    city_results.mean_delivery_time,
    city_results.median_delivery_time,
    city_results.p90_delivery_time,
    city_results.slow_delivery_count,
    city_results.slow_delivery_rate,
    CASE WHEN city_results.delivery_count >= 30 THEN 'qualifies' ELSE 'small_sample' END
        AS sample_size_status,
    qualifying_city_ranks.fastest_mean_rank,
    qualifying_city_ranks.slowest_mean_rank,
    qualifying_city_ranks.fastest_median_rank,
    qualifying_city_ranks.slowest_median_rank,
    qualifying_city_ranks.lowest_slow_rate_rank,
    qualifying_city_ranks.highest_slow_rate_rank,
    population_counts.total_train_rows,
    population_counts.valid_target_rows,
    population_counts.valid_target_rows
        - population_counts.valid_targets_with_missing_city
        AS valid_targets_with_city,
    population_counts.valid_targets_with_missing_city
        AS valid_targets_excluded_for_missing_city
FROM city_results
LEFT JOIN qualifying_city_ranks USING (city)
CROSS JOIN population_counts
ORDER BY city_results.city;
