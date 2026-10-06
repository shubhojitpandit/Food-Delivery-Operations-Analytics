-- Temporal delivery metrics using the fixed Step 5.1 slow threshold (> 40 min).
-- Load data/processed/train_clean.csv into a SQLite table named train_clean.
-- SQLite has no built-in PERCENTILE_CONT; all group percentiles and pickup-delay
-- percentiles use continuous linear interpolation at rank 1 + (n - 1) * p.
-- Cleaned dates/times are parsed explicitly from YYYY-MM-DD and HH:MM:SS.
-- Same-day negative pickup differences are reported as ambiguous and excluded
-- from the primary non-negative pickup-delay distribution.

CREATE TEMP VIEW time_analysis_valid AS
SELECT
    CAST("Time_taken(min)" AS REAL) AS delivery_time,
    CASE
        WHEN date("Order_Date") = "Order_Date"
        THEN strftime('%Y-%m-%d', "Order_Date")
    END AS order_date,
    CASE
        WHEN "Time_Orderd" GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
         AND CAST(substr("Time_Orderd", 1, 2) AS INTEGER) BETWEEN 0 AND 23
         AND time("Time_Orderd") IS NOT NULL
        THEN CAST(substr("Time_Orderd", 1, 2) AS INTEGER) * 60.0
             + CAST(substr("Time_Orderd", 4, 2) AS INTEGER)
             + CAST(substr("Time_Orderd", 7, 2) AS REAL) / 60.0
    END AS order_minutes,
    CASE
        WHEN "Time_Order_picked" GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
         AND CAST(substr("Time_Order_picked", 1, 2) AS INTEGER) BETWEEN 0 AND 23
         AND time("Time_Order_picked") IS NOT NULL
        THEN CAST(substr("Time_Order_picked", 1, 2) AS INTEGER) * 60.0
             + CAST(substr("Time_Order_picked", 4, 2) AS INTEGER)
             + CAST(substr("Time_Order_picked", 7, 2) AS REAL) / 60.0
    END AS pickup_minutes
FROM train_clean
WHERE "Time_taken(min)" IS NOT NULL
  AND typeof("Time_taken(min)") IN ('integer', 'real');

CREATE TEMP VIEW time_analysis_groups AS
SELECT
    'order_date' AS dimension_name,
    order_date AS category,
    order_date AS category_label,
    order_date AS sort_key,
    delivery_time
FROM time_analysis_valid
WHERE order_date IS NOT NULL

UNION ALL

SELECT
    'day_of_week',
    CASE CAST(strftime('%w', order_date) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END,
    CASE CAST(strftime('%w', order_date) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END,
    printf('%02d', (CAST(strftime('%w', order_date) AS INTEGER) + 6) % 7),
    delivery_time
FROM time_analysis_valid
WHERE order_date IS NOT NULL

UNION ALL

SELECT
    'month',
    strftime('%m', order_date),
    CASE strftime('%m', order_date)
        WHEN '01' THEN 'January'
        WHEN '02' THEN 'February'
        WHEN '03' THEN 'March'
        WHEN '04' THEN 'April'
        WHEN '05' THEN 'May'
        WHEN '06' THEN 'June'
        WHEN '07' THEN 'July'
        WHEN '08' THEN 'August'
        WHEN '09' THEN 'September'
        WHEN '10' THEN 'October'
        WHEN '11' THEN 'November'
        WHEN '12' THEN 'December'
    END,
    strftime('%m', order_date),
    delivery_time
FROM time_analysis_valid
WHERE order_date IS NOT NULL

UNION ALL

SELECT
    'order_time',
    CASE
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN 'Night'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN 'Evening'
        ELSE 'Late Night'
    END,
    CASE
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN 'Night'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN 'Evening'
        ELSE 'Late Night'
    END,
    CASE
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN '1'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN '2'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN '3'
        WHEN CAST(order_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN '4'
        ELSE '5'
    END,
    delivery_time
FROM time_analysis_valid
WHERE order_minutes IS NOT NULL

UNION ALL

SELECT
    'pickup_time',
    CASE
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN 'Night'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN 'Evening'
        ELSE 'Late Night'
    END,
    CASE
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN 'Night'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN 'Evening'
        ELSE 'Late Night'
    END,
    CASE
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 0 AND 5 THEN '1'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 6 AND 11 THEN '2'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 12 AND 16 THEN '3'
        WHEN CAST(pickup_minutes / 60 AS INTEGER) BETWEEN 17 AND 20 THEN '4'
        ELSE '5'
    END,
    delivery_time
FROM time_analysis_valid
WHERE pickup_minutes IS NOT NULL

UNION ALL

SELECT
    'pickup_delay_band',
    CASE
        WHEN pickup_minutes - order_minutes <= 5 THEN '0-5 minutes'
        WHEN pickup_minutes - order_minutes <= 10 THEN '6-10 minutes'
        WHEN pickup_minutes - order_minutes <= 15 THEN '11-15 minutes'
        WHEN pickup_minutes - order_minutes <= 20 THEN '16-20 minutes'
        WHEN pickup_minutes - order_minutes <= 30 THEN '21-30 minutes'
        ELSE '31+ minutes'
    END,
    CASE
        WHEN pickup_minutes - order_minutes <= 5 THEN '0-5 minutes'
        WHEN pickup_minutes - order_minutes <= 10 THEN '6-10 minutes'
        WHEN pickup_minutes - order_minutes <= 15 THEN '11-15 minutes'
        WHEN pickup_minutes - order_minutes <= 20 THEN '16-20 minutes'
        WHEN pickup_minutes - order_minutes <= 30 THEN '21-30 minutes'
        ELSE '31+ minutes'
    END,
    CASE
        WHEN pickup_minutes - order_minutes <= 5 THEN '1'
        WHEN pickup_minutes - order_minutes <= 10 THEN '2'
        WHEN pickup_minutes - order_minutes <= 15 THEN '3'
        WHEN pickup_minutes - order_minutes <= 20 THEN '4'
        WHEN pickup_minutes - order_minutes <= 30 THEN '5'
        ELSE '6'
    END,
    delivery_time
FROM time_analysis_valid
WHERE order_minutes IS NOT NULL
  AND pickup_minutes IS NOT NULL
  AND pickup_minutes >= order_minutes;

WITH
weekdays(category, sort_order) AS (
    VALUES
        ('Monday', 1), ('Tuesday', 2), ('Wednesday', 3),
        ('Thursday', 4), ('Friday', 5), ('Saturday', 6), ('Sunday', 7)
),
time_bands(category, sort_order) AS (
    VALUES
        ('Night', 1), ('Morning', 2), ('Afternoon', 3),
        ('Evening', 4), ('Late Night', 5)
),
delay_bands(category, sort_order) AS (
    VALUES
        ('0-5 minutes', 1), ('6-10 minutes', 2), ('11-15 minutes', 3),
        ('16-20 minutes', 4), ('21-30 minutes', 5), ('31+ minutes', 6)
),
dimensions(dimension_name, category, category_label, sort_key) AS (
    SELECT DISTINCT dimension_name, category, category_label, sort_key
    FROM time_analysis_groups
    WHERE dimension_name NOT IN (
        'day_of_week', 'order_time', 'pickup_time', 'pickup_delay_band'
    )
    UNION ALL
    SELECT 'day_of_week', category, category, printf('%02d', sort_order)
    FROM weekdays
    UNION ALL
    SELECT 'order_time', category, category, printf('%02d', sort_order)
    FROM time_bands
    UNION ALL
    SELECT 'pickup_time', category, category, printf('%02d', sort_order)
    FROM time_bands
    UNION ALL
    SELECT 'pickup_delay_band', category, category, printf('%02d', sort_order)
    FROM delay_bands
),
group_counts AS (
    SELECT
        dimension_name,
        category,
        COUNT(*) AS delivery_count,
        AVG(delivery_time) AS mean_delivery_time,
        SUM(CASE WHEN delivery_time > 40 THEN 1 ELSE 0 END)
            AS slow_delivery_count
    FROM time_analysis_groups
    GROUP BY dimension_name, category
),
ordered_values AS (
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
    FROM time_analysis_groups
),
percentile_positions AS (
    SELECT DISTINCT
        dimension_name,
        category,
        delivery_count,
        1.0 + (delivery_count - 1) * 0.50 AS median_rank,
        1.0 + (delivery_count - 1) * 0.90 AS p90_rank
    FROM ordered_values
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
    JOIN ordered_values AS median_lower
      ON median_lower.dimension_name = positions.dimension_name
     AND median_lower.category = positions.category
     AND median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN ordered_values AS median_upper
      ON median_upper.dimension_name = positions.dimension_name
     AND median_upper.category = positions.category
     AND median_upper.row_number =
         CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN ordered_values AS p90_lower
      ON p90_lower.dimension_name = positions.dimension_name
     AND p90_lower.category = positions.category
     AND p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN ordered_values AS p90_upper
      ON p90_upper.dimension_name = positions.dimension_name
     AND p90_upper.category = positions.category
     AND p90_upper.row_number =
         CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
)
SELECT
    dimensions.dimension_name,
    dimensions.category,
    dimensions.category_label,
    dimensions.sort_key,
    COALESCE(group_counts.delivery_count, 0) AS delivery_count,
    group_counts.mean_delivery_time,
    percentile_values.median_delivery_time,
    percentile_values.p90_delivery_time,
    COALESCE(group_counts.slow_delivery_count, 0) AS slow_delivery_count,
    CASE
        WHEN group_counts.delivery_count IS NULL THEN NULL
        ELSE 1.0 * group_counts.slow_delivery_count / group_counts.delivery_count
    END AS slow_delivery_rate,
    CASE
        WHEN COALESCE(group_counts.delivery_count, 0) >= 30 THEN 'qualifies'
        ELSE 'small_sample'
    END AS sample_size_status
FROM dimensions
LEFT JOIN group_counts USING (dimension_name, category)
LEFT JOIN percentile_values USING (dimension_name, category)
ORDER BY dimensions.dimension_name, dimensions.sort_key;

WITH valid_rows AS (
    SELECT *
    FROM time_analysis_valid
),
paired AS (
    SELECT
        order_minutes,
        pickup_minutes,
        pickup_minutes - order_minutes AS pickup_delay_minutes
    FROM valid_rows
    WHERE order_minutes IS NOT NULL
      AND pickup_minutes IS NOT NULL
),
nonnegative_delays AS (
    SELECT
        pickup_delay_minutes,
        ROW_NUMBER() OVER (ORDER BY pickup_delay_minutes) AS row_number,
        COUNT(*) OVER () AS delay_count
    FROM paired
    WHERE pickup_delay_minutes >= 0
),
delay_positions AS (
    SELECT DISTINCT
        delay_count,
        1.0 + (delay_count - 1) * 0.25 AS p25_rank,
        1.0 + (delay_count - 1) * 0.50 AS median_rank,
        1.0 + (delay_count - 1) * 0.75 AS p75_rank,
        1.0 + (delay_count - 1) * 0.90 AS p90_rank
    FROM nonnegative_delays
),
delay_percentiles AS (
    SELECT
        p25_lower.pickup_delay_minutes
            + (p25_upper.pickup_delay_minutes - p25_lower.pickup_delay_minutes)
            * (positions.p25_rank - CAST(positions.p25_rank AS INTEGER)) AS p25,
        median_lower.pickup_delay_minutes
            + (median_upper.pickup_delay_minutes - median_lower.pickup_delay_minutes)
            * (positions.median_rank - CAST(positions.median_rank AS INTEGER)) AS median,
        p75_lower.pickup_delay_minutes
            + (p75_upper.pickup_delay_minutes - p75_lower.pickup_delay_minutes)
            * (positions.p75_rank - CAST(positions.p75_rank AS INTEGER)) AS p75,
        p90_lower.pickup_delay_minutes
            + (p90_upper.pickup_delay_minutes - p90_lower.pickup_delay_minutes)
            * (positions.p90_rank - CAST(positions.p90_rank AS INTEGER)) AS p90
    FROM delay_positions AS positions
    JOIN nonnegative_delays AS p25_lower
      ON p25_lower.row_number = CAST(positions.p25_rank AS INTEGER)
    JOIN nonnegative_delays AS p25_upper
      ON p25_upper.row_number = CAST(positions.p25_rank AS INTEGER)
         + CASE WHEN positions.p25_rank > CAST(positions.p25_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN nonnegative_delays AS median_lower
      ON median_lower.row_number = CAST(positions.median_rank AS INTEGER)
    JOIN nonnegative_delays AS median_upper
      ON median_upper.row_number = CAST(positions.median_rank AS INTEGER)
         + CASE WHEN positions.median_rank > CAST(positions.median_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN nonnegative_delays AS p75_lower
      ON p75_lower.row_number = CAST(positions.p75_rank AS INTEGER)
    JOIN nonnegative_delays AS p75_upper
      ON p75_upper.row_number = CAST(positions.p75_rank AS INTEGER)
         + CASE WHEN positions.p75_rank > CAST(positions.p75_rank AS INTEGER)
                THEN 1 ELSE 0 END
    JOIN nonnegative_delays AS p90_lower
      ON p90_lower.row_number = CAST(positions.p90_rank AS INTEGER)
    JOIN nonnegative_delays AS p90_upper
      ON p90_upper.row_number = CAST(positions.p90_rank AS INTEGER)
         + CASE WHEN positions.p90_rank > CAST(positions.p90_rank AS INTEGER)
                THEN 1 ELSE 0 END
),
row_counts AS (
    SELECT
        (SELECT COUNT(*) FROM train_clean) AS total_train_rows,
        COUNT(*) AS valid_target_rows,
        SUM(CASE WHEN order_date IS NOT NULL THEN 1 ELSE 0 END)
            AS valid_order_date_count,
        SUM(CASE WHEN order_date IS NULL THEN 1 ELSE 0 END)
            AS missing_invalid_order_date_count,
        SUM(CASE WHEN order_minutes IS NOT NULL THEN 1 ELSE 0 END)
            AS valid_order_time_count,
        SUM(CASE WHEN order_minutes IS NULL THEN 1 ELSE 0 END)
            AS missing_invalid_order_time_count,
        SUM(CASE WHEN pickup_minutes IS NOT NULL THEN 1 ELSE 0 END)
            AS valid_pickup_time_count,
        SUM(CASE WHEN pickup_minutes IS NULL THEN 1 ELSE 0 END)
            AS missing_invalid_pickup_time_count,
        MIN(order_date) AS minimum_order_date,
        MAX(order_date) AS maximum_order_date
    FROM valid_rows
),
pair_counts AS (
    SELECT
        COUNT(*) AS paired_valid_clock_count,
        SUM(CASE WHEN pickup_delay_minutes < 0 THEN 1 ELSE 0 END)
            AS negative_difference_count,
        SUM(CASE WHEN pickup_delay_minutes >= 0 THEN 1 ELSE 0 END)
            AS nonnegative_delay_count
    FROM paired
),
delay_extremes AS (
    SELECT
        MIN(pickup_delay_minutes) AS minimum_delay,
        MAX(pickup_delay_minutes) AS maximum_delay,
        AVG(pickup_delay_minutes) AS mean_delay
    FROM nonnegative_delays
)
SELECT
    row_counts.*,
    pair_counts.paired_valid_clock_count,
    pair_counts.negative_difference_count,
    CASE
        WHEN pair_counts.paired_valid_clock_count = 0 THEN NULL
        ELSE 1.0 * pair_counts.negative_difference_count
             / pair_counts.paired_valid_clock_count
    END AS negative_difference_rate,
    pair_counts.nonnegative_delay_count,
    delay_extremes.minimum_delay,
    delay_percentiles.p25 AS p25_delay,
    delay_percentiles.median AS median_delay,
    delay_percentiles.p75 AS p75_delay,
    delay_percentiles.p90 AS p90_delay,
    delay_extremes.maximum_delay,
    delay_extremes.mean_delay
FROM row_counts
CROSS JOIN pair_counts
CROSS JOIN delay_extremes
LEFT JOIN delay_percentiles ON 1 = 1;
