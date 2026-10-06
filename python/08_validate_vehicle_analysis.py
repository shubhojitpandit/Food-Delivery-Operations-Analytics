"""Validate vehicle-type and vehicle-condition metrics against SQLite."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "05_vehicle_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "vehicle_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
DIMENSIONS = ("Type_of_vehicle", "Vehicle_condition")
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
RANK_SPECS = (
    ("fastest_mean_rank", "mean_delivery_time", True),
    ("slowest_mean_rank", "mean_delivery_time", False),
    ("fastest_median_rank", "median_delivery_time", True),
    ("slowest_median_rank", "median_delivery_time", False),
    ("lowest_slow_rate_rank", "slow_delivery_rate", True),
    ("highest_slow_rate_rank", "slow_delivery_rate", False),
)


def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest for read-only source validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating-point values with the tolerance used in previous steps."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Render a numeric result compactly for Markdown."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format a Markdown table and escape cell separators."""
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


def calculate_dimension(frame: pd.DataFrame, dimension: str) -> tuple[pd.DataFrame, int, int, int]:
    """Independently calculate grouped metrics and eligible-category ranks."""
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [dimension]].copy()
    valid[TARGET_COLUMN] = target.loc[valid_mask]
    if dimension == "Vehicle_condition":
        valid[dimension] = valid[dimension].map(
            lambda value: str(int(value)) if pd.notna(value) else pd.NA
        )

    total_rows = len(frame)
    valid_count = int(valid_mask.sum())
    missing_dimension_count = int(valid[dimension].isna().sum())
    categorized = valid.loc[valid[dimension].notna()]
    rows: list[dict[str, object]] = []
    for category, group in categorized.groupby(dimension, sort=True, dropna=True):
        values = group[TARGET_COLUMN].to_numpy(dtype="float64")
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        rows.append(
            {
                "dimension_name": dimension,
                "category": str(category),
                "delivery_count": len(group),
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(np.percentile(values, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / len(group),
            }
        )
    results = pd.DataFrame(rows)

    qualifying = results.loc[results["delivery_count"] >= MIN_GROUP_SIZE].copy()
    for rank_name, metric, ascending in RANK_SPECS:
        qualifying[rank_name] = qualifying[metric].rank(
            method="min",
            ascending=ascending,
        ).astype(int)
    results = results.merge(
        qualifying[["category", *RANK_METRICS]],
        on="category",
        how="left",
        validate="one_to_one",
    )
    results["sample_size_status"] = np.where(
        results["delivery_count"] >= MIN_GROUP_SIZE,
        "qualifies",
        "small_sample",
    )
    return results, total_rows, valid_count, missing_dimension_count


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Execute the SQL file against an in-memory SQLite relation."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        results = pd.read_sql_query(query, connection)
        return results, sqlite3.sqlite_version
    finally:
        connection.close()


def validate_dimension(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
    dimension: str,
) -> list[list[object]]:
    """Compare all category metrics and qualifying ranks for one dimension."""
    sql_dim = sql_results.loc[sql_results["dimension_name"] == dimension].set_index("category")
    python_dim = python_results.set_index("category")
    if set(sql_dim.index) != set(python_dim.index):
        raise AssertionError(f"SQL and Python categories differ for {dimension}.")

    comparisons: list[list[object]] = []
    for category in sorted(sql_dim.index):
        sql_row = sql_dim.loc[category]
        python_row = python_dim.loc[category]
        for metric in COUNT_METRICS:
            sql_value = int(sql_row[metric])
            python_value = int(python_row[metric])
            matched = sql_value == python_value
            comparisons.append(
                [
                    dimension,
                    category,
                    metric.replace("_", " "),
                    f"{sql_value:,}",
                    f"{python_value:,}",
                    "MATCH" if matched else "MISMATCH",
                ]
            )
            if not matched:
                raise AssertionError(f"{dimension} {category} {metric} mismatch.")
        for metric in FLOAT_METRICS:
            sql_value = float(sql_row[metric])
            python_value = float(python_row[metric])
            matched = close_enough(sql_value, python_value)
            comparisons.append(
                [
                    dimension,
                    category,
                    metric.replace("_", " "),
                    format_number(sql_value),
                    format_number(python_value),
                    "MATCH" if matched else "MISMATCH",
                ]
            )
            if not matched:
                raise AssertionError(f"{dimension} {category} {metric} mismatch.")
        for metric in RANK_METRICS:
            sql_value = sql_row[metric]
            python_value = python_row[metric]
            if pd.isna(sql_value) and pd.isna(python_value):
                matched = True
                sql_text = python_text = "not ranked"
            else:
                matched = int(sql_value) == int(python_value)
                sql_text = python_text = ""
                sql_text = str(int(sql_value))
                python_text = str(int(python_value))
            comparisons.append(
                [
                    dimension,
                    category,
                    metric.replace("_", " "),
                    sql_text,
                    python_text,
                    "MATCH" if matched else "MISMATCH",
                ]
            )
            if not matched:
                raise AssertionError(f"{dimension} {category} {metric} differs.")
    return comparisons


def ranking_rows(
    frame: pd.DataFrame,
    metric: str,
    ascending: bool,
    rank_column: str,
) -> list[list[object]]:
    """Create category rankings, limited to groups that meet the sample rule."""
    ranked = frame.loc[frame["delivery_count"] >= MIN_GROUP_SIZE].copy()
    ranked = ranked.sort_values(
        [metric, "category"],
        ascending=[ascending, True],
        kind="stable",
    )
    rows = []
    for _, row in ranked.iterrows():
        value = float(row[metric])
        value_text = f"{value * 100:.4f}%" if metric == "slow_delivery_rate" else format_number(value)
        rows.append(
            [
                int(row[rank_column]),
                row["category"],
                f"{int(row['delivery_count']):,}",
                value_text,
            ]
        )
    return rows


def append_dimension_section(
    lines: list[str],
    title: str,
    dimension: str,
    sql_results: pd.DataFrame,
    missing_count: int,
    valid_count: int,
) -> None:
    """Append one dimension's results, rankings, and slow-rate denominators."""
    subset = sql_results.loc[sql_results["dimension_name"] == dimension].copy()
    categorized_count = valid_count - missing_count
    lines.extend(
        [
            f"## {title}",
            "",
            f"### Results",
            "",
            f"- Valid targets overall: **{valid_count:,}**.",
            f"- Valid targets with non-missing {dimension}: **{categorized_count:,}**.",
            f"- Valid targets excluded because {dimension} is missing: **{missing_count:,}**.",
            "- Missing values are not inferred; the excluded rows remain in the overall target population.",
            "- The dimension is compared as categorical values; no ordinal meaning is imposed.",
            "",
        ]
    )
    result_rows: list[list[object]] = []
    slow_rows: list[list[object]] = []
    for _, row in subset.iterrows():
        count = int(row["delivery_count"])
        status = "Meets minimum; ranked" if count >= MIN_GROUP_SIZE else "Small sample; descriptive only"
        result_rows.append(
            [
                row["category"],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                status,
            ]
        )
        slow_rows.append(
            [
                row["category"],
                f"{int(row['slow_delivery_count']):,}",
                f"{count:,}",
                f"{int(row['slow_delivery_count']):,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                status,
            ]
        )
    lines.extend(
        markdown_table(
            ["Category", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Sample-size status"],
            result_rows,
        )
    )

    lines.extend(["", "### Rankings", ""])
    rank_sets = (
        ("Fastest by mean delivery time", "mean_delivery_time", True, "fastest_mean_rank"),
        ("Slowest by mean delivery time", "mean_delivery_time", False, "slowest_mean_rank"),
        ("Fastest by median delivery time", "median_delivery_time", True, "fastest_median_rank"),
        ("Slowest by median delivery time", "median_delivery_time", False, "slowest_median_rank"),
        ("Lowest slow-delivery rate", "slow_delivery_rate", True, "lowest_slow_rate_rank"),
        ("Highest slow-delivery rate", "slow_delivery_rate", False, "highest_slow_rate_rank"),
    )
    for heading, metric, ascending, rank in rank_sets:
        lines.extend([f"#### {heading}", ""])
        lines.extend(
            markdown_table(
                [
                    "Rank",
                    "Category",
                    "Delivery count",
                    "Slow-delivery rate" if metric == "slow_delivery_rate" else "Value (minutes)",
                ],
                ranking_rows(subset, metric, ascending, rank),
            )
        )
        lines.append("")

    lines.extend(
        [
            "### Slow-Delivery Analysis",
            "",
            "The fixed global threshold is strictly greater than 40 minutes. "
            "Slow-delivery rate = slow deliveries in the group / all valid deliveries in "
            "the group; numerator and denominator are displayed.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Category",
                "Slow count (numerator)",
                "Delivery count (denominator)",
                "Rate calculation",
                "Slow rate",
                "Sample-size status",
            ],
            slow_rows,
        )
    )
    lines.extend(["", f"Category counts sum to {categorized_count:,} valid-target records.", ""])


def main() -> None:
    """Run SQL/Python metrics for both vehicle dimensions and generate the report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET_COLUMN, *DIMENSIONS]
    if any(column not in frame.columns for column in required):
        raise ValueError("A required target or vehicle dimension column is missing.")

    python_results = []
    missing_by_dimension: dict[str, int] = {}
    total_rows = len(frame)
    target_numeric = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_count = int(target_numeric.notna().sum())
    if valid_count == 0:
        raise ValueError("No valid numeric delivery targets were found.")
    for dimension in DIMENSIONS:
        result, py_total, py_valid, missing = calculate_dimension(frame, dimension)
        if py_total != total_rows or py_valid != valid_count:
            raise AssertionError(f"Valid target population differs for {dimension}.")
        if int(result["delivery_count"].sum()) != valid_count - missing:
            raise AssertionError(f"Python category counts do not reconcile for {dimension}.")
        python_results.append(result)
        missing_by_dimension[dimension] = missing
    python_all = pd.concat(python_results, ignore_index=True)

    query = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(frame, query)
    if sql_results.empty:
        raise AssertionError("The SQL query returned no grouped vehicle metrics.")

    all_comparisons: list[list[object]] = []
    for dimension in DIMENSIONS:
        sql_subset = sql_results.loc[sql_results["dimension_name"] == dimension]
        py_subset = python_all.loc[python_all["dimension_name"] == dimension]
        if int(sql_subset["total_train_rows"].iloc[0]) != total_rows:
            raise AssertionError(f"SQL total row count differs for {dimension}.")
        if int(sql_subset["valid_target_rows"].iloc[0]) != valid_count:
            raise AssertionError(f"SQL valid target count differs for {dimension}.")
        if int(sql_subset["valid_targets_excluded_for_missing_dimension"].iloc[0]) != missing_by_dimension[dimension]:
            raise AssertionError(f"SQL missing dimension count differs for {dimension}.")
        if int(sql_subset["delivery_count"].sum()) != valid_count - missing_by_dimension[dimension]:
            raise AssertionError(f"SQL group counts do not reconcile for {dimension}.")
        all_comparisons.extend(validate_dimension(sql_results, py_subset, dimension))

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned dataset schema changed during analysis.")

    lines = [
        "# Vehicle Analysis",
        "",
        "## Objective",
        "",
        "Describe observed delivery-performance differences across vehicle type and "
        "vehicle condition as two separate dimensions. No causal interpretation is made.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only.",
        f"- **Target:** `{TARGET_COLUMN}`, included only when non-null and numeric.",
        "- **Dimensions:** `Type_of_vehicle` and `Vehicle_condition`, analyzed separately.",
        "- **Slow threshold:** fixed at 40 minutes from Step 5.1; a slow delivery is "
        "strictly `Time_taken(min) > 40`. No dimension-specific threshold was calculated.",
        "- Continuous linear interpolation was used for median and P90: rank "
        "`1 + (n - 1) × p`.",
        f"- At least {MIN_GROUP_SIZE} valid deliveries are required for rankings or "
        "substantive comparisons; smaller groups, if any, are descriptive only.",
        "",
        f"Total train rows: **{total_rows:,}**; valid numeric targets: **{valid_count:,}**; "
        f"missing/invalid target rows: **{total_rows - valid_count:,}**.",
        "",
    ]
    append_dimension_section(
        lines,
        "Vehicle Type Analysis",
        "Type_of_vehicle",
        sql_results,
        missing_by_dimension["Type_of_vehicle"],
        valid_count,
    )
    append_dimension_section(
        lines,
        "Vehicle Condition Analysis",
        "Vehicle_condition",
        sql_results,
        missing_by_dimension["Vehicle_condition"],
        valid_count,
    )
    lines.extend(
        [
            "## SQL vs Python Validation",
            "",
            f"SQL was executed from `sql/05_vehicle_analysis.sql` against an in-memory "
            f"SQLite table (version `{sqlite_version}`). Python independently grouped "
            "each dimension with Pandas and calculated median/P90 using NumPy's "
            "`percentile(method='linear')`. Standard SQLite does not provide built-in "
            "`PERCENTILE_CONT`; the SQL implements the same continuous rank interpolation.",
            "",
            f"Counts and qualifying-group rankings must match exactly. Floating-point "
            f"metrics use `numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` "
            f"and relative tolerance `{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Dimension", "Category", "Metric", "SQL", "Python", "Result"],
            all_comparisons,
        )
    )
    lines.extend(
        [
            "",
            "Both dimension-specific category counts reconcile to their valid target rows "
            "after only the relevant missing dimension values are excluded. Ranking "
            "consistency was checked for mean, median, and slow-delivery rate in both "
            "directions; groups below the minimum are not ranked.",
            "",
            "## Interpretation",
            "",
            "The reported metrics and rankings describe observed associations for vehicle "
            "type and vehicle condition separately. All rankings are accompanied by "
            "delivery counts and distribution metrics. They do not establish that vehicle "
            "type or vehicle condition causes faster or slower delivery. Vehicle condition "
            "is treated as categorical; no ordered or causal meaning is assigned to its "
            "numeric labels.",
            "",
            "## Limitations",
            "",
            "- This is an observational, unadjusted comparison; other dimensions are not "
            "analyzed here.",
            "- The 30-record rule is a reporting guardrail, not a guarantee of statistical "
            "precision.",
            "- Missing vehicle type and missing vehicle condition are excluded separately "
            "from their own group comparisons and are not inferred.",
            "- Group P90 is descriptive; slow-delivery classification uses the fixed "
            "global threshold of > 40 minutes.",
            "- Findings are limited to valid targets in the cleaned training data.",
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
        f"Validated {len(DIMENSIONS)} dimensions and {len(all_comparisons)} "
        f"SQL/Python metric and ranking comparisons."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
