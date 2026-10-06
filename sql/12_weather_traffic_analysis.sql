-- Weatherconditions x Road_traffic_density descriptive analysis.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Missing dimensions are excluded from grouped cells only. An observed-category
-- grid is returned so empty pairs are visible as well as small-sample pairs.
-- Slow delivery uses the fixed Step 5.1 rule: Time_taken(min) > 40.
-- SQLite has no built-in PERCENTILE_CONT; median/P90 use linear interpolation
-- at rank 1 + (n - 1) * p. Ranks are assigned only where cell count >= 30.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        "Weatherconditions" AS weather_category,
        "Road_traffic_density" AS traffic_category
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
categorized_targets AS (
    SELECT *
    FROM valid_targets
    WHERE weather_category IS NOT NULL
      AND traffic_category IS NOT NULL
),
weather_categories AS (
    SELECT DISTINCT weather_category
    FROM valid_targets
    WHERE weather_category IS NOT NULL
),
traffic_categories AS (
    SELECT DISTINCT traffic_category
    FROM valid_targets
    WHERE traffic_category IS NOT NULL
),
category_grid AS (
    SELECT weather_category, traffic_category
    FROM weather_categories CROSS JOIN traffic_categories
),
group_metrics AS (
    SELECT
        weather_category,
        traffic_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY weather_category, traffic_category
),
ordered_targets AS (
    SELECT
        weather_category,
        traffic_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY weather_category, traffic_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY weather_category, traffic_category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        weather_category,
        traffic_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.weather_category,
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
      ON median_lower.weather_category = positions.weather_category
     AND median_lower.traffic_category = positions.traffic_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.weather_category = positions.weather_category
     AND median_upper.traffic_category = positions.traffic_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.weather_category = positions.weather_category
     AND p90_lower.traffic_category = positions.traffic_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.weather_category = positions.weather_category
     AND p90_upper.traffic_category = positions.traffic_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
metrics AS (
    SELECT
        category_grid.weather_category,
        category_grid.traffic_category,
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
      USING (weather_category, traffic_category)
    LEFT JOIN percentile_values
      USING (weather_category, traffic_category)
),
qualifying AS (
    SELECT *
    FROM metrics
    WHERE delivery_count >= 30
),
within_weather_ranks AS (
    SELECT
        weather_category,
        traffic_category,
        RANK() OVER (
            PARTITION BY weather_category ORDER BY mean_delivery_time
        ) AS mean_rank_within_weather,
        RANK() OVER (
            PARTITION BY weather_category ORDER BY mean_delivery_time DESC
        ) AS highest_mean_rank_within_weather,
        RANK() OVER (
            PARTITION BY weather_category ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_weather,
        RANK() OVER (
            PARTITION BY weather_category ORDER BY slow_delivery_rate DESC
        ) AS highest_slow_rate_rank_within_weather
    FROM qualifying
),
within_traffic_ranks AS (
    SELECT
        weather_category,
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
standalone_weather AS (
    SELECT
        weather_category,
        COUNT(*) AS standalone_weather_count,
        AVG(delivery_time) AS standalone_weather_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS standalone_weather_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS standalone_weather_slow_rate
    FROM valid_targets
    WHERE weather_category IS NOT NULL
    GROUP BY weather_category
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
population AS (
    SELECT
        COUNT(*) AS total_train_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END) AS valid_target_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Weatherconditions" IS NULL
                 THEN 1 ELSE 0 END) AS missing_weather_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Road_traffic_density" IS NULL
                 THEN 1 ELSE 0 END) AS missing_traffic_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Weatherconditions" IS NULL
                           OR "Road_traffic_density" IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_for_missing_either_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND "Time_taken(min)" > 40
                 THEN 1 ELSE 0 END) AS all_slow_delivery_count,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                      AND ("Weatherconditions" IS NULL
                           OR "Road_traffic_density" IS NULL)
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
    within_weather_ranks.mean_rank_within_weather,
    within_weather_ranks.highest_mean_rank_within_weather,
    within_weather_ranks.slow_rate_rank_within_weather,
    within_weather_ranks.highest_slow_rate_rank_within_weather,
    within_traffic_ranks.mean_rank_within_traffic,
    within_traffic_ranks.highest_mean_rank_within_traffic,
    within_traffic_ranks.slow_rate_rank_within_traffic,
    within_traffic_ranks.highest_slow_rate_rank_within_traffic,
    standalone_weather.standalone_weather_count,
    standalone_weather.standalone_weather_mean,
    standalone_weather.standalone_weather_slow_count,
    standalone_weather.standalone_weather_slow_rate,
    standalone_traffic.standalone_traffic_count,
    standalone_traffic.standalone_traffic_mean,
    standalone_traffic.standalone_traffic_slow_count,
    standalone_traffic.standalone_traffic_slow_rate,
    population.*,
    two_way_population.eligible_combination_population
FROM metrics
LEFT JOIN within_weather_ranks
  USING (weather_category, traffic_category)
LEFT JOIN within_traffic_ranks
  USING (weather_category, traffic_category)
JOIN standalone_weather USING (weather_category)
JOIN standalone_traffic USING (traffic_category)
CROSS JOIN population
CROSS JOIN two_way_population
ORDER BY metrics.weather_category, metrics.traffic_category;
