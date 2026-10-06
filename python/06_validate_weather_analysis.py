"""Validate weather-category performance with independent SQL and Pandas results."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "03_weather_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "weather_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
DIMENSION = "Weatherconditions"
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
FLOAT_METRICS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
COUNT_METRICS = ("delivery_count", "slow_delivery_count")


def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest to check input integrity."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating-point metrics using the documented tolerance."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Format metrics compactly for Markdown."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format a Markdown table and escape cell delimiters."""
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


def calculate_python_metrics(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, int, int, int]:
    """Calculate category metrics with NumPy's continuous linear percentiles."""
    numeric_target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = numeric_target.notna()
    valid = frame.loc[valid_mask, [DIMENSION]].copy()
    valid[TARGET_COLUMN] = numeric_target.loc[valid_mask]
    total_rows = len(frame)
    valid_count = int(valid_mask.sum())
    missing_weather_count = int(valid[DIMENSION].isna().sum())
    categorized = valid.loc[valid[DIMENSION].notna()]

    results: list[dict[str, object]] = []
    for category, group in categorized.groupby(DIMENSION, sort=True, dropna=True):
        values = group[TARGET_COLUMN].to_numpy(dtype="float64")
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        results.append(
            {
                DIMENSION: str(category),
                "delivery_count": len(group),
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(np.percentile(values, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / len(group),
            }
        )

    return pd.DataFrame(results), total_rows, valid_count, missing_weather_count


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Execute the SQL artifact on a temporary SQLite table."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        results = pd.read_sql_query(query, connection)
        return results, sqlite3.sqlite_version
    finally:
        connection.close()


def validate_results(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
) -> list[list[object]]:
    """Compare every requested count and floating-point metric by category."""
    sql_by_category = sql_results.set_index(DIMENSION)
    python_by_category = python_results.set_index(DIMENSION)
    if set(sql_by_category.index) != set(python_by_category.index):
        raise AssertionError("SQL and Python returned different weather categories.")

    rows: list[list[object]] = []
    for category in sorted(sql_by_category.index):
        sql_row = sql_by_category.loc[category]
        python_row = python_by_category.loc[category]
        for metric in COUNT_METRICS:
            sql_value = int(sql_row[metric])
            python_value = int(python_row[metric])
            matched = sql_value == python_value
            rows.append(
                [
                    category,
                    metric.replace("_", " "),
                    f"{sql_value:,}",
                    f"{python_value:,}",
                    "MATCH" if matched else "MISMATCH",
                ]
            )
            if not matched:
                raise AssertionError(
                    f"{category} {metric} mismatch: SQL={sql_value}, Python={python_value}"
                )
        for metric in FLOAT_METRICS:
            sql_value = float(sql_row[metric])
            python_value = float(python_row[metric])
            matched = close_enough(sql_value, python_value)
            rows.append(
                [
                    category,
                    metric.replace("_", " "),
                    format_number(sql_value),
                    format_number(python_value),
                    "MATCH" if matched else "MISMATCH",
                ]
            )
            if not matched:
                raise AssertionError(
                    f"{category} {metric} mismatch: SQL={sql_value}, Python={python_value}"
                )
    return rows


def create_report(
    sql_results: pd.DataFrame,
    validation_rows: list[list[object]],
    total_rows: int,
    valid_targets: int,
    missing_or_invalid_targets: int,
    missing_weather: int,
    sqlite_version: str,
    source_hash: str,
) -> str:
    """Render the required weather analysis report from calculated results."""
    categorized_targets = valid_targets - missing_weather
    result_rows: list[list[object]] = []
    slow_rows: list[list[object]] = []
    interpretable_summaries: list[str] = []
    for _, row in sql_results.iterrows():
        category = str(row[DIMENSION])
        count = int(row["delivery_count"])
        status = "Meets minimum" if count >= MIN_GROUP_SIZE else "Small sample; descriptive only"
        result_rows.append(
            [
                category,
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                status,
            ]
        )
        slow_rows.append(
            [
                category,
                f"{int(row['slow_delivery_count']):,}",
                f"{count:,}",
                f"{int(row['slow_delivery_count']):,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                status,
            ]
        )
        if count >= MIN_GROUP_SIZE:
            interpretable_summaries.append(
                f"{category} has {count:,} valid deliveries, mean "
                f"{format_number(float(row['mean_delivery_time']))} minutes, median "
                f"{format_number(float(row['median_delivery_time']))} minutes, and P90 "
                f"{format_number(float(row['p90_delivery_time']))} minutes"
            )

    categorized_slow = int(sql_results["slow_delivery_count"].sum())
    lines = [
        "# Weather Analysis",
        "",
        "## Objective",
        "",
        "Describe how observed delivery performance differs across weather conditions. "
        "This is a descriptive association analysis, not a causal analysis.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only; test data is not used.",
        f"- **Target:** `{TARGET_COLUMN}`.",
        f"- **Primary dimension:** `{DIMENSION}`.",
        "- **Valid-target rule:** include only rows where the target is non-null and numeric.",
        "- **Missing weather treatment:** do not infer a category; exclude missing weather "
        "only from category comparisons while retaining those rows in the valid-target "
        "population.",
        f"- **Fixed slow threshold:** **{FIXED_SLOW_THRESHOLD:g} minutes**, using the "
        "strict rule `Time_taken(min) > 40`. No weather-specific threshold is calculated.",
        "",
        "## Results",
        "",
        f"- Total training rows: **{total_rows:,}**.",
        f"- Total valid numeric targets: **{valid_targets:,}**.",
        f"- Missing/invalid target rows: **{missing_or_invalid_targets:,}**.",
        f"- Valid targets with non-null weather: **{categorized_targets:,}**.",
        f"- Valid targets excluded because weather is missing: **{missing_weather:,}**.",
        "",
        "## Comparison Across Weather Categories",
        "",
        "Median and P90 use continuous linear interpolation with rank "
        "`1 + (n - 1) × p`, equivalent to NumPy `percentile(method='linear')`. "
        f"Groups need at least {MIN_GROUP_SIZE} valid records for comparative "
        "interpretation; smaller groups, if present, are descriptive only.",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                "Weather condition",
                "Delivery count",
                "Mean (min)",
                "Median (min)",
                "P90 (min)",
                "Sample-size status",
            ],
            result_rows,
        )
    )
    lines.extend(
        [
            "",
            "## Slow-Delivery Analysis",
            "",
            f"All groups use the fixed global threshold of strictly greater than "
            f"{FIXED_SLOW_THRESHOLD:g} minutes. Each rate is calculated as the slow "
            "delivery count divided by all valid deliveries in that weather category; "
            "the numerator and denominator are explicit.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Weather condition",
                "Slow count (numerator)",
                "Delivery count (denominator)",
                "Rate calculation",
                "Slow rate",
                "Sample-size status",
            ],
            slow_rows,
        )
    )
    lines.extend(
        [
            "",
            f"The fixed threshold classified {categorized_slow:,} of "
            f"{categorized_targets:,} categorized valid-target records as slow; "
            f"{missing_weather:,} additional valid-target records had missing weather "
            "and are not allocated to any weather group.",
            "",
            "## SQL vs Python Validation",
            "",
            f"SQL from `sql/03_weather_analysis.sql` was executed against an in-memory "
            f"SQLite table loaded from the cleaned training file (SQLite `{sqlite_version}`). "
            "Pandas independently grouped the same valid-target population; NumPy computed "
            "median/P90 with continuous linear interpolation. Standard SQLite has no "
            "built-in `PERCENTILE_CONT`, so the SQL query implements rank interpolation "
            "at `1 + (n - 1) × p`.",
            "",
            f"Counts must match exactly. Floating-point values use `numpy.isclose` with "
            f"absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and relative tolerance "
            f"`{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Category", "Metric", "SQL", "Python", "Result"],
            validation_rows,
        )
    )
    lines.extend(
        [
            "",
            f"Grouped delivery counts total {categorized_targets:,}; the remaining "
            f"{missing_weather:,} valid-target rows have no weather category.",
            "",
            "## Interpretation",
            "",
            "The metrics describe observed delivery-time differences across weather "
            "categories only. "
            + (
                "; ".join(interpretable_summaries) + "."
                if interpretable_summaries
                else "No weather category met the minimum sample-size rule."
            )
            + " These are associations in the observed data and do not establish that "
            "weather causes delivery-time differences. Categories below 30 valid "
            "records, if any, are descriptive only and are not ranked or substantively "
            "compared.",
            "",
            "## Limitations",
            "",
            "- This observational comparison does not establish causation.",
            "- Missing weather values are excluded only from weather-group comparison; "
            "no category is imputed or inferred.",
            "- Group P90 values describe within-category distributions; the slow "
            "classification still uses only the fixed global 40-minute threshold.",
            "- Results cover valid observed targets in the cleaned training data and may "
            "not generalize beyond this dataset.",
            "- No traffic, city, vehicle, courier, distance, time-pattern, or combined-factor "
            "analysis is included.",
            "",
            "Read-only validation: the cleaned training file SHA-256 before/after analysis "
            f"is `{source_hash}`; no derived columns were persisted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Run the SQL and Pandas analyses, validate agreement, and write the report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    for column in (TARGET_COLUMN, DIMENSION):
        if column not in frame.columns:
            raise ValueError(f"Required column not found: {column}")

    python_results, total_rows, valid_targets, missing_weather = calculate_python_metrics(frame)
    missing_or_invalid_targets = total_rows - valid_targets
    if valid_targets == 0:
        raise ValueError("No valid numeric targets were found.")

    sql_query = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(frame, sql_query)
    if sql_results.empty:
        raise AssertionError("SQL returned no weather categories.")

    if int(sql_results["total_train_rows"].iloc[0]) != total_rows:
        raise AssertionError("SQL total row count does not match the source.")
    if int(sql_results["valid_target_rows"].iloc[0]) != valid_targets:
        raise AssertionError("SQL valid-target count does not match Pandas.")
    if int(sql_results["valid_targets_excluded_for_missing_weather"].iloc[0]) != missing_weather:
        raise AssertionError("SQL missing-weather count does not match Pandas.")
    expected_group_count = valid_targets - missing_weather
    if int(sql_results["delivery_count"].sum()) != expected_group_count:
        raise AssertionError("SQL category counts do not reconcile to the eligible population.")
    if int(python_results["delivery_count"].sum()) != expected_group_count:
        raise AssertionError("Python category counts do not reconcile to the eligible population.")

    validation_rows = validate_results(sql_results, python_results)

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned training schema changed during analysis.")

    report = create_report(
        sql_results,
        validation_rows,
        total_rows,
        valid_targets,
        missing_or_invalid_targets,
        missing_weather,
        sqlite_version,
        source_hash_before,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(
        f"Validated {len(sql_results)} weather categories, {valid_targets:,} valid targets, "
        f"{missing_weather:,} missing-weather rows, and {len(validation_rows)} metric comparisons."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
