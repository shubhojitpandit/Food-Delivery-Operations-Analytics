"""Validate city-level delivery metrics and rankings against SQLite."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "04_city_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "city_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
DIMENSION = "City"
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
COUNT_METRICS = ("delivery_count", "slow_delivery_count")
FLOAT_METRICS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
RANK_METRICS = (
    "fastest_mean_rank",
    "slowest_mean_rank",
    "fastest_median_rank",
    "slowest_median_rank",
    "lowest_slow_rate_rank",
    "highest_slow_rate_rank",
)
RANK_SOURCE_METRICS = {
    "fastest_mean_rank": ("mean_delivery_time", True),
    "slowest_mean_rank": ("mean_delivery_time", False),
    "fastest_median_rank": ("median_delivery_time", True),
    "slowest_median_rank": ("median_delivery_time", False),
    "lowest_slow_rate_rank": ("slow_delivery_rate", True),
    "highest_slow_rate_rank": ("slow_delivery_rate", False),
}


def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest to check read-only behavior."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating point values using the shared analysis tolerance."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Format calculated metrics for display."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format a Markdown table and escape pipes in cells."""
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
    """Compute city metrics independently with Pandas and NumPy linear quantiles."""
    numeric_target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = numeric_target.notna()
    valid = frame.loc[valid_mask, [DIMENSION]].copy()
    valid[TARGET_COLUMN] = numeric_target.loc[valid_mask]
    total_rows = len(frame)
    valid_count = int(valid_mask.sum())
    missing_city_count = int(valid[DIMENSION].isna().sum())
    categorized = valid.loc[valid[DIMENSION].notna()]

    metrics: list[dict[str, object]] = []
    for city, group in categorized.groupby(DIMENSION, sort=True, dropna=True):
        values = group[TARGET_COLUMN].to_numpy(dtype="float64")
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        metrics.append(
            {
                DIMENSION: str(city),
                "delivery_count": len(group),
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(np.percentile(values, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / len(group),
            }
        )
    results = pd.DataFrame(metrics)

    qualifying = results.loc[results["delivery_count"] >= MIN_GROUP_SIZE].copy()
    for rank_name, (metric, ascending) in RANK_SOURCE_METRICS.items():
        qualifying[rank_name] = qualifying[metric].rank(
            method="min",
            ascending=ascending,
        ).astype(int)
    results = results.merge(
        qualifying[[DIMENSION, *RANK_METRICS]],
        on=DIMENSION,
        how="left",
        validate="one_to_one",
    )
    results["sample_size_status"] = np.where(
        results["delivery_count"] >= MIN_GROUP_SIZE,
        "qualifies",
        "small_sample",
    )
    return results, total_rows, valid_count, missing_city_count


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Run the SQL artifact against an in-memory SQLite copy of the input."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        result = pd.read_sql_query(query, connection)
        return result, sqlite3.sqlite_version
    finally:
        connection.close()


def compare_results(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
) -> list[list[object]]:
    """Compare metrics and qualifying-city rank fields category by category."""
    sql_by_city = sql_results.set_index(DIMENSION)
    python_by_city = python_results.set_index(DIMENSION)
    if set(sql_by_city.index) != set(python_by_city.index):
        raise AssertionError("SQL and Python returned different city categories.")

    rows: list[list[object]] = []
    for city in sorted(sql_by_city.index):
        sql_row = sql_by_city.loc[city]
        python_row = python_by_city.loc[city]
        for metric in COUNT_METRICS:
            sql_value = int(sql_row[metric])
            python_value = int(python_row[metric])
            match = sql_value == python_value
            rows.append(
                [
                    city,
                    metric.replace("_", " "),
                    f"{sql_value:,}",
                    f"{python_value:,}",
                    "MATCH" if match else "MISMATCH",
                ]
            )
            if not match:
                raise AssertionError(f"{city} {metric} mismatch: {sql_value} != {python_value}")
        for metric in FLOAT_METRICS:
            sql_value = float(sql_row[metric])
            python_value = float(python_row[metric])
            match = close_enough(sql_value, python_value)
            rows.append(
                [
                    city,
                    metric.replace("_", " "),
                    format_number(sql_value),
                    format_number(python_value),
                    "MATCH" if match else "MISMATCH",
                ]
            )
            if not match:
                raise AssertionError(f"{city} {metric} mismatch: {sql_value} != {python_value}")
        for metric in RANK_METRICS:
            sql_value = sql_row[metric]
            python_value = python_row[metric]
            if pd.isna(sql_value) and pd.isna(python_value):
                match = True
                sql_text = python_text = "not ranked"
            else:
                match = int(sql_value) == int(python_value)
                sql_text = str(int(sql_value))
                python_text = str(int(python_value))
            rows.append(
                [
                    city,
                    metric.replace("_", " "),
                    sql_text,
                    python_text,
                    "MATCH" if match else "MISMATCH",
                ]
            )
            if not match:
                raise AssertionError(f"{city} {metric} differs between SQL and Python.")
    return rows


def ranking_rows(
    frame: pd.DataFrame,
    rank_column: str,
    metric_column: str,
    ascending: bool,
) -> list[list[object]]:
    """List qualifying-city rankings in a metric direction with tied ranks."""
    eligible = frame.loc[frame["delivery_count"] >= MIN_GROUP_SIZE].copy()
    eligible = eligible.sort_values(
        [metric_column, DIMENSION],
        ascending=[ascending, True],
        kind="stable",
    )
    rows = []
    for _, row in eligible.iterrows():
        value = float(row[metric_column])
        if metric_column == "slow_delivery_rate":
            value_text = f"{value * 100:.4f}%"
        else:
            value_text = format_number(value)
        rows.append(
            [
                int(row[rank_column]),
                row[DIMENSION],
                f"{int(row['delivery_count']):,}",
                value_text,
            ]
        )
    return rows


def build_report(
    sql_results: pd.DataFrame,
    validation_rows: list[list[object]],
    total_rows: int,
    valid_targets: int,
    missing_targets: int,
    missing_city: int,
    sqlite_version: str,
    source_hash: str,
) -> str:
    """Create the requested city report using validated SQL results."""
    categorized_count = valid_targets - missing_city
    result_rows = []
    slow_rows = []
    for _, row in sql_results.iterrows():
        count = int(row["delivery_count"])
        status = (
            "Meets minimum; ranked"
            if count >= MIN_GROUP_SIZE
            else "Small sample; not ranked"
        )
        result_rows.append(
            [
                row[DIMENSION],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                status,
            ]
        )
        slow_rows.append(
            [
                row[DIMENSION],
                f"{int(row['slow_delivery_count']):,}",
                f"{count:,}",
                f"{int(row['slow_delivery_count']):,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                status,
            ]
        )

    ranked = sql_results.loc[sql_results["delivery_count"] >= MIN_GROUP_SIZE].copy()
    ranking_specs = [
        ("Fastest cities by mean delivery time", "fastest_mean_rank", "mean_delivery_time", True),
        ("Slowest cities by mean delivery time", "slowest_mean_rank", "mean_delivery_time", False),
        ("Fastest cities by median delivery time", "fastest_median_rank", "median_delivery_time", True),
        ("Slowest cities by median delivery time", "slowest_median_rank", "median_delivery_time", False),
        ("Lowest slow-delivery rate", "lowest_slow_rate_rank", "slow_delivery_rate", True),
        ("Highest slow-delivery rate", "highest_slow_rate_rank", "slow_delivery_rate", False),
    ]

    lines = [
        "# City Analysis",
        "",
        "## Objective",
        "",
        "Describe observed delivery-performance differences among city categories. "
        "All comparisons are descriptive and observational.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only.",
        f"- **Target:** `{TARGET_COLUMN}`; valid records have a non-null numeric target.",
        f"- **Primary dimension:** `{DIMENSION}`.",
        f"- **Fixed slow threshold:** {FIXED_SLOW_THRESHOLD:g} minutes, using strict "
        "`Time_taken(min) > 40`; no city-specific threshold is calculated.",
        "- City values were read from the cleaned file, where the approved "
        "`Metropolitian` → `Metropolitan` standardization has already been applied.",
        "",
        "## City Coverage",
        "",
        f"- Total train rows: **{total_rows:,}**.",
        f"- Total valid targets: **{valid_targets:,}**.",
        f"- Missing/invalid target rows: **{missing_targets:,}**.",
        f"- Valid targets with non-null city: **{categorized_count:,}**.",
        f"- Valid targets excluded from city comparisons because city is missing: "
        f"**{missing_city:,}**.",
        "- Missing city values are not imputed or inferred; those records remain in the "
        "overall valid-target population.",
        "",
        "## Results",
        "",
        "Median and P90 use continuous linear interpolation, rank `1 + (n - 1) × p`, "
        "matching NumPy `percentile(method='linear')`. The minimum city sample for ranking "
        f"or substantive comparison is {MIN_GROUP_SIZE} valid records.",
        "",
        "## City Performance Comparison",
        "",
    ]
    lines.extend(
        markdown_table(
            ["City", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Sample-size status"],
            result_rows,
        )
    )
    for title, rank_column, metric, ascending in ranking_specs:
        lines.extend(["", f"### {title}", ""])
        lines.extend(
            markdown_table(
                [
                    "Rank",
                    "City",
                    "Delivery count",
                    "Slow-delivery rate"
                    if metric == "slow_delivery_rate"
                    else "Value (minutes)",
                ],
                ranking_rows(ranked, rank_column, metric, ascending),
            )
        )
        unit = "%" if metric == "slow_delivery_rate" else "minutes"
        if metric == "slow_delivery_rate":
            lines.append("")
            lines.append("Rates are shown as percentages; ties share a rank.")
        else:
            lines.append("")
            lines.append(f"Values are in {unit}; ties share a rank.")

    lines.extend(
        [
            "",
            "## Slow-Delivery Analysis",
            "",
            f"Every city uses the fixed threshold of strictly greater than "
            f"{FIXED_SLOW_THRESHOLD:g} minutes. Rate = city slow count / all valid "
            "deliveries in that city; the numerator and denominator are shown explicitly.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "City",
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
            "## SQL vs Python Validation",
            "",
            f"SQL from `sql/04_city_analysis.sql` was executed in SQLite `{sqlite_version}` "
            "using an in-memory copy of the cleaned train data. Pandas independently "
            "reproduced the grouped metrics; NumPy used continuous linear interpolation "
            "for medians and P90. Standard SQLite has no built-in `PERCENTILE_CONT`, so "
            "the SQL implements the equivalent row-rank interpolation.",
            "",
            f"Counts and integer ranks must match exactly. Floating metrics use "
            f"`numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and relative "
            f"tolerance `{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["City", "Metric", "SQL", "Python", "Result"],
            validation_rows,
        )
    )
    lines.extend(
        [
            "",
            f"SQL/Python category counts reconcile to {categorized_count:,} valid-target "
            f"rows with city; {missing_city:,} valid-target rows have missing city.",
            "Qualifying-city ranks match for mean, median, and slow-delivery rate in both "
            "directions.",
            "",
            "## Interpretation",
            "",
            "Observed city metrics differ in the displayed summaries and rankings. "
            "Rankings are limited to cities with at least 30 valid records and should be "
            "read alongside delivery counts, mean, median, P90, and slow-delivery rate. "
            "These observed differences do not show that city itself causes delivery "
            "performance differences. No causal explanation is made.",
            "",
            "## Limitations",
            "",
            "- This is an observational, unadjusted city comparison; other dimensions are "
            "not analyzed in this step.",
            "- The 30-record minimum is a reporting guardrail and does not guarantee "
            "statistical precision.",
            "- Missing city records are excluded only from city-category comparisons.",
            "- Slow delivery uses the globally fixed 40-minute threshold; group medians "
            "and P90 values are descriptive city percentiles.",
            "- Results are limited to valid targets in the cleaned training data.",
            "",
            f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is "
            f"`{source_hash}` before and after; no columns were persisted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Execute the SQL and Python city analyses, validate them, and write report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    if TARGET_COLUMN not in frame or DIMENSION not in frame:
        raise ValueError("Cleaned train data is missing a required column.")

    python_results, total_rows, valid_targets, missing_city = calculate_python_metrics(frame)
    missing_targets = total_rows - valid_targets
    sql_query = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(frame, sql_query)
    if sql_results.empty:
        raise AssertionError("SQL returned no city categories.")

    if int(sql_results["total_train_rows"].iloc[0]) != total_rows:
        raise AssertionError("SQL train row count does not match Pandas.")
    if int(sql_results["valid_target_rows"].iloc[0]) != valid_targets:
        raise AssertionError("SQL valid-target count does not match Pandas.")
    if int(sql_results["valid_targets_excluded_for_missing_city"].iloc[0]) != missing_city:
        raise AssertionError("SQL missing-city count does not match Pandas.")
    expected_categorized = valid_targets - missing_city
    if int(sql_results["delivery_count"].sum()) != expected_categorized:
        raise AssertionError("SQL city counts do not reconcile to city-present targets.")
    if int(python_results["delivery_count"].sum()) != expected_categorized:
        raise AssertionError("Python city counts do not reconcile to city-present targets.")

    validation_rows = compare_results(sql_results, python_results)

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("Cleaned training data changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("Cleaned training schema changed during analysis.")

    report = build_report(
        sql_results,
        validation_rows,
        total_rows,
        valid_targets,
        missing_targets,
        missing_city,
        sqlite_version,
        source_hash_before,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(
        f"Validated {len(sql_results)} city categories, {valid_targets:,} valid targets, "
        f"{missing_city:,} missing-city rows, and {len(validation_rows)} metric/rank comparisons."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
