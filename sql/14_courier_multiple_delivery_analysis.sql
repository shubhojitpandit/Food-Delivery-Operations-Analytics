-- Delivery_person_ID x multiple_deliveries descriptive analysis.
-- Load data/processed/train_clean.csv into a SQLite relation named train_clean.
-- Courier IDs remain identifiers; multiple-delivery values remain categories.
-- Slow delivery uses the fixed Step 5.1 rule: Time_taken(min) > 40.
-- A courier must have >= 30 valid-target records overall, and a courier/category
-- cell must also have >= 30 records, to enter substantive comparisons.
-- SQLite has no built-in PERCENTILE_CONT; all medians/P90 use linear interpolation
-- at rank 1 + (n - 1) * p.

WITH valid_targets AS (
    SELECT
        CAST("Time_taken(min)" AS REAL) AS delivery_time,
        "Delivery_person_ID" AS courier_id,
        CASE
            WHEN "multiple_deliveries" IS NULL THEN NULL
            ELSE printf('%g', CAST("multiple_deliveries" AS REAL))
        END AS multiple_category
    FROM train_clean
    WHERE "Time_taken(min)" IS NOT NULL
      AND typeof("Time_taken(min)") IN ('integer', 'real')
),
courier_totals AS (
    SELECT
        courier_id,
        COUNT(*) AS courier_total_count,
        AVG(delivery_time) AS courier_overall_mean,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS courier_overall_slow_count,
        1.0 * SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END) / COUNT(*)
            AS courier_overall_slow_rate
    FROM valid_targets
    WHERE courier_id IS NOT NULL
    GROUP BY courier_id
),
categorized_targets AS (
    SELECT valid_targets.*
    FROM valid_targets
    WHERE courier_id IS NOT NULL
      AND multiple_category IS NOT NULL
),
group_metrics AS (
    SELECT
        courier_id,
        multiple_category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM categorized_targets
    GROUP BY courier_id, multiple_category
),
ordered_targets AS (
    SELECT
        courier_id,
        multiple_category,
        delivery_time,
        ROW_NUMBER() OVER (
            PARTITION BY courier_id, multiple_category
            ORDER BY delivery_time
        ) AS row_number,
        COUNT(*) OVER (
            PARTITION BY courier_id, multiple_category
        ) AS delivery_count
    FROM categorized_targets
),
percentile_positions AS (
    SELECT DISTINCT
        courier_id,
        multiple_category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_targets
),
percentile_values AS (
    SELECT
        positions.courier_id,
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
      ON median_lower.courier_id = positions.courier_id
     AND median_lower.multiple_category = positions.multiple_category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_targets AS median_upper
      ON median_upper.courier_id = positions.courier_id
     AND median_upper.multiple_category = positions.multiple_category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_targets AS p90_lower
      ON p90_lower.courier_id = positions.courier_id
     AND p90_lower.multiple_category = positions.multiple_category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_targets AS p90_upper
      ON p90_upper.courier_id = positions.courier_id
     AND p90_upper.multiple_category = positions.multiple_category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
cell_metrics AS (
    SELECT
        group_metrics.courier_id,
        group_metrics.multiple_category,
        group_metrics.delivery_count,
        group_metrics.mean_delivery_time,
        percentile_values.median_delivery_time,
        percentile_values.p90_delivery_time,
        group_metrics.slow_delivery_count,
        1.0 * group_metrics.slow_delivery_count / group_metrics.delivery_count
            AS slow_delivery_rate
    FROM group_metrics
    JOIN percentile_values
      USING (courier_id, multiple_category)
),
qualified_cells AS (
    SELECT cell_metrics.*
    FROM cell_metrics
    JOIN courier_totals USING (courier_id)
    WHERE courier_totals.courier_total_count >= 30
      AND cell_metrics.delivery_count >= 30
),
ranked_cells AS (
    SELECT
        qualified_cells.*,
        RANK() OVER (
            PARTITION BY courier_id ORDER BY mean_delivery_time
        ) AS mean_rank_within_courier,
        RANK() OVER (
            PARTITION BY courier_id ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_courier,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY mean_delivery_time
        ) AS mean_rank_within_category,
        RANK() OVER (
            PARTITION BY multiple_category ORDER BY slow_delivery_rate
        ) AS slow_rate_rank_within_category
    FROM qualified_cells
),
courier_comparison AS (
    SELECT
        courier_id,
        COUNT(*) AS qualifying_category_count,
        MIN(mean_delivery_time) AS lowest_qualifying_mean,
        MAX(mean_delivery_time) AS highest_qualifying_mean,
        MIN(slow_delivery_rate) AS lowest_qualifying_slow_rate,
        MAX(slow_delivery_rate) AS highest_qualifying_slow_rate
    FROM qualified_cells
    GROUP BY courier_id
),
category_ordered AS (
    SELECT
        ranked_cells.*,
        ROW_NUMBER() OVER (
            PARTITION BY multiple_category ORDER BY mean_delivery_time
        ) AS mean_row_number,
        COUNT(*) OVER (
            PARTITION BY multiple_category
        ) AS qualifying_courier_count,
        ROW_NUMBER() OVER (
            PARTITION BY multiple_category ORDER BY slow_delivery_rate
        ) AS slow_rate_row_number
    FROM ranked_cells
),
category_summary AS (
    SELECT
        multiple_category,
        MAX(qualifying_courier_count) AS qualifying_courier_count,
        MIN(mean_delivery_time) AS minimum_courier_mean,
        MAX(mean_delivery_time) AS maximum_courier_mean,
        AVG(
            CASE
                WHEN mean_row_number IN (
                    CAST((qualifying_courier_count + 1) / 2 AS INTEGER),
                    CAST((qualifying_courier_count + 2) / 2 AS INTEGER)
                ) THEN mean_delivery_time
            END
        ) AS median_courier_mean,
        MIN(slow_delivery_rate) AS minimum_courier_slow_rate,
        MAX(slow_delivery_rate) AS maximum_courier_slow_rate,
        AVG(
            CASE
                WHEN slow_rate_row_number IN (
                    CAST((qualifying_courier_count + 1) / 2 AS INTEGER),
                    CAST((qualifying_courier_count + 2) / 2 AS INTEGER)
                ) THEN slow_delivery_rate
            END
        ) AS median_courier_slow_rate
    FROM category_ordered
    GROUP BY multiple_category
),
population AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL THEN 1 ELSE 0 END)
            AS valid_target_count,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL
                      AND valid_targets.courier_id IS NULL
                 THEN 1 ELSE 0 END) AS missing_courier_count,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL
                      AND valid_targets.multiple_category IS NULL
                 THEN 1 ELSE 0 END) AS missing_multiple_count,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL
                      AND (valid_targets.courier_id IS NULL
                           OR valid_targets.multiple_category IS NULL)
                 THEN 1 ELSE 0 END) AS excluded_for_missing_either_count,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL
                      AND valid_targets.delivery_time > 40
                 THEN 1 ELSE 0 END) AS all_slow_delivery_count,
        SUM(CASE WHEN valid_targets.delivery_time IS NOT NULL
                      AND (valid_targets.courier_id IS NULL
                           OR valid_targets.multiple_category IS NULL)
                      AND valid_targets.delivery_time > 40
                 THEN 1 ELSE 0 END) AS excluded_slow_delivery_count,
        COUNT(DISTINCT valid_targets.courier_id)
            AS unique_couriers_valid_target,
        (SELECT COUNT(*) FROM courier_totals
         WHERE courier_total_count >= 30) AS eligible_courier_count,
        (SELECT COUNT(*) FROM courier_totals
         WHERE courier_total_count < 30) AS below_threshold_courier_count,
        (SELECT COUNT(DISTINCT courier_id) FROM categorized_targets)
            AS unique_couriers_combined,
        (SELECT COUNT(*) FROM categorized_targets)
            AS combined_analysis_record_count,
        (SELECT COUNT(*) FROM cell_metrics)
            AS observed_courier_category_cell_count,
        (SELECT COUNT(*) FROM qualified_cells)
            AS qualifying_cell_count,
        (SELECT COUNT(DISTINCT courier_id) FROM qualified_cells)
            AS couriers_with_qualifying_cells,
        (SELECT SUM(slow_delivery_count) FROM qualified_cells)
            AS slow_delivery_count_in_qualifying_cells,
        (SELECT COUNT(*) FROM cell_metrics
         WHERE NOT EXISTS (
             SELECT 1 FROM courier_totals
             WHERE courier_totals.courier_id = cell_metrics.courier_id
               AND courier_totals.courier_total_count >= 30
         )
            OR delivery_count < 30) AS subminimum_cell_count,
        (SELECT SUM(cell_metrics.slow_delivery_count) FROM cell_metrics
         WHERE NOT EXISTS (
             SELECT 1 FROM courier_totals
             WHERE courier_totals.courier_id = cell_metrics.courier_id
               AND courier_totals.courier_total_count >= 30
         )
            OR delivery_count < 30) AS slow_delivery_count_in_subminimum_cells
    FROM valid_targets
),
two_way_population AS (
    SELECT COUNT(*) AS combined_analysis_record_count
    FROM categorized_targets
)
SELECT
    cell_metrics.*,
    courier_totals.courier_total_count,
    CASE WHEN courier_totals.courier_total_count >= 30
         THEN 'qualifies' ELSE 'below_minimum' END AS courier_sample_status,
    CASE WHEN courier_totals.courier_total_count >= 30
                   AND cell_metrics.delivery_count >= 30
         THEN 'qualifies' ELSE 'small_sample' END AS cell_sample_status,
    ranked_cells.mean_rank_within_courier,
    ranked_cells.slow_rate_rank_within_courier,
    ranked_cells.mean_rank_within_category,
    ranked_cells.slow_rate_rank_within_category,
    courier_comparison.qualifying_category_count,
    courier_comparison.lowest_qualifying_mean,
    courier_comparison.highest_qualifying_mean,
    courier_comparison.lowest_qualifying_slow_rate,
    courier_comparison.highest_qualifying_slow_rate,
    category_summary.qualifying_courier_count,
    category_summary.minimum_courier_mean,
    category_summary.median_courier_mean,
    category_summary.maximum_courier_mean,
    category_summary.minimum_courier_slow_rate,
    category_summary.median_courier_slow_rate,
    category_summary.maximum_courier_slow_rate,
    population.*,
    (SELECT COUNT(*) FROM courier_totals) AS unique_courier_count,
    (SELECT COUNT(*) FROM categorized_targets)
        AS combined_analysis_population
FROM cell_metrics
JOIN courier_totals USING (courier_id)
LEFT JOIN ranked_cells USING (courier_id, multiple_category)
LEFT JOIN courier_comparison USING (courier_id)
LEFT JOIN category_summary USING (multiple_category)
CROSS JOIN population
ORDER BY cell_metrics.multiple_category, cell_metrics.courier_id;
