"""Validate Vehicle x multiple-delivery results against SQLite and write report."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "13_vehicle_multiple_delivery_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "vehicle_multiple_delivery_analysis.md"
TARGET = "Time_taken(min)"
VEHICLE = "Type_of_vehicle"
MULTIPLE = "multiple_deliveries"
SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABS_TOL = 1e-9
REL_TOL = 1e-12

COUNT_FIELDS = ("delivery_count", "slow_delivery_count")
FLOAT_FIELDS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
RANK_FIELDS = (
    "mean_rank_within_vehicle",
    "highest_mean_rank_within_vehicle",
    "slow_rate_rank_within_vehicle",
    "highest_slow_rate_rank_within_vehicle",
    "mean_rank_within_multiple",
    "highest_mean_rank_within_multiple",
    "slow_rate_rank_within_multiple",
    "highest_slow_rate_rank_within_multiple",
)
BASELINE_FIELDS = (
    "standalone_vehicle_count",
    "standalone_vehicle_mean",
    "standalone_vehicle_slow_count",
    "standalone_vehicle_slow_rate",
    "standalone_multiple_count",
    "standalone_multiple_mean",
    "standalone_multiple_slow_count",
    "standalone_multiple_slow_rate",
)


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for source-integrity validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    return bool(np.isclose(left, right, atol=ABS_TOL, rtol=REL_TOL))


def fmt(value: float, decimals: int = 8) -> str:
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def multiple_label(value: object) -> str:
    """Render the cleaned numeric label as a categorical key, not a metric."""
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


def rank_within(
    groups: pd.DataFrame,
    partition: str,
    metric: str,
    ascending: bool,
) -> pd.Series:
    """Match SQLite RANK; leave subminimum cells unranked."""
    qualifying = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    ranks = pd.Series(np.nan, index=groups.index, dtype="float64")
    ranks.loc[qualifying.index] = qualifying.groupby(partition)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return ranks


def calculate_python(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int], list[str], list[str]]:
    """Independently calculate two-way cells, standalone references and coverage."""
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    multiple_values = pd.to_numeric(frame[MULTIPLE], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [VEHICLE]].copy()
    valid[TARGET] = target.loc[valid_mask].astype("float64")
    valid["multiple_category"] = multiple_values.loc[valid_mask].map(
        lambda value: multiple_label(value) if pd.notna(value) else pd.NA
    )

    missing_vehicle = int(valid[VEHICLE].isna().sum())
    missing_multiple = int(valid["multiple_category"].isna().sum())
    missing_either = int(
        (valid[VEHICLE].isna() | valid["multiple_category"].isna()).sum()
    )
    categorized = valid.dropna(subset=[VEHICLE, "multiple_category"]).copy()
    vehicle_categories = sorted(categorized[VEHICLE].astype(str).unique())
    multiple_categories = sorted(
        categorized["multiple_category"].astype(str).unique(),
        key=float,
    )

    rows: list[dict[str, object]] = []
    for vehicle in vehicle_categories:
        for multiple in multiple_categories:
            subset = categorized.loc[
                (categorized[VEHICLE].astype(str) == vehicle)
                & (categorized["multiple_category"] == multiple)
            ]
            count = len(subset)
            slow_count = int((subset[TARGET] > SLOW_THRESHOLD).sum())
            if count:
                values = subset[TARGET].to_numpy(dtype="float64")
                mean = float(np.mean(values))
                median = float(np.percentile(values, 50, method="linear"))
                p90 = float(np.percentile(values, 90, method="linear"))
                rate = slow_count / count
            else:
                mean = median = p90 = rate = np.nan
            rows.append(
                {
                    "vehicle_category": vehicle,
                    "multiple_category": multiple,
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
        ("mean_rank_within_vehicle", "vehicle_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_vehicle", "vehicle_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_vehicle", "vehicle_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_vehicle", "vehicle_category", "slow_delivery_rate", False),
        ("mean_rank_within_multiple", "multiple_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_multiple", "multiple_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_multiple", "multiple_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_multiple", "multiple_category", "slow_delivery_rate", False),
    )
    for output, partition, metric, ascending in rank_specs:
        groups[output] = rank_within(groups, partition, metric, ascending)

    standalone_rows = []
    for vehicle, subset in valid.dropna(subset=[VEHICLE]).groupby(VEHICLE, sort=True):
        n = len(subset)
        slow = int((subset[TARGET] > SLOW_THRESHOLD).sum())
        standalone_rows.append(
            {
                "dimension": "vehicle",
                "category": str(vehicle),
                "standalone_count": n,
                "standalone_mean": float(subset[TARGET].mean()),
                "standalone_slow_count": slow,
                "standalone_slow_rate": slow / n,
            }
        )
    multiple_valid = valid.dropna(subset=["multiple_category"])
    for multiple, subset in multiple_valid.groupby("multiple_category", sort=True):
        n = len(subset)
        slow = int((subset[TARGET] > SLOW_THRESHOLD).sum())
        standalone_rows.append(
            {
                "dimension": "multiple",
                "category": str(multiple),
                "standalone_count": n,
                "standalone_mean": float(subset[TARGET].mean()),
                "standalone_slow_count": slow,
                "standalone_slow_rate": slow / n,
            }
        )
    standalone = pd.DataFrame(standalone_rows)
    vehicle_base = standalone.loc[standalone["dimension"] == "vehicle"].set_index(
        "category"
    )
    multiple_base = standalone.loc[standalone["dimension"] == "multiple"].set_index(
        "category"
    )
    for suffix, metric in (
        ("count", "standalone_count"),
        ("mean", "standalone_mean"),
        ("slow_count", "standalone_slow_count"),
        ("slow_rate", "standalone_slow_rate"),
    ):
        groups[f"standalone_vehicle_{suffix}"] = groups["vehicle_category"].map(
            vehicle_base[metric]
        )
        groups[f"standalone_multiple_{suffix}"] = groups["multiple_category"].map(
            multiple_base[metric]
        )

    all_slow = int((valid[TARGET] > SLOW_THRESHOLD).sum())
    excluded_slow = int(
        (
            (valid[TARGET] > SLOW_THRESHOLD)
            & (valid[VEHICLE].isna() | valid["multiple_category"].isna())
        ).sum()
    )
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "missing_vehicle_count": missing_vehicle,
        "missing_multiple_count": missing_multiple,
        "excluded_for_missing_either_count": missing_either,
        "all_slow_delivery_count": all_slow,
        "excluded_slow_delivery_count": excluded_slow,
        "eligible_combination_population": len(categorized),
    }
    return groups, standalone, metadata, vehicle_categories, multiple_categories


def validate(
    sql: pd.DataFrame,
    python: pd.DataFrame,
    metadata: dict[str, int],
) -> tuple[int, int]:
    """Compare grid membership, metrics, reference baselines, and ranks."""
    keys = ["vehicle_category", "multiple_category"]
    sql_idx = sql.set_index(keys).sort_index()
    py_idx = python.set_index(keys).sort_index()
    if not sql_idx.index.equals(py_idx.index):
        raise AssertionError("SQL and Python Vehicle x multiple-delivery grids differ.")
    metric_checks = rank_checks = 0
    for key in sql_idx.index:
        sql_row = sql_idx.loc[key]
        py_row = py_idx.loc[key]
        for field in COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        if str(sql_row["sample_size_status"]) != str(py_row["sample_size_status"]):
            raise AssertionError(f"{key} eligibility differs.")
        for field in FLOAT_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or not close_enough(float(left), float(right)):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        for field in RANK_FIELDS:
            left, right = sql_row[field], py_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or int(left) != int(right):
                raise AssertionError(f"{key} {field} differs.")
            rank_checks += 1
        for field in BASELINE_FIELDS:
            left, right = sql_row[field], py_row[field]
            if field.endswith(("_count", "_slow_count")):
                if int(left) != int(right):
                    raise AssertionError(f"{key} {field} differs.")
            elif not close_enough(float(left), float(right)):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
    sql_first = sql.iloc[0]
    for field, expected in metadata.items():
        if int(sql_first[field]) != expected:
            raise AssertionError(f"SQL/Python population differs for {field}.")
        metric_checks += 1
    return metric_checks, rank_checks


def extreme_labels(
    subset: pd.DataFrame, metric: str, label_column: str, highest: bool
) -> str:
    subset = subset.loc[subset["delivery_count"] >= MIN_GROUP_SIZE]
    if len(subset) < 2:
        return "Not comparable (fewer than 2 qualifying groups)"
    value = subset[metric].max() if highest else subset[metric].min()
    tied = subset.loc[np.isclose(subset[metric], value, atol=ABS_TOL, rtol=REL_TOL)]
    descriptions = []
    for _, row in tied.iterrows():
        stat = float(row[metric])
        rendered = (
            f"{stat * 100:.4f}%"
            if metric == "slow_delivery_rate"
            else f"{fmt(stat)} min"
        )
        descriptions.append(
            f"{row[label_column]} (n={int(row['delivery_count']):,}; {rendered}; "
            f"median {fmt(float(row['median_delivery_time']))}; "
            f"P90 {fmt(float(row['p90_delivery_time']))})"
        )
    return "; ".join(descriptions)


def ordered_labels(labels: list[str]) -> list[str]:
    """Sort observed numeric category labels for descriptive trend inspection."""
    return sorted(labels, key=float)


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET, VEHICLE, MULTIPLE]
    missing_columns = [name for name in required if name not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required analysis columns are missing: {missing_columns}")

    python_groups, standalone, metadata, vehicles, multiples = calculate_python(frame)
    sql_groups, sqlite_version = run_sql(
        frame, SQL_PATH.read_text(encoding="utf-8")
    )
    if sql_groups.empty:
        raise AssertionError("SQL returned no Vehicle x multiple-delivery cells.")
    metric_checks, rank_checks = validate(sql_groups, python_groups, metadata)

    if int(sql_groups["delivery_count"].sum()) != metadata["eligible_combination_population"]:
        raise AssertionError("Two-way delivery counts do not reconcile.")
    qualifying = python_groups.loc[
        python_groups["delivery_count"] >= MIN_GROUP_SIZE
    ].copy()
    subminimum = python_groups.loc[
        python_groups["delivery_count"] < MIN_GROUP_SIZE
    ]
    total_slow = metadata["all_slow_delivery_count"]
    qualifying_slow = int(qualifying["slow_delivery_count"].sum())
    subminimum_slow = int(subminimum["slow_delivery_count"].sum())
    if qualifying_slow + subminimum_slow + metadata["excluded_slow_delivery_count"] != total_slow:
        raise AssertionError("Slow-delivery counts do not reconcile.")

    grid_rows = []
    for _, row in python_groups.iterrows():
        n, slow = int(row["delivery_count"]), int(row["slow_delivery_count"])
        grid_rows.append(
            [
                row["vehicle_category"],
                row["multiple_category"],
                f"{n:,}",
                "—" if pd.isna(row["mean_delivery_time"]) else fmt(float(row["mean_delivery_time"])),
                "—" if pd.isna(row["median_delivery_time"]) else fmt(float(row["median_delivery_time"])),
                "—" if pd.isna(row["p90_delivery_time"]) else fmt(float(row["p90_delivery_time"])),
                f"{slow:,}",
                f"{slow:,} / {n:,}" if n else "0 / 0",
                "—" if pd.isna(row["slow_delivery_rate"]) else f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                "Qualifies" if n >= MIN_GROUP_SIZE else "Small sample; descriptive only",
            ]
        )

    within_vehicle_summary_rows = []
    within_vehicle_detail_rows = []
    vehicle_pattern_rows = []
    vehicle_pattern_metrics: dict[str, tuple[str, str, int]] = {}
    for vehicle in vehicles:
        subset = qualifying.loc[qualifying["vehicle_category"] == vehicle].copy()
        observed = python_groups.loc[python_groups["vehicle_category"] == vehicle]
        observed_counts = "; ".join(
            f"{row.multiple_category} (n={int(row.delivery_count):,})"
            for row in observed.itertuples()
        )
        within_vehicle_summary_rows.append(
            [
                vehicle,
                observed_counts,
                int(subset["multiple_category"].nunique()),
                extreme_labels(subset, "mean_delivery_time", "multiple_category", False),
                extreme_labels(subset, "mean_delivery_time", "multiple_category", True),
                extreme_labels(subset, "slow_delivery_rate", "multiple_category", False),
                extreme_labels(subset, "slow_delivery_rate", "multiple_category", True),
            ]
        )

        subset["multiple_order"] = subset["multiple_category"].map(float)
        for _, row in subset.sort_values("multiple_order").iterrows():
            within_vehicle_detail_rows.append(
                [
                    vehicle,
                    f"  category {row['multiple_category']}",
                    f"{int(row['delivery_count']):,}",
                    fmt(float(row["mean_delivery_time"])),
                    fmt(float(row["median_delivery_time"])),
                    fmt(float(row["p90_delivery_time"])),
                    f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                    f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    int(row["mean_rank_within_vehicle"]),
                    int(row["slow_rate_rank_within_vehicle"]),
                ]
            )
        if len(subset) >= 2:
            ordered = subset.sort_values("multiple_order")
            mean_diffs = np.diff(ordered["mean_delivery_time"].to_numpy(dtype="float64"))
            rate_diffs = np.diff(ordered["slow_delivery_rate"].to_numpy(dtype="float64"))
            mean_pattern = (
                "increasing" if np.all(mean_diffs > 0)
                else "decreasing" if np.all(mean_diffs < 0)
                else "mixed / ties"
            )
            rate_pattern = (
                "increasing" if np.all(rate_diffs > 0)
                else "decreasing" if np.all(rate_diffs < 0)
                else "mixed / ties"
            )
            vehicle_pattern_metrics[vehicle] = (mean_pattern, rate_pattern, len(subset))
            vehicle_pattern_rows.append([vehicle, len(subset), mean_pattern, rate_pattern])
        else:
            vehicle_pattern_rows.append(
                [vehicle, len(subset), "Insufficient qualifying categories", "Insufficient qualifying categories"]
            )

    within_multiple_rows = []
    vehicle_order_rows = []
    for multiple in ordered_labels(multiples):
        subset = qualifying.loc[qualifying["multiple_category"] == multiple]
        for _, row in subset.sort_values("mean_delivery_time").iterrows():
            within_multiple_rows.append(
                [
                    multiple,
                    row["vehicle_category"],
                    f"{int(row['delivery_count']):,}",
                    fmt(float(row["mean_delivery_time"])),
                    fmt(float(row["median_delivery_time"])),
                    fmt(float(row["p90_delivery_time"])),
                    f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                    f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    int(row["mean_rank_within_multiple"]),
                    int(row["slow_rate_rank_within_multiple"]),
                ]
            )
        if len(subset) >= 2:
            vehicle_order_rows.append(
                [
                    multiple,
                    len(subset),
                    " > ".join(
                        subset.sort_values("mean_delivery_time", ascending=False)["vehicle_category"]
                    ),
                    " > ".join(
                        subset.sort_values("slow_delivery_rate", ascending=False)["vehicle_category"]
                    ),
                ]
            )

    standalone_vehicle = standalone.loc[
        standalone["dimension"] == "vehicle"
    ].set_index("category")
    standalone_multiple = standalone.loc[
        standalone["dimension"] == "multiple"
    ].set_index("category")
    vehicle_high = str(standalone_vehicle["standalone_slow_rate"].idxmax())
    vehicle_low = str(standalone_vehicle["standalone_slow_rate"].idxmin())
    multiple_high_mean = str(standalone_multiple["standalone_mean"].idxmax())
    multiple_low_mean = str(standalone_multiple["standalone_mean"].idxmin())
    multiple_high_slow = str(standalone_multiple["standalone_slow_rate"].idxmax())
    multiple_low_slow = str(standalone_multiple["standalone_slow_rate"].idxmin())

    vehicle_signal_rows = []
    high_vehicle_top_count = 0
    high_vehicle_comparable = 0
    vehicle_rank_signatures: list[tuple[str, ...]] = []
    for multiple in ordered_labels(multiples):
        subset = qualifying.loc[qualifying["multiple_category"] == multiple].copy()
        if subset.empty:
            vehicle_signal_rows.append(
                [multiple, "No qualifying vehicle cells", "Not comparable", "Not comparable", "Not comparable"]
            )
            continue
        max_rate = float(subset["slow_delivery_rate"].max())
        highest = subset.loc[
            np.isclose(subset["slow_delivery_rate"], max_rate, atol=ABS_TOL, rtol=REL_TOL)
        ]
        if vehicle_high in subset["vehicle_category"].values:
            high_vehicle_comparable += 1
            high_row = subset.loc[subset["vehicle_category"] == vehicle_high].iloc[0]
            high_vehicle_top_count += int(
                close_enough(float(high_row["slow_delivery_rate"]), max_rate)
            )
            high_vehicle_rank = int(high_row["highest_slow_rate_rank_within_multiple"])
        else:
            high_vehicle_rank = None
        vehicle_rank_signatures.append(
            tuple(
                subset.sort_values(
                    ["slow_delivery_rate", "vehicle_category"],
                    ascending=[False, True],
                )["vehicle_category"]
            )
        )
        rates = subset["slow_delivery_rate"].to_numpy(dtype="float64")
        means = subset["mean_delivery_time"].to_numpy(dtype="float64")
        vehicle_signal_rows.append(
            [
                multiple,
                "; ".join(f"{row['vehicle_category']} (n={int(row['delivery_count']):,})" for _, row in highest.iterrows()),
                f"{vehicle_high} rate {float(high_row['slow_delivery_rate']) * 100:.4f}%"
                if vehicle_high in subset["vehicle_category"].values
                else f"{vehicle_high}: no qualifying cell",
                f"Rate range {rates.min() * 100:.4f}–{rates.max() * 100:.4f}% "
                f"({(rates.max() - rates.min()) * 100:.4f} pp)",
                f"Mean range {means.min():.4f}–{means.max():.4f} min; "
                f"high standalone vehicle rank {high_vehicle_rank if high_vehicle_rank is not None else 'n/a'}",
            ]
        )

    standalone_mean_high = float(
        standalone_multiple.loc[multiple_high_mean, "standalone_mean"]
    )
    standalone_mean_low = float(
        standalone_multiple.loc[multiple_low_mean, "standalone_mean"]
    )
    standalone_rate_high = float(
        standalone_multiple.loc[multiple_high_slow, "standalone_slow_rate"]
    )
    standalone_rate_low = float(
        standalone_multiple.loc[multiple_low_slow, "standalone_slow_rate"]
    )
    standalone_mean_endpoint_gap = standalone_mean_high - standalone_mean_low
    standalone_rate_endpoint_gap = standalone_rate_high - standalone_rate_low
    multiple_signal_rows = []
    multiple_comparison_results: list[tuple[str, float, float]] = []
    for vehicle in vehicles:
        subset = qualifying.loc[qualifying["vehicle_category"] == vehicle].copy()
        subset["multiple_order"] = subset["multiple_category"].map(float)
        by_multiple = subset.set_index("multiple_category")
        high_row = by_multiple.loc[multiple_high_slow] if multiple_high_slow in by_multiple.index else None
        low_row = by_multiple.loc[multiple_low_slow] if multiple_low_slow in by_multiple.index else None
        if high_row is None or low_row is None:
            multiple_signal_rows.append(
                [
                    vehicle,
                    len(subset),
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "Highest/lowest standalone slow-rate endpoint missing or below minimum",
                ]
            )
        else:
            mean_gap = float(high_row["mean_delivery_time"] - low_row["mean_delivery_time"])
            rate_gap = float(high_row["slow_delivery_rate"] - low_row["slow_delivery_rate"])
            multiple_comparison_results.append((vehicle, mean_gap, rate_gap))
            sequence_mean = vehicle_pattern_metrics.get(vehicle, ("not testable", "not testable", 0))[0]
            sequence_rate = vehicle_pattern_metrics.get(vehicle, ("not testable", "not testable", 0))[1]
            multiple_signal_rows.append(
                [
                    vehicle,
                    len(subset),
                    f"{int(low_row['delivery_count']):,} / {int(high_row['delivery_count']):,}",
                    f"{float(low_row['mean_delivery_time']):.4f} → {float(high_row['mean_delivery_time']):.4f}",
                    f"{float(low_row['slow_delivery_rate']) * 100:.4f}% → {float(high_row['slow_delivery_rate']) * 100:.4f}%",
                    f"Endpoint mean delta {mean_gap:+.4f} min; rate delta {rate_gap * 100:+.4f} pp; "
                    f"category sequences: mean {sequence_mean}, rate {sequence_rate}",
                ]
            )

    # Top observed rate cells below n=30 are surfaced separately rather than ranked.
    small_rate_rows = []
    for _, row in subminimum.loc[subminimum["slow_delivery_rate"].notna()].sort_values(
        ["slow_delivery_rate", "delivery_count"], ascending=[False, True]
    ).head(5).iterrows():
        small_rate_rows.append(
            [
                row["vehicle_category"],
                row["multiple_category"],
                f"{int(row['delivery_count']):,}",
                f"{int(row['slow_delivery_count']):,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                "Descriptive only; below n=30",
            ]
        )

    top = qualifying.sort_values(
        ["slow_delivery_count", "slow_delivery_rate", "delivery_count"],
        ascending=[False, False, False],
        kind="stable",
    ).head(5)
    top_slow = int(top["slow_delivery_count"].sum())
    contribution_rows = []
    for _, row in top.iterrows():
        n, slow = int(row["delivery_count"]), int(row["slow_delivery_count"])
        contribution_rows.append(
            [
                row["vehicle_category"],
                row["multiple_category"],
                f"{n:,}",
                f"{slow:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                fmt(float(row["mean_delivery_time"])),
                fmt(float(row["median_delivery_time"])),
                fmt(float(row["p90_delivery_time"])),
                f"{slow:,} / {total_slow:,} ({slow / total_slow * 100:.2f}%)",
            ]
        )

    standalone_vehicle_rows = []
    for vehicle in vehicles:
        row = standalone_vehicle.loc[vehicle]
        standalone_vehicle_rows.append(
            [
                vehicle,
                f"{int(row['standalone_count']):,}",
                fmt(float(row["standalone_mean"])),
                fmt(float(row["standalone_slow_rate"]) * 100) + "%",
                f"{int(row['standalone_slow_count']):,} / {int(row['standalone_count']):,}",
            ]
        )
    standalone_multiple_rows = []
    for multiple in ordered_labels(multiples):
        row = standalone_multiple.loc[multiple]
        standalone_multiple_rows.append(
            [
                multiple,
                f"{int(row['standalone_count']):,}",
                fmt(float(row["standalone_mean"])),
                f"{float(row['standalone_slow_rate']) * 100:.4f}%",
                f"{int(row['standalone_slow_count']):,} / {int(row['standalone_count']):,}",
            ]
        )

    if vehicle_rank_signatures:
        baseline_signature = vehicle_rank_signatures[0]
        vehicle_rank_changes = sum(
            signature != baseline_signature for signature in vehicle_rank_signatures[1:]
        )
    else:
        vehicle_rank_changes = 0
    mean_pattern_count = sum(
        result[0] == "increasing" for result in vehicle_pattern_metrics.values()
    )
    rate_pattern_count = sum(
        result[1] == "increasing" for result in vehicle_pattern_metrics.values()
    )
    comparable_vehicle_count = len(multiple_comparison_results)
    mean_gap_reduced = sum(
        gap >= 0 and gap < standalone_mean_endpoint_gap
        for _, gap, _ in multiple_comparison_results
    )
    mean_gap_increased = sum(
        gap > standalone_mean_endpoint_gap
        for _, gap, _ in multiple_comparison_results
    )
    mean_gap_reversed = sum(
        gap < 0 for _, gap, _ in multiple_comparison_results
    )
    rate_gap_reduced = sum(
        gap >= 0 and gap < standalone_rate_endpoint_gap
        for _, _, gap in multiple_comparison_results
    )
    rate_gap_increased = sum(
        gap > standalone_rate_endpoint_gap
        for _, _, gap in multiple_comparison_results
    )
    rate_gap_reversed = sum(
        gap < 0 for _, _, gap in multiple_comparison_results
    )

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training CSV changed during validation.")

    lines = [
        "# Vehicle × Multiple Deliveries Analysis",
        "",
        "## Objective",
        "",
        "Describe whether observed vehicle-type differences in delivery performance remain visible within multiple-delivery categories, and whether the multiple-delivery pattern remains visible within vehicle types. This is observational analysis only.",
        "",
        "## Analytical Context",
        "",
        "The standalone vehicle analysis reported the highest slow-delivery rate for motorcycle (11.7685%; 3,111/26,435) and the lowest for electric_scooter (4.7457%; 181/3,814). The standalone multiple-delivery analysis reported increasing mean delivery time and slow-delivery rate over categorical labels 0–3; label 3 had a 100% slow rate (361/361). Both findings motivate this focused two-variable comparison.",
        "",
        "Standalone vehicle results:",
        "",
        *markdown_table(
            ["Vehicle type", "Count", "Mean (min)", "Slow rate", "Slow count / n"],
            standalone_vehicle_rows,
        ),
        "",
        "Standalone multiple-delivery results:",
        "",
        *markdown_table(
            ["multiple_deliveries label", "Count", "Mean (min)", "Slow rate", "Slow count / n"],
            standalone_multiple_rows,
        ),
        "",
        "## Data Coverage",
        "",
        f"- Total valid-target records: **{metadata['valid_target_count']:,}** of {metadata['total_train_rows']:,} training records.",
        f"- Valid-target records with missing vehicle type: **{metadata['missing_vehicle_count']:,}**.",
        f"- Valid-target records with missing multiple-delivery category: **{metadata['missing_multiple_count']:,}**.",
        f"- Records with both dimensions available: **{metadata['eligible_combination_population']:,}**.",
        f"- Records missing either dimension (union): **{metadata['excluded_for_missing_either_count']:,}**; the separate missing counts may overlap.",
        "Missing dimensions remain in the valid-target population and are excluded only from this two-way comparison.",
        "",
        "## Two-Way Analysis",
        "",
        "Slow delivery uses the fixed global definition `Time_taken(min) > 40`; no threshold was recalculated. Both dimensions are categorical. Multiple-delivery labels are presented as observed and are only numerically ordered for the explicitly requested descriptive label-pattern check; they are not treated as a continuous variable.",
        "",
        "Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Every observed vehicle × multiple-delivery pair is shown; cells with fewer than 30 records remain descriptive and are not ranked or used for substantive comparisons.",
        "",
        "### Vehicle × Multiple Deliveries Results",
        "",
        *markdown_table(
            ["Vehicle type", "multiple_deliveries", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow count / n", "Slow rate", "Eligibility"],
            grid_rows,
        ),
        "",
        "## Within-Vehicle Multiple-Delivery Comparison",
        "",
        "The extrema below use only qualifying cells. The detailed rows show count, mean, median, P90, slow numerator/denominator, slow rate, and within-vehicle ranks. Numeric labels are sorted only to inspect descriptive successive-category patterns.",
        "",
        *markdown_table(
            ["Vehicle", "Observed category cells (counts)", "Qualifying cells", "Lowest mean category", "Highest mean category", "Lowest slow-rate category", "Highest slow-rate category"],
            within_vehicle_summary_rows,
        ),
        "",
        "Qualifying category-level comparison details:",
        "",
        *markdown_table(
            ["Vehicle", "multiple_deliveries category", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_vehicle_detail_rows,
        ),
        "",
        "Descriptive sequences across observed numeric category labels:",
        "",
        *markdown_table(
            ["Vehicle", "Qualifying categories", "Mean pattern", "Slow-rate pattern"],
            vehicle_pattern_rows,
        ),
        "",
        "## Within-Multiple-Delivery Vehicle Comparison",
        "",
        "Only vehicle cells with at least 30 records for each multiple-delivery category are ranked or compared. Rank 1 is the lowest mean/rate; ties share ranks.",
        "",
        *markdown_table(
            ["multiple_deliveries", "Vehicle", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_multiple_rows,
        ),
        "",
        "Vehicle orders, highest to lowest, within each qualifying multiple-delivery category:",
        "",
        *markdown_table(
            ["multiple_deliveries", "Qualifying vehicle types", "Mean order", "Slow-rate order"],
            vehicle_order_rows,
        ),
        "",
        "## Vehicle Signal Check",
        "",
        f"The standalone highest-rate vehicle was **{vehicle_high}**; the lowest was **{vehicle_low}**. Among {high_vehicle_comparable} multiple-delivery categories where {vehicle_high} had a qualifying cell, it had the highest or tied-highest vehicle slow rate in {high_vehicle_top_count}. Vehicle slow-rate order changed across {vehicle_rank_changes} successive multiple-delivery category comparisons where at least two vehicle types qualified.",
        "",
        *markdown_table(
            ["multiple_deliveries", "Highest slow-rate vehicle(s)", "Standalone-high vehicle rate", "Qualifying vehicle slow-rate spread", "Vehicle mean range"],
            vehicle_signal_rows,
        ),
        "",
        "The ranges and within-category ranks indicate where observed vehicle differences remain separated, narrow, tie, or change order; no difference is declared to have disappeared using an arbitrary cutoff.",
        "",
        "## Multiple-Delivery Signal Check",
        "",
        f"Standalone mean endpoints were labels {multiple_low_mean} and {multiple_high_mean} (difference {standalone_mean_endpoint_gap:.4f} minutes); slow-rate endpoints were labels {multiple_low_slow} and {multiple_high_slow} (difference {standalone_rate_endpoint_gap * 100:.4f} percentage points). The comparisons below use those endpoint categories only where both vehicle-specific cells meet n ≥ 30.",
        "",
        *markdown_table(
            ["Vehicle", "Qualifying multiple-delivery cells", "Counts: low / high slow-rate endpoint", "Means: low mean / high mean endpoint (min)", "Slow rates: low / high endpoint", "Endpoint change and category pattern"],
            multiple_signal_rows,
        ),
        "",
        f"Among {comparable_vehicle_count} vehicle types comparable at both slow-rate endpoints, the high-minus-low endpoint mean gap was smaller than standalone in {mean_gap_reduced}, larger in {mean_gap_increased}, and reversed in {mean_gap_reversed}; the slow-rate gap was smaller in {rate_gap_reduced}, larger in {rate_gap_increased}, and reversed in {rate_gap_reversed}. Increasing labels are not modeled as a continuous predictor.",
        "",
        "Subminimum cells with the highest observed slow rates (descriptive only):",
        "",
        *markdown_table(
            ["Vehicle", "multiple_deliveries", "Count", "Slow count", "Slow rate", "Status"],
            small_rate_rows
            or [["None", "—", "—", "—", "—", "No subminimum observed cells"]],
        ),
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, **{total_slow:,}** are slow. Of these, **{qualifying_slow:,}** occur in qualifying cells, **{subminimum_slow:,}** in subminimum cells, and **{metadata['excluded_slow_delivery_count']:,}** in records with at least one missing dimension. The five qualifying cells with the largest slow counts account for **{top_slow:,} ({top_slow / total_slow * 100:.2f}%)** of all slow deliveries.",
        "",
        *markdown_table(
            ["Vehicle", "multiple_deliveries", "Count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            contribution_rows,
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"SQL from `sql/13_vehicle_multiple_delivery_analysis.sql` ran against an in-memory SQLite {sqlite_version} table. Python independently grouped the same valid-target records with Pandas and NumPy linear interpolation. Counts and ranks were compared exactly; floating-point metrics use `numpy.isclose` with absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Two-way cell metrics, standalone references, and population counts", metric_checks, "MATCH"],
                ["Within-vehicle and within-multiple-delivery rankings", rank_checks, "MATCH"],
                ["Vehicle signal comparisons", high_vehicle_comparable, "MATCH"],
                ["Multiple-delivery endpoint comparisons", comparable_vehicle_count, "MATCH"],
                ["Slow-delivery population reconciliation", "all", "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- The standalone highest-rate vehicle ({vehicle_high}) was highest or tied-highest in {high_vehicle_top_count}/{high_vehicle_comparable} qualifying multiple-delivery strata in which it was comparable; rankings otherwise vary as listed.",
        f"- Mean delivery time increased across qualifying successive multiple-delivery labels in {mean_pattern_count} vehicle types; slow rate increased in {rate_pattern_count}. Other strata were mixed, tied, or insufficiently comparable.",
        f"- Standalone high-to-low multiple-delivery endpoint differences in mean and slow rate were reduced in {mean_gap_reduced}/{comparable_vehicle_count} and {rate_gap_reduced}/{comparable_vehicle_count} comparable vehicle types, respectively; direction changes are reported separately.",
        f"- The five largest qualifying slow-delivery contributors account for {top_slow:,} of {total_slow:,} slow records ({top_slow / total_slow * 100:.2f}%).",
        "",
        "## Interpretation",
        "",
        "The two-way descriptive results assess whether the standalone vehicle and multiple-delivery patterns remain visible within the other dimension. Patterns are not uniform where rankings, ranges, or successive category summaries differ. Small cells are shown but do not support substantive comparison. These observed associations do not show that vehicle type or multiple deliveries cause delivery-time differences.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.",
        "- Vehicle type and multiple deliveries may be related to other operational factors.",
        "- This analysis does not control for city, distance, weather, traffic, courier, or time.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.",
        "- `multiple_deliveries` is treated as categorical, not continuous.",
        "- Missing categories are not inferred; records are excluded only from the two-way cells requiring both dimensions.",
        "",
        f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; its schema is unchanged.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(sql_groups)} Vehicle x multiple-delivery cells: "
        f"{metric_checks} metric/population checks and {rank_checks} ranking checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
