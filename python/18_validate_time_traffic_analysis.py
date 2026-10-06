"""Validate the Time x Traffic SQL analysis and generate its report."""

import hashlib
from pathlib import Path
import re
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "15_time_traffic_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "time_traffic_analysis.md"
TARGET = "Time_taken(min)"
ORDER_TIME = "Time_Orderd"
TRAFFIC = "Road_traffic_density"
SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABS_TOL = 1e-9
REL_TOL = 1e-12

TIME_BANDS = ("Night", "Morning", "Afternoon", "Evening", "Late Night")
TIME_BAND_ORDER = {band: index for index, band in enumerate(TIME_BANDS)}
TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d\Z")

COUNT_FIELDS = ("delivery_count", "slow_delivery_count")
FLOAT_FIELDS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
TIME_RANK_FIELDS = (
    "mean_rank_within_time",
    "highest_mean_rank_within_time",
    "slow_rate_rank_within_time",
    "highest_slow_rate_rank_within_time",
)
TRAFFIC_RANK_FIELDS = (
    "mean_rank_within_traffic",
    "highest_mean_rank_within_traffic",
    "slow_rate_rank_within_traffic",
    "highest_slow_rate_rank_within_traffic",
)
STANDALONE_FIELDS = (
    "standalone_traffic_count",
    "standalone_traffic_mean",
    "standalone_traffic_slow_count",
    "standalone_traffic_slow_rate",
    "standalone_time_count",
    "standalone_time_mean",
    "standalone_time_slow_count",
    "standalone_time_slow_rate",
)
POPULATION_FIELDS = (
    "total_train_rows",
    "valid_target_count",
    "valid_order_time_count",
    "missing_invalid_order_time_count",
    "valid_traffic_count",
    "missing_traffic_count",
    "valid_time_missing_traffic_count",
    "invalid_time_valid_traffic_count",
    "excluded_for_missing_either_count",
    "all_slow_delivery_count",
    "excluded_slow_delivery_count",
    "combined_analysis_record_count",
    "slow_delivery_count_in_qualifying_cells",
    "slow_delivery_count_in_subminimum_cells",
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


def classify_time(value: object) -> tuple[float | None, str | None]:
    """Strictly parse the established HH:MM:SS order-time format and bands."""
    if pd.isna(value):
        return None, None
    text = str(value)
    if not TIME_PATTERN.fullmatch(text):
        return None, None
    parsed = pd.to_datetime(text, format="%H:%M:%S", errors="coerce")
    if pd.isna(parsed):
        return None, None
    minutes = float(parsed.hour * 60 + parsed.minute) + parsed.second / 60.0
    hour = int(minutes // 60)
    if 0 <= hour <= 5:
        band = "Night"
    elif 6 <= hour <= 11:
        band = "Morning"
    elif 12 <= hour <= 16:
        band = "Afternoon"
    elif 17 <= hour <= 20:
        band = "Evening"
    elif 21 <= hour <= 23:
        band = "Late Night"
    else:
        return None, None
    return minutes, band


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        return pd.read_sql_query(query, connection), sqlite3.sqlite_version
    finally:
        connection.close()


def rank_groups(
    groups: pd.DataFrame,
    partition: str,
    metric: str,
    ascending: bool,
) -> pd.Series:
    eligible = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    ranks = pd.Series(np.nan, index=groups.index, dtype="float64")
    ranks.loc[eligible.index] = eligible.groupby(partition)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return ranks


def calculate_python(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame, pd.DataFrame]:
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [ORDER_TIME, TRAFFIC]].copy()
    valid[TARGET] = target.loc[valid_mask].astype("float64")
    parsed = valid[ORDER_TIME].map(classify_time)
    valid["order_minutes"] = parsed.map(lambda value: value[0])
    valid["time_band"] = parsed.map(lambda value: value[1])

    traffic_categories = sorted(
        valid.loc[valid[TRAFFIC].notna(), TRAFFIC].astype(str).unique().tolist()
    )
    categorized = valid.dropna(subset=["time_band", TRAFFIC]).copy()
    categorized["traffic_category"] = categorized[TRAFFIC].astype(str)

    rows: list[dict[str, object]] = []
    for band in TIME_BANDS:
        for traffic in traffic_categories:
            group = categorized.loc[
                (categorized["time_band"] == band)
                & (categorized["traffic_category"] == traffic)
            ]
            values = group[TARGET].to_numpy(dtype="float64")
            count = len(values)
            slow_count = int((values > SLOW_THRESHOLD).sum())
            if count:
                mean = float(np.mean(values))
                median = float(np.percentile(values, 50, method="linear"))
                p90 = float(np.percentile(values, 90, method="linear"))
                rate = slow_count / count
            else:
                mean = median = p90 = rate = np.nan
            rows.append(
                {
                    "time_band": band,
                    "sort_order": TIME_BAND_ORDER[band] + 1,
                    "traffic_category": traffic,
                    "delivery_count": count,
                    "mean_delivery_time": mean,
                    "median_delivery_time": median,
                    "p90_delivery_time": p90,
                    "slow_delivery_count": slow_count,
                    "slow_delivery_rate": rate,
                    "sample_size_status": (
                        "qualifies" if count >= MIN_GROUP_SIZE else "small_sample"
                    ),
                }
            )
    groups = pd.DataFrame(rows)
    rank_specs = (
        ("mean_rank_within_time", "time_band", "mean_delivery_time", True),
        ("highest_mean_rank_within_time", "time_band", "mean_delivery_time", False),
        ("slow_rate_rank_within_time", "time_band", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_time", "time_band", "slow_delivery_rate", False),
        ("mean_rank_within_traffic", "traffic_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_traffic", "traffic_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", False),
    )
    for output, partition, metric, ascending in rank_specs:
        groups[output] = rank_groups(groups, partition, metric, ascending)

    standalone_traffic = (
        valid.dropna(subset=[TRAFFIC])
        .assign(traffic_category=lambda table: table[TRAFFIC].astype(str))
        .groupby("traffic_category", sort=True)
        .agg(
            standalone_traffic_count=(TARGET, "size"),
            standalone_traffic_mean=(TARGET, "mean"),
            standalone_traffic_slow_count=(
                TARGET,
                lambda values: int((values > SLOW_THRESHOLD).sum()),
            ),
        )
    )
    standalone_traffic["standalone_traffic_slow_rate"] = (
        standalone_traffic["standalone_traffic_slow_count"]
        / standalone_traffic["standalone_traffic_count"]
    )
    standalone_time = (
        valid.dropna(subset=["time_band"])
        .groupby("time_band", sort=False)
        .agg(
            standalone_time_count=(TARGET, "size"),
            standalone_time_mean=(TARGET, "mean"),
            standalone_time_slow_count=(
                TARGET,
                lambda values: int((values > SLOW_THRESHOLD).sum()),
            ),
        )
    )
    standalone_time["standalone_time_slow_rate"] = (
        standalone_time["standalone_time_slow_count"]
        / standalone_time["standalone_time_count"]
    )
    groups["standalone_traffic_count"] = groups["traffic_category"].map(
        standalone_traffic["standalone_traffic_count"]
    )
    groups["standalone_traffic_mean"] = groups["traffic_category"].map(
        standalone_traffic["standalone_traffic_mean"]
    )
    groups["standalone_traffic_slow_count"] = groups["traffic_category"].map(
        standalone_traffic["standalone_traffic_slow_count"]
    )
    groups["standalone_traffic_slow_rate"] = groups["traffic_category"].map(
        standalone_traffic["standalone_traffic_slow_rate"]
    )
    groups["standalone_time_count"] = groups["time_band"].map(
        standalone_time["standalone_time_count"]
    )
    groups["standalone_time_mean"] = groups["time_band"].map(
        standalone_time["standalone_time_mean"]
    )
    groups["standalone_time_slow_count"] = groups["time_band"].map(
        standalone_time["standalone_time_slow_count"]
    )
    groups["standalone_time_slow_rate"] = groups["time_band"].map(
        standalone_time["standalone_time_slow_rate"]
    )

    missing_time = valid["time_band"].isna()
    missing_traffic = valid[TRAFFIC].isna()
    slow_mask = valid[TARGET] > SLOW_THRESHOLD
    valid_order = valid["order_minutes"].notna()
    combined_slow = int((categorized[TARGET] > SLOW_THRESHOLD).sum())
    subminimum = groups.loc[groups["delivery_count"] < MIN_GROUP_SIZE]
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "valid_order_time_count": int(valid_order.sum()),
        "missing_invalid_order_time_count": int(missing_time.sum()),
        "valid_traffic_count": int((~missing_traffic).sum()),
        "missing_traffic_count": int(missing_traffic.sum()),
        "valid_time_missing_traffic_count": int((~missing_time & missing_traffic).sum()),
        "invalid_time_valid_traffic_count": int((missing_time & ~missing_traffic).sum()),
        "excluded_for_missing_either_count": int((missing_time | missing_traffic).sum()),
        "all_slow_delivery_count": int(slow_mask.sum()),
        "excluded_slow_delivery_count": int((slow_mask & (missing_time | missing_traffic)).sum()),
        "combined_analysis_record_count": len(categorized),
        "slow_delivery_count_in_qualifying_cells": int(
            groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE, "slow_delivery_count"].sum()
        ),
        "slow_delivery_count_in_subminimum_cells": int(
            subminimum["slow_delivery_count"].sum()
        ),
        "slow_delivery_count_in_combined_population": combined_slow,
    }
    return groups, metadata, standalone_traffic.reset_index(), standalone_time.reset_index()


def validate(
    sql: pd.DataFrame,
    python: pd.DataFrame,
    metadata: dict[str, int],
) -> tuple[int, int, int]:
    keys = ["time_band", "traffic_category"]
    sql_idx = sql.set_index(keys).sort_index()
    py_idx = python.set_index(keys).sort_index()
    if not sql_idx.index.equals(py_idx.index):
        raise AssertionError("SQL and Python Time x Traffic grids differ.")
    metric_checks = time_rank_checks = traffic_rank_checks = 0
    for key in sql_idx.index:
        sql_row, py_row = sql_idx.loc[key], py_idx.loc[key]
        for field in COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key}: {field} differs.")
            metric_checks += 1
        if int(sql_row["sort_order"]) != int(py_row["sort_order"]):
            raise AssertionError(f"{key}: time-band order differs.")
        metric_checks += 1
        if str(sql_row["sample_size_status"]) != str(py_row["sample_size_status"]):
            raise AssertionError(f"{key}: sample eligibility differs.")
        metric_checks += 1
        for field in FLOAT_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or not close_enough(float(left), float(right)):
                raise AssertionError(f"{key}: {field} differs.")
            metric_checks += 1
        for field in TIME_RANK_FIELDS + TRAFFIC_RANK_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or int(left) != int(right):
                raise AssertionError(f"{key}: {field} differs.")
            if field in TIME_RANK_FIELDS:
                time_rank_checks += 1
            else:
                traffic_rank_checks += 1
        for field in STANDALONE_FIELDS:
            left, right = sql_row[field], py_row[field]
            if field.endswith(("_count", "_slow_count")):
                if int(left) != int(right):
                    raise AssertionError(f"{key}: {field} differs.")
            elif not close_enough(float(left), float(right)):
                raise AssertionError(f"{key}: {field} differs.")
            metric_checks += 1
    first = sql.iloc[0]
    for field in POPULATION_FIELDS:
        if int(first[field]) != metadata[field]:
            raise AssertionError(
                f"Population mismatch {field}: {first[field]} != {metadata[field]}"
            )
        metric_checks += 1
    return metric_checks, time_rank_checks, traffic_rank_checks


def order_text(
    subset: pd.DataFrame,
    metric: str,
    ascending: bool,
) -> str:
    subset = subset.loc[subset["delivery_count"] >= MIN_GROUP_SIZE]
    if subset.empty:
        return "No qualifying combinations"
    sorted_subset = subset.sort_values(
        metric, ascending=ascending, kind="stable"
    )
    return " → ".join(sorted_subset["traffic_category"].astype(str))


def best_worst_rows(
    groups: pd.DataFrame,
    partition: str,
    partition_values: list[str],
    comparison_label: str,
) -> list[list[object]]:
    rows = []
    for value in partition_values:
        subset = groups.loc[groups[partition] == value].copy()
        eligible = subset.loc[subset["delivery_count"] >= MIN_GROUP_SIZE]
        if eligible.empty:
            rows.append([value, "0", "No qualifying comparisons"])
            continue
        low_mean = eligible.loc[eligible["mean_delivery_time"].idxmin()]
        high_mean = eligible.loc[eligible["mean_delivery_time"].idxmax()]
        low_rate = eligible.loc[eligible["slow_delivery_rate"].idxmin()]
        high_rate = eligible.loc[eligible["slow_delivery_rate"].idxmax()]

        def describe(row: pd.Series, metric: str, as_rate: bool = False) -> str:
            result = float(row[metric])
            rendered = f"{result * 100:.4f}%" if as_rate else f"{result:.4f} min"
            return (
                f"{row[comparison_label]} (n={int(row['delivery_count']):,}; "
                f"{rendered}; median {fmt(float(row['median_delivery_time']))}; "
                f"P90 {fmt(float(row['p90_delivery_time']))})"
            )

        rows.append(
            [
                value,
                int(len(eligible)),
                "Lowest/highest mean: "
                + describe(low_mean, "mean_delivery_time")
                + " / "
                + describe(high_mean, "mean_delivery_time")
                + "; lowest/highest slow rate: "
                + describe(low_rate, "slow_delivery_rate", True)
                + " / "
                + describe(high_rate, "slow_delivery_rate", True),
            ]
        )
    return rows


def category_metrics(
    groups: pd.DataFrame,
    partition: str,
    category_values: list[str],
    group_value: str,
) -> list[list[object]]:
    rows = []
    for category in category_values:
        subset = groups.loc[
            (groups[partition] == category)
            & (groups["delivery_count"] >= MIN_GROUP_SIZE)
        ].copy()
        if subset.empty:
            rows.append([category, "0", "No qualifying combinations"])
            continue
        rows.append(
            [
                category,
                len(subset),
                "; ".join(
                    f"{getattr(row, group_value)} (n={int(row.delivery_count):,}; "
                    f"mean {fmt(float(row.mean_delivery_time))}; "
                    f"median {fmt(float(row.median_delivery_time))}; "
                    f"P90 {fmt(float(row.p90_delivery_time))}; "
                    f"slow {int(row.slow_delivery_count):,}/{int(row.delivery_count):,} "
                    f"({float(row.slow_delivery_rate) * 100:.4f}%))"
                    for row in (
                        subset.sort_values("sort_order")
                        if group_value == "traffic_category"
                        and partition == "time_band"
                        else subset.sort_values(group_value)
                    ).itertuples()
                ),
            ]
        )
    return rows


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET, ORDER_TIME, TRAFFIC]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Required columns are missing: {missing}")

    python_groups, metadata, standalone_traffic, standalone_time = calculate_python(frame)
    sql_groups, sqlite_version = run_sql(
        frame, SQL_PATH.read_text(encoding="utf-8")
    )
    if sql_groups.empty:
        raise AssertionError("SQL returned no Time x Traffic combinations.")
    metric_checks, time_rank_checks, traffic_rank_checks = validate(
        sql_groups, python_groups, metadata
    )
    if int(python_groups["delivery_count"].sum()) != metadata["combined_analysis_record_count"]:
        raise AssertionError("Two-way delivery counts do not reconcile.")
    if (
        metadata["slow_delivery_count_in_qualifying_cells"]
        + metadata["slow_delivery_count_in_subminimum_cells"]
        + metadata["excluded_slow_delivery_count"]
        != metadata["all_slow_delivery_count"]
    ):
        raise AssertionError("Slow-delivery counts do not reconcile.")

    traffic_categories = sorted(
        python_groups["traffic_category"].unique().tolist()
    )
    qualifying = python_groups.loc[
        python_groups["delivery_count"] >= MIN_GROUP_SIZE
    ].copy()
    subminimum = python_groups.loc[
        python_groups["delivery_count"] < MIN_GROUP_SIZE
    ].copy()

    grid_rows = []
    for row in python_groups.sort_values(
        ["sort_order", "traffic_category"]
    ).itertuples(index=False):
        count, slow = int(row.delivery_count), int(row.slow_delivery_count)
        grid_rows.append(
            [
                row.time_band,
                row.traffic_category,
                f"{count:,}",
                "—" if pd.isna(row.mean_delivery_time) else fmt(float(row.mean_delivery_time)),
                "—" if pd.isna(row.median_delivery_time) else fmt(float(row.median_delivery_time)),
                "—" if pd.isna(row.p90_delivery_time) else fmt(float(row.p90_delivery_time)),
                f"{slow:,}",
                f"{slow:,} / {count:,}" if count else "0 / 0",
                "—" if pd.isna(row.slow_delivery_rate) else f"{float(row.slow_delivery_rate) * 100:.4f}%",
                "Qualifies" if count >= MIN_GROUP_SIZE else "Small sample; descriptive only",
            ]
        )

    within_time_rows = best_worst_rows(
        python_groups, "time_band", list(TIME_BANDS), "traffic_category"
    )
    within_time_details = category_metrics(
        python_groups, "time_band", list(TIME_BANDS), "traffic_category"
    )
    within_traffic_rows = best_worst_rows(
        python_groups, "traffic_category", traffic_categories, "time_band"
    )
    within_traffic_details = category_metrics(
        python_groups, "traffic_category", traffic_categories, "time_band"
    )

    standalone_traffic["mean_rank"] = standalone_traffic[
        "standalone_traffic_mean"
    ].rank(method="min")
    standalone_traffic["slow_rate_rank"] = standalone_traffic[
        "standalone_traffic_slow_rate"
    ].rank(method="min")
    standalone_time["mean_rank"] = standalone_time[
        "standalone_time_mean"
    ].rank(method="min")
    standalone_time["slow_rate_rank"] = standalone_time[
        "standalone_time_slow_rate"
    ].rank(method="min")
    standalone_traffic_mean_order = standalone_traffic.sort_values(
        "standalone_traffic_mean", ascending=False
    )["traffic_category"].tolist()
    standalone_traffic_rate_order = standalone_traffic.sort_values(
        "standalone_traffic_slow_rate", ascending=False
    )["traffic_category"].tolist()
    standalone_time_mean_order = standalone_time.sort_values(
        "standalone_time_mean", ascending=False
    )["time_band"].tolist()
    standalone_time_rate_order = standalone_time.sort_values(
        "standalone_time_slow_rate", ascending=False
    )["time_band"].tolist()

    traffic_signal_rows = []
    traffic_rank_agreement_rows = []
    traffic_mean_gaps = []
    traffic_slow_gaps = []
    traffic_pair_order_totals = {
        "mean_delivery_time": [0, 0],
        "slow_delivery_rate": [0, 0],
    }
    for band in TIME_BANDS:
        subset = qualifying.loc[qualifying["time_band"] == band].copy()
        mean_order = order_text(subset, "mean_delivery_time", False)
        rate_order = order_text(subset, "slow_delivery_rate", False)
        if len(subset) >= 2:
            traffic_mean_gaps.append(
                float(subset["mean_delivery_time"].max() - subset["mean_delivery_time"].min())
            )
            traffic_slow_gaps.append(
                float(subset["slow_delivery_rate"].max() - subset["slow_delivery_rate"].min())
            )
        traffic_signal_rows.append([band, mean_order, rate_order, len(subset)])
        for metric in ("mean_delivery_time", "slow_delivery_rate"):
            eligible_standalone = standalone_traffic.loc[
                standalone_traffic["traffic_category"].isin(subset["traffic_category"])
            ].sort_values(f"standalone_{'traffic_mean' if metric == 'mean_delivery_time' else 'traffic_slow_rate'}", ascending=False)
            standalone_order = eligible_standalone["traffic_category"].tolist()
            observed_order = subset.sort_values(metric, ascending=False)["traffic_category"].tolist()
            if len(standalone_order) > 1 and len(observed_order) > 1:
                pos_standalone = {value: i for i, value in enumerate(standalone_order)}
                pos_observed = {value: i for i, value in enumerate(observed_order)}
                pairs = concordant_pairs = 0
                for index, left in enumerate(standalone_order):
                    for right in standalone_order[index + 1:]:
                        pairs += 1
                        if (pos_standalone[left] - pos_standalone[right]) * (
                            pos_observed[left] - pos_observed[right]
                        ) > 0:
                            concordant_pairs += 1
                traffic_pair_order_totals[metric][0] += concordant_pairs
                traffic_pair_order_totals[metric][1] += pairs
                agreement = f"{concordant_pairs}/{pairs} pair orders preserved"
            else:
                agreement = "Not enough qualifying categories"
            traffic_rank_agreement_rows.append(
                [band, metric.replace("_", " "), " > ".join(observed_order), agreement]
            )

    time_signal_rows = []
    time_mean_gaps = []
    time_slow_gaps = []
    time_rank_agreement_rows = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic].copy()
        mean_order = " → ".join(
            subset.sort_values("mean_delivery_time", ascending=False)["time_band"]
        )
        rate_order = " → ".join(
            subset.sort_values("slow_delivery_rate", ascending=False)["time_band"]
        )
        if len(subset) >= 2:
            time_mean_gaps.append(
                float(subset["mean_delivery_time"].max() - subset["mean_delivery_time"].min())
            )
            time_slow_gaps.append(
                float(subset["slow_delivery_rate"].max() - subset["slow_delivery_rate"].min())
            )
        time_signal_rows.append([traffic, len(subset), mean_order, rate_order])
        for metric, standalone_order in (
            ("mean_delivery_time", standalone_time_mean_order),
            ("slow_delivery_rate", standalone_time_rate_order),
        ):
            observed_order = subset.sort_values(metric, ascending=False)["time_band"].tolist()
            shared_categories = [band for band in standalone_order if band in observed_order]
            if len(shared_categories) > 1:
                standalone_filtered = [band for band in standalone_order if band in shared_categories]
                observed_filtered = [band for band in observed_order if band in shared_categories]
                pos_standalone = {value: i for i, value in enumerate(standalone_filtered)}
                pos_observed = {value: i for i, value in enumerate(observed_filtered)}
                pairs = concordant_pairs = 0
                for index, left in enumerate(standalone_filtered):
                    for right in standalone_filtered[index + 1:]:
                        pairs += 1
                        if (pos_standalone[left] - pos_standalone[right]) * (
                            pos_observed[left] - pos_observed[right]
                        ) > 0:
                            concordant_pairs += 1
                agreement = f"{concordant_pairs}/{pairs} pair orders preserved"
            else:
                agreement = "Not enough qualifying bands"
            time_rank_agreement_rows.append(
                [
                    traffic,
                    metric.replace("_", " "),
                    " > ".join(observed_order) if observed_order else "No qualifying bands",
                    agreement,
                ]
            )

    standalone_traffic_order_rows = []
    for _, row in standalone_traffic.sort_values("traffic_category").iterrows():
        standalone_traffic_order_rows.append(
            [
                row["traffic_category"],
                f"{int(row['standalone_traffic_count']):,}",
                fmt(float(row["standalone_traffic_mean"])),
                f"{float(row['standalone_traffic_slow_rate']) * 100:.4f}%",
            ]
        )
    standalone_time_rows = []
    for band in TIME_BANDS:
        row = standalone_time.loc[standalone_time["time_band"] == band].iloc[0]
        standalone_time_rows.append(
            [
                band,
                f"{int(row['standalone_time_count']):,}",
                fmt(float(row["standalone_time_mean"])),
                f"{float(row['standalone_time_slow_rate']) * 100:.4f}%",
            ]
        )

    top_combinations = qualifying.sort_values(
        ["slow_delivery_count", "delivery_count"],
        ascending=[False, False],
        kind="stable",
    ).head(5)
    top_slow_count = int(top_combinations["slow_delivery_count"].sum())
    contribution_rows = []
    for row in top_combinations.itertuples(index=False):
        count, slow = int(row.delivery_count), int(row.slow_delivery_count)
        contribution_rows.append(
            [
                row.time_band,
                row.traffic_category,
                f"{count:,}",
                f"{slow:,}",
                f"{float(row.slow_delivery_rate) * 100:.4f}%",
                fmt(float(row.mean_delivery_time)),
                fmt(float(row.median_delivery_time)),
                fmt(float(row.p90_delivery_time)),
                f"{slow:,} / {metadata['all_slow_delivery_count']:,} "
                f"({slow / metadata['all_slow_delivery_count'] * 100:.2f}%)",
            ]
        )
    subminimum_rows = []
    for row in subminimum.sort_values(
        ["slow_delivery_rate", "delivery_count"],
        ascending=[False, False],
        na_position="last",
    ).itertuples(index=False):
        if int(row.delivery_count) == 0:
            continue
        subminimum_rows.append(
            [
                row.time_band,
                row.traffic_category,
                int(row.delivery_count),
                int(row.slow_delivery_count),
                f"{float(row.slow_delivery_rate) * 100:.4f}%",
            ]
        )

    common_traffic = {"Jam", "Low"}
    jam_low_rows = []
    jam_low_mean_gaps = []
    jam_low_rate_gaps = []
    for band in TIME_BANDS:
        subset = qualifying.loc[
            (qualifying["time_band"] == band)
            & qualifying["traffic_category"].isin(common_traffic)
        ].set_index("traffic_category")
        if common_traffic.issubset(subset.index):
            jam_mean = float(subset.loc["Jam", "mean_delivery_time"])
            low_mean = float(subset.loc["Low", "mean_delivery_time"])
            jam_rate = float(subset.loc["Jam", "slow_delivery_rate"])
            low_rate = float(subset.loc["Low", "slow_delivery_rate"])
            mean_gap = jam_mean - low_mean
            rate_gap = jam_rate - low_rate
            jam_low_mean_gaps.append(mean_gap)
            jam_low_rate_gaps.append(rate_gap)
            jam_low_rows.append(
                [
                    band,
                    fmt(mean_gap) + " min",
                    f"{rate_gap * 100:+.4f} pp",
                ]
            )
    standalone_traffic_index = standalone_traffic.set_index("traffic_category")
    standalone_jam_low_mean_gap = (
        float(standalone_traffic_index.loc["Jam", "standalone_traffic_mean"])
        - float(standalone_traffic_index.loc["Low", "standalone_traffic_mean"])
    )
    standalone_jam_low_rate_gap = (
        float(standalone_traffic_index.loc["Jam", "standalone_traffic_slow_rate"])
        - float(standalone_traffic_index.loc["Low", "standalone_traffic_slow_rate"])
    )
    evening_traffic = set(
        qualifying.loc[
            qualifying["time_band"] == "Evening", "traffic_category"
        ]
    )
    morning_traffic = set(
        qualifying.loc[
            qualifying["time_band"] == "Morning", "traffic_category"
        ]
    )
    shared_evening_morning_traffic = evening_traffic.intersection(morning_traffic)

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training CSV changed during validation.")

    lines = [
        "# Time × Traffic Analysis",
        "",
        "## Objective",
        "",
        "Describe whether traffic-related delivery-performance differences remain visible across the established order-time bands, and whether time-of-day patterns remain visible within traffic categories. This is observational analysis only.",
        "",
        "## Analytical Context",
        "",
        "The standalone Traffic analysis found the longest observed delivery times and highest slow-delivery rate in Jam, while Low had the shortest times and lowest slow rate. The standalone Time analysis found higher order-time means and slow rates in Evening than Morning. This combined analysis checks those descriptive patterns within the second dimension.",
        "",
        "Standalone traffic results:",
        "",
        *markdown_table(
            ["Traffic category", "Count", "Mean (min)", "Slow rate"],
            standalone_traffic_order_rows,
        ),
        "",
        "Standalone order-time results:",
        "",
        *markdown_table(
            ["Time band", "Count", "Mean (min)", "Slow rate"],
            standalone_time_rows,
        ),
        "",
        "## Data Coverage",
        "",
        f"- Total valid-target records: **{metadata['valid_target_count']:,}** of {metadata['total_train_rows']:,}.",
        f"- Valid order times: **{metadata['valid_order_time_count']:,}**.",
        f"- Missing/invalid order times: **{metadata['missing_invalid_order_time_count']:,}**.",
        f"- Valid-target records with missing traffic: **{metadata['missing_traffic_count']:,}**.",
        f"- Valid time but missing traffic: **{metadata['valid_time_missing_traffic_count']:,}**; invalid time but valid traffic: **{metadata['invalid_time_valid_traffic_count']:,}**.",
        f"- Records with both a valid time band and traffic category: **{metadata['combined_analysis_record_count']:,}**.",
        f"- Records excluded from the two-way grouping due to at least one missing/invalid dimension: **{metadata['excluded_for_missing_either_count']:,}**.",
        "Missing and invalid dimensions are reported rather than assigned a fabricated band or traffic category; no source rows are modified.",
        "",
        "## Time-Band Method",
        "",
        "`Time_Orderd` is parsed strictly as `HH:MM:SS`, then converted to minutes after midnight. The classification is inherited unchanged from Step 5.7: Night (00:00–05:59), Morning (06:00–11:59), Afternoon (12:00–16:59), Evening (17:00–20:59), and Late Night (21:00–23:59). Values that are missing, malformed, or outside a valid clock time are not classified and are counted separately.",
        "",
        "## Two-Way Analysis",
        "",
        "Slow delivery is the fixed global condition `Time_taken(min) > 40`. Medians and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (`numpy.percentile(method='linear')`). All five established time bands crossed with each observed non-missing traffic category are shown. Cells with fewer than 30 records are descriptive only and excluded from substantive comparisons and rankings.",
        "",
        "### Time × Traffic Results",
        "",
        *markdown_table(
            ["Time band", "Traffic", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow count / n", "Slow rate", "Status"],
            grid_rows,
        ),
        "",
        "## Within-Time Traffic Comparison",
        "",
        "For each time band, extrema are selected only among cells with at least 30 records. Counts, means, medians, P90, and slow rates are included in the extrema descriptions; the complete cell metrics are available above.",
        "",
        *markdown_table(
            ["Time band", "Qualifying traffic categories", "Traffic extrema by mean and slow rate"],
            within_time_rows,
        ),
        "",
        "Qualifying traffic-category detail by time band:",
        "",
        *markdown_table(
            ["Time band", "Qualifying traffic categories", "Category metrics"],
            within_time_details,
        ),
        "",
        "Qualifying traffic categories ordered from highest to lowest within each time band:",
        "",
        *markdown_table(
            ["Time band", "Mean order", "Slow-rate order", "Qualifying cells"],
            traffic_signal_rows,
        ),
        "",
        "## Within-Traffic Time Comparison",
        "",
        "Only time bands with at least 30 records for a given traffic category are compared. The detailed table includes the category-level count, mean, median, P90, and slow-delivery rate.",
        "",
        *markdown_table(
            ["Traffic category", "Qualifying time bands", "Time-band metrics"],
            within_traffic_details,
        ),
        "",
        "For each traffic category, lowest/highest mean and slow-rate time-band extrema:",
        "",
        *markdown_table(
            ["Traffic category", "Qualifying time bands", "Extrema with count, median, and P90"],
            within_traffic_rows,
        ),
        "",
        "## Traffic Signal Check",
        "",
        f"The standalone traffic mean order (highest to lowest) is `{ ' > '.join(standalone_traffic_mean_order) }`; its slow-rate order is `{ ' > '.join(standalone_traffic_rate_order) }`. No time band has qualifying cells for all four traffic categories, so a full four-category order comparison is unavailable. Among qualifying pairwise category comparisons, {traffic_pair_order_totals['mean_delivery_time'][0]}/{traffic_pair_order_totals['mean_delivery_time'][1]} mean-order pairs and {traffic_pair_order_totals['slow_delivery_rate'][0]}/{traffic_pair_order_totals['slow_delivery_rate'][1]} slow-rate-order pairs preserve their standalone pairwise order. These partial comparisons do not establish complete rank stability.",
        "",
        *markdown_table(
            ["Time band", "Metric", "Within-band order, high to low", "Agreement with standalone order"],
            traffic_rank_agreement_rows,
        ),
        "",
        "Jam versus Low mean/slow-rate gaps, where both cells qualify:",
        "",
        *markdown_table(
            ["Time band", "Jam − Low mean difference", "Jam − Low slow-rate difference"],
            jam_low_rows
            or [["No band", "Not comparable", "Not comparable"]],
        ),
        "",
        f"Jam versus Low is the strongest standalone contrast: the mean gap is {standalone_jam_low_mean_gap:.4f} minutes and the slow-rate gap is {standalone_jam_low_rate_gap * 100:.4f} percentage points. They both have qualifying cells together in {len(jam_low_rows)} time band(s); those within-band gaps are shown above.",
        "",
        "## Time Signal Check",
        "",
        f"The standalone time-band mean order (highest to lowest) is `{ ' > '.join(standalone_time_mean_order) }`; its slow-rate order is `{ ' > '.join(standalone_time_rate_order) }`. No traffic category has qualifying cells in both Morning and Evening (shared categories: {', '.join(sorted(shared_evening_morning_traffic)) if shared_evening_morning_traffic else 'none'}), so the standalone strongest-versus-weakest time-band contrast cannot be evaluated within a common traffic stratum. Other within-traffic band orders and qualifying counts are shown below; missing strata do not establish that a temporal pattern disappears.",
        "",
        *markdown_table(
            ["Traffic category", "Qualifying time bands", "Mean order (high to low)", "Slow-rate order (high to low)"],
            time_signal_rows,
        ),
        "",
        "Within-traffic time-band rank-order agreement with the standalone time order:",
        "",
        *markdown_table(
            ["Traffic category", "Metric", "Within-traffic time order", "Agreement with standalone order"],
            time_rank_agreement_rows,
        ),
        "",
        f"Across strata with at least two qualifying bands, mean ranges vary from {fmt(min(time_mean_gaps)) if time_mean_gaps else 'not comparable'} to {fmt(max(time_mean_gaps)) if time_mean_gaps else 'not comparable'} minutes; slow-rate ranges vary from {min(time_slow_gaps) * 100:.4f} to {max(time_slow_gaps) * 100:.4f} percentage points." if time_slow_gaps else "No traffic category has at least two qualifying time bands.",
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, **{metadata['all_slow_delivery_count']:,}** deliveries are slow. **{metadata['slow_delivery_count_in_qualifying_cells']:,}** occur in qualifying cells, **{metadata['slow_delivery_count_in_subminimum_cells']:,}** in subminimum cells, and **{metadata['excluded_slow_delivery_count']:,}** in records with at least one missing/invalid dimension. The five qualifying combinations with the largest slow counts account for **{top_slow_count:,} ({top_slow_count / metadata['all_slow_delivery_count'] * 100:.2f}%)** of all slow deliveries.",
        "",
        *markdown_table(
            ["Time band", "Traffic", "Count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            contribution_rows,
        ),
        "",
        "Subminimum nonempty cells, shown descriptively and excluded from rankings:",
        "",
        *markdown_table(
            ["Time band", "Traffic", "Count", "Slow count", "Slow rate"],
            subminimum_rows or [["None", "—", "—", "—", "No nonempty subminimum cells"]],
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"SQL from `sql/15_time_traffic_analysis.sql` ran against an in-memory SQLite {sqlite_version} table. Python independently parsed `Time_Orderd`, applied the Step 5.7 time-band boundaries, and grouped the same target records. Counts, categories, and ranks were checked exactly; floating-point metrics use absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Cell metrics, standalone references, time-band order, and population counts", metric_checks, "MATCH"],
                ["Within-time traffic rankings", time_rank_checks, "MATCH"],
                ["Within-traffic time rankings", traffic_rank_checks, "MATCH"],
                ["All established time bands × observed traffic categories", f"{len(python_groups)} / {len(sql_groups)}", "MATCH"],
                ["Slow-delivery population reconciliation", "all slow target records", "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- The combined analysis includes {metadata['combined_analysis_record_count']:,} of {metadata['valid_target_count']:,} valid-target records; {metadata['missing_invalid_order_time_count']:,} lack a valid order time, while {metadata['missing_traffic_count']:,} lack traffic.",
        f"- No time band supports a full four-category traffic comparison. Of qualifying pairwise comparisons, {traffic_pair_order_totals['mean_delivery_time'][0]}/{traffic_pair_order_totals['mean_delivery_time'][1]} mean and {traffic_pair_order_totals['slow_delivery_rate'][0]}/{traffic_pair_order_totals['slow_delivery_rate'][1]} slow-rate orders match the standalone pairwise ordering.",
        f"- The standalone time-band mean order is { ' > '.join(standalone_time_mean_order) }; within-traffic orders and coverage are shown in the signal-check table.",
        f"- Jam and Low are jointly comparable in {len(jam_low_rows)} time band(s), and no traffic category has qualifying Morning and Evening cells to assess the strongest standalone time contrast within that traffic stratum.",
        f"- The five largest qualifying cells represent {top_slow_count:,}/{metadata['all_slow_delivery_count']:,} slow deliveries ({top_slow_count / metadata['all_slow_delivery_count'] * 100:.2f}%).",
        "- Small groups remain visible in the main table but are not used as if equally reliable in rankings or substantive comparisons.",
        "",
        "## Interpretation",
        "",
        "The stratified results indicate whether the standalone traffic and time-of-day patterns remain visible in the observed qualifying cells. Changes in ordering, ranges, or missing qualifying cells show where those patterns are not uniform. These descriptive comparisons do not establish that traffic or time of day causes delivery-time differences.",
        "",
        "Pickup-time context from Step 5.7: pickup-time bands also showed time-related differences, and the prior order-to-pickup delay distribution was concentrated in non-negative 0–15 minute intervals. Pickup delay is not regrouped or analyzed in this step and is not part of the Time × Traffic comparison.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.",
        "- Time-of-day and traffic may be related to other operational factors.",
        "- Missing/invalid order-time values reduce the combined-analysis population.",
        "- This analysis does not control for city, distance, weather, vehicle, courier, or multiple deliveries.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.",
        "- Invalid or missing order times were not assigned time bands.",
        "",
        f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; its schema is unchanged.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(sql_groups)} Time x Traffic cells: "
        f"{metric_checks} metric/population checks, {time_rank_checks} within-time "
        f"rank checks, {traffic_rank_checks} within-traffic rank checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
