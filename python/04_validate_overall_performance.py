"""Validate overall cleaned delivery-time metrics against the SQLite query."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "01_overall_delivery_performance.sql"
REPORT_PATH = ROOT / "outputs" / "overall_delivery_performance.md"
SOURCE_PATHS = {
    "data/raw/train.csv": ROOT / "data" / "raw" / "train.csv",
    "data/raw/test.csv": ROOT / "data" / "raw" / "test.csv",
    "data/raw/Sample_Submission.csv": ROOT / "data" / "raw" / "Sample_Submission.csv",
    "data/processed/train_clean.csv": TRAIN_PATH,
    "data/processed/test_clean.csv": ROOT / "data" / "processed" / "test_clean.csv",
}
TARGET_COLUMN = "Time_taken(min)"
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12


def sha256_file(path: Path) -> str:
    """Calculate a streaming SHA-256 digest for a non-modification check."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating-point results using documented absolute/relative tolerance."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float | int, decimals: int = 10) -> str:
    """Format a metric without hiding the unrounded value used for validation."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Build a small readable Markdown table."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", r"\|").replace("\n", " ") for value in row) + " |"
        for row in rows
    )
    return lines


def calculate_python_metrics(frame: pd.DataFrame) -> tuple[pd.Series, dict[str, float | int]]:
    """Compute valid-target metrics independently with NumPy linear quantiles."""
    numeric_target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_target = numeric_target[numeric_target.notna()].astype("float64")
    if valid_target.empty:
        raise ValueError("No valid numeric delivery targets were found.")

    values = valid_target.to_numpy()
    p90 = float(np.percentile(values, 90, method="linear"))
    slow_count = int((valid_target > p90).sum())
    metrics: dict[str, float | int] = {
        "total_train_rows": len(frame),
        "valid_target_rows": len(valid_target),
        "missing_or_invalid_target_rows": len(frame) - len(valid_target),
        "valid_target_percentage": 100.0 * len(valid_target) / len(frame),
        "valid_record_count": len(valid_target),
        "mean_delivery_time": float(valid_target.mean()),
        "median_delivery_time": float(np.percentile(values, 50, method="linear")),
        "p75_delivery_time": float(np.percentile(values, 75, method="linear")),
        "p90_delivery_time": p90,
        "minimum_delivery_time": float(valid_target.min()),
        "maximum_delivery_time": float(valid_target.max()),
        "slow_delivery_count": slow_count,
        "slow_delivery_rate": slow_count / len(valid_target),
    }
    return valid_target, metrics


def run_sql(frame: pd.DataFrame, query: str) -> tuple[dict[str, object], str]:
    """Load the cleaned CSV into in-memory SQLite and execute the SQL artifact."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        cursor = connection.execute(query)
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("The SQL query returned no result row.")
        sql_metrics = dict(zip((item[0] for item in cursor.description), row))
        sqlite_version = sqlite3.sqlite_version
        return sql_metrics, sqlite_version
    finally:
        connection.close()


def create_report(
    frame: pd.DataFrame,
    valid_target: pd.Series,
    python_metrics: dict[str, float | int],
    sql_metrics: dict[str, object],
    sqlite_version: str,
    checks: list[str],
    source_hashes_before: dict[str, str],
    source_hashes_after: dict[str, str],
) -> str:
    """Render the requested baseline report from executed SQL/Python results."""
    threshold = float(python_metrics["p90_delivery_time"])
    frequency = valid_target.value_counts().sort_index()
    max_frequency = int(frequency.max())
    modes = [value for value, count in frequency.items() if int(count) == max_frequency]
    distribution_rows = [
        [format_number(float(value)), int(count)]
        for value, count in frequency.items()
    ]
    percentile_rows = [
        [label, format_number(float(np.percentile(valid_target, quantile * 100, method="linear")))]
        for label, quantile in (
            ("P25", 0.25),
            ("P50 / median", 0.50),
            ("P75", 0.75),
            ("P90", 0.90),
            ("P95", 0.95),
        )
    ]

    lines = [
        "# Overall Delivery Performance",
        "",
        "## Objective",
        "",
        "Establish the baseline delivery-time distribution before examining any "
        "explanatory dimensions. This report contains descriptive metrics only.",
        "",
        "## Input Data",
        "",
        f"- **Source dataset:** `data/processed/train_clean.csv`.",
        f"- **Rows read:** {len(frame):,}.",
        f"- **Target column:** `{TARGET_COLUMN}`.",
        "- `test_clean.csv` was not used for target performance metrics.",
        "- No source dataset was modified and no derived columns were persisted.",
        "",
        "## Valid Target Population",
        "",
        "The rule is to include only rows where the target is non-null and numeric. "
        "The cleaned target was independently parsed with `pandas.to_numeric(errors='coerce')`; "
        "the SQL relation used the numeric target column and filtered to SQLite integer/real "
        "types. Invalid or missing target rows are excluded from all delivery metrics.",
        "",
    ]
    population_rows = [
        ["Total train rows", f"{int(python_metrics['total_train_rows']):,}"],
        ["Valid numeric target rows", f"{int(python_metrics['valid_target_rows']):,}"],
        ["Missing/invalid target rows", f"{int(python_metrics['missing_or_invalid_target_rows']):,}"],
        [
            "Valid target percentage",
            f"{float(python_metrics['valid_target_percentage']):.6f}%",
        ],
    ]
    lines.extend(markdown_table(["Population measure", "Value"], population_rows))

    lines.extend(
        [
            "",
            "## Core Metrics",
            "",
            "All delivery-time values are in minutes. Percentiles use **continuous linear "
            "interpolation** with 1-based rank `1 + (n - 1) × p`, equivalent to NumPy "
            "`percentile(method='linear')`.",
            "",
        ]
    )
    metric_labels = [
        ("Valid record count", "valid_record_count", "count"),
        ("Mean delivery time", "mean_delivery_time", "minutes"),
        ("Median delivery time", "median_delivery_time", "minutes"),
        ("P75", "p75_delivery_time", "minutes"),
        ("P90", "p90_delivery_time", "minutes"),
        ("Minimum delivery time", "minimum_delivery_time", "minutes"),
        ("Maximum delivery time", "maximum_delivery_time", "minutes"),
    ]
    lines.extend(
        markdown_table(
            ["Metric", "Value", "Unit"],
            [
                [
                    label,
                    f"{int(python_metrics[key]):,}"
                    if unit == "count"
                    else format_number(float(python_metrics[key])),
                    unit,
                ]
                for label, key, unit in metric_labels
            ],
        )
    )

    slow_count = int(python_metrics["slow_delivery_count"])
    valid_count = int(python_metrics["valid_record_count"])
    slow_rate = float(python_metrics["slow_delivery_rate"])
    lines.extend(
        [
            "",
            "## Slow-Delivery Threshold",
            "",
            f"- **Fixed threshold:** P90 = **{format_number(threshold)} minutes** from "
            "the complete valid training-target population.",
            "- **Classification rule:** slow when `Time_taken(min) > P90` (strictly greater; "
            "ties at P90 are not slow). No subgroup-specific threshold is used.",
            f"- **Slow numerator:** {slow_count:,}.",
            f"- **Denominator:** {valid_count:,} valid target records.",
            f"- **Slow-delivery rate:** {slow_count:,} / {valid_count:,} = "
            f"{slow_rate:.6%} ({slow_rate * 100:.4f}%).",
            "",
            "## Distribution Observations",
            "",
            "### Percentile points",
            "",
        ]
    )
    lines.extend(markdown_table(["Point", "Delivery time (minutes)"], percentile_rows))
    lines.extend(
        [
            "",
            f"- **Distinct observed delivery-time values:** {len(frequency):,}.",
            f"- **Most frequent observed value(s):** "
            f"{', '.join(format_number(float(value)) for value in modes)} minutes "
            f"({max_frequency:,} records each).",
            "- **Frequency by exact delivery-time value:**",
            "",
        ]
    )
    lines.extend(markdown_table(["Delivery time (minutes)", "Record count"], distribution_rows))
    lines.extend(
        [
            "",
            "These are descriptive properties of the cleaned target distribution; no "
            "distributional cause or business explanation is inferred.",
            "",
            "## SQL vs Python Validation",
            "",
            "SQL was executed from `sql/01_overall_delivery_performance.sql` against a "
            "temporary in-memory SQLite table loaded from the cleaned training CSV. Python "
            "independently calculated target metrics with NumPy's linear percentile method. "
            f"SQLite version: `{sqlite_version}`. Standard SQLite lacks built-in "
            "`PERCENTILE_CONT`; the SQL query implements the equivalent continuous linear "
            "interpolation over row-numbered target values.",
            "",
            "Floating-point metrics match when absolute error is at most "
            f"`{ABSOLUTE_TOLERANCE:g}` or relative error is at most `{RELATIVE_TOLERANCE:g}` "
            "(NumPy `isclose` criterion). Counts must match exactly.",
            "",
        ]
    )
    compare_keys = [
        "total_train_rows",
        "valid_target_rows",
        "missing_or_invalid_target_rows",
        "valid_target_percentage",
        "valid_record_count",
        "mean_delivery_time",
        "median_delivery_time",
        "p75_delivery_time",
        "p90_delivery_time",
        "minimum_delivery_time",
        "maximum_delivery_time",
        "slow_delivery_count",
        "slow_delivery_rate",
    ]
    comparison_rows = []
    for key in compare_keys:
        sql_value = sql_metrics[key]
        python_value = python_metrics[key]
        if key in {
            "total_train_rows",
            "valid_target_rows",
            "missing_or_invalid_target_rows",
            "valid_record_count",
            "slow_delivery_count",
        }:
            sql_text = f"{int(sql_value):,}"
            python_text = f"{int(python_value):,}"
            match = int(sql_value) == int(python_value)
        else:
            sql_text = format_number(float(sql_value))
            python_text = format_number(float(python_value))
            match = close_enough(float(sql_value), float(python_value))
        comparison_rows.append([key.replace("_", " "), sql_text, python_text, "MATCH" if match else "MISMATCH"])
    lines.extend(
        markdown_table(
            ["Metric", "SQL", "Python", "Result"],
            comparison_rows,
        )
    )
    lines.extend(["", "Validation checks:", ""])
    lines.extend(f"- {check}" for check in checks)
    lines.extend(["", "### Source file integrity", ""])
    lines.extend(
        markdown_table(
            ["File", "SHA-256 before", "SHA-256 after", "Unchanged"],
            [
                [
                    filename,
                    f"`{source_hashes_before[filename]}`",
                    f"`{source_hashes_after[filename]}`",
                    "Yes"
                    if source_hashes_before[filename] == source_hashes_after[filename]
                    else "No",
                ]
                for filename in source_hashes_before
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The cleaned training set contains {valid_count:,} valid delivery-time records. "
            f"The observed delivery times range from "
            f"{format_number(float(python_metrics['minimum_delivery_time']))} to "
            f"{format_number(float(python_metrics['maximum_delivery_time']))} minutes; "
            f"the mean is {format_number(float(python_metrics['mean_delivery_time']))}, "
            f"the median is {format_number(float(python_metrics['median_delivery_time']))}, "
            f"and P90 is {format_number(threshold)} minutes. Under the predefined strict "
            f"`>` rule, {slow_count:,} of {valid_count:,} records "
            f"({slow_rate * 100:.4f}%) are classified as slow. These statements describe "
            "the computed target distribution only.",
            "",
            "## Limitations",
            "",
            "- The target population is limited to valid observed target values in the "
            "cleaned training file; it does not include test records.",
            "- The P90 threshold is distribution-defined for this training population and "
            "depends on the specified continuous linear percentile convention.",
            "- SQLite percentile results are computed by the documented row-rank "
            "interpolation because standard SQLite does not supply `PERCENTILE_CONT`.",
            "- This baseline is descriptive and observational. It does not explain the "
            "observed values or establish causes.",
            "- No explanatory dimensions or business recommendations are included.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Run SQL and Python calculations, validate equivalence, and write the report."""
    source_hashes_before = {
        filename: sha256_file(path) for filename, path in SOURCE_PATHS.items()
    }
    frame = pd.read_csv(TRAIN_PATH)
    train_headers_before = frame.columns.tolist()
    if TARGET_COLUMN not in frame.columns:
        raise ValueError(f"Required target column is missing: {TARGET_COLUMN}")

    valid_target, python_metrics = calculate_python_metrics(frame)
    query = SQL_PATH.read_text(encoding="utf-8")
    sql_metrics, sqlite_version = run_sql(frame, query)

    checks: list[str] = []
    for key, label in (
        ("total_train_rows", "Total train rows"),
        ("valid_target_rows", "Valid target rows"),
        ("missing_or_invalid_target_rows", "Missing/invalid target rows"),
        ("valid_record_count", "Valid metric record count"),
        ("slow_delivery_count", "Slow-delivery count"),
    ):
        if int(sql_metrics[key]) != int(python_metrics[key]):
            raise AssertionError(
                f"{label} mismatch: SQL={sql_metrics[key]}, Python={python_metrics[key]}"
            )
        checks.append(f"{label} reconciles exactly at {int(python_metrics[key]):,}.")

    for key in (
        "valid_target_percentage",
        "mean_delivery_time",
        "median_delivery_time",
        "p75_delivery_time",
        "p90_delivery_time",
        "minimum_delivery_time",
        "maximum_delivery_time",
        "slow_delivery_rate",
    ):
        if not close_enough(float(sql_metrics[key]), float(python_metrics[key])):
            raise AssertionError(
                f"Metric mismatch for {key}: SQL={sql_metrics[key]}, Python={python_metrics[key]}"
            )
    checks.append(
        "All floating-point metrics match within absolute tolerance "
        f"{ABSOLUTE_TOLERANCE:g} or relative tolerance {RELATIVE_TOLERANCE:g}."
    )
    checks.append(
        "The slow count uses the overall P90 and strict greater-than comparison; "
        "ties at P90 are excluded."
    )

    source_hashes_after = {
        filename: sha256_file(path) for filename, path in SOURCE_PATHS.items()
    }
    changed_files = [
        filename
        for filename, before_hash in source_hashes_before.items()
        if before_hash != source_hashes_after[filename]
    ]
    if changed_files:
        raise AssertionError(f"Source files changed during analysis: {changed_files}")
    checks.append("SHA-256 checks confirm all raw and processed source files are unchanged.")

    train_headers_after = pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist()
    if train_headers_after != train_headers_before:
        raise AssertionError("Analysis unexpectedly changed the cleaned training schema.")
    checks.append("The cleaned training schema is unchanged; no derived columns were persisted.")

    report = create_report(
        frame,
        valid_target,
        python_metrics,
        sql_metrics,
        sqlite_version,
        checks,
        source_hashes_before,
        source_hashes_after,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"SQLite {sqlite_version}: {int(sql_metrics['valid_target_rows']):,} valid rows.")
    print(
        f"P90={float(sql_metrics['p90_delivery_time']):.10f}; "
        f"slow={int(sql_metrics['slow_delivery_count']):,}/"
        f"{int(sql_metrics['valid_target_rows']):,}."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
