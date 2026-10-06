-- Courier dimension summaries using the fixed Step 5.1 slow threshold of 40 minutes.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- A valid target is a non-NULL numeric Time_taken(min). Missing courier fields
-- remain in the target population and are excluded only from their comparison.
--
-- SQLite has no built-in PERCENTILE_CONT. Median, P25, P75, and P90 below use
-- continuous linear interpolation at rank 1 + (n - 1) * p.
-- Ranking columns are populated only for groups with at least 30 deliveries.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        CAST("Delivery_person_Ratings" AS REAL) AS rating,
        CAST("rating_out_of_range" AS INTEGER) AS rating_out_of_range,
        CAST("Delivery_person_Age" AS REAL) AS courier_age,
        CAST("multiple_deliveries" AS REAL) AS multiple_deliveries
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
dimension_targets AS (
    SELECT
        'rating_primary' AS dimension_name,
        printf('%g', rating) AS category,
        delivery_time
    FROM valid_targets
    WHERE rating IS NOT NULL
      AND rating_out_of_range = 0
      AND rating BETWEEN 1 AND 5

    UNION ALL

    SELECT
        'rating_all',
        printf('%g', rating),
        delivery_time
    FROM valid_targets
    WHERE rating IS NOT NULL

    UNION ALL

    SELECT
        'age_band',
        CASE
            WHEN courier_age < 20 THEN 'Under 20'
            WHEN courier_age < 30 THEN '20-29'
            WHEN courier_age < 40 THEN '30-39'
            WHEN courier_age < 50 THEN '40-49'
            ELSE '50+'
        END,
        delivery_time
    FROM valid_targets
    WHERE courier_age IS NOT NULL

    UNION ALL

    SELECT
        'multiple_deliveries',
        printf('%g', multiple_deliveries),
        delivery_time
    FROM valid_targets
    WHERE multiple_deliveries IS NOT NULL

    UNION ALL

    SELECT
        'rating_sensitivity',
        'Primary: in-range ratings (1-5)',
        delivery_time
    FROM valid_targets
    WHERE rating IS NOT NULL
      AND rating_out_of_range = 0
      AND rating BETWEEN 1 AND 5

    UNION ALL

    SELECT
        'rating_sensitivity',
        'Sensitivity: all ratings (non-missing; includes out-of-range)',
        delivery_time
    FROM valid_targets
    WHERE rating IS NOT NULL
),
age_band_categories(category) AS (
    VALUES ('Under 20'), ('20-29'), ('30-39'), ('40-49'), ('50+')
),
dimension_categories AS (
    SELECT DISTINCT dimension_name, category
    FROM dimension_targets
    UNION
    SELECT 'age_band', category
    FROM age_band_categories
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
    FROM dimension_targets
),
group_counts AS (
    SELECT
        dimension_name,
        category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM dimension_targets
    GROUP BY dimension_name, category
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
         + CASE
             WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
             THEN 1 ELSE 0
           END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.dimension_name = positions.dimension_name
     AND p90_lower.category = positions.category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.dimension_name = positions.dimension_name
     AND p90_upper.category = positions.category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE
             WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
             THEN 1 ELSE 0
           END
),
metrics AS (
    SELECT
        categories.dimension_name,
        categories.category,
        COALESCE(group_counts.delivery_count, 0) AS delivery_count,
        group_counts.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        COALESCE(group_counts.slow_delivery_count, 0) AS slow_delivery_count,
        CASE
            WHEN group_counts.delivery_count IS NULL THEN NULL
            ELSE 1.0 * group_counts.slow_delivery_count / group_counts.delivery_count
        END AS slow_delivery_rate
    FROM dimension_categories AS categories
    LEFT JOIN group_counts
      USING (dimension_name, category)
    LEFT JOIN percentile_values
      USING (dimension_name, category)
),
ranked_groups AS (
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
      AND dimension_name != 'rating_sensitivity'
),
age_ordered AS (
    SELECT
        courier_age,
        ROW_NUMBER() OVER (ORDER BY courier_age) AS row_number,
        COUNT(*) OVER () AS age_count
    FROM valid_targets
    WHERE courier_age IS NOT NULL
),
age_percentile_positions AS (
    SELECT DISTINCT
        1.0 + (age_count - 1) * 0.25 AS p25_rank,
        1.0 + (age_count - 1) * 0.50 AS median_rank,
        1.0 + (age_count - 1) * 0.75 AS p75_rank
    FROM age_ordered
),
age_percentiles AS (
    SELECT
        p25_lower.courier_age
            + (p25_upper.courier_age - p25_lower.courier_age)
            * (positions.p25_rank - CAST(positions.p25_rank AS INTEGER))
            AS p25_age,
        median_lower.courier_age
            + (median_upper.courier_age - median_lower.courier_age)
            * (positions.median_rank - CAST(positions.median_rank AS INTEGER))
            AS median_age,
        p75_lower.courier_age
            + (p75_upper.courier_age - p75_lower.courier_age)
            * (positions.p75_rank - CAST(positions.p75_rank AS INTEGER))
            AS p75_age
    FROM age_percentile_positions AS positions
    JOIN age_ordered AS p25_lower
      ON p25_lower.row_number = CAST(positions.p25_rank AS INTEGER)
    JOIN age_ordered AS p25_upper
      ON p25_upper.row_number =
         CAST(positions.p25_rank AS INTEGER)
         + CASE WHEN positions.p25_rank > CAST(positions.p25_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN age_ordered AS median_lower
      ON median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN age_ordered AS median_upper
      ON median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN age_ordered AS p75_lower
      ON p75_lower.row_number = CAST(positions.p75_rank AS INTEGER)
    JOIN age_ordered AS p75_upper
      ON p75_upper.row_number =
         CAST(positions.p75_rank AS INTEGER)
         + CASE WHEN positions.p75_rank > CAST(positions.p75_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
age_summary AS (
    SELECT
        COUNT(*) AS valid_age_count,
        MIN(courier_age) AS minimum_age,
        MAX(courier_age) AS maximum_age
    FROM valid_targets
    WHERE courier_age IS NOT NULL
),
population AS (
    SELECT
        COUNT(*) AS total_train_rows,
        SUM(CASE WHEN "Time_taken(min)" IS NOT NULL
                      AND typeof("Time_taken(min)") IN ('integer', 'real')
                 THEN 1 ELSE 0 END) AS valid_target_rows
    FROM train_clean
),
rating_quality AS (
    SELECT
        SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END)
            AS valid_targets_missing_rating,
        SUM(CASE WHEN rating IS NOT NULL AND rating_out_of_range = 1
                 THEN 1 ELSE 0 END) AS valid_targets_out_of_range_rating
    FROM valid_targets
),
dimension_coverage(dimension_name, valid_targets_missing_dimension,
                   valid_targets_excluded_out_of_range) AS (
    SELECT 'rating_primary',
           valid_targets_missing_rating,
           valid_targets_out_of_range_rating
    FROM rating_quality
    UNION ALL
    SELECT 'rating_all', valid_targets_missing_rating, 0
    FROM rating_quality
    UNION ALL
    SELECT 'age_band',
           SUM(CASE WHEN courier_age IS NULL THEN 1 ELSE 0 END), 0
    FROM valid_targets
    UNION ALL
    SELECT 'multiple_deliveries',
           SUM(CASE WHEN multiple_deliveries IS NULL THEN 1 ELSE 0 END), 0
    FROM valid_targets
    UNION ALL
    SELECT 'rating_sensitivity', 0, 0
),
final_rows AS (
    SELECT
        metrics.*,
        CASE
            WHEN metrics.delivery_count >= 30 THEN 'qualifies'
            ELSE 'small_sample'
        END AS sample_size_status,
        ranked_groups.fastest_mean_rank,
        ranked_groups.slowest_mean_rank,
        ranked_groups.fastest_median_rank,
        ranked_groups.slowest_median_rank,
        ranked_groups.lowest_slow_rate_rank,
        ranked_groups.highest_slow_rate_rank,
        population.total_train_rows,
        population.valid_target_rows,
        dimension_coverage.valid_targets_missing_dimension,
        dimension_coverage.valid_targets_excluded_out_of_range,
        age_summary.valid_age_count,
        population.valid_target_rows - age_summary.valid_age_count
            AS valid_targets_missing_age,
        age_summary.minimum_age,
        age_summary.maximum_age,
        age_percentiles.median_age,
        age_percentiles.p25_age,
        age_percentiles.p75_age
    FROM metrics
    LEFT JOIN ranked_groups
      USING (dimension_name, category)
    JOIN dimension_coverage
      USING (dimension_name)
    CROSS JOIN population
    CROSS JOIN age_summary
    CROSS JOIN age_percentiles
)
SELECT *
FROM final_rows
ORDER BY dimension_name, category;
