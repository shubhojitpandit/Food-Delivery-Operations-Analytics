"""Validate traffic x multiple-delivery descriptive analysis against SQLite."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "09_traffic_multiple_delivery_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "traffic_multiple_delivery_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
TRAFFIC_COLUMN = "Road_traffic_density"
MULTIPLE_COLUMN = "multiple_deliveries"
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
COMBINATION_COUNT_METRICS = ("delivery_count", "slow_delivery_count")
COMBINATION_FLOAT_METRICS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
RANK_COLUMNS = (
    "mean_rank_within_traffic",
    "slowest_mean_rank_within_traffic",
    "slow_rate_rank_within_traffic",
    "highest_slow_rate_rank_within_traffic",
    "mean_rank_within_multiple",
    "slowest_mean_rank_within_multiple",
    "slow_rate_rank_within_multiple",
    "highest_slow_rate_rank_within_multiple",
)
STANDALONE_METRICS = (
    "standalone_traffic_count",
    "standalone_traffic_mean",
    "standalone_traffic_slow_count",
    "standalone_traffic_slow_rate",
    "standalone_multiple_count",
    "standalone_multiple_mean",
    "standalone_multiple_slow_count",
    "standalone_multiple_slow_rate",
)
TRAFFIC_RANK_SPECS = (
    ("mean_rank_within_traffic", "mean_delivery_time", True),
    ("slowest_mean_rank_within_traffic", "mean_delivery_time", False),
    ("slow_rate_rank_within_traffic", "slow_delivery_rate", True),
    ("highest_slow_rate_rank_within_traffic", "slow_delivery_rate", False),
)
MULTIPLE_RANK_SPECS = (
    ("mean_rank_within_multiple", "mean_delivery_time", True),
    ("slowest_mean_rank_within_multiple", "mean_delivery_time", False),
    ("slow_rate_rank_within_multiple", "slow_delivery_rate", True),
    ("highest_slow_rate_rank_within_multiple", "slow_delivery_rate", False),
)


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for source-integrity validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floats using the tolerance established in prior steps."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Render numbers compactly for Markdown."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def category_text(value: object) -> str:
    """Format numeric category labels as SQLite printf('%g') does."""
    return format(float(value), "g")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Build Markdown tables with escaped separators."""
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


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Execute the SQL artifact against an in-memory SQLite table."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        result = pd.read_sql_query(query, connection)
        return result, sqlite3.sqlite_version
    finally:
        connection.close()


def rank_within(
    frame: pd.DataFrame,
    partition_column: str,
    metric: str,
    ascending: bool,
) -> pd.Series:
    """Return SQL RANK-equivalent ranks, leaving subminimum groups unranked."""
    eligible = frame.loc[frame["delivery_count"] >= MIN_GROUP_SIZE].copy()
    ranks = pd.Series(np.nan, index=frame.index, dtype="float64")
    ranks.loc[eligible.index] = eligible.groupby(partition_column)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return ranks


def calculate_python_results(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Independently calculate combo/standalone metrics and within-axis ranks."""
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [TRAFFIC_COLUMN, MULTIPLE_COLUMN]].copy()
    valid[TARGET_COLUMN] = target.loc[valid_mask].astype("float64")
    valid[MULTIPLE_COLUMN] = pd.to_numeric(
        valid[MULTIPLE_COLUMN],
        errors="coerce",
    )

    missing_traffic = int(valid[TRAFFIC_COLUMN].isna().sum())
    missing_multiple = int(valid[MULTIPLE_COLUMN].isna().sum())
    missing_either = int(
        (valid[TRAFFIC_COLUMN].isna() | valid[MULTIPLE_COLUMN].isna()).sum()
    )
    categorized = valid.dropna(subset=[TRAFFIC_COLUMN, MULTIPLE_COLUMN]).copy()
    categorized["multiple_deliveries_category"] = categorized[
        MULTIPLE_COLUMN
    ].map(category_text)
    categorized["slow"] = categorized[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD

    combo_rows: list[dict[str, object]] = []
    for (traffic, multiple), group in categorized.groupby(
        [TRAFFIC_COLUMN, "multiple_deliveries_category"],
        sort=True,
        dropna=True,
    ):
        values = group[TARGET_COLUMN].to_numpy(dtype="float64")
        count = len(group)
        slow_count = int(group["slow"].sum())
        combo_rows.append(
            {
                "traffic_category": str(traffic),
                "multiple_deliveries_category": str(multiple),
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
    combinations = pd.DataFrame(combo_rows)

    for rank_column, metric, ascending in TRAFFIC_RANK_SPECS:
        combinations[rank_column] = rank_within(
            combinations,
            "traffic_category",
            metric,
            ascending,
        )
    for rank_column, metric, ascending in MULTIPLE_RANK_SPECS:
        combinations[rank_column] = rank_within(
            combinations,
            "multiple_deliveries_category",
            metric,
            ascending,
        )

    standalone_rows: list[dict[str, object]] = []
    for category, group in valid.dropna(subset=[TRAFFIC_COLUMN]).groupby(
        TRAFFIC_COLUMN,
        sort=True,
    ):
        count = len(group)
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        standalone_rows.append(
            {
                "dimension": "traffic",
                "category": str(category),
                "standalone_count": count,
                "standalone_mean": float(group[TARGET_COLUMN].mean()),
                "standalone_slow_count": slow_count,
                "standalone_slow_rate": slow_count / count,
            }
        )
    standalone_multiple_valid = valid.dropna(subset=[MULTIPLE_COLUMN]).copy()
    standalone_multiple_valid["multiple_deliveries_category"] = (
        standalone_multiple_valid[MULTIPLE_COLUMN].map(category_text)
    )
    for category, group in standalone_multiple_valid.groupby(
        "multiple_deliveries_category", sort=True
    ):
        count = len(group)
        slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
        standalone_rows.append(
            {
                "dimension": "multiple",
                "category": str(category),
                "standalone_count": count,
                "standalone_mean": float(group[TARGET_COLUMN].mean()),
                "standalone_slow_count": slow_count,
                "standalone_slow_rate": slow_count / count,
            }
        )
    standalone = pd.DataFrame(standalone_rows)

    traffic_standalone = standalone.loc[
        standalone["dimension"] == "traffic"
    ].set_index("category")
    multiple_standalone = standalone.loc[
        standalone["dimension"] == "multiple"
    ].set_index("category")
    combinations["standalone_traffic_count"] = combinations[
        "traffic_category"
    ].map(traffic_standalone["standalone_count"])
    combinations["standalone_traffic_mean"] = combinations[
        "traffic_category"
    ].map(traffic_standalone["standalone_mean"])
    combinations["standalone_traffic_slow_count"] = combinations[
        "traffic_category"
    ].map(traffic_standalone["standalone_slow_count"])
    combinations["standalone_traffic_slow_rate"] = combinations[
        "traffic_category"
    ].map(traffic_standalone["standalone_slow_rate"])
    combinations["standalone_multiple_count"] = combinations[
        "multiple_deliveries_category"
    ].map(multiple_standalone["standalone_count"])
    combinations["standalone_multiple_mean"] = combinations[
        "multiple_deliveries_category"
    ].map(multiple_standalone["standalone_mean"])
    combinations["standalone_multiple_slow_count"] = combinations[
        "multiple_deliveries_category"
    ].map(multiple_standalone["standalone_slow_count"])
    combinations["standalone_multiple_slow_rate"] = combinations[
        "multiple_deliveries_category"
    ].map(multiple_standalone["standalone_slow_rate"])

    all_slow_count = int((valid[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
    excluded_slow_count = int(
        (
            (valid[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD)
            & (valid[TRAFFIC_COLUMN].isna() | valid[MULTIPLE_COLUMN].isna())
        ).sum()
    )
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "missing_traffic_count": missing_traffic,
        "missing_multiple_count": missing_multiple,
        "excluded_for_missing_either_count": missing_either,
        "all_slow_delivery_count": all_slow_count,
        "excluded_slow_delivery_count": excluded_slow_count,
        "eligible_combination_population": int(len(categorized)),
    }
    return combinations, standalone.reset_index(drop=True), metadata


def validate_results(
    sql: pd.DataFrame,
    python: pd.DataFrame,
    metadata: dict[str, int],
) -> tuple[int, int]:
    """Compare all combination metrics, ranks, standalone metrics, and population."""
    sql_indexed = sql.set_index(
        ["traffic_category", "multiple_deliveries_category"]
    ).sort_index()
    python_indexed = python.set_index(
        ["traffic_category", "multiple_deliveries_category"]
    ).sort_index()
    if not sql_indexed.index.equals(python_indexed.index):
        raise AssertionError("SQL and Python traffic-delivery combinations differ.")

    metric_checks = rank_checks = 0
    for key in sql_indexed.index:
        sql_row = sql_indexed.loc[key]
        python_row = python_indexed.loc[key]
        for field in COMBINATION_COUNT_METRICS:
            if int(sql_row[field]) != int(python_row[field]):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        for field in COMBINATION_FLOAT_METRICS:
            if not close_enough(float(sql_row[field]), float(python_row[field])):
                raise AssertionError(
                    f"{key} {field} differs: {sql_row[field]} vs {python_row[field]}."
                )
            metric_checks += 1
        if str(sql_row["sample_size_status"]) != str(
            python_row["sample_size_status"]
        ):
            raise AssertionError(f"{key} sample-size status differs.")
        for field in RANK_COLUMNS:
            left = sql_row[field]
            right = python_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or int(left) != int(right):
                raise AssertionError(f"{key} {field} differs.")
            rank_checks += 1
        for field in STANDALONE_METRICS:
            left = sql_row[field]
            right = python_row[field]
            if field.endswith("_count"):
                if int(left) != int(right):
                    raise AssertionError(f"{key} standalone {field} differs.")
            elif not close_enough(float(left), float(right)):
                raise AssertionError(f"{key} standalone {field} differs.")
            metric_checks += 1

    sql_metadata_row = sql.iloc[0]
    for field, expected in metadata.items():
        if int(sql_metadata_row[field]) != expected:
            raise AssertionError(
                f"SQL and Python population metadata differ for {field}."
            )
        metric_checks += 1
    return metric_checks, rank_checks


def sorted_categories(frame: pd.DataFrame, column: str) -> list[str]:
    """Sort labels as numeric categories without making them continuous metrics."""
    return sorted(frame[column].astype(str).unique(), key=float)


def extreme_description(
    subset: pd.DataFrame,
    metric: str,
    category_column: str,
    lowest: bool,
) -> str:
    """Format all tied extreme categories with their sample counts."""
    extreme_value = subset[metric].min() if lowest else subset[metric].max()
    tied = subset.loc[
        np.isclose(
            subset[metric].astype(float),
            float(extreme_value),
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    ]
    descriptions = []
    for _, row in tied.iterrows():
        value = float(row[metric])
        value_text = (
            f"{value * 100:.4f}%"
            if metric == "slow_delivery_rate"
            else f"{format_number(value)} min"
        )
        descriptions.append(
            f"{row[category_column]} ({int(row['delivery_count']):,}; {value_text})"
        )
    return "; ".join(descriptions)


def format_qualifying_combinations(rows: pd.DataFrame) -> list[list[object]]:
    """Render every two-way cell with explicit slow numerator/denominator."""
    output = []
    for _, row in rows.sort_values(
        ["traffic_category", "multiple_deliveries_category"],
        key=lambda series: series.map(float)
        if series.name == "multiple_deliveries_category"
        else series,
    ).iterrows():
        count = int(row["delivery_count"])
        slow = int(row["slow_delivery_count"])
        output.append(
            [
                row["traffic_category"],
                row["multiple_deliveries_category"],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                f"{slow:,}",
                f"{slow:,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                "Qualifies" if count >= MIN_GROUP_SIZE else "Small sample; descriptive only",
            ]
        )
    return output


def main() -> None:
    """Run two-way SQL/Pandas validation and generate the report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET_COLUMN, TRAFFIC_COLUMN, MULTIPLE_COLUMN]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required analysis columns are missing: {missing_columns}")

    python_groups, python_standalone, python_metadata = calculate_python_results(frame)
    query = SQL_PATH.read_text(encoding="utf-8")
    sql_groups, sqlite_version = run_sql(frame, query)
    if sql_groups.empty:
        raise AssertionError("SQL returned no traffic x multiple-delivery groups.")

    metric_checks, rank_checks = validate_results(
        sql_groups,
        python_groups,
        python_metadata,
    )
    if int(sql_groups["delivery_count"].sum()) != python_metadata[
        "eligible_combination_population"
    ]:
        raise AssertionError("Combination counts do not reconcile to the eligible population.")
    if int(sql_groups["slow_delivery_count"].sum()) + python_metadata[
        "excluded_slow_delivery_count"
    ] != python_metadata["all_slow_delivery_count"]:
        raise AssertionError("Slow delivery contribution does not reconcile.")

    traffic_categories = sorted(sql_groups["traffic_category"].unique())
    multiple_categories = sorted_categories(
        sql_groups,
        "multiple_deliveries_category",
    )
    qualifying = sql_groups.loc[
        sql_groups["delivery_count"] >= MIN_GROUP_SIZE
    ].copy()
    qualifying["multiple_order"] = qualifying[
        "multiple_deliveries_category"
    ].map(float)

    traffic_extremes_rows = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        if subset.empty:
            traffic_extremes_rows.append(
                [traffic, "No qualifying categories", "No qualifying categories",
                 "No qualifying categories", "No qualifying categories"]
            )
            continue
        traffic_extremes_rows.append(
            [
                traffic,
                extreme_description(
                    subset,
                    "mean_delivery_time",
                    "multiple_deliveries_category",
                    lowest=True,
                ),
                extreme_description(
                    subset,
                    "mean_delivery_time",
                    "multiple_deliveries_category",
                    lowest=False,
                ),
                extreme_description(
                    subset,
                    "slow_delivery_rate",
                    "multiple_deliveries_category",
                    lowest=True,
                ),
                extreme_description(
                    subset,
                    "slow_delivery_rate",
                    "multiple_deliveries_category",
                    lowest=False,
                ),
            ]
        )

    multiple_extremes_rows = []
    for multiple in multiple_categories:
        subset = qualifying.loc[
            qualifying["multiple_deliveries_category"] == multiple
        ]
        if subset.empty:
            multiple_extremes_rows.append(
                [multiple, "No qualifying traffic categories",
                 "No qualifying traffic categories", "No qualifying traffic categories",
                 "No qualifying traffic categories"]
            )
            continue
        multiple_extremes_rows.append(
            [
                multiple,
                extreme_description(
                    subset, "mean_delivery_time", "traffic_category", lowest=True
                ),
                extreme_description(
                    subset, "mean_delivery_time", "traffic_category", lowest=False
                ),
                extreme_description(
                    subset, "slow_delivery_rate", "traffic_category", lowest=True
                ),
                extreme_description(
                    subset, "slow_delivery_rate", "traffic_category", lowest=False
                ),
            ]
        )

    # Check whether category-label ordering is monotonic within each traffic stratum.
    multiple_pattern_rows: list[list[object]] = []
    multiple_pattern_counts = {"mean_increasing": 0, "rate_increasing": 0, "strata_testable": 0}
    for traffic in traffic_categories:
        subset = qualifying.loc[
            qualifying["traffic_category"] == traffic
        ].sort_values("multiple_order")
        if len(subset) < 2:
            multiple_pattern_rows.append(
                [traffic, len(subset), "Insufficient qualifying category pairs"]
            )
            continue
        multiple_pattern_counts["strata_testable"] += 1
        mean_diffs = np.diff(subset["mean_delivery_time"].to_numpy())
        rate_diffs = np.diff(subset["slow_delivery_rate"].to_numpy())
        mean_direction = (
            "increasing" if np.all(mean_diffs > 0)
            else "decreasing" if np.all(mean_diffs < 0)
            else "mixed / ties"
        )
        rate_direction = (
            "increasing" if np.all(rate_diffs > 0)
            else "decreasing" if np.all(rate_diffs < 0)
            else "mixed / ties"
        )
        if mean_direction == "increasing":
            multiple_pattern_counts["mean_increasing"] += 1
        if rate_direction == "increasing":
            multiple_pattern_counts["rate_increasing"] += 1
        multiple_pattern_rows.append(
            [
                traffic,
                len(subset),
                f"Mean: {mean_direction}; slow rate: {rate_direction}",
            ]
        )

    traffic_pattern_rows: list[list[object]] = []
    jam_highest_mean = jam_highest_rate = rate_tie_categories = 0
    traffic_pattern_count = 0
    for multiple in multiple_categories:
        subset = qualifying.loc[
            qualifying["multiple_deliveries_category"] == multiple
        ]
        if len(subset) < 2:
            traffic_pattern_rows.append(
                [multiple, len(subset), "Insufficient qualifying traffic pairs"]
            )
            continue
        traffic_pattern_count += 1
        highest_mean = subset.loc[subset["mean_delivery_time"].idxmax()]
        lowest_mean = subset.loc[subset["mean_delivery_time"].idxmin()]
        highest_rate = subset.loc[subset["slow_delivery_rate"].idxmax()]
        highest_rate_categories = subset.loc[
            np.isclose(
                subset["slow_delivery_rate"].astype(float),
                float(highest_rate["slow_delivery_rate"]),
                atol=ABSOLUTE_TOLERANCE,
                rtol=RELATIVE_TOLERANCE,
            ),
            "traffic_category",
        ].tolist()
        jam_highest_mean += int(highest_mean["traffic_category"] == "Jam")
        jam_highest_rate += int("Jam" in highest_rate_categories)
        rate_tie_categories += int(len(highest_rate_categories) > 1)
        traffic_pattern_rows.append(
            [
                multiple,
                len(subset),
                f"{highest_mean['traffic_category']} highest mean "
                f"({format_number(float(highest_mean['mean_delivery_time']))} min); "
                f"{lowest_mean['traffic_category']} lowest "
                f"({format_number(float(lowest_mean['mean_delivery_time']))} min)",
            ]
        )

    total_slow = python_metadata["all_slow_delivery_count"]
    qualifying_slow = int(qualifying["slow_delivery_count"].sum())
    subminimum_slow = int(
        sql_groups.loc[
            sql_groups["delivery_count"] < MIN_GROUP_SIZE,
            "slow_delivery_count",
        ].sum()
    )
    qualifying_slow_share = (
        qualifying_slow / total_slow if total_slow else float("nan")
    )
    if (
        qualifying_slow
        + subminimum_slow
        + python_metadata["excluded_slow_delivery_count"]
        != total_slow
    ):
        raise AssertionError("All slow deliveries do not reconcile across eligibility groups.")
    top_contributors = qualifying.sort_values(
        ["slow_delivery_count", "slow_delivery_rate", "delivery_count"],
        ascending=[False, False, False],
        kind="stable",
    ).head(5)
    contributor_rows = []
    top_contributor_slow = int(top_contributors["slow_delivery_count"].sum())
    for _, row in top_contributors.iterrows():
        slow_count = int(row["slow_delivery_count"])
        count = int(row["delivery_count"])
        contributor_rows.append(
            [
                row["traffic_category"],
                row["multiple_deliveries_category"],
                f"{count:,}",
                f"{slow_count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                f"{slow_count:,} / {total_slow:,} "
                f"({100 * slow_count / total_slow:.2f}%)",
            ]
        )

    baseline_multiple = (
        python_standalone.loc[python_standalone["dimension"] == "multiple"]
        .set_index("category")
    )
    standalone_multiple_categories = sorted(
        baseline_multiple.index.astype(str), key=float
    )
    standalone_endpoint_mean_diff = (
        float(baseline_multiple.loc[standalone_multiple_categories[-1], "standalone_mean"])
        - float(baseline_multiple.loc[standalone_multiple_categories[0], "standalone_mean"])
    )
    standalone_endpoint_rate_diff = (
        float(baseline_multiple.loc[standalone_multiple_categories[-1], "standalone_slow_rate"])
        - float(baseline_multiple.loc[standalone_multiple_categories[0], "standalone_slow_rate"])
    )

    # Compare the multiple-category endpoint span inside each traffic stratum to
    # its standalone endpoint span, only when both endpoints qualify.
    span_rows: list[list[object]] = []
    span_counts = {
        "comparable": 0,
        "mean_smaller": 0,
        "mean_larger": 0,
        "rate_smaller": 0,
        "rate_larger": 0,
    }
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic].set_index(
            "multiple_deliveries_category"
        )
        low_label, high_label = standalone_multiple_categories[0], standalone_multiple_categories[-1]
        if low_label not in subset.index or high_label not in subset.index:
            span_rows.append(
                [
                    traffic,
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                ]
            )
            continue
        mean_span = (
            float(subset.loc[high_label, "mean_delivery_time"])
            - float(subset.loc[low_label, "mean_delivery_time"])
        )
        rate_span = (
            float(subset.loc[high_label, "slow_delivery_rate"])
            - float(subset.loc[low_label, "slow_delivery_rate"])
        )
        span_counts["comparable"] += 1
        span_counts["mean_smaller"] += int(
            abs(mean_span) < abs(standalone_endpoint_mean_diff)
        )
        span_counts["mean_larger"] += int(
            abs(mean_span) > abs(standalone_endpoint_mean_diff)
        )
        span_counts["rate_smaller"] += int(
            abs(rate_span) < abs(standalone_endpoint_rate_diff)
        )
        span_counts["rate_larger"] += int(
            abs(rate_span) > abs(standalone_endpoint_rate_diff)
        )
        span_rows.append(
            [
                traffic,
                format_number(mean_span),
                f"{rate_span * 100:+.4f} percentage points",
                (
                    "larger" if abs(mean_span) > abs(standalone_endpoint_mean_diff)
                    else "smaller" if abs(mean_span) < abs(standalone_endpoint_mean_diff)
                    else "same"
                )
                + " mean endpoint span than standalone",
                (
                    "larger"
                    if abs(rate_span) > abs(standalone_endpoint_rate_diff)
                    else "smaller"
                    if abs(rate_span) < abs(standalone_endpoint_rate_diff)
                    else "same"
                )
                + " slow-rate endpoint span than standalone",
            ]
        )

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned dataset schema changed during analysis.")

    valid_targets = python_metadata["valid_target_count"]
    eligible_count = python_metadata["eligible_combination_population"]
    missing_union = python_metadata["excluded_for_missing_either_count"]
    if eligible_count + missing_union != valid_targets:
        raise AssertionError("Eligible and missing-dimension populations do not reconcile.")

    qualifying_mean_increasing = (
        multiple_pattern_counts["mean_increasing"]
        == multiple_pattern_counts["strata_testable"]
        and multiple_pattern_counts["strata_testable"] > 0
    )
    qualifying_rate_increasing = (
        multiple_pattern_counts["rate_increasing"]
        == multiple_pattern_counts["strata_testable"]
        and multiple_pattern_counts["strata_testable"] > 0
    )
    jam_mean_consistent = (
        traffic_pattern_count > 0
        and jam_highest_mean == traffic_pattern_count
    )
    jam_rate_consistent = (
        traffic_pattern_count > 0
        and jam_highest_rate == traffic_pattern_count
    )

    lines = [
        "# Traffic × Multiple Deliveries Analysis",
        "",
        "## Objective",
        "",
        "Examine descriptively whether multiple-delivery-category differences in delivery "
        "performance are visible across traffic categories, and whether traffic-category "
        "differences remain visible within multiple-delivery categories. This is not a "
        "causal analysis.",
        "",
        "## Analytical Context",
        "",
        "The standalone multiple-delivery analysis reported increasing mean delivery time "
        "across labels 0–3 (22.8763, 26.8559, 40.4549, and 47.8199 minutes) and increasing "
        "slow-delivery rates (4.5406%, 7.4008%, 45.7431%, and 100.0000%). Standalone traffic "
        "metrics also varied: Jam had the highest mean (31.1766 minutes) and slow rate "
        "(20.0099%), while Low had the lowest mean (21.2670 minutes) and slow rate (1.3827%). "
        "These Step 5 findings motivate the two-way descriptive check below.",
        "",
        "## Two-Way Analysis",
        "",
        f"- Source: `data/processed/train_clean.csv`; valid numeric targets: **{valid_targets:,}**.",
        "- Slow delivery remains strictly `Time_taken(min) > 40` minutes.",
        f"- Categories are preserved as stored; the 30-record comparison minimum is applied "
        "to individual combinations.",
        f"- Valid targets with both dimensions present: **{eligible_count:,}**.",
        f"- Excluded only from this two-way grouping because at least one dimension is "
        f"missing: **{missing_union:,}** (missing traffic: "
        f"{python_metadata['missing_traffic_count']:,}; missing multiple_deliveries: "
        f"{python_metadata['missing_multiple_count']:,}).",
        "",
        "### Traffic × Multiple Deliveries Results",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                "Traffic",
                "multiple_deliveries",
                "Delivery count",
                "Mean (min)",
                "Median (min)",
                "P90 (min)",
                "Slow count",
                "Slow count / denominator",
                "Slow rate",
                "Sample-size status",
            ],
            format_qualifying_combinations(sql_groups),
        )
    )
    lines.extend(
        [
            "",
            "Combination counts sum to "
            f"**{eligible_count:,}** eligible records; each row appears in exactly one "
            "observed category pair. Combination-level ranks are only populated for "
            "groups meeting the minimum size.",
            "",
            "## Within-Traffic Comparison",
            "",
            "Within each traffic category, only combinations with at least 30 records "
            "are used to identify the lowest/highest mean and slow-delivery rate. Counts "
            "are shown with each identified category.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Traffic",
                "Lowest mean category (n; mean)",
                "Highest mean category (n; mean)",
                "Lowest slow-rate category (n; rate)",
                "Highest slow-rate category (n; rate)",
            ],
            traffic_extremes_rows,
        )
    )
    lines.extend(
        [
            "",
            "Within-traffic comparison across successive numeric category labels "
            "(labels remain categorical; missing or subminimum combinations are not inferred):",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Traffic category", "Qualifying multiple-delivery categories", "Direction across successive represented labels"],
            multiple_pattern_rows,
        )
    )
    lines.extend(
        [
            "",
            "## Within-Multiple-Delivery Comparison",
            "",
            "For each multiple-delivery category, traffic categories are compared only when "
            "the pair contains at least 30 records. Traffic values are treated as distinct "
            "category labels, not placed on a numeric or causal scale.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "multiple_deliveries",
                "Lowest mean traffic (n; mean)",
                "Highest mean traffic (n; mean)",
                "Lowest slow-rate traffic (n; rate)",
                "Highest slow-rate traffic (n; rate)",
            ],
            multiple_extremes_rows,
        )
    )
    lines.extend(
        [
            "",
            "Highest- and lowest-mean traffic categories within each multiple-delivery "
            "category:",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["multiple_deliveries", "Qualifying traffic categories", "Observed mean extremes"],
            traffic_pattern_rows,
        )
    )
    lines.extend(
        [
            "",
            "## Slow-Delivery Contribution",
            "",
            f"Across all valid targets, **{total_slow:,}** deliveries meet the fixed "
            "slow rule. Of these, "
            f"**{qualifying_slow:,} ({qualifying_slow_share * 100:.2f}%)** occur in "
            "qualifying (n ≥ 30) combinations; "
            f"**{subminimum_slow:,}** occur in subminimum combinations and remain "
            "descriptive only; "
            f"**{python_metadata['excluded_slow_delivery_count']:,}** slow records have at "
            "least one missing grouping dimension and are not assigned to a combination.",
            f"The five qualifying combinations with the largest slow-delivery counts "
            f"account for **{top_contributor_slow:,} ({100 * top_contributor_slow / total_slow:.2f}%)** "
            "of all slow deliveries.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "Traffic",
                "multiple_deliveries",
                "Delivery count",
                "Slow count",
                "Slow rate",
                "Mean (min)",
                "Median (min)",
                "P90 (min)",
                "Share of all slow deliveries",
            ],
            contributor_rows,
        )
    )

    lines.extend(
        [
            "",
            "## SQL vs Python Validation",
            "",
            f"SQL from `sql/09_traffic_multiple_delivery_analysis.sql` was run against an "
            f"in-memory SQLite table (version `{sqlite_version}`). Python independently "
            "grouped the same valid-target rows with Pandas and calculated median/P90 "
            "using NumPy `percentile(method='linear')`. SQLite implements the same "
            "continuous linear interpolation at rank `1 + (n - 1) × p`.",
            "",
            f"Counts and ranks were compared exactly; floating-point values use "
            f"`numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and relative "
            f"tolerance `{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Combination metrics and standalone reference metrics", metric_checks, "MATCH"],
                ["Within-traffic/within-multiple ranks", rank_checks, "MATCH"],
                ["Combination eligibility and slow-count reconciliation", "all", "MATCH"],
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Key Observations",
            "",
            (
                f"- Across the {multiple_pattern_counts['strata_testable']} traffic "
                "strata with at least two qualifying multiple-delivery categories, "
                + (
                    "mean delivery time increases at every successive observed numeric "
                    "multiple-delivery label."
                    if qualifying_mean_increasing
                    else "mean delivery time does not increase consistently at every "
                    "successive observed numeric multiple-delivery label."
                )
            ),
            (
                "- Slow-delivery rate "
                + (
                    "also increases consistently at each successive observed numeric "
                    "multiple-delivery label within those strata."
                    if qualifying_rate_increasing
                    else "does not increase consistently at each successive observed "
                    "numeric multiple-delivery label within those strata."
                )
            ),
            (
                f"- Among {traffic_pattern_count} multiple-delivery categories with at "
                "least two qualifying traffic comparisons, Jam "
                + (
                    "has the highest mean delivery time in every category."
                    if jam_mean_consistent
                    else f"has the highest mean in {jam_highest_mean} categories; the "
                    "highest-mean traffic label is not consistent across categories."
                )
            ),
            (
                "- Jam "
                + (
                    "has the highest or tied-highest slow-delivery rate in every "
                    "multiple-delivery category with at least two qualifying traffic "
                    "comparisons."
                    if jam_rate_consistent
                    else f"is highest or tied for highest slow-delivery rate in "
                    f"{jam_highest_rate} of {traffic_pattern_count} comparable "
                    "multiple-delivery categories."
                )
            ),
            (
                f"- Highest slow-rate ties occur in {rate_tie_categories} of the "
                f"{traffic_pattern_count} comparable multiple-delivery categories."
            ),
            (
                f"- In the standalone analysis, the mean endpoint difference between "
                f"multiple-delivery labels {standalone_multiple_categories[0]} and "
                f"{standalone_multiple_categories[-1]} was "
                f"{standalone_endpoint_mean_diff:.4f} minutes, and the slow-rate "
                f"difference was {standalone_endpoint_rate_diff * 100:.4f} percentage "
                "points. Conditional endpoint spans are listed below where both endpoints "
                "meet the minimum."
            ),
            (
                f"- Across {span_counts['comparable']} traffic categories where both "
                f"multiple-delivery endpoint groups qualify, the mean endpoint span is "
                f"smaller than standalone in {span_counts['mean_smaller']} categories; "
                f"the slow-rate span is smaller in {span_counts['rate_smaller']} and larger "
                f"in {span_counts['rate_larger']}."
            ),
            "",
            "Multiple-delivery endpoint spans within traffic strata (category labels "
            "remain categorical; endpoint subtraction is descriptive only):",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Traffic", "Mean difference: label 3 − label 0 (min)", "Slow-rate difference", "Mean span vs standalone", "Slow-rate span vs standalone"],
            span_rows,
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This descriptive two-way analysis checks whether the standalone multiple-"
            "delivery and traffic patterns remain visible within categories of the other "
            "variable. It does not establish that traffic causes or modifies a multiple-"
            "delivery association, nor that multiple deliveries cause delays. Any "
            "directional differences are observed associations and may reflect other "
            "operational factors.",
            "",
            "## Limitations",
            "",
            "- This is observational analysis; no causal relationship is established.",
            f"- Combinations with fewer than {MIN_GROUP_SIZE} records are excluded from "
            "substantive comparisons and rankings, though their counts and metrics remain "
            "visible in the two-way table.",
            "- Traffic and multiple-delivery categories may themselves be related to "
            "other operational factors.",
            "- This analysis does not control for city, distance, weather, vehicle, courier, "
            "or time.",
            "- No regression, machine learning, or formal statistical interaction model "
            "was fitted.",
            "- Missing values are not fabricated or silently dropped from the overall "
            "valid-target population; they are excluded only from the relevant two-way "
            "grouping and reported explicitly.",
            "- The 30-record rule is a reporting guardrail, not a guarantee of statistical "
            "precision.",
            "",
            f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is "
            f"`{source_hash_before}` before and after; the input schema is unchanged.",
            "",
        ]
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(sql_groups)} observed combinations: {metric_checks} "
        f"metric/population comparisons and {rank_checks} within-axis ranking checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
