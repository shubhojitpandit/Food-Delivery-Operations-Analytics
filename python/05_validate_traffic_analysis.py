"""Validate grouped traffic performance with independent SQL and Pandas results."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "02_traffic_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "traffic_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
DIMENSION = "Road_traffic_density"
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
COUNT_METRICS = (
    "delivery_count",
    "slow_delivery_count",
)


def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest to ensure the input remains unchanged."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating-point metrics using the documented NumPy tolerance."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Render concise numeric values without changing computed precision."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format report tables and escape Markdown cell separators."""
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
    """Calculate traffic-category metrics with continuous linear percentiles."""
    numeric_target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_target_mask = numeric_target.notna()
    valid_targets = frame.loc[valid_target_mask, [DIMENSION]].copy()
    valid_targets[TARGET_COLUMN] = numeric_target.loc[valid_target_mask]

    total_rows = len(frame)
    valid_count = int(valid_target_mask.sum())
    missing_or_invalid_target_count = total_rows - valid_count
    missing_dimension_count = int(valid_targets[DIMENSION].isna().sum())
    categorized = valid_targets[valid_targets[DIMENSION].notna()]

    rows: list[dict[str, object]] = []
    for category, group in categorized.groupby(DIMENSION, sort=True, dropna=True):
        values = group[TARGET_COLUMN].to_numpy(dtype="float64")
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        rows.append(
            {
                DIMENSION: str(category),
                "delivery_count": len(group),
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(np.percentile(values, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
                "minimum_delivery_time": float(np.min(values)),
                "maximum_delivery_time": float(np.max(values)),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / len(group),
            }
        )
    return (
        pd.DataFrame(rows),
        total_rows,
        valid_count,
        missing_dimension_count,
    )


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Execute the SQL artifact against a temporary in-memory SQLite table."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        results = pd.read_sql_query(query, connection)
        return results, sqlite3.sqlite_version
    finally:
        connection.close()


def create_report(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
    total_rows: int,
    valid_target_count: int,
    missing_or_invalid_target_count: int,
    missing_dimension_count: int,
    validation_rows: list[list[object]],
    sqlite_version: str,
) -> str:
    """Create the requested report from validated SQL and Pandas output."""
    categorized_count = valid_target_count - missing_dimension_count
    result_rows: list[list[object]] = []
    slow_rows: list[list[object]] = []
    interpretation_parts: list[str] = []

    for _, row in sql_results.iterrows():
        category = str(row[DIMENSION])
        count = int(row["delivery_count"])
        qualifies = count >= MIN_GROUP_SIZE
        sample_label = "Meets minimum" if qualifies else "Small sample; descriptive only"
        result_rows.append(
            [
                category,
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                sample_label,
            ]
        )
        slow_rows.append(
            [
                category,
                f"{int(row['slow_delivery_count']):,}",
                f"{count:,}",
                f"{int(row['slow_delivery_count']):,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                sample_label,
            ]
        )
        if qualifies:
            interpretation_parts.append(
                f"{category} has {count:,} valid deliveries, a mean of "
                f"{format_number(float(row['mean_delivery_time']))} minutes, a median of "
                f"{format_number(float(row['median_delivery_time']))} minutes, and a P90 "
                f"of {format_number(float(row['p90_delivery_time']))} minutes"
            )

    excluded_slow_count = int(
        pd.to_numeric(sql_results["valid_targets_excluded_for_missing_traffic"].iloc[0])
    )
    lines = [
        "# Traffic Analysis",
        "",
        "## Objective",
        "",
        "Describe how observed delivery performance differs across road traffic density "
        "categories. This is a descriptive association analysis, not a causal analysis.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only; test data is not used.",
        f"- **Target:** `{TARGET_COLUMN}`.",
        f"- **Dimension:** `{DIMENSION}`.",
        "- **Valid-target rule:** include only rows with a non-null numeric target.",
        f"- **Slow threshold:** fixed at **{FIXED_SLOW_THRESHOLD:g} minutes** from Step 5.1; "
        "a slow delivery is strictly `Time_taken(min) > 40`.",
        "- The threshold was not recalculated for traffic groups.",
        "",
        "## Results",
        "",
        f"- Total training rows: **{total_rows:,}**.",
        f"- Valid numeric-target rows: **{valid_target_count:,}**.",
        f"- Missing/invalid target rows: **{missing_or_invalid_target_count:,}**.",
        f"- Valid targets with a non-null traffic category: **{categorized_count:,}**.",
        f"- Valid targets excluded from category comparisons because traffic is missing: "
        f"**{missing_dimension_count:,}**.",
        "- This exclusion applies only to the traffic-category comparison; those records "
        "remain in the overall valid-target population.",
        "",
        "## Comparison Across Traffic Categories",
        "",
        f"Percentiles use continuous linear interpolation (rank `1 + (n - 1) × p`, "
        "equivalent to NumPy `percentile(method='linear')`). The framework's minimum of "
        f"{MIN_GROUP_SIZE} valid records is used as an interpretation guardrail.",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                "Road traffic density",
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
            f"Every category uses the already-fixed global threshold of > "
            f"{FIXED_SLOW_THRESHOLD:g} minutes. Slow-delivery rate is the slow count "
            "divided by all valid target deliveries in that category; numerator and "
            "denominator are shown explicitly.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Road traffic density",
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
            f"- The fixed threshold classified {int(sql_results['slow_delivery_count'].sum()):,} "
            f"of {categorized_count:,} categorized valid-target rows as slow. A further "
            f"{excluded_slow_count:,} valid-target row(s) with missing traffic categories "
            "are outside this grouped comparison.",
            "",
            "## SQL vs Python Validation",
            "",
            f"SQL was executed from `sql/02_traffic_analysis.sql` against an in-memory "
            f"SQLite table loaded from the cleaned training CSV (SQLite `{sqlite_version}`). "
            "Python independently grouped the same numeric target population with Pandas "
            "and computed median/P90 using NumPy continuous linear interpolation. SQLite "
            "has no standard built-in `PERCENTILE_CONT`; the query implements the same "
            "rank interpolation by category.",
            "",
            f"Counts are required to match exactly. Floating-point metrics use "
            f"`numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and relative "
            f"tolerance `{RELATIVE_TOLERANCE:g}`.",
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
            f"- Total train rows: {total_rows:,}; valid target rows: "
            f"{valid_target_count:,}; invalid/missing target rows: "
            f"{missing_or_invalid_target_count:,}.",
            f"- Valid target rows with non-null traffic: {categorized_count:,}; "
            f"valid target rows with missing traffic excluded from groups: "
            f"{missing_dimension_count:,}.",
            "- SQL/Python category counts reconcile to the same eligible population.",
            "",
            "## Interpretation",
            "",
            "The grouped metrics describe observed delivery-time differences by road "
            "traffic category only. "
            + (
                "; ".join(interpretation_parts) + "."
                if interpretation_parts
                else "No category met the minimum sample-size rule for comparative interpretation."
            )
            + " These are associations in the observed data and do not establish that "
            "traffic causes the delivery-time differences. Groups below 30 records, if "
            "any, are descriptive only and are not substantively compared or ranked.",
            "",
            "## Limitations",
            "",
            "- The analysis is observational; no causal conclusion is supported.",
            "- Records with missing traffic category are not assigned a fabricated category "
            "and are excluded only from grouped traffic comparisons.",
            "- P90 is group-specific for this required comparison; the slow threshold is not. "
            "All slow rates use the fixed global 40-minute threshold.",
            "- Results describe valid observed target records in the cleaned training file "
            "and may not generalize beyond this dataset.",
            "- Only road traffic density is analyzed in this step; no other explanatory "
            "dimensions or combined factors are included.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_sql_python(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
) -> list[list[object]]:
    """Match every required category metric and fail if any comparison diverges."""
    sql_by_category = sql_results.set_index(DIMENSION)
    python_by_category = python_results.set_index(DIMENSION)
    if set(sql_by_category.index) != set(python_by_category.index):
        raise AssertionError("SQL and Python returned different traffic categories.")

    rows: list[list[object]] = []
    for category in sorted(sql_by_category.index):
        sql_row = sql_by_category.loc[category]
        python_row = python_by_category.loc[category]
        for metric in COUNT_METRICS:
            sql_value = int(sql_row[metric])
            python_value = int(python_row[metric])
            matches = sql_value == python_value
            rows.append(
                [
                    category,
                    metric.replace("_", " "),
                    f"{sql_value:,}",
                    f"{python_value:,}",
                    "MATCH" if matches else "MISMATCH",
                ]
            )
            if not matches:
                raise AssertionError(
                    f"Count mismatch for {category} {metric}: {sql_value} != {python_value}"
                )
        for metric in FLOAT_METRICS:
            sql_value = float(sql_row[metric])
            python_value = float(python_row[metric])
            matches = close_enough(sql_value, python_value)
            rows.append(
                [
                    category,
                    metric.replace("_", " "),
                    format_number(sql_value),
                    format_number(python_value),
                    "MATCH" if matches else "MISMATCH",
                ]
            )
            if not matches:
                raise AssertionError(
                    f"Metric mismatch for {category} {metric}: "
                    f"{sql_value} != {python_value}"
                )
    return rows


def main() -> None:
    """Run the SQL analysis, validate independently in Python, and write report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    if TARGET_COLUMN not in frame or DIMENSION not in frame:
        raise ValueError("The cleaned training file is missing a required analysis column.")

    numeric_target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_target_mask = numeric_target.notna()
    total_rows = len(frame)
    valid_target_count = int(valid_target_mask.sum())
    missing_or_invalid_target_count = total_rows - valid_target_count
    if valid_target_count == 0:
        raise ValueError("The cleaned training file has no valid numeric targets.")
    expected_missing_dimension_count = int(
        frame.loc[valid_target_mask, DIMENSION].isna().sum()
    )

    python_results, python_total, python_valid, python_missing_dimension = (
        calculate_python_metrics(frame)
    )
    if (
        python_total != total_rows
        or python_valid != valid_target_count
        or python_missing_dimension != expected_missing_dimension_count
    ):
        raise AssertionError("Python valid-population counts failed reconciliation.")

    query = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(frame, query)
    if sql_results.empty:
        raise AssertionError("SQL returned no valid traffic categories.")
    sql_total = int(sql_results["total_train_rows"].iloc[0])
    sql_valid = int(sql_results["valid_target_rows"].iloc[0])
    sql_missing_dimension = int(
        sql_results["valid_targets_excluded_for_missing_traffic"].iloc[0]
    )
    if (
        sql_total != total_rows
        or sql_valid != valid_target_count
        or sql_missing_dimension != expected_missing_dimension_count
    ):
        raise AssertionError("SQL valid-population counts failed reconciliation.")
    if int(sql_results["delivery_count"].sum()) != valid_target_count - expected_missing_dimension_count:
        raise AssertionError("SQL traffic-category counts do not reconcile to eligible targets.")
    if int(python_results["delivery_count"].sum()) != valid_target_count - expected_missing_dimension_count:
        raise AssertionError("Python traffic-category counts do not reconcile to eligible targets.")

    validation_rows = validate_sql_python(sql_results, python_results)
    if not sql_results["delivery_count"].equals(python_results.set_index(DIMENSION).loc[
        sql_results[DIMENSION], "delivery_count"
    ].reset_index(drop=True)):
        raise AssertionError("Traffic category counts differ between SQL and Python.")

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if len(pd.read_csv(TRAIN_PATH, nrows=0).columns) != len(frame.columns):
        raise AssertionError("The cleaned training schema changed during analysis.")

    report = create_report(
        sql_results,
        python_results,
        total_rows,
        valid_target_count,
        missing_or_invalid_target_count,
        expected_missing_dimension_count,
        validation_rows,
        sqlite_version,
    )
    report += (
        "\nRead-only validation: SHA-256 of `data/processed/train_clean.csv` is unchanged "
        f"(`{source_hash_before}`); cleaned column count remains {len(frame.columns)}. "
        "No derived columns were persisted.\n"
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(
        f"Validated {len(sql_results)} traffic categories, {valid_target_count:,} valid "
        f"targets, and {len(validation_rows)} SQL/Python metric comparisons."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
