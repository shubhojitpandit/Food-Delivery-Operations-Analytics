"""Validate temporal delivery-time summaries against SQLite."""

import calendar
import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "07_time_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "time_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
DATE_COLUMN = "Order_Date"
ORDER_TIME_COLUMN = "Time_Orderd"
PICKUP_TIME_COLUMN = "Time_Order_picked"
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
TIME_BANDS = ("Night", "Morning", "Afternoon", "Evening", "Late Night")
DELAY_BANDS = (
    "0-5 minutes",
    "6-10 minutes",
    "11-15 minutes",
    "16-20 minutes",
    "21-30 minutes",
    "31+ minutes",
)
DIMENSIONS = (
    "order_date",
    "day_of_week",
    "month",
    "order_time",
    "pickup_time",
    "pickup_delay_band",
)
COUNT_METRICS = ("delivery_count", "slow_delivery_count")
FLOAT_METRICS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
SORT_ORDERS = {
    "day_of_week": {value: index for index, value in enumerate(WEEKDAYS, start=1)},
    "order_time": {value: index for index, value in enumerate(TIME_BANDS, start=1)},
    "pickup_time": {value: index for index, value in enumerate(TIME_BANDS, start=1)},
    "pickup_delay_band": {
        value: index for index, value in enumerate(DELAY_BANDS, start=1)
    },
}


def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest for source-integrity validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floats using the tolerance from prior analysis steps."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Render numeric results compactly for Markdown."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format rows as a Markdown table and escape cell separators."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(
            str(value).replace("|", r"\|").replace("\n", " ")
            for value in row
        ) + " |"
        for row in rows
    )
    return lines


def parse_sql_script(connection: sqlite3.Connection, sql_text: str) -> list[pd.DataFrame]:
    """Execute a SQL script statement-by-statement and collect SELECT results."""
    cursor = connection.cursor()
    statement_lines: list[str] = []
    result_frames: list[pd.DataFrame] = []
    for line in sql_text.splitlines():
        statement_lines.append(line)
        candidate = "\n".join(statement_lines)
        if not sqlite3.complete_statement(candidate):
            continue
        statement = "\n".join(
            line
            for line in candidate.splitlines()
            if not line.lstrip().startswith("--")
        ).strip()
        statement_lines.clear()
        if not statement:
            continue
        cursor.execute(statement)
        if cursor.description is not None:
            result_frames.append(
                pd.DataFrame(cursor.fetchall(), columns=[item[0] for item in cursor.description])
            )
    if "\n".join(statement_lines).strip():
        raise ValueError("The SQL script ends with an incomplete statement.")
    return result_frames


def run_sql(frame: pd.DataFrame, sql_text: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Run SQL against an in-memory copy and return group and summary results."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        result_frames = parse_sql_script(connection, sql_text)
        if len(result_frames) != 2:
            raise AssertionError(
                f"Expected two SQL result sets, received {len(result_frames)}."
            )
        return result_frames[0], result_frames[1], sqlite3.sqlite_version
    finally:
        connection.close()


def parse_times(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Parse strict HH:MM:SS values and return timestamps and fractional minutes."""
    parsed = pd.to_datetime(values, format="%H:%M:%S", errors="coerce")
    minutes = (
        parsed.dt.hour * 60.0
        + parsed.dt.minute
        + parsed.dt.second / 60.0
    )
    return parsed, minutes.astype("float64")


def time_band(minutes: pd.Series) -> pd.Series:
    """Assign the fixed clock bands from the hour of day."""
    hour = np.floor(minutes / 60).where(minutes.notna())
    conditions = [
        hour.between(0, 5, inclusive="both"),
        hour.between(6, 11, inclusive="both"),
        hour.between(12, 16, inclusive="both"),
        hour.between(17, 20, inclusive="both"),
        hour.between(21, 23, inclusive="both"),
    ]
    return pd.Series(
        np.select(conditions, TIME_BANDS, default=None),
        index=minutes.index,
        dtype="object",
    ).where(minutes.notna(), pd.NA)


def delay_band(delays: pd.Series) -> pd.Series:
    """Assign non-negative same-day delays to the six requested ranges."""
    conditions = [
        delays.le(5),
        delays.le(10),
        delays.le(15),
        delays.le(20),
        delays.le(30),
    ]
    return pd.Series(
        np.select(conditions, DELAY_BANDS[:-1], default=DELAY_BANDS[-1]),
        index=delays.index,
        dtype="object",
    ).where(delays.notna(), pd.NA)


def make_group_rows(
    valid: pd.DataFrame,
    dimension: str,
    categories: pd.Series,
    labels: pd.Series | None = None,
    sort_keys: pd.Series | None = None,
    scaffold: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Calculate delivery performance for a dimension independently in Pandas."""
    mask = categories.notna()
    base = pd.DataFrame(
        {
            "category": categories.loc[mask].astype(str),
            "delivery_time": valid.loc[mask, TARGET_COLUMN].astype(float),
        },
        index=valid.index[mask],
    )
    if labels is not None:
        base["category_label"] = labels.loc[mask].astype(str)
    else:
        base["category_label"] = base["category"]
    if sort_keys is not None:
        base["sort_key"] = sort_keys.loc[mask].astype(str)
    else:
        base["sort_key"] = base["category"]

    rows: list[dict[str, object]] = []
    for category, group in base.groupby("category", sort=False, dropna=True):
        values = group["delivery_time"].to_numpy(dtype="float64")
        count = len(group)
        slow_count = int((group["delivery_time"] > FIXED_SLOW_THRESHOLD).sum())
        rows.append(
            {
                "dimension_name": dimension,
                "category": category,
                "category_label": group["category_label"].iloc[0],
                "sort_key": group["sort_key"].iloc[0],
                "delivery_count": count,
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(np.percentile(values, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / count,
                "sample_size_status": (
                    "qualifies" if count >= MIN_GROUP_SIZE else "small_sample"
                ),
            }
        )

    present = {row["category"] for row in rows}
    for index, category in enumerate(scaffold, start=1):
        if category in present:
            continue
        rows.append(
            {
                "dimension_name": dimension,
                "category": category,
                "category_label": category,
                "sort_key": f"{index:02d}",
                "delivery_count": 0,
                "mean_delivery_time": np.nan,
                "median_delivery_time": np.nan,
                "p90_delivery_time": np.nan,
                "slow_delivery_count": 0,
                "slow_delivery_rate": np.nan,
                "sample_size_status": "small_sample",
            }
        )
    return rows


def calculate_python_results(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Calculate temporal group metrics and pickup-delay statistics in Pandas."""
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask].copy()
    valid[TARGET_COLUMN] = target.loc[valid_mask].astype(float)

    dates = pd.to_datetime(valid[DATE_COLUMN], format="%Y-%m-%d", errors="coerce")
    _, order_minutes = parse_times(valid[ORDER_TIME_COLUMN])
    _, pickup_minutes = parse_times(valid[PICKUP_TIME_COLUMN])
    valid["parsed_date"] = dates
    valid["order_minutes"] = order_minutes
    valid["pickup_minutes"] = pickup_minutes
    valid["pickup_delay_minutes"] = pickup_minutes - order_minutes

    date_categories = dates.dt.strftime("%Y-%m-%d")
    weekday_categories = dates.dt.day_name()
    weekday_sort = dates.dt.dayofweek.map(lambda value: f"{int(value) + 1:02d}" if pd.notna(value) else pd.NA)
    month_numbers = dates.dt.month
    month_categories = month_numbers.map(
        lambda value: f"{int(value):02d}" if pd.notna(value) else pd.NA
    )
    month_labels = month_numbers.map(
        lambda value: calendar.month_name[int(value)] if pd.notna(value) else pd.NA
    )
    order_bands = time_band(order_minutes)
    pickup_bands = time_band(pickup_minutes)
    order_sort = order_bands.map(
        lambda value: f"{SORT_ORDERS['order_time'][value]:02d}"
        if pd.notna(value)
        else pd.NA
    )
    pickup_sort = pickup_bands.map(
        lambda value: f"{SORT_ORDERS['pickup_time'][value]:02d}"
        if pd.notna(value)
        else pd.NA
    )
    delay_valid = valid["pickup_delay_minutes"].ge(0)
    delay_categories = delay_band(valid["pickup_delay_minutes"].where(delay_valid))
    delay_sort = delay_categories.map(
        lambda value: f"{SORT_ORDERS['pickup_delay_band'][value]:02d}"
        if pd.notna(value)
        else pd.NA
    )

    group_rows: list[dict[str, object]] = []
    group_rows.extend(make_group_rows(valid, "order_date", date_categories))
    group_rows.extend(
        make_group_rows(
            valid,
            "day_of_week",
            weekday_categories,
            sort_keys=weekday_sort,
            scaffold=WEEKDAYS,
        )
    )
    group_rows.extend(
        make_group_rows(
            valid,
            "month",
            month_categories,
            labels=month_labels,
            sort_keys=month_categories,
        )
    )
    group_rows.extend(
        make_group_rows(
            valid,
            "order_time",
            order_bands,
            sort_keys=order_sort,
            scaffold=TIME_BANDS,
        )
    )
    group_rows.extend(
        make_group_rows(
            valid,
            "pickup_time",
            pickup_bands,
            sort_keys=pickup_sort,
            scaffold=TIME_BANDS,
        )
    )
    group_rows.extend(
        make_group_rows(
            valid,
            "pickup_delay_band",
            delay_categories,
            sort_keys=delay_sort,
            scaffold=DELAY_BANDS,
        )
    )
    python_groups = pd.DataFrame(group_rows)
    python_groups["sort_key"] = python_groups["sort_key"].astype(str)

    valid_dates = dates.dropna()
    valid_orders = order_minutes.dropna()
    valid_pickups = pickup_minutes.dropna()
    paired = order_minutes.notna() & pickup_minutes.notna()
    negative = paired & valid["pickup_delay_minutes"].lt(0)
    nonnegative = paired & valid["pickup_delay_minutes"].ge(0)
    delay_values = valid.loc[nonnegative, "pickup_delay_minutes"].to_numpy(
        dtype="float64"
    )
    if delay_values.size == 0:
        raise ValueError("No valid non-negative pickup delays are available.")
    delay_stats = {
        "valid_count": int(delay_values.size),
        "minimum": float(np.min(delay_values)),
        "p25": float(np.percentile(delay_values, 25, method="linear")),
        "median": float(np.percentile(delay_values, 50, method="linear")),
        "p75": float(np.percentile(delay_values, 75, method="linear")),
        "p90": float(np.percentile(delay_values, 90, method="linear")),
        "maximum": float(np.max(delay_values)),
        "mean": float(np.mean(delay_values)),
    }
    summary: dict[str, object] = {
        "total_train_rows": len(frame),
        "valid_target_rows": int(valid_mask.sum()),
        "valid_order_date_count": int(valid_dates.count()),
        "missing_invalid_order_date_count": int(len(valid) - valid_dates.count()),
        "valid_order_time_count": int(valid_orders.count()),
        "missing_invalid_order_time_count": int(len(valid) - valid_orders.count()),
        "valid_pickup_time_count": int(valid_pickups.count()),
        "missing_invalid_pickup_time_count": int(len(valid) - valid_pickups.count()),
        "minimum_order_date": valid_dates.min().strftime("%Y-%m-%d"),
        "maximum_order_date": valid_dates.max().strftime("%Y-%m-%d"),
        "paired_valid_clock_count": int(paired.sum()),
        "negative_difference_count": int(negative.sum()),
        "negative_difference_rate": (
            float(negative.sum() / paired.sum()) if paired.sum() else np.nan
        ),
        "nonnegative_delay_count": int(nonnegative.sum()),
        "minimum_delay": delay_stats["minimum"],
        "p25_delay": delay_stats["p25"],
        "median_delay": delay_stats["median"],
        "p75_delay": delay_stats["p75"],
        "p90_delay": delay_stats["p90"],
        "maximum_delay": delay_stats["maximum"],
        "mean_delay": delay_stats["mean"],
    }
    return python_groups, summary


def validate_group_results(
    sql_groups: pd.DataFrame,
    python_groups: pd.DataFrame,
) -> dict[str, dict[str, int]]:
    """Compare group membership, metrics, status, and ordered-category sequence."""
    validation: dict[str, dict[str, int]] = {}
    for dimension in DIMENSIONS:
        sql_part = (
            sql_groups.loc[sql_groups["dimension_name"] == dimension]
            .set_index("category")
        )
        python_part = (
            python_groups.loc[python_groups["dimension_name"] == dimension]
            .set_index("category")
        )
        if set(sql_part.index) != set(python_part.index):
            raise AssertionError(f"SQL/Python categories differ for {dimension}.")

        sql_order = sql_part.sort_values("sort_key", kind="stable").index.tolist()
        python_order = python_part.sort_values("sort_key", kind="stable").index.tolist()
        if sql_order != python_order:
            raise AssertionError(f"SQL/Python ordering differs for {dimension}.")

        metric_checks = 0
        for category in sql_part.index:
            sql_row = sql_part.loc[category]
            python_row = python_part.loc[category]
            if str(sql_row["category_label"]) != str(python_row["category_label"]):
                raise AssertionError(f"Category labels differ for {dimension}/{category}.")
            if str(sql_row["sample_size_status"]) != str(
                python_row["sample_size_status"]
            ):
                raise AssertionError(f"Sample-size status differs for {dimension}/{category}.")
            for metric in COUNT_METRICS:
                if int(sql_row[metric]) != int(python_row[metric]):
                    raise AssertionError(
                        f"{dimension}/{category} {metric} differs."
                    )
                metric_checks += 1
            for metric in FLOAT_METRICS:
                sql_value = sql_row[metric]
                python_value = python_row[metric]
                if pd.isna(sql_value) and pd.isna(python_value):
                    continue
                if pd.isna(sql_value) or pd.isna(python_value) or not close_enough(
                    float(sql_value), float(python_value)
                ):
                    raise AssertionError(
                        f"{dimension}/{category} {metric} differs: "
                        f"{sql_value} vs {python_value}."
                    )
                metric_checks += 1
        validation[dimension] = {
            "groups": len(sql_part),
            "metric_checks": metric_checks,
        }
    return validation


def validate_summary(
    sql_summary: pd.Series,
    python_summary: dict[str, object],
) -> int:
    """Compare data coverage, paired-time counts, and delay distribution metrics."""
    integer_fields = (
        "total_train_rows",
        "valid_target_rows",
        "valid_order_date_count",
        "missing_invalid_order_date_count",
        "valid_order_time_count",
        "missing_invalid_order_time_count",
        "valid_pickup_time_count",
        "missing_invalid_pickup_time_count",
        "paired_valid_clock_count",
        "negative_difference_count",
        "nonnegative_delay_count",
    )
    float_fields = (
        "negative_difference_rate",
        "minimum_delay",
        "p25_delay",
        "median_delay",
        "p75_delay",
        "p90_delay",
        "maximum_delay",
        "mean_delay",
    )
    checks = 0
    for field in integer_fields:
        if int(sql_summary[field]) != int(python_summary[field]):
            raise AssertionError(f"SQL/Python summary count differs for {field}.")
        checks += 1
    for field in float_fields:
        if not close_enough(float(sql_summary[field]), float(python_summary[field])):
            raise AssertionError(f"SQL/Python summary metric differs for {field}.")
        checks += 1
    for field in ("minimum_order_date", "maximum_order_date"):
        if str(sql_summary[field]) != str(python_summary[field]):
            raise AssertionError(f"SQL/Python date coverage differs for {field}.")
        checks += 1
    return checks


def metric_rows(frame: pd.DataFrame) -> list[list[object]]:
    """Format group metrics, including slow-rate numerator and denominator."""
    output = []
    for _, row in frame.iterrows():
        count = int(row["delivery_count"])
        if count == 0:
            output.append(
                [row["category_label"], "0", "—", "—", "—", "0 / 0", "—", "No records"]
            )
            continue
        slow = int(row["slow_delivery_count"])
        status = (
            "Meets minimum"
            if count >= MIN_GROUP_SIZE
            else "Small sample; descriptive only"
        )
        output.append(
            [
                row["category_label"],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                f"{slow:,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                status,
            ]
        )
    return output


def sorted_dimension(
    groups: pd.DataFrame,
    dimension: str,
    chronological: bool = False,
) -> pd.DataFrame:
    """Return one dimension in its declared SQL category order."""
    selected = groups.loc[groups["dimension_name"] == dimension].copy()
    selected = selected.sort_values("sort_key", kind="stable")
    if chronological and dimension == "order_date":
        selected = selected.sort_values("category", kind="stable")
    return selected


def append_group_section(
    lines: list[str],
    title: str,
    description: str,
    groups: pd.DataFrame,
    heading_level: int = 2,
) -> None:
    """Add an ordered table with all required performance and slow-rate fields."""
    lines.extend([f"{'#' * heading_level} {title}", "", description, ""])
    lines.extend(
        markdown_table(
            [
                "Category",
                "Delivery count",
                "Mean (min)",
                "Median (min)",
                "P90 (min)",
                "Slow count / denominator",
                "Slow rate",
                "Sample-size status",
            ],
            metric_rows(groups),
        )
    )
    lines.append("")


def main() -> None:
    """Run SQL/Python temporal validation and write the analysis report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [
        TARGET_COLUMN,
        DATE_COLUMN,
        ORDER_TIME_COLUMN,
        PICKUP_TIME_COLUMN,
    ]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required temporal analysis columns are missing: {missing_columns}")

    python_groups, python_summary = calculate_python_results(frame)
    sql_text = SQL_PATH.read_text(encoding="utf-8")
    sql_groups, sql_summary_frame, sqlite_version = run_sql(frame, sql_text)
    if sql_groups.empty or len(sql_summary_frame) != 1:
        raise AssertionError("The SQL script returned missing or malformed result sets.")
    sql_summary = sql_summary_frame.iloc[0]

    target_numeric = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_target_count = int(target_numeric.notna().sum())
    if int(sql_summary["valid_target_rows"]) != valid_target_count:
        raise AssertionError("SQL valid-target population does not match Pandas.")

    for dimension in DIMENSIONS:
        sql_part = sql_groups.loc[sql_groups["dimension_name"] == dimension]
        if sql_part.empty:
            raise AssertionError(f"SQL returned no category rows for {dimension}.")
        expected_total = int(sql_part["delivery_count"].sum())
        if dimension in ("order_date", "day_of_week", "month"):
            expected_total = int(python_summary["valid_order_date_count"])
        elif dimension == "order_time":
            expected_total = int(python_summary["valid_order_time_count"])
        elif dimension == "pickup_time":
            expected_total = int(python_summary["valid_pickup_time_count"])
        elif dimension == "pickup_delay_band":
            expected_total = int(python_summary["nonnegative_delay_count"])
        if int(sql_part["delivery_count"].sum()) != expected_total:
            raise AssertionError(f"SQL group counts do not reconcile for {dimension}.")
        python_part = python_groups.loc[python_groups["dimension_name"] == dimension]
        if int(python_part["delivery_count"].sum()) != expected_total:
            raise AssertionError(f"Python group counts do not reconcile for {dimension}.")

    validation = validate_group_results(sql_groups, python_groups)
    summary_checks = validate_summary(sql_summary, python_summary)

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned dataset schema changed during analysis.")

    date_groups = sorted_dimension(sql_groups, "order_date", chronological=True)
    weekday_groups = sorted_dimension(sql_groups, "day_of_week")
    month_groups = sorted_dimension(sql_groups, "month")
    order_groups = sorted_dimension(sql_groups, "order_time")
    pickup_groups = sorted_dimension(sql_groups, "pickup_time")
    delay_groups = sorted_dimension(sql_groups, "pickup_delay_band")
    month_count = date_groups["category"].str.slice(0, 7).nunique()

    high_volume = date_groups.sort_values(
        ["delivery_count", "category"],
        ascending=[False, True],
        kind="stable",
    ).head(5)
    low_volume = date_groups.sort_values(
        ["delivery_count", "category"],
        ascending=[True, True],
        kind="stable",
    ).head(5)
    delay_summary_rows = [
        [
            f"{int(sql_summary['nonnegative_delay_count']):,}",
            format_number(float(sql_summary["minimum_delay"])),
            format_number(float(sql_summary["p25_delay"])),
            format_number(float(sql_summary["median_delay"])),
            format_number(float(sql_summary["p75_delay"])),
            format_number(float(sql_summary["p90_delay"])),
            format_number(float(sql_summary["maximum_delay"])),
            format_number(float(sql_summary["mean_delay"])),
        ]
    ]
    negative_rate_pct = float(sql_summary["negative_difference_rate"]) * 100.0

    lines = [
        "# Time Analysis",
        "",
        "## Objective",
        "",
        "Describe observed delivery-performance patterns by order date, weekday, month, "
        "order-time band, pickup-time band, and valid non-negative order-to-pickup delay. "
        "These are separate unadjusted temporal comparisons.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only; no test targets are used.",
        f"- **Target:** `{TARGET_COLUMN}`, included only when non-null and numeric.",
        "- **Fixed slow threshold:** 40 minutes; slow means strictly `Time_taken(min) > 40`.",
        "- **Percentiles:** continuous linear interpolation at rank `1 + (n - 1) × p`.",
        f"- **Minimum group size:** {MIN_GROUP_SIZE}; smaller groups are shown descriptively "
        "and not substantively compared.",
        "- Dates are parsed strictly as `YYYY-MM-DD`; clock values are parsed strictly as "
        "`HH:MM:SS`. SQLite uses explicit date/time parsing and minute-of-day conversion.",
        "",
        f"Total train rows: **{int(sql_summary['total_train_rows']):,}**; valid numeric "
        f"targets: **{int(sql_summary['valid_target_rows']):,}**.",
        "",
        "## Order Date Coverage",
        "",
        f"- Minimum valid date: **{sql_summary['minimum_order_date']}**.",
        f"- Maximum valid date: **{sql_summary['maximum_order_date']}**.",
        f"- Valid dates among valid targets: **{int(sql_summary['valid_order_date_count']):,}**.",
        f"- Missing/invalid dates among valid targets: "
        f"**{int(sql_summary['missing_invalid_order_date_count']):,}**.",
        f"- Observed calendar-month coverage: **{month_count} month(s)**.",
        "",
        "Delivery performance by calendar date:",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                "Order date",
                "Delivery count",
                "Mean (min)",
                "Median (min)",
                "P90 (min)",
                "Slow count / denominator",
                "Slow rate",
                "Sample-size status",
            ],
            metric_rows(date_groups),
        )
    )
    lines.extend(
        [
            "",
            "Highest-volume dates (descriptive counts):",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Date", "Valid deliveries"],
            [
                [row["category"], f"{int(row['delivery_count']):,}"]
                for _, row in high_volume.iterrows()
            ],
        )
    )
    lines.extend(["", "Lowest-volume dates (descriptive counts):", ""])
    lines.extend(
        markdown_table(
            ["Date", "Valid deliveries"],
            [
                [row["category"], f"{int(row['delivery_count']):,}"]
                for _, row in low_volume.iterrows()
            ],
        )
    )
    append_group_section(
        lines,
        "Day-of-Week Analysis",
        "Weekday is derived from valid Order_Date. Order is chronological, Monday through "
        "Sunday (Python weekday convention Monday=0); every category meets the same "
        "30-record reporting rule.",
        weekday_groups,
    )
    append_group_section(
        lines,
        "Monthly Analysis",
        f"Months are ordered by calendar month number. The observed training data covers "
        f"{month_count} calendar month(s), from {sql_summary['minimum_order_date']} to "
        f"{sql_summary['maximum_order_date']}; this is not a full-year seasonal sample.",
        month_groups.assign(
            category_label=month_groups["category"]
            + " — "
            + month_groups["category_label"]
        ),
    )
    band_definitions = (
        "Night (00:00–05:59), Morning (06:00–11:59), Afternoon (12:00–16:59), "
        "Evening (17:00–20:59), and Late Night (21:00–23:59)."
    )
    append_group_section(
        lines,
        "Order-Time Analysis",
        f"Valid order times are converted from HH:MM:SS into minutes after midnight, then "
        f"classified into the fixed bands: {band_definitions} Missing/invalid order times "
        f"among valid targets: **{int(sql_summary['missing_invalid_order_time_count']):,}**; "
        f"valid parsed order times: **{int(sql_summary['valid_order_time_count']):,}**.",
        order_groups,
    )
    append_group_section(
        lines,
        "Pickup-Time Analysis",
        f"Pickup time is analyzed separately using the same fixed bands: {band_definitions} "
        f"Missing/invalid pickup times among valid targets: "
        f"**{int(sql_summary['missing_invalid_pickup_time_count']):,}**; valid parsed "
        f"pickup times: **{int(sql_summary['valid_pickup_time_count']):,}**.",
        pickup_groups,
    )
    lines.extend(
        [
            "## Order-to-Pickup Delay",
            "",
            "### Time Parsing",
            "",
            "Valid clock strings were parsed strictly as HH:MM:SS and converted to "
            "fractional minutes after midnight. The direct same-day difference is "
            "`pickup time − order time`; it was not made positive or adjusted by 24 hours.",
            f"- Valid paired order/pickup clocks: "
            f"**{int(sql_summary['paired_valid_clock_count']):,}**.",
            f"- Missing/invalid order times among valid targets: "
            f"**{int(sql_summary['missing_invalid_order_time_count']):,}**.",
            f"- Missing/invalid pickup times among valid targets: "
            f"**{int(sql_summary['missing_invalid_pickup_time_count']):,}**.",
            "",
            "### Negative/Ambiguous Differences",
            "",
            f"- Negative same-day differences treated as ambiguous: "
            f"**{int(sql_summary['negative_difference_count']):,}**.",
            f"- Denominator (valid paired clocks): "
            f"**{int(sql_summary['paired_valid_clock_count']):,}**.",
            f"- Negative/ambiguous proportion: **{negative_rate_pct:.4f}%**.",
            f"- Non-negative differences retained for the primary delay distribution: "
            f"**{int(sql_summary['nonnegative_delay_count']):,}**.",
            "- Negative cases are excluded from the primary delay distribution because "
            "the available dates do not establish whether midnight was crossed.",
            "",
            "### Valid Pickup Delay Distribution",
            "",
            "Statistics below include only valid paired clocks with a non-negative direct "
            "same-day difference. Percentiles use continuous linear interpolation.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Count",
                "Minimum (min)",
                "P25 (min)",
                "Median (min)",
                "P75 (min)",
                "P90 (min)",
                "Maximum (min)",
                "Mean (min)",
            ],
            delay_summary_rows,
        )
    )
    append_group_section(
        lines,
        "Pickup Delay Band Analysis",
        "Bands use direct same-day delay minutes: 0–5, >5–10, >10–15, >15–20, "
        ">20–30, and >30 minutes. Negative and unpaired clock records are excluded. "
        "Exact fractional-minute values are retained for summary statistics.",
        delay_groups,
        heading_level=3,
    )

    validation_rows = [
        [
            dimension,
            summary["groups"],
            summary["metric_checks"],
            "MATCH",
        ]
        for dimension, summary in validation.items()
    ]
    validation_rows.append(["Coverage and delay distribution", "1", summary_checks, "MATCH"])
    validation_rows.append(
        [
            "Weekday/month/time/delay band order and classification",
            "4 dimensions",
            "category sets, counts, labels, and order checked",
            "MATCH",
        ]
    )
    lines.extend(
        [
            "## SQL vs Python Validation",
            "",
            f"SQL statements in `sql/07_time_analysis.sql` were executed against an "
            f"in-memory SQLite table (version `{sqlite_version}`). Python independently "
            "parsed the source strings and calculated groups and continuous percentiles "
            "with Pandas/NumPy. SQLite has no built-in PERCENTILE_CONT; SQL implements "
            "continuous linear interpolation.",
            "",
            f"Counts, classifications, and category ordering were checked exactly. "
            f"Floating-point metrics use `numpy.isclose` with absolute tolerance "
            f"`{ABSOLUTE_TOLERANCE:g}` and relative tolerance `{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Analysis", "Groups", "Validated fields", "Result"],
            validation_rows,
        )
    )
    total_metric_checks = sum(
        item["metric_checks"] for item in validation.values()
    ) + summary_checks
    lines.extend(
        [
            "",
            f"All SQL/Python checks passed: **{total_metric_checks} metric/count checks** "
            "across grouped results and coverage/delay summaries. Weekday and month "
            "ordering, fixed clock bands, and pickup-delay band classifications matched.",
            "",
            "## Interpretation",
            "",
            "The tables describe observed delivery-time variation across calendar dates, "
            "weekdays, months, order-time bands, pickup-time bands, and non-negative "
            "same-day pickup delays. These temporal associations do not establish that a "
            "date, weekday, month, time band, or pickup delay causes delivery-time "
            "differences.",
            "",
            "## Limitations",
            "",
            "- The data spans "
            f"{month_count} calendar month(s), so it cannot establish annual seasonality "
            "or a full-year temporal pattern.",
            "- Daily performance can be sensitive to per-date sample size; dates below "
            f"{MIN_GROUP_SIZE} valid targets are descriptive only.",
            "- Clock-only negative differences are ambiguous; no midnight rollover is "
            "assumed without a pickup date.",
            "- Order-to-pickup elapsed-time metrics omit negative and unpaired clock "
            "records from the primary distribution.",
            "- Comparisons are observational and unadjusted; other explanatory dimensions "
            "are not combined or analyzed in this step.",
            "- The 30-record rule is a reporting guardrail, not a guarantee of statistical "
            "precision.",
            "",
            f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is "
            f"`{source_hash_before}` before and after; the input schema is unchanged and "
            "no derived columns were persisted.",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(DIMENSIONS)} temporal dimensions; "
        f"{total_metric_checks} grouped/summary metrics and "
        f"{sum(item['groups'] for item in validation.values())} category sets matched."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
