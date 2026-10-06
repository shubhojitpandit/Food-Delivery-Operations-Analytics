"""Validate City x traffic descriptive analysis against SQLite and write report."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "10_city_traffic_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "city_traffic_analysis.md"
TARGET = "Time_taken(min)"
CITY = "City"
TRAFFIC = "Road_traffic_density"
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
    "mean_rank_within_city",
    "highest_mean_rank_within_city",
    "slow_rate_rank_within_city",
    "highest_slow_rate_rank_within_city",
    "mean_rank_within_traffic",
    "highest_mean_rank_within_traffic",
    "slow_rate_rank_within_traffic",
    "highest_slow_rate_rank_within_traffic",
)
BASELINE_FIELDS = (
    "standalone_city_count",
    "standalone_city_mean",
    "standalone_city_slow_count",
    "standalone_city_slow_rate",
    "standalone_traffic_count",
    "standalone_traffic_mean",
    "standalone_traffic_slow_count",
    "standalone_traffic_slow_rate",
)
POPULATION_FIELDS = (
    "total_train_rows",
    "valid_target_count",
    "missing_city_count",
    "missing_traffic_count",
    "excluded_for_missing_either_count",
    "all_slow_delivery_count",
    "excluded_slow_delivery_count",
    "eligible_combination_population",
)


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    return bool(np.isclose(left, right, atol=ABS_TOL, rtol=REL_TOL))


def fmt(value: float, decimals: int = 8) -> str:
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


def rank_within(
    groups: pd.DataFrame,
    partition: str,
    metric: str,
    ascending: bool,
) -> pd.Series:
    """Return SQL RANK-equivalent values for groups meeting the minimum size."""
    eligible = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    ranks = pd.Series(np.nan, index=groups.index, dtype="float64")
    ranks.loc[eligible.index] = eligible.groupby(partition)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return ranks


def calculate_python(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Independently calculate cell metrics, rankings and population metadata."""
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [CITY, TRAFFIC]].copy()
    valid[TARGET] = target.loc[valid_mask].astype("float64")

    missing_city = int(valid[CITY].isna().sum())
    missing_traffic = int(valid[TRAFFIC].isna().sum())
    missing_either = int((valid[CITY].isna() | valid[TRAFFIC].isna()).sum())
    categorized = valid.dropna(subset=[CITY, TRAFFIC]).copy()
    categorized["slow"] = categorized[TARGET] > SLOW_THRESHOLD

    rows: list[dict[str, object]] = []
    for (city, traffic), group in categorized.groupby(
        [CITY, TRAFFIC], sort=True, dropna=True
    ):
        values = group[TARGET].to_numpy(dtype="float64")
        count = len(group)
        slow_count = int(group["slow"].sum())
        rows.append(
            {
                "city_category": str(city),
                "traffic_category": str(traffic),
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
                "sample_size_status": (
                    "qualifies" if count >= MIN_GROUP_SIZE else "small_sample"
                ),
            }
        )
    groups = pd.DataFrame(rows)

    rank_specs = (
        ("mean_rank_within_city", "city_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_city", "city_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_city", "city_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_city", "city_category", "slow_delivery_rate", False),
        ("mean_rank_within_traffic", "traffic_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_traffic", "traffic_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", False),
    )
    for output, partition, metric, ascending in rank_specs:
        groups[output] = rank_within(groups, partition, metric, ascending)

    for dimension, column, prefix in (
        ("city", CITY, "standalone_city"),
        ("traffic", TRAFFIC, "standalone_traffic"),
    ):
        baseline_rows = []
        for category, subset in valid.dropna(subset=[column]).groupby(column, sort=True):
            count = len(subset)
            slow_count = int((subset[TARGET] > SLOW_THRESHOLD).sum())
            baseline_rows.append(
                {
                    "category": str(category),
                    f"{prefix}_count": count,
                    f"{prefix}_mean": float(subset[TARGET].mean()),
                    f"{prefix}_slow_count": slow_count,
                    f"{prefix}_slow_rate": slow_count / count,
                }
            )
        baseline = pd.DataFrame(baseline_rows).set_index("category")
        key = "city_category" if dimension == "city" else "traffic_category"
        for suffix in ("count", "mean", "slow_count", "slow_rate"):
            groups[f"{prefix}_{suffix}"] = groups[key].map(
                baseline[f"{prefix}_{suffix}"]
            )

    all_slow = int((valid[TARGET] > SLOW_THRESHOLD).sum())
    excluded_slow = int(
        (
            (valid[TARGET] > SLOW_THRESHOLD)
            & (valid[CITY].isna() | valid[TRAFFIC].isna())
        ).sum()
    )
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "missing_city_count": missing_city,
        "missing_traffic_count": missing_traffic,
        "excluded_for_missing_either_count": missing_either,
        "all_slow_delivery_count": all_slow,
        "excluded_slow_delivery_count": excluded_slow,
        "eligible_combination_population": len(categorized),
    }
    return groups, metadata


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        return pd.read_sql_query(query, connection), sqlite3.sqlite_version
    finally:
        connection.close()


def validate(
    sql: pd.DataFrame, python: pd.DataFrame, metadata: dict[str, int]
) -> tuple[int, int]:
    """Require exact cell/rank matches and tolerant floating-point agreement."""
    keys = ["city_category", "traffic_category"]
    sql_indexed = sql.set_index(keys).sort_index()
    python_indexed = python.set_index(keys).sort_index()
    if not sql_indexed.index.equals(python_indexed.index):
        raise AssertionError("SQL and Python City x traffic cells differ.")

    metric_checks = rank_checks = 0
    for key in sql_indexed.index:
        sql_row = sql_indexed.loc[key]
        py_row = python_indexed.loc[key]
        for field in COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        for field in FLOAT_FIELDS:
            if not close_enough(float(sql_row[field]), float(py_row[field])):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        if str(sql_row["sample_size_status"]) != str(py_row["sample_size_status"]):
            raise AssertionError(f"{key} sample-size status differs.")
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

    first_row = sql.iloc[0]
    for field, expected in metadata.items():
        if int(first_row[field]) != expected:
            raise AssertionError(f"SQL and Python differ for {field}.")
        metric_checks += 1
    return metric_checks, rank_checks


def extreme_labels(
    subset: pd.DataFrame, metric: str, label_column: str, low: bool
) -> str:
    if len(subset) < 2:
        return "Not comparable (fewer than 2 qualifying groups)"
    value = subset[metric].min() if low else subset[metric].max()
    tied = subset.loc[
        np.isclose(subset[metric], value, atol=ABS_TOL, rtol=REL_TOL)
    ]
    formatted = []
    for _, row in tied.iterrows():
        val = float(row[metric])
        val_text = f"{val * 100:.4f}%" if metric == "slow_delivery_rate" else f"{fmt(val)} min"
        formatted.append(f"{row[label_column]} (n={int(row['delivery_count']):,}; {val_text})")
    return "; ".join(formatted)


def comparison_table(groups: pd.DataFrame) -> list[list[object]]:
    rows = []
    for _, row in groups.sort_values(["city_category", "traffic_category"]).iterrows():
        n = int(row["delivery_count"])
        slow = int(row["slow_delivery_count"])
        rows.append(
            [
                row["city_category"],
                row["traffic_category"],
                f"{n:,}",
                fmt(float(row["mean_delivery_time"])),
                fmt(float(row["median_delivery_time"])),
                fmt(float(row["p90_delivery_time"])),
                f"{slow:,}",
                f"{slow:,} / {n:,} ({float(row['slow_delivery_rate']) * 100:.4f}%)",
                "Qualifies" if n >= MIN_GROUP_SIZE else "Small sample; descriptive only",
            ]
        )
    return rows


def semi_urban_signature(groups: pd.DataFrame) -> dict[str, tuple[float, ...]]:
    """Summarize qualifying Semi-Urban gaps against qualifying peer cities."""
    qualifying = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    signatures: dict[str, tuple[float, ...]] = {}
    for traffic in sorted(groups["traffic_category"].astype(str).unique()):
        semi = qualifying.loc[
            (qualifying["traffic_category"] == traffic)
            & (qualifying["city_category"] == "Semi-Urban")
        ]
        peers = qualifying.loc[
            (qualifying["traffic_category"] == traffic)
            & (qualifying["city_category"] != "Semi-Urban")
        ]
        if semi.empty or peers.empty:
            continue
        semi_row = semi.iloc[0]
        mean_gap = float(
            semi_row["mean_delivery_time"] - peers["mean_delivery_time"].max()
        )
        rate_gap = float(
            semi_row["slow_delivery_rate"] - peers["slow_delivery_rate"].max()
        )
        signatures[traffic] = (
            float(semi_row["delivery_count"]),
            float(semi_row["mean_delivery_time"]),
            float(semi_row["slow_delivery_rate"]),
            mean_gap,
            rate_gap,
        )
    return signatures


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    missing_columns = [column for column in (TARGET, CITY, TRAFFIC) if column not in frame]
    if missing_columns:
        raise ValueError(f"Required analysis columns are missing: {missing_columns}")

    python_groups, metadata = calculate_python(frame)
    query = SQL_PATH.read_text(encoding="utf-8")
    sql_groups, sqlite_version = run_sql(frame, query)
    if sql_groups.empty:
        raise AssertionError("SQL returned no City x traffic groups.")
    metric_checks, rank_checks = validate(sql_groups, python_groups, metadata)
    sql_semi = semi_urban_signature(sql_groups)
    python_semi = semi_urban_signature(python_groups)
    if sql_semi.keys() != python_semi.keys():
        raise AssertionError("SQL/Python Semi-Urban comparison coverage differs.")
    for traffic, sql_values in sql_semi.items():
        if not all(
            close_enough(sql_value, py_value)
            for sql_value, py_value in zip(sql_values, python_semi[traffic])
        ):
            raise AssertionError(
                f"SQL/Python Semi-Urban comparison differs for {traffic}."
            )

    if int(sql_groups["delivery_count"].sum()) != metadata["eligible_combination_population"]:
        raise AssertionError("Two-way cell counts do not reconcile.")
    qualifying = sql_groups.loc[sql_groups["delivery_count"] >= MIN_GROUP_SIZE].copy()
    subminimum = sql_groups.loc[sql_groups["delivery_count"] < MIN_GROUP_SIZE]
    qualifying_slow = int(qualifying["slow_delivery_count"].sum())
    subminimum_slow = int(subminimum["slow_delivery_count"].sum())
    total_slow = metadata["all_slow_delivery_count"]
    excluded_slow = metadata["excluded_slow_delivery_count"]
    if qualifying_slow + subminimum_slow + excluded_slow != total_slow:
        raise AssertionError("Slow-delivery counts do not reconcile.")

    cities = sorted(sql_groups["city_category"].astype(str).unique())
    traffic_categories = sorted(sql_groups["traffic_category"].astype(str).unique())
    within_city_rows = []
    for city in cities:
        subset = qualifying.loc[qualifying["city_category"] == city]
        qualifying_traffic_count = subset["traffic_category"].nunique()
        within_city_rows.append(
            [
                city,
                "; ".join(f"{t} (n={n:,})" for t, n in zip(
                    sql_groups.loc[sql_groups["city_category"] == city, "traffic_category"],
                    sql_groups.loc[sql_groups["city_category"] == city, "delivery_count"],
                )),
                qualifying_traffic_count,
                extreme_labels(subset, "mean_delivery_time", "traffic_category", True),
                extreme_labels(subset, "mean_delivery_time", "traffic_category", False),
                extreme_labels(subset, "slow_delivery_rate", "traffic_category", True),
                extreme_labels(subset, "slow_delivery_rate", "traffic_category", False),
            ]
        )

    within_traffic_rows = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        ordered = subset.sort_values("mean_delivery_time", ascending=True)
        within_traffic_rows.extend(
            [
                traffic,
                row["city_category"],
                f"{int(row['delivery_count']):,}",
                fmt(float(row["mean_delivery_time"])),
                fmt(float(row["median_delivery_time"])),
                fmt(float(row["p90_delivery_time"])),
                f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                int(row["mean_rank_within_traffic"]),
                int(row["slow_rate_rank_within_traffic"]),
            ]
            for _, row in ordered.iterrows()
        )

    city_order_rows = []
    traffic_order_rows = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        if len(subset) >= 2:
            mean_order = " > ".join(
                subset.sort_values("mean_delivery_time", ascending=False)["city_category"]
            )
            rate_order = " > ".join(
                subset.sort_values("slow_delivery_rate", ascending=False)["city_category"]
            )
            city_order_rows.append([traffic, len(subset), mean_order, rate_order])
    for city in cities:
        subset = qualifying.loc[qualifying["city_category"] == city]
        if len(subset) >= 2:
            mean_order = " > ".join(
                subset.sort_values("mean_delivery_time", ascending=False)["traffic_category"]
            )
            rate_order = " > ".join(
                subset.sort_values("slow_delivery_rate", ascending=False)["traffic_category"]
            )
            traffic_order_rows.append([city, len(subset), mean_order, rate_order])

    metro_urban_comparisons = []
    for traffic in traffic_categories:
        subset = qualifying.loc[
            (qualifying["traffic_category"] == traffic)
            & (qualifying["city_category"].isin(["Metropolitan", "Urban"]))
        ].set_index("city_category")
        if {"Metropolitan", "Urban"}.issubset(subset.index):
            metro_urban_comparisons.append(
                (
                    float(
                        subset.loc["Metropolitan", "mean_delivery_time"]
                        - subset.loc["Urban", "mean_delivery_time"]
                    ),
                    float(
                        subset.loc["Metropolitan", "slow_delivery_rate"]
                        - subset.loc["Urban", "slow_delivery_rate"]
                    ),
                )
            )
    metro_higher_mean = sum(mean_gap > ABS_TOL for mean_gap, _ in metro_urban_comparisons)
    metro_higher_rate = sum(rate_gap > ABS_TOL for _, rate_gap in metro_urban_comparisons)

    traffic_extremes = []
    for city in cities:
        subset = qualifying.loc[qualifying["city_category"] == city]
        if len(subset) >= 2:
            traffic_extremes.append(
                (
                    city,
                    subset.loc[subset["mean_delivery_time"].idxmax(), "traffic_category"],
                    subset.loc[subset["mean_delivery_time"].idxmin(), "traffic_category"],
                    subset.loc[subset["slow_delivery_rate"].idxmax(), "traffic_category"],
                    subset.loc[subset["slow_delivery_rate"].idxmin(), "traffic_category"],
                )
            )
    worst_mean_traffic = {str(row[1]) for row in traffic_extremes}
    best_mean_traffic = {str(row[2]) for row in traffic_extremes}
    worst_rate_traffic = {str(row[3]) for row in traffic_extremes}
    best_rate_traffic = {str(row[4]) for row in traffic_extremes}
    city_strata_count = len(traffic_extremes)
    mean_worst_consistency = sum(
        row[1] == sorted(worst_mean_traffic)[0] for row in traffic_extremes
    ) if len(worst_mean_traffic) == 1 else 0
    mean_best_consistency = sum(
        row[2] == sorted(best_mean_traffic)[0] for row in traffic_extremes
    ) if len(best_mean_traffic) == 1 else 0
    rate_worst_consistency = sum(
        row[3] == sorted(worst_rate_traffic)[0] for row in traffic_extremes
    ) if len(worst_rate_traffic) == 1 else 0
    rate_best_consistency = sum(
        row[4] == sorted(best_rate_traffic)[0] for row in traffic_extremes
    ) if len(best_rate_traffic) == 1 else 0

    standalone_city = sql_groups.drop_duplicates("city_category").set_index("city_category")
    non_semi_cities = [city for city in cities if city != "Semi-Urban"]
    if "Semi-Urban" in standalone_city.index and non_semi_cities:
        semi_base = standalone_city.loc["Semi-Urban"]
        baseline_comparison = standalone_city.loc[non_semi_cities]
        baseline_mean_peer = baseline_comparison["standalone_city_mean"].idxmax()
        baseline_rate_peer = baseline_comparison["standalone_city_slow_rate"].idxmax()
        standalone_mean_gap = float(
            semi_base["standalone_city_mean"]
            - baseline_comparison["standalone_city_mean"].max()
        )
        standalone_rate_gap = float(
            semi_base["standalone_city_slow_rate"]
            - baseline_comparison["standalone_city_slow_rate"].max()
        )
    else:
        standalone_mean_gap = standalone_rate_gap = float("nan")
        baseline_mean_peer = baseline_rate_peer = "Not comparable"

    semi_rows = []
    for traffic in traffic_categories:
        all_cells = sql_groups.loc[
            (sql_groups["traffic_category"] == traffic)
            & (sql_groups["city_category"] == "Semi-Urban")
        ]
        semi_cell = all_cells.iloc[0] if not all_cells.empty else None
        peers = qualifying.loc[
            (qualifying["traffic_category"] == traffic)
            & (qualifying["city_category"] != "Semi-Urban")
        ]
        semi_qualifies = semi_cell is not None and int(semi_cell["delivery_count"]) >= MIN_GROUP_SIZE
        if not semi_qualifies or peers.empty:
            if semi_cell is None:
                comparison_note = "No Semi-Urban cell; not comparable"
            elif not semi_qualifies:
                comparison_note = (
                    "Semi-Urban cell below 30; not comparable with peer cities"
                )
            else:
                comparison_note = "No other qualifying city for comparison"
            semi_rows.append(
                [
                    traffic,
                    "No" if semi_cell is None else f"{int(semi_cell['delivery_count']):,} (below 30)",
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    comparison_note,
                ]
            )
            continue
        highest_peer_mean = float(peers["mean_delivery_time"].max())
        highest_peer_rate = float(peers["slow_delivery_rate"].max())
        mean_gap = float(semi_cell["mean_delivery_time"]) - highest_peer_mean
        rate_gap = float(semi_cell["slow_delivery_rate"]) - highest_peer_rate
        mean_direction = "highest mean" if mean_gap > ABS_TOL else "tied highest" if abs(mean_gap) <= ABS_TOL else "not highest"
        rate_direction = "highest rate" if rate_gap > ABS_TOL else "tied highest" if abs(rate_gap) <= ABS_TOL else "not highest"
        semi_rows.append(
            [
                traffic,
                f"{int(semi_cell['delivery_count']):,} (qualifies)",
                fmt(float(semi_cell["mean_delivery_time"])),
                f"{float(semi_cell['slow_delivery_rate']) * 100:.4f}%",
                f"{mean_gap:+.4f} min vs highest non-Semi-Urban mean",
                f"{rate_gap * 100:+.4f} pp vs highest non-Semi-Urban rate",
                f"{mean_direction}; {rate_direction}",
            ]
        )

    top = qualifying.sort_values(
        ["slow_delivery_count", "slow_delivery_rate", "delivery_count"],
        ascending=[False, False, False],
        kind="stable",
    ).head(5)
    top_rows = []
    for _, row in top.iterrows():
        n, slow = int(row["delivery_count"]), int(row["slow_delivery_count"])
        top_rows.append(
            [
                row["city_category"],
                row["traffic_category"],
                f"{n:,}",
                f"{slow:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                fmt(float(row["mean_delivery_time"])),
                fmt(float(row["median_delivery_time"])),
                fmt(float(row["p90_delivery_time"])),
                f"{slow:,} / {total_slow:,} ({slow / total_slow * 100:.2f}%)",
            ]
        )
    top_five_slow = int(top["slow_delivery_count"].sum())

    # Summarize whether the Semi-Urban gap narrows, widens, or reverses by stratum.
    semi_comparable = []
    mean_narrowed = mean_widened = mean_reversed = 0
    rate_narrowed = rate_widened = rate_reversed = 0
    for traffic in traffic_categories:
        cell = qualifying.loc[
            (qualifying["city_category"] == "Semi-Urban")
            & (qualifying["traffic_category"] == traffic)
        ]
        peers = qualifying.loc[
            (qualifying["city_category"] != "Semi-Urban")
            & (qualifying["traffic_category"] == traffic)
        ]
        if cell.empty or peers.empty:
            continue
        mean_gap = float(cell.iloc[0]["mean_delivery_time"] - peers["mean_delivery_time"].max())
        rate_gap = float(cell.iloc[0]["slow_delivery_rate"] - peers["slow_delivery_rate"].max())
        if not np.isnan(standalone_mean_gap):
            mean_narrowed += int(mean_gap >= 0 and mean_gap < standalone_mean_gap)
            mean_widened += int(mean_gap > standalone_mean_gap)
            mean_reversed += int(mean_gap < 0)
        if not np.isnan(standalone_rate_gap):
            rate_narrowed += int(rate_gap >= 0 and rate_gap < standalone_rate_gap)
            rate_widened += int(rate_gap > standalone_rate_gap)
            rate_reversed += int(rate_gap < 0)
        semi_comparable.append(traffic)

    missing_summary = (
        f"{metadata['missing_city_count']:,} valid targets have missing City; "
        f"{metadata['missing_traffic_count']:,} have missing traffic; "
        f"{metadata['excluded_for_missing_either_count']:,} are excluded from the "
        "two-way cells because either dimension is missing."
    )
    lines = [
        "# City × Traffic Analysis",
        "",
        "## Objective",
        "",
        "Describe whether observed city-level delivery-time differences remain visible within traffic categories, and whether traffic differences remain visible within cities. This is observational; it does not establish causality.",
        "",
        "## Analytical Context",
        "",
        "The standalone City analysis reported means of 22.9840 minutes for Urban (n=10,136), 27.3152 for Metropolitan (n=34,093), and 49.7317 for Semi-Urban (n=164); Semi-Urban's slow-delivery rate was 100% (164/164). Standalone traffic results ranged from a 21.2670-minute mean and 1.3827% slow rate in Low traffic to a 31.1766-minute mean and 20.0099% slow rate in Jam. This step stratifies only by City × `Road_traffic_density`.",
        "",
        "## Two-Way Analysis",
        "",
        f"- Source: `data/processed/train_clean.csv`; {metadata['total_train_rows']:,} rows and {metadata['valid_target_count']:,} valid numeric targets.",
        f"- Fixed slow rule: `Time_taken(min) > 40`; no group-specific threshold was calculated.",
        f"- {missing_summary}",
        "- Every observed City × traffic cell is shown. Cells with fewer than 30 targets remain visible as descriptive results but are not ranked or used for substantive comparisons.",
        "",
        "### City × Traffic Results",
        "",
        "Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow rate is slow count / delivery count.",
        "",
        *markdown_table(
            ["City", "Traffic", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow rate (numerator / denominator)", "Eligibility"],
            comparison_table(sql_groups),
        ),
        "",
        "## Within-City Traffic Comparison",
        "",
        "Extremes use only qualifying traffic cells within each city; counts are included, and ties are retained.",
        "",
        *markdown_table(
            ["City", "Observed cells (counts)", "Qualifying traffic categories", "Lowest mean traffic", "Highest mean traffic", "Lowest slow-rate traffic", "Highest slow-rate traffic"],
            within_city_rows,
        ),
        "",
        "Traffic category rankings by mean and slow rate within each city:",
        "",
        *markdown_table(["City", "Qualifying cells", "Mean order (highest to lowest)", "Slow-rate order (highest to lowest)"], traffic_order_rows),
        "",
        "## Within-Traffic City Comparison",
        "",
        "Only cells with n ≥ 30 are shown in this comparison. Mean rank and slow-rate rank use 1 for the lowest value; ties share ranks.",
        "",
        *markdown_table(
            ["Traffic", "City", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_traffic_rows,
        ),
        "",
        "City category rankings by mean and slow rate within each traffic category:",
        "",
        *markdown_table(["Traffic", "Qualifying cities", "Mean order (highest to lowest)", "Slow-rate order (highest to lowest)"], city_order_rows),
        "",
        "## Semi-Urban Signal Check",
        "",
        f"Standalone Semi-Urban differences versus the highest standalone non-Semi-Urban city were {standalone_mean_gap:.4f} minutes in mean delivery time and {standalone_rate_gap * 100:.4f} percentage points in slow rate (mean peer: {baseline_mean_peer}; slow-rate peer: {baseline_rate_peer}).",
        "",
        *markdown_table(
            ["Traffic", "Semi-Urban sample", "Semi mean (min)", "Semi slow rate", "Mean gap vs highest other qualifying city", "Slow-rate gap vs highest other qualifying city", "Within-stratum position"],
            semi_rows,
        ),
        "",
        f"Semi-Urban is comparable to at least one other qualifying city in {len(semi_comparable)} traffic categories: {', '.join(semi_comparable) if semi_comparable else 'none'}. Across those comparisons, the mean gap narrowed in {mean_narrowed}, widened in {mean_widened}, and reversed in {mean_reversed}; the slow-rate gap narrowed in {rate_narrowed}, widened in {rate_widened}, and reversed in {rate_reversed}. A stratum without a qualifying Semi-Urban cell or qualifying peer is explicitly not compared.",
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, {total_slow:,} deliveries meet the fixed slow rule. Of these, {qualifying_slow:,} occur in qualifying cells, {subminimum_slow:,} occur in subminimum cells, and {excluded_slow:,} have at least one missing grouping dimension. The five qualifying cells with the largest slow counts account for {top_five_slow:,} ({top_five_slow / total_slow * 100:.2f}%) of all slow deliveries.",
        "",
        *markdown_table(
            ["City", "Traffic", "Count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            top_rows,
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"SQL from `sql/10_city_traffic_analysis.sql` ran in in-memory SQLite {sqlite_version}; Pandas independently grouped the cleaned source. SQLite percentile values use the same continuous linear interpolation as NumPy. Counts and ranks were compared exactly; floating metrics use `numpy.isclose` with absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Cell metrics, standalone references, and population counts", metric_checks, "MATCH"],
                ["Within-city and within-traffic rankings", rank_checks, "MATCH"],
                ["Cell eligibility and slow-count reconciliation", "all", "MATCH"],
                ["Semi-Urban qualifying-cell comparisons", len(sql_semi), "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- Across {len(metro_urban_comparisons)} traffic strata where both Metropolitan and Urban qualify, Metropolitan has a higher mean in {metro_higher_mean} and a higher slow rate in {metro_higher_rate}; Semi-Urban is comparable to other cities only in {', '.join(semi_comparable) if semi_comparable else 'no'} traffic stratum.",
        f"- Among {city_strata_count} cities with at least two qualifying traffic categories, the highest/lowest mean traffic labels are {', '.join(sorted(worst_mean_traffic))} / {', '.join(sorted(best_mean_traffic))}; the highest/lowest slow-rate labels are {', '.join(sorted(worst_rate_traffic))} / {', '.join(sorted(best_rate_traffic))}. Consistency is {mean_worst_consistency}/{city_strata_count} and {mean_best_consistency}/{city_strata_count} for highest and lowest mean, and {rate_worst_consistency}/{city_strata_count} and {rate_best_consistency}/{city_strata_count} for highest and lowest slow rate. Full per-city orders appear above.",
        f"- The qualifying coverage is {len(qualifying)} of {len(sql_groups)} observed cells. Read every ranking alongside its count; single-group city strata are not labeled as within-city comparisons.",
        f"- Standalone Semi-Urban had a {standalone_mean_gap:.4f}-minute mean gap and a {standalone_rate_gap * 100:.4f}-percentage-point slow-rate gap versus the highest other standalone city. The within-traffic comparisons show those gaps narrowed in {mean_narrowed}/{len(semi_comparable)} and {rate_narrowed}/{len(semi_comparable)} comparable traffic categories respectively; direction changes are counted separately.",
        f"- The five largest qualifying slow-delivery contributors account for {top_five_slow:,} of {total_slow:,} slow deliveries; contribution depends on both group volume and its slow rate.",
        "",
        "## Interpretation",
        "",
        "The two-way tables show whether the standalone city and traffic differences remain visible within observed strata. Semi-Urban's position is assessed only where both the Semi-Urban cell and another city cell meet the 30-record rule; no value is imputed or comparison manufactured for nonqualifying cells. All differences are descriptive associations and do not show that city or traffic causes delivery-time differences.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings; all observed cells and counts remain displayed.",
        "- City and traffic may be related to other operational factors.",
        "- This analysis does not control for distance, weather, vehicle, courier, multiple deliveries, or time.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record rule is a reporting guardrail, not a guarantee of statistical precision.",
        "- Missing City/traffic values are excluded only from the two-way grouping and reported above; no observations are silently removed from the source.",
        "",
    ]

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training source changed during validation.")
    lines.extend(
        [
            f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; the source schema is unchanged.",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(sql_groups)} City x traffic cells: "
        f"{metric_checks} metric/population checks and {rank_checks} ranking checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
