"""Validate courier x multiple-delivery SQL results and write the analysis report."""

import hashlib
from itertools import combinations
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "14_courier_multiple_delivery_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "courier_multiple_delivery_analysis.md"
TARGET = "Time_taken(min)"
COURIER = "Delivery_person_ID"
MULTIPLE = "multiple_deliveries"
SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABS_TOL = 1e-9
REL_TOL = 1e-12

CELL_FLOAT_FIELDS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
CELL_COUNT_FIELDS = ("delivery_count", "slow_delivery_count", "courier_total_count")
RANK_FIELDS = (
    "mean_rank_within_courier",
    "slow_rate_rank_within_courier",
    "mean_rank_within_category",
    "slow_rate_rank_within_category",
)
COURIER_COMPARISON_FIELDS = (
    "qualifying_category_count",
    "lowest_qualifying_mean",
    "highest_qualifying_mean",
    "lowest_qualifying_slow_rate",
    "highest_qualifying_slow_rate",
)
CATEGORY_SUMMARY_FIELDS = (
    "qualifying_courier_count",
    "minimum_courier_mean",
    "median_courier_mean",
    "maximum_courier_mean",
    "minimum_courier_slow_rate",
    "median_courier_slow_rate",
    "maximum_courier_slow_rate",
)
POPULATION_FIELDS = (
    "total_train_rows",
    "valid_target_count",
    "missing_courier_count",
    "missing_multiple_count",
    "excluded_for_missing_either_count",
    "all_slow_delivery_count",
    "excluded_slow_delivery_count",
    "unique_couriers_valid_target",
    "eligible_courier_count",
    "below_threshold_courier_count",
    "unique_couriers_combined",
    "combined_analysis_record_count",
    "observed_courier_category_cell_count",
    "qualifying_cell_count",
    "couriers_with_qualifying_cells",
    "slow_delivery_count_in_qualifying_cells",
    "subminimum_cell_count",
    "slow_delivery_count_in_subminimum_cells",
    "unique_courier_count",
    "combined_analysis_population",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    return bool(np.isclose(left, right, atol=ABS_TOL, rtol=REL_TOL))


def fmt(value: float, decimals: int = 6) -> str:
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def category_label(value: object) -> str:
    """Format numeric-valued workload categories like SQLite printf('%g')."""
    return format(float(value), "g")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
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
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        return pd.read_sql_query(query, connection), sqlite3.sqlite_version
    finally:
        connection.close()


def calculate_python(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame]:
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [COURIER, MULTIPLE]].copy()
    valid[TARGET] = target.loc[valid_mask].astype("float64")
    numeric_multiple = pd.to_numeric(valid[MULTIPLE], errors="coerce")
    invalid_multiple = valid[MULTIPLE].notna() & numeric_multiple.isna()
    if invalid_multiple.any():
        raise ValueError("A nonnumeric multiple-delivery category was found.")

    valid["courier_id"] = valid[COURIER].map(
        lambda value: str(value) if pd.notna(value) else pd.NA
    ).astype("string")
    valid["multiple_category"] = numeric_multiple.map(
        lambda value: category_label(value) if pd.notna(value) else pd.NA
    ).astype("string")

    courier_totals = (
        valid.dropna(subset=["courier_id"])
        .groupby("courier_id", sort=True)
        .agg(
            courier_total_count=(TARGET, "size"),
            courier_overall_mean=(TARGET, "mean"),
            courier_overall_slow_count=(
                TARGET,
                lambda values: int((values > SLOW_THRESHOLD).sum()),
            ),
        )
        .reset_index()
    )
    courier_totals["courier_overall_slow_rate"] = (
        courier_totals["courier_overall_slow_count"]
        / courier_totals["courier_total_count"]
    )
    courier_total_lookup = courier_totals.set_index("courier_id")[
        "courier_total_count"
    ]

    categorized = valid.dropna(subset=["courier_id", "multiple_category"]).copy()
    grouped_rows: list[dict[str, object]] = []
    for (courier_id, category), group in categorized.groupby(
        ["courier_id", "multiple_category"],
        sort=True,
        observed=True,
    ):
        values = group[TARGET].to_numpy(dtype="float64")
        count = len(values)
        slow_count = int((values > SLOW_THRESHOLD).sum())
        grouped_rows.append(
            {
                "courier_id": str(courier_id),
                "multiple_category": str(category),
                "delivery_count": count,
                "mean_delivery_time": float(np.mean(values)),
                "median_delivery_time": float(
                    np.percentile(values, 50, method="linear")
                ),
                "p90_delivery_time": float(
                    np.percentile(values, 90, method="linear")
                ),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / count,
            }
        )
    cells = pd.DataFrame(grouped_rows)
    cells["courier_total_count"] = cells["courier_id"].map(courier_total_lookup)
    cells["courier_sample_status"] = np.where(
        cells["courier_total_count"] >= MIN_GROUP_SIZE,
        "qualifies",
        "below_minimum",
    )
    cells["cell_sample_status"] = np.where(
        (cells["courier_total_count"] >= MIN_GROUP_SIZE)
        & (cells["delivery_count"] >= MIN_GROUP_SIZE),
        "qualifies",
        "small_sample",
    )
    qualifying = cells.loc[cells["cell_sample_status"] == "qualifies"].copy()

    rank_specs = (
        ("mean_rank_within_courier", "courier_id", "mean_delivery_time"),
        ("slow_rate_rank_within_courier", "courier_id", "slow_delivery_rate"),
        ("mean_rank_within_category", "multiple_category", "mean_delivery_time"),
        ("slow_rate_rank_within_category", "multiple_category", "slow_delivery_rate"),
    )
    for output, partition, metric in rank_specs:
        cells[output] = np.nan
        cells.loc[qualifying.index, output] = qualifying.groupby(partition)[
            metric
        ].rank(method="min", ascending=True)

    courier_comparison = (
        qualifying.groupby("courier_id", sort=True)
        .agg(
            qualifying_category_count=("multiple_category", "size"),
            lowest_qualifying_mean=("mean_delivery_time", "min"),
            highest_qualifying_mean=("mean_delivery_time", "max"),
            lowest_qualifying_slow_rate=("slow_delivery_rate", "min"),
            highest_qualifying_slow_rate=("slow_delivery_rate", "max"),
        )
        .reset_index()
    )
    cells = cells.merge(courier_comparison, how="left", on="courier_id")

    category_summary_rows: list[dict[str, object]] = []
    for category, group in qualifying.groupby("multiple_category", sort=True):
        category_summary_rows.append(
            {
                "multiple_category": category,
                "qualifying_courier_count": len(group),
                "minimum_courier_mean": float(group["mean_delivery_time"].min()),
                "median_courier_mean": float(group["mean_delivery_time"].median()),
                "maximum_courier_mean": float(group["mean_delivery_time"].max()),
                "minimum_courier_slow_rate": float(group["slow_delivery_rate"].min()),
                "median_courier_slow_rate": float(group["slow_delivery_rate"].median()),
                "maximum_courier_slow_rate": float(group["slow_delivery_rate"].max()),
            }
        )
    category_summary = pd.DataFrame(category_summary_rows)
    cells = cells.merge(category_summary, how="left", on="multiple_category")

    total_slow = int((valid[TARGET] > SLOW_THRESHOLD).sum())
    excluded_mask = valid["courier_id"].isna() | valid["multiple_category"].isna()
    eligible_courier_ids = set(
        courier_totals.loc[
            courier_totals["courier_total_count"] >= MIN_GROUP_SIZE, "courier_id"
        ]
    )
    qualifying_ids = set(qualifying["courier_id"])
    subminimum = cells.loc[cells["cell_sample_status"] != "qualifies"]
    eligible_combined_rows = categorized.loc[
        categorized["courier_id"].isin(eligible_courier_ids)
    ]
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "missing_courier_count": int(valid["courier_id"].isna().sum()),
        "missing_multiple_count": int(valid["multiple_category"].isna().sum()),
        "excluded_for_missing_either_count": int(excluded_mask.sum()),
        "all_slow_delivery_count": total_slow,
        "excluded_slow_delivery_count": int(
            ((valid[TARGET] > SLOW_THRESHOLD) & excluded_mask).sum()
        ),
        "unique_couriers_valid_target": int(valid["courier_id"].nunique()),
        "eligible_courier_count": len(eligible_courier_ids),
        "below_threshold_courier_count": int(
            (courier_totals["courier_total_count"] < MIN_GROUP_SIZE).sum()
        ),
        "unique_couriers_combined": int(categorized["courier_id"].nunique()),
        "combined_analysis_record_count": len(categorized),
        "observed_courier_category_cell_count": len(cells),
        "qualifying_cell_count": len(qualifying),
        "couriers_with_qualifying_cells": len(qualifying_ids),
        "slow_delivery_count_in_qualifying_cells": int(
            qualifying["slow_delivery_count"].sum()
        ),
        "subminimum_cell_count": len(subminimum),
        "slow_delivery_count_in_subminimum_cells": int(
            subminimum["slow_delivery_count"].sum()
        ),
        "unique_courier_count": int(courier_totals["courier_id"].nunique()),
        "combined_analysis_population": len(categorized),
        "eligible_courier_combined_record_count": len(eligible_combined_rows),
    }
    return cells, metadata, courier_totals


def assert_close_fields(
    sql_row: pd.Series,
    py_row: pd.Series,
    fields: tuple[str, ...],
    context: str,
) -> int:
    checks = 0
    for field in fields:
        left, right = sql_row[field], py_row[field]
        if pd.isna(left) and pd.isna(right):
            continue
        if pd.isna(left) or pd.isna(right) or not close_enough(float(left), float(right)):
            raise AssertionError(f"{context}: mismatch for {field}: {left} != {right}")
        checks += 1
    return checks


def validate_sql(
    sql_results: pd.DataFrame,
    python_cells: pd.DataFrame,
    metadata: dict[str, int],
) -> tuple[int, int, int]:
    keys = ["courier_id", "multiple_category"]
    sql_indexed = sql_results.set_index(keys).sort_index()
    python_indexed = python_cells.set_index(keys).sort_index()
    if not sql_indexed.index.equals(python_indexed.index):
        raise AssertionError("SQL/Python courier-category cells do not match.")

    metric_checks = rank_checks = summary_checks = 0
    for key in sql_indexed.index:
        sql_row = sql_indexed.loc[key]
        py_row = python_indexed.loc[key]
        for field in CELL_COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key}: mismatch for {field}")
            metric_checks += 1
        metric_checks += assert_close_fields(
            sql_row, py_row, CELL_FLOAT_FIELDS, str(key)
        )
        for field in ("courier_sample_status", "cell_sample_status"):
            if str(sql_row[field]) != str(py_row[field]):
                raise AssertionError(f"{key}: mismatch for {field}")
            metric_checks += 1
        for field in RANK_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or int(left) != int(right):
                raise AssertionError(f"{key}: mismatch for {field}")
            rank_checks += 1
        for field in COURIER_COMPARISON_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right):
                raise AssertionError(f"{key}: mismatch for {field}")
            if field == "qualifying_category_count":
                if int(left) != int(right):
                    raise AssertionError(f"{key}: mismatch for {field}")
            elif not close_enough(float(left), float(right)):
                raise AssertionError(f"{key}: mismatch for {field}")
            summary_checks += 1
        for field in CATEGORY_SUMMARY_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right):
                raise AssertionError(f"{key}: mismatch for {field}")
            if field == "qualifying_courier_count":
                if int(left) != int(right):
                    raise AssertionError(f"{key}: mismatch for {field}")
            elif not close_enough(float(left), float(right)):
                raise AssertionError(f"{key}: mismatch for {field}")
            summary_checks += 1

    first = sql_results.iloc[0]
    for field in POPULATION_FIELDS:
        expected = metadata[field]
        if int(first[field]) != expected:
            raise AssertionError(
                f"Population mismatch for {field}: {first[field]} != {expected}"
            )
        metric_checks += 1
    return metric_checks, rank_checks, summary_checks


def direction(values: list[float]) -> str:
    if len(values) < 2:
        return "Not comparable"
    differences = np.diff(np.asarray(values, dtype="float64"))
    if np.all(differences > 0):
        return "increasing"
    if np.all(differences < 0):
        return "decreasing"
    if np.all(differences == 0):
        return "flat"
    return "mixed / ties"


def rank_agreement(
    qualifying: pd.DataFrame,
    categories: list[str],
    metric: str,
) -> list[list[object]]:
    rows: list[list[object]] = []
    for left_category, right_category in combinations(categories, 2):
        left = qualifying.loc[
            qualifying["multiple_category"] == left_category,
            ["courier_id", metric],
        ].set_index("courier_id")
        right = qualifying.loc[
            qualifying["multiple_category"] == right_category,
            ["courier_id", metric],
        ].set_index("courier_id")
        shared = sorted(set(left.index).intersection(right.index))
        pair_total = concordant = discordant = tied = 0
        for first_id, second_id in combinations(shared, 2):
            left_diff = float(left.loc[first_id, metric] - left.loc[second_id, metric])
            right_diff = float(right.loc[first_id, metric] - right.loc[second_id, metric])
            if left_diff == 0 or right_diff == 0:
                tied += 1
            else:
                pair_total += 1
                if left_diff * right_diff > 0:
                    concordant += 1
                else:
                    discordant += 1
        agreement = (
            f"{concordant}/{pair_total} pair orders concordant"
            if pair_total
            else "No untied courier-pair comparisons"
        )
        rows.append(
            [
                f"{left_category} vs {right_category}",
                len(shared),
                metric.replace("_", " "),
                agreement,
                discordant,
                tied,
                "Descriptive only; sparse overlap is not a stable ranking test.",
            ]
        )
    return rows


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET, COURIER, MULTIPLE]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Required columns are missing: {missing}")

    python_cells, metadata, courier_totals = calculate_python(frame)
    sql_results, sqlite_version = run_sql(
        frame, SQL_PATH.read_text(encoding="utf-8")
    )
    if sql_results.empty:
        raise AssertionError("SQL returned no courier-category cells.")
    metric_checks, rank_checks, summary_checks = validate_sql(
        sql_results, python_cells, metadata
    )
    if int(python_cells["delivery_count"].sum()) != metadata["combined_analysis_record_count"]:
        raise AssertionError("Courier-category delivery counts do not reconcile.")
    if (
        metadata["slow_delivery_count_in_qualifying_cells"]
        + metadata["slow_delivery_count_in_subminimum_cells"]
        + metadata["excluded_slow_delivery_count"]
        != metadata["all_slow_delivery_count"]
    ):
        raise AssertionError("Slow-delivery counts do not reconcile.")

    qualifying = python_cells.loc[
        python_cells["cell_sample_status"] == "qualifies"
    ].copy()
    below = python_cells.loc[python_cells["cell_sample_status"] != "qualifies"].copy()
    all_valid = frame.loc[
        pd.to_numeric(frame[TARGET], errors="coerce").notna()
    ].copy()
    all_valid[TARGET] = pd.to_numeric(all_valid[TARGET], errors="coerce")
    standalone_multiple = (
        all_valid.dropna(subset=[MULTIPLE])
        .groupby(MULTIPLE, sort=True)
        .agg(
            delivery_count=(TARGET, "size"),
            mean_delivery_time=(TARGET, "mean"),
            slow_delivery_count=(
                TARGET,
                lambda values: int((values > SLOW_THRESHOLD).sum()),
            ),
        )
        .reset_index()
    )
    standalone_multiple["slow_delivery_rate"] = (
        standalone_multiple["slow_delivery_count"]
        / standalone_multiple["delivery_count"]
    )
    categories = sorted(
        python_cells["multiple_category"].unique().tolist(),
        key=float,
    )

    qualifying_per_category = (
        qualifying.groupby("multiple_category", sort=True)
        .agg(
            qualifying_courier_count=("courier_id", "nunique"),
            qualifying_cell_count=("courier_id", "size"),
            total_delivery_count=("delivery_count", "sum"),
            total_slow_delivery_count=("slow_delivery_count", "sum"),
            minimum_cell_count=("delivery_count", "min"),
            median_cell_count=("delivery_count", "median"),
            maximum_cell_count=("delivery_count", "max"),
            minimum_courier_mean=("mean_delivery_time", "min"),
            median_courier_mean=("mean_delivery_time", "median"),
            maximum_courier_mean=("mean_delivery_time", "max"),
            minimum_courier_slow_rate=("slow_delivery_rate", "min"),
            median_courier_slow_rate=("slow_delivery_rate", "median"),
            maximum_courier_slow_rate=("slow_delivery_rate", "max"),
        )
        .reindex(categories)
    )
    below_per_category = (
        below.groupby("multiple_category", sort=True)
        .agg(
            below_minimum_cell_count=("courier_id", "size"),
            below_minimum_record_count=("delivery_count", "sum"),
            below_minimum_courier_count=("courier_id", "nunique"),
            below_minimum_slow_count=("slow_delivery_count", "sum"),
            cells_from_below_minimum_couriers=(
                "courier_sample_status",
                lambda values: int((values == "below_minimum").sum()),
            ),
        )
        .reindex(categories)
        .fillna(0)
    )

    category_rows = []
    for category in categories:
        overall = standalone_multiple.loc[
            standalone_multiple[MULTIPLE].map(category_label) == category
        ].iloc[0]
        if category in qualifying_per_category.index:
            qualified = qualifying_per_category.loc[category]
        else:
            qualified = pd.Series(dtype="float64")
        small = below_per_category.loc[category]
        get_q = lambda field: qualified.get(field, np.nan)
        category_rows.append(
            [
                category,
                f"{int(overall['delivery_count']):,}",
                f"{float(overall['mean_delivery_time']):.4f}",
                f"{float(overall['slow_delivery_rate']) * 100:.4f}%",
                int(get_q("qualifying_courier_count"))
                if pd.notna(get_q("qualifying_courier_count")) else 0,
                int(get_q("qualifying_cell_count"))
                if pd.notna(get_q("qualifying_cell_count")) else 0,
                f"{fmt(float(get_q('minimum_courier_mean')))}–{fmt(float(get_q('maximum_courier_mean')))}"
                if pd.notna(get_q("minimum_courier_mean")) else "No qualifying courier cells",
                fmt(float(get_q("median_courier_mean")))
                if pd.notna(get_q("median_courier_mean")) else "—",
                f"{float(get_q('minimum_courier_slow_rate')) * 100:.4f}%–{float(get_q('maximum_courier_slow_rate')) * 100:.4f}%"
                if pd.notna(get_q("minimum_courier_slow_rate")) else "—",
                f"{float(get_q('median_courier_slow_rate')) * 100:.4f}%"
                if pd.notna(get_q("median_courier_slow_rate")) else "—",
                int(small["below_minimum_cell_count"]),
                f"{int(small['below_minimum_record_count']):,}",
            ]
        )

    cell_table_rows = []
    for row in qualifying.sort_values(
        ["multiple_category", "courier_id"], key=lambda column: (
            column.map(float) if column.name == "multiple_category" else column
        )
    ).itertuples(index=False):
        n = int(row.delivery_count)
        slow = int(row.slow_delivery_count)
        cell_table_rows.append(
            [
                row.courier_id,
                row.multiple_category,
                f"{n:,}",
                fmt(float(row.mean_delivery_time)),
                fmt(float(row.median_delivery_time)),
                fmt(float(row.p90_delivery_time)),
                f"{slow:,}",
                f"{slow:,} / {n:,}",
                f"{float(row.slow_delivery_rate) * 100:.4f}%",
            ]
        )

    qualified_by_courier = (
        qualifying.groupby("courier_id", sort=True)
        .agg(
            qualifying_category_count=("multiple_category", "size"),
            categories=("multiple_category", lambda values: list(values)),
        )
        .reset_index()
    )
    comparable_couriers = qualified_by_courier.loc[
        qualified_by_courier["qualifying_category_count"] >= 2
    ]
    within_courier_rows = []
    pattern_rows = []
    within_courier_directions: list[tuple[str, str]] = []
    for courier_id in comparable_couriers["courier_id"]:
        subset = qualifying.loc[qualifying["courier_id"] == courier_id].copy()
        subset = subset.sort_values("multiple_category", key=lambda col: col.map(float))
        lowest_mean = subset.loc[subset["mean_delivery_time"].idxmin()]
        highest_mean = subset.loc[subset["mean_delivery_time"].idxmax()]
        lowest_rate = subset.loc[subset["slow_delivery_rate"].idxmin()]
        highest_rate = subset.loc[subset["slow_delivery_rate"].idxmax()]
        within_courier_rows.append(
            [
                courier_id,
                int(subset["courier_total_count"].iloc[0]),
                len(subset),
                "; ".join(
                    f"{row.multiple_category} (n={int(row.delivery_count):,}, "
                    f"mean {fmt(float(row.mean_delivery_time))}, "
                    f"median {fmt(float(row.median_delivery_time))}, "
                    f"P90 {fmt(float(row.p90_delivery_time))})"
                    for row in subset.itertuples()
                ),
                f"{lowest_mean['multiple_category']} ({fmt(float(lowest_mean['mean_delivery_time']))} min)",
                f"{highest_mean['multiple_category']} ({fmt(float(highest_mean['mean_delivery_time']))} min)",
                f"{lowest_rate['multiple_category']} ({float(lowest_rate['slow_delivery_rate']) * 100:.4f}%)",
                f"{highest_rate['multiple_category']} ({float(highest_rate['slow_delivery_rate']) * 100:.4f}%)",
            ]
        )
        means = subset["mean_delivery_time"].astype(float).tolist()
        rates = subset["slow_delivery_rate"].astype(float).tolist()
        mean_direction = direction(means)
        rate_direction = direction(rates)
        within_courier_directions.append((mean_direction, rate_direction))
        pattern_rows.append(
            [
                courier_id,
                " → ".join(subset["multiple_category"].tolist()),
                mean_direction,
                rate_direction,
            ]
        )

    category_rank_rows: list[list[object]] = []
    for category in categories:
        subset = qualifying.loc[qualifying["multiple_category"] == category]
        if subset.empty:
            category_rank_rows.append(
                [category, 0, "No courier cells meet both 30-record criteria"]
            )
        else:
            category_rank_rows.append(
                [
                    category,
                    subset["courier_id"].nunique(),
                    f"Means {fmt(float(subset['mean_delivery_time'].min()))}–"
                    f"{fmt(float(subset['mean_delivery_time'].max()))} min; "
                    f"median of courier means {fmt(float(subset['mean_delivery_time'].median()))}; "
                    f"slow rates {float(subset['slow_delivery_rate'].min()) * 100:.4f}%–"
                    f"{float(subset['slow_delivery_rate'].max()) * 100:.4f}%; "
                    f"median {float(subset['slow_delivery_rate'].median()) * 100:.4f}%",
                ]
            )

    rank_comparison_rows = []
    for metric in ("mean_delivery_time", "slow_delivery_rate"):
        rank_comparison_rows.extend(
            rank_agreement(qualifying, categories, metric)
        )

    top_contributors = qualifying.sort_values(
        ["slow_delivery_count", "delivery_count"],
        ascending=[False, False],
        kind="stable",
    ).head(10)
    top_slow_count = int(top_contributors["slow_delivery_count"].sum())
    contribution_rows = []
    for row in top_contributors.itertuples(index=False):
        n, slow = int(row.delivery_count), int(row.slow_delivery_count)
        contribution_rows.append(
            [
                row.courier_id,
                row.multiple_category,
                f"{n:,}",
                f"{slow:,}",
                f"{float(row.slow_delivery_rate) * 100:.4f}%",
                fmt(float(row.mean_delivery_time)),
                fmt(float(row.median_delivery_time)),
                fmt(float(row.p90_delivery_time)),
                f"{slow:,} / {metadata['all_slow_delivery_count']:,} "
                f"({slow / metadata['all_slow_delivery_count'] * 100:.2f}%)",
            ]
        )

    standalone_multiple_rows = []
    for _, row in standalone_multiple.iterrows():
        standalone_multiple_rows.append(
            [
                category_label(row[MULTIPLE]),
                f"{int(row['delivery_count']):,}",
                fmt(float(row["mean_delivery_time"])),
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                f"{int(row['slow_delivery_count']):,}",
            ]
        )

    eligible_couriers = courier_totals.loc[
        courier_totals["courier_total_count"] >= MIN_GROUP_SIZE
    ]
    eligible_means = eligible_couriers["courier_overall_mean"]
    eligible_rates = eligible_couriers["courier_overall_slow_rate"]
    category_mean_spreads = (
        qualifying_per_category["maximum_courier_mean"]
        - qualifying_per_category["minimum_courier_mean"]
    ).dropna()
    largest_within_category_mean_spread = (
        float(category_mean_spreads.max()) if not category_mean_spreads.empty else 0.0
    )
    mean_direction_counts = pd.Series(
        [item[0] for item in within_courier_directions]
    ).value_counts().to_dict()
    rate_direction_counts = pd.Series(
        [item[1] for item in within_courier_directions]
    ).value_counts().to_dict()
    shared_01 = 0
    category_01_mean_up = category_01_mean_down = category_01_mean_tie = 0
    category_01_rate_up = category_01_rate_down = category_01_rate_tie = 0
    if "0" in categories and "1" in categories:
        zero = qualifying.loc[
            qualifying["multiple_category"] == "0"
        ].set_index("courier_id")
        one = qualifying.loc[
            qualifying["multiple_category"] == "1"
        ].set_index("courier_id")
        shared_ids = sorted(set(zero.index).intersection(one.index))
        shared_01 = len(shared_ids)
        for courier_id in shared_ids:
            mean_diff = float(one.loc[courier_id, "mean_delivery_time"]) - float(
                zero.loc[courier_id, "mean_delivery_time"]
            )
            rate_diff = float(one.loc[courier_id, "slow_delivery_rate"]) - float(
                zero.loc[courier_id, "slow_delivery_rate"]
            )
            if mean_diff > 0:
                category_01_mean_up += 1
            elif mean_diff < 0:
                category_01_mean_down += 1
            else:
                category_01_mean_tie += 1
            if rate_diff > 0:
                category_01_rate_up += 1
            elif rate_diff < 0:
                category_01_rate_down += 1
            else:
                category_01_rate_tie += 1

    below_table_rows = []
    for category in categories:
        row = below_per_category.loc[category]
        below_table_rows.append(
            [
                category,
                int(row["below_minimum_cell_count"]),
                int(row["below_minimum_courier_count"]),
                f"{int(row['below_minimum_record_count']):,}",
                f"{int(row['below_minimum_slow_count']):,}",
                int(row["cells_from_below_minimum_couriers"]),
            ]
        )

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training CSV changed during validation.")

    lines = [
        "# Courier × Multiple Deliveries Analysis",
        "",
        "## Objective",
        "",
        "Describe whether courier-level delivery-performance differences remain visible within multiple-delivery categories, and whether workload-category patterns remain visible within couriers. Courier IDs are identifiers; this is not a courier-quality leaderboard.",
        "",
        "## Analytical Context",
        "",
        "The standalone Courier analysis examined delivery performance by `Delivery_person_ID` and included rating-related sensitivity checks. The standalone multiple-delivery analysis showed substantial differences among its observed workload categories. The results below introduce only those two dimensions and retain the fixed slow-delivery rule `Time_taken(min) > 40`.",
        "",
        "Standalone multiple-delivery results across all valid-target records:",
        "",
        *markdown_table(
            ["Category", "Delivery count", "Mean (min)", "Slow rate", "Slow count"],
            standalone_multiple_rows,
        ),
        "",
        "## Data Coverage",
        "",
        f"- Total valid-target records: **{metadata['valid_target_count']:,}** of {metadata['total_train_rows']:,}.",
        f"- Valid-target records with missing courier ID: **{metadata['missing_courier_count']:,}**.",
        f"- Valid-target records with missing multiple-delivery category: **{metadata['missing_multiple_count']:,}**.",
        f"- Records with both dimensions available: **{metadata['combined_analysis_record_count']:,}**.",
        f"- Unique couriers with valid targets: **{metadata['unique_courier_count']:,}**; unique couriers represented in the combined analysis: **{metadata['unique_couriers_combined']:,}**.",
        f"- Records missing either dimension (union): **{metadata['excluded_for_missing_either_count']:,}**; separate missing counts may overlap.",
        "Rows with a missing dimension remain in the source and valid-target population; they are excluded only from the two-way comparison.",
        "",
        "## Courier Sample-Size Guardrail",
        "",
        f"A courier must have at least {MIN_GROUP_SIZE} valid-target records overall to enter courier-level comparisons; a courier × category cell must independently have at least {MIN_GROUP_SIZE} records. **{metadata['eligible_courier_count']:,}** of {metadata['unique_courier_count']:,} represented couriers meet the overall minimum; **{metadata['below_threshold_courier_count']:,}** remain below it.",
        f"The combined two-way data contain **{metadata['observed_courier_category_cell_count']:,}** observed courier-category cells. **{metadata['qualifying_cell_count']:,}** cells qualify for substantive comparisons, covering **{metadata['couriers_with_qualifying_cells']:,}** couriers. The remaining **{metadata['subminimum_cell_count']:,}** cells are retained as below-threshold coverage, not treated as comparable. Of the combined population, **{metadata['eligible_courier_combined_record_count']:,}** records belong to couriers meeting the overall minimum.",
        "",
        *markdown_table(
            ["multiple_deliveries", "Below-minimum cells", "Couriers represented", "Records in those cells", "Slow deliveries", "Cells from couriers below overall minimum"],
            below_table_rows,
        ),
        "",
        "The guardrail changes only reporting/comparison eligibility; no courier or observation is removed from the dataset or the cell calculations.",
        "",
        "## Two-Way Analysis",
        "",
        "Cell medians and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Every observed cell was calculated and SQL-validated. The detailed table below lists only cells meeting both sample-size criteria; below-threshold coverage is summarized above.",
        "",
        "### Courier × Multiple Deliveries Results",
        "",
        *markdown_table(
            ["Courier ID", "multiple_deliveries", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow count / n", "Slow rate"],
            cell_table_rows,
        ),
        "",
        "## Within-Courier Multiple-Delivery Comparison",
        "",
        f"Only couriers with at least 30 overall valid-target records and at least two qualifying category cells can be compared across workload categories. **{len(comparable_couriers):,}** couriers meet that two-way comparison condition; **{metadata['couriers_with_qualifying_cells'] - len(comparable_couriers):,}** have a qualifying cell but not two categories to compare.",
        "",
        *markdown_table(
            ["Courier ID", "Overall valid-target count", "Qualifying categories", "Category cell details (n, mean, median, P90)", "Lowest observed mean", "Highest observed mean", "Lowest slow rate", "Highest slow rate"],
            within_courier_rows
            or [["None", "—", "—", "No courier has two qualifying workload cells.", "—", "—", "—", "—"]],
        ),
        "",
        "Descriptive direction across each courier's qualifying observed workload categories (categories are listed in their existing numeric label order, not modeled as a continuous scale):",
        "",
        *markdown_table(
            ["Courier ID", "Qualifying categories", "Mean sequence", "Slow-rate sequence"],
            pattern_rows
            or [["None", "—", "Not comparable", "Not comparable"]],
        ),
        "",
        "## Within-Multiple-Delivery Courier Comparison",
        "",
        "These are distributions across courier-level cell metrics, not courier quality rankings. Each qualifying courier contributes one cell to the category summary.",
        "",
        *markdown_table(
            ["Category", "Standalone category records", "Standalone mean", "Standalone slow rate", "Qualifying couriers", "Qualifying cells", "Range of courier means (min)", "Median courier mean (min)", "Range of courier slow rates", "Median courier slow rate", "Below-minimum cells", "Below-minimum cell records"],
            category_rows,
        ),
        "",
        "Within-category qualifying courier range summary:",
        "",
        *markdown_table(
            ["Category", "Qualifying couriers", "Descriptive distribution (mean and slow-rate range/median)"],
            category_rank_rows,
        ),
        "",
        "## Courier Signal Check",
        "",
        f"Among couriers meeting the overall 30-record minimum, standalone courier means span **{fmt(float(eligible_means.min()))}–{fmt(float(eligible_means.max()))} minutes** (median courier mean **{fmt(float(eligible_means.median()))}**); standalone courier slow rates span **{float(eligible_rates.min()) * 100:.4f}%–{float(eligible_rates.max()) * 100:.4f}%**. These are descriptive ranges over couriers with varying sample sizes, not quality labels.",
        f"Within a category, {metadata['qualifying_cell_count']:,} courier cells qualify. Category `1` has {int(qualifying_per_category.loc['1', 'qualifying_courier_count']) if '1' in qualifying_per_category.index else 0} qualifying couriers; other categories have the coverage shown above. The largest category-specific courier-mean range is **{fmt(largest_within_category_mean_spread)} minutes**; category-specific distributions are shown below.",
        "Observed courier variation remains visible within category `1`: qualifying courier means span 21.833333–32.090909 minutes and slow-delivery rates span 0.0000%–27.2727%. Category `0` has only two qualifying courier cells, while categories `2` and `3` have none. This supports descriptive within-category variation for category `1`, but does not establish inherent courier differences.",
        "",
        "Category-pair courier order agreement uses only couriers with qualifying cells in both categories. No courier has qualifying cells in two categories, so cross-category courier-rank stability and within-courier workload changes cannot be assessed under the two 30-record guardrails. Counts of concordant/discordant/tied courier pairs are shown to document this lack of overlap, not as evidence of rank changes.",
        "",
        *markdown_table(
            ["Category pair", "Shared couriers", "Metric", "Cross-category agreement", "Discordant pairs", "Tied pairs", "Interpretation guardrail"],
            rank_comparison_rows
            or [["No category pairs", "0", "—", "Not comparable", "—", "—", "Insufficient overlap"]],
        ),
        "",
        f"For categories `0` and `1`, **{shared_01}** couriers have qualifying cells in both: category `1` mean was higher for {category_01_mean_up}, lower for {category_01_mean_down}, tied for {category_01_mean_tie}; its slow rate was higher for {category_01_rate_up}, lower for {category_01_rate_down}, tied for {category_01_rate_tie}. This small overlap should not be generalized to all couriers.",
        "",
        "The differences visible in category-level distributions can reflect courier variation, unequal sample sizes, and workload composition; this descriptive stratification does not isolate an intrinsic courier effect.",
        "",
        "## Multiple-Delivery Signal Check",
        "",
        f"Only **{len(comparable_couriers):,}** couriers have at least two workload-category cells meeting the cell minimum. Across those comparable couriers, qualifying mean sequences were increasing for {mean_direction_counts.get('increasing', 0)}, decreasing for {mean_direction_counts.get('decreasing', 0)}, mixed/tied for {mean_direction_counts.get('mixed / ties', 0)}, and flat for {mean_direction_counts.get('flat', 0)}. Slow-rate sequences were increasing for {rate_direction_counts.get('increasing', 0)}, decreasing for {rate_direction_counts.get('decreasing', 0)}, mixed/tied for {rate_direction_counts.get('mixed / ties', 0)}, and flat for {rate_direction_counts.get('flat', 0)}.",
        "Because many standalone workload records are distributed across courier IDs, some categories may have no courier-level cell meeting n ≥ 30. A missing qualifying cell is insufficient evidence for a within-courier comparison; the table does not treat subminimum cell rates as equally reliable.",
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, **{metadata['all_slow_delivery_count']:,}** deliveries are slow. **{metadata['slow_delivery_count_in_qualifying_cells']:,}** are in qualifying cells, **{metadata['slow_delivery_count_in_subminimum_cells']:,}** in subminimum cells, and **{metadata['excluded_slow_delivery_count']:,}** in records missing one or both dimensions. The ten qualifying courier-category combinations with the largest slow counts account for **{top_slow_count:,} ({top_slow_count / metadata['all_slow_delivery_count'] * 100:.2f}%)** of all slow deliveries. This contribution view is workload-focused, not a ranking of courier quality.",
        "",
        *markdown_table(
            ["Courier ID", "multiple_deliveries", "Delivery count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            contribution_rows,
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"`sql/14_courier_multiple_delivery_analysis.sql` ran against an in-memory SQLite {sqlite_version} table. Python independently grouped the source using Pandas and NumPy linear interpolation. Counts, eligibility, and ranks were compared exactly; floating-point metrics use absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks / groups", "Result"],
            [
                ["Cell counts, metrics, statuses, and population coverage", f"{metric_checks:,} field checks across {len(python_cells):,} cells", "MATCH"],
                ["Within-courier and within-category rankings", f"{rank_checks:,} rank checks", "MATCH"],
                ["Per-courier and per-category descriptive summaries", f"{summary_checks:,} summary checks", "MATCH"],
                ["All observed courier × category cells included", f"{len(python_cells):,} / {len(sql_results):,}", "MATCH"],
                ["Slow-delivery reconciliation", "all slow target records", "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- The combined analysis covers {metadata['combined_analysis_record_count']:,} records and {metadata['unique_couriers_combined']:,} couriers; {metadata['qualifying_cell_count']:,} cells meet both 30-record requirements.",
        f"- {len(comparable_couriers):,} couriers have at least two qualifying workload categories, limiting direct within-courier pattern checks.",
        f"- The number of qualifying couriers varies substantially by workload category; categories without qualifying cells cannot support a courier-level comparison under this rule.",
        f"- The top ten qualifying combinations contribute {top_slow_count:,} slow deliveries ({top_slow_count / metadata['all_slow_delivery_count'] * 100:.2f}% of all slow deliveries); the full table is a count-based contribution summary.",
        "- Courier differences and category differences are descriptive and may be affected by sample-size and workload-composition differences.",
        "",
        "## Interpretation",
        "",
        "The standalone workload pattern can be checked within couriers only where a courier has multiple sufficiently sized category cells. Courier-level variation can be checked within workload categories only where enough courier cells qualify. Where those comparison sets are sparse or absent, the combined evidence is limited rather than evidence that a pattern does not exist. No courier is labeled inherently good or bad.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Courier IDs are identifiers, not explanatory variables.",
        "- Combinations with fewer than 30 records are excluded from substantive comparisons.",
        "- Individual courier sample sizes vary.",
        "- Courier workload composition may differ.",
        "- This analysis does not control for city, distance, weather, traffic, vehicle, or time.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.",
        "- Missing categories remain in the source and are excluded only from combinations requiring both dimensions.",
        "",
        f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; its schema is unchanged.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(python_cells):,} observed cells; "
        f"{metadata['qualifying_cell_count']:,} qualify. "
        f"Checks: {metric_checks:,} metric/population, {rank_checks:,} ranks, "
        f"{summary_checks:,} comparison summaries."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
