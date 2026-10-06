"""Validate Weather x traffic grouped results against SQLite and write report."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "12_weather_traffic_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "weather_traffic_analysis.md"
TARGET = "Time_taken(min)"
WEATHER = "Weatherconditions"
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
    "mean_rank_within_weather",
    "highest_mean_rank_within_weather",
    "slow_rate_rank_within_weather",
    "highest_slow_rate_rank_within_weather",
    "mean_rank_within_traffic",
    "highest_mean_rank_within_traffic",
    "slow_rate_rank_within_traffic",
    "highest_slow_rate_rank_within_traffic",
)
BASELINE_FIELDS = (
    "standalone_weather_count",
    "standalone_weather_mean",
    "standalone_weather_slow_count",
    "standalone_weather_slow_rate",
    "standalone_traffic_count",
    "standalone_traffic_mean",
    "standalone_traffic_slow_count",
    "standalone_traffic_slow_rate",
)
POPULATION_FIELDS = (
    "total_train_rows",
    "valid_target_count",
    "missing_weather_count",
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
    """Match SQLite RANK while leaving subminimum and empty cells unranked."""
    qualifying = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    ranks = pd.Series(np.nan, index=groups.index, dtype="float64")
    ranks.loc[qualifying.index] = qualifying.groupby(partition)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return ranks


def calculate_python(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int], pd.DataFrame, pd.DataFrame]:
    """Independently calculate cell, standalone, and coverage metrics."""
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    valid_mask = target.notna()
    valid = frame.loc[valid_mask, [WEATHER, TRAFFIC]].copy()
    valid[TARGET] = target.loc[valid_mask].astype("float64")

    missing_weather = int(valid[WEATHER].isna().sum())
    missing_traffic = int(valid[TRAFFIC].isna().sum())
    missing_either = int((valid[WEATHER].isna() | valid[TRAFFIC].isna()).sum())
    categorized = valid.dropna(subset=[WEATHER, TRAFFIC]).copy()

    weather_categories = sorted(valid[WEATHER].dropna().astype(str).unique())
    traffic_categories = sorted(valid[TRAFFIC].dropna().astype(str).unique())
    rows: list[dict[str, object]] = []
    for weather in weather_categories:
        for traffic in traffic_categories:
            group = categorized.loc[
                (categorized[WEATHER].astype(str) == weather)
                & (categorized[TRAFFIC].astype(str) == traffic)
            ]
            count = len(group)
            slow_count = int((group[TARGET] > SLOW_THRESHOLD).sum())
            if count:
                values = group[TARGET].to_numpy(dtype="float64")
                mean = float(np.mean(values))
                median = float(np.percentile(values, 50, method="linear"))
                p90 = float(np.percentile(values, 90, method="linear"))
                rate = slow_count / count
            else:
                mean = median = p90 = rate = np.nan
            rows.append(
                {
                    "weather_category": weather,
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
        ("mean_rank_within_weather", "weather_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_weather", "weather_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_weather", "weather_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_weather", "weather_category", "slow_delivery_rate", False),
        ("mean_rank_within_traffic", "traffic_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_traffic", "traffic_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", False),
    )
    for output, partition, metric, ascending in rank_specs:
        groups[output] = rank_within(groups, partition, metric, ascending)

    standalone_rows = []
    for dimension, column in (
        ("weather", WEATHER),
        ("traffic", TRAFFIC),
    ):
        for category, subset in valid.dropna(subset=[column]).groupby(column, sort=True):
            count = len(subset)
            slow_count = int((subset[TARGET] > SLOW_THRESHOLD).sum())
            standalone_rows.append(
                {
                    "dimension": dimension,
                    "category": str(category),
                    "standalone_count": count,
                    "standalone_mean": float(subset[TARGET].mean()),
                    "standalone_slow_count": slow_count,
                    "standalone_slow_rate": slow_count / count,
                }
            )
    standalone = pd.DataFrame(standalone_rows)
    weather_base = standalone.loc[standalone["dimension"] == "weather"].set_index("category")
    traffic_base = standalone.loc[standalone["dimension"] == "traffic"].set_index("category")
    groups["standalone_weather_count"] = groups["weather_category"].map(
        weather_base["standalone_count"]
    )
    groups["standalone_weather_mean"] = groups["weather_category"].map(
        weather_base["standalone_mean"]
    )
    groups["standalone_weather_slow_count"] = groups["weather_category"].map(
        weather_base["standalone_slow_count"]
    )
    groups["standalone_weather_slow_rate"] = groups["weather_category"].map(
        weather_base["standalone_slow_rate"]
    )
    groups["standalone_traffic_count"] = groups["traffic_category"].map(
        traffic_base["standalone_count"]
    )
    groups["standalone_traffic_mean"] = groups["traffic_category"].map(
        traffic_base["standalone_mean"]
    )
    groups["standalone_traffic_slow_count"] = groups["traffic_category"].map(
        traffic_base["standalone_slow_count"]
    )
    groups["standalone_traffic_slow_rate"] = groups["traffic_category"].map(
        traffic_base["standalone_slow_rate"]
    )

    all_slow = int((valid[TARGET] > SLOW_THRESHOLD).sum())
    excluded_slow = int(
        (
            (valid[TARGET] > SLOW_THRESHOLD)
            & (valid[WEATHER].isna() | valid[TRAFFIC].isna())
        ).sum()
    )
    metadata = {
        "total_train_rows": len(frame),
        "valid_target_count": int(valid_mask.sum()),
        "missing_weather_count": missing_weather,
        "missing_traffic_count": missing_traffic,
        "excluded_for_missing_either_count": missing_either,
        "all_slow_delivery_count": all_slow,
        "excluded_slow_delivery_count": excluded_slow,
        "eligible_combination_population": len(categorized),
    }
    coverage = pd.DataFrame(
        [
            {
                "weather_category": weather,
                "traffic_category": traffic,
                "delivery_count": len(
                    categorized.loc[
                        (categorized[WEATHER].astype(str) == weather)
                        & (categorized[TRAFFIC].astype(str) == traffic)
                    ]
                ),
            }
            for weather in weather_categories
            for traffic in traffic_categories
        ]
    )
    return groups, metadata, standalone, coverage


def validate(
    sql: pd.DataFrame,
    python: pd.DataFrame,
    metadata: dict[str, int],
) -> tuple[int, int]:
    """Validate all cells, baselines, population counts, and ranks."""
    keys = ["weather_category", "traffic_category"]
    sql_indexed = sql.set_index(keys).sort_index()
    python_indexed = python.set_index(keys).sort_index()
    if not sql_indexed.index.equals(python_indexed.index):
        raise AssertionError("SQL and Python Weather x traffic grids differ.")

    metric_checks = rank_checks = 0
    for key in sql_indexed.index:
        sql_row = sql_indexed.loc[key]
        py_row = python_indexed.loc[key]
        for field in COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        if str(sql_row["sample_size_status"]) != str(py_row["sample_size_status"]):
            raise AssertionError(f"{key} sample-size status differs.")
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
    first = sql.iloc[0]
    for field, expected in metadata.items():
        if int(first[field]) != expected:
            raise AssertionError(f"SQL/Python population mismatch for {field}.")
        metric_checks += 1
    return metric_checks, rank_checks


def extreme_description(
    subset: pd.DataFrame, metric: str, label: str, highest: bool
) -> str:
    qualifying = subset.loc[subset["delivery_count"] >= MIN_GROUP_SIZE]
    if len(qualifying) < 2:
        return "Not comparable (fewer than 2 qualifying groups)"
    value = qualifying[metric].max() if highest else qualifying[metric].min()
    tied = qualifying.loc[
        np.isclose(qualifying[metric], value, atol=ABS_TOL, rtol=REL_TOL)
    ]
    descriptions = []
    for _, row in tied.iterrows():
        value_text = (
            f"{float(row[metric]) * 100:.4f}%"
            if metric == "slow_delivery_rate"
            else f"{fmt(float(row[metric]))} min"
        )
        descriptions.append(
            f"{row[label]} (n={int(row['delivery_count']):,}; {value_text}; "
            f"median {fmt(float(row['median_delivery_time']))}; "
            f"P90 {fmt(float(row['p90_delivery_time']))})"
        )
    return "; ".join(descriptions)


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [TARGET, WEATHER, TRAFFIC]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required analysis columns are missing: {missing_columns}")

    python_groups, metadata, standalone, coverage = calculate_python(frame)
    sql_groups, sqlite_version = run_sql(
        frame, SQL_PATH.read_text(encoding="utf-8")
    )
    if sql_groups.empty:
        raise AssertionError("SQL returned no Weather x traffic combinations.")
    metric_checks, rank_checks = validate(sql_groups, python_groups, metadata)

    if int(sql_groups["delivery_count"].sum()) != metadata["eligible_combination_population"]:
        raise AssertionError("Weather x traffic group counts do not reconcile.")
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

    weather_categories = sorted(python_groups["weather_category"].astype(str).unique())
    traffic_categories = sorted(python_groups["traffic_category"].astype(str).unique())

    combination_rows = []
    for _, row in python_groups.iterrows():
        n = int(row["delivery_count"])
        slow = int(row["slow_delivery_count"])
        combination_rows.append(
            [
                row["weather_category"],
                row["traffic_category"],
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

    within_weather_rows = []
    for weather in weather_categories:
        subset = qualifying.loc[qualifying["weather_category"] == weather]
        observed_counts = coverage.loc[coverage["weather_category"] == weather]
        count_text = "; ".join(
            f"{row.traffic_category} (n={int(row.delivery_count):,})"
            for row in observed_counts.itertuples()
        )
        within_weather_rows.append(
            [
                weather,
                count_text,
                int(subset["traffic_category"].nunique()),
                extreme_description(subset, "mean_delivery_time", "traffic_category", False),
                extreme_description(subset, "mean_delivery_time", "traffic_category", True),
                extreme_description(subset, "slow_delivery_rate", "traffic_category", False),
                extreme_description(subset, "slow_delivery_rate", "traffic_category", True),
            ]
        )

    within_traffic_rows = []
    traffic_weather_order_rows = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        for _, row in subset.sort_values("mean_delivery_time").iterrows():
            within_traffic_rows.append(
                [
                    traffic,
                    row["weather_category"],
                    f"{int(row['delivery_count']):,}",
                    fmt(float(row["mean_delivery_time"])),
                    fmt(float(row["median_delivery_time"])),
                    fmt(float(row["p90_delivery_time"])),
                    f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                    f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    int(row["mean_rank_within_traffic"]),
                    int(row["slow_rate_rank_within_traffic"]),
                ]
            )
        if len(subset) >= 2:
            traffic_weather_order_rows.append(
                [
                    traffic,
                    len(subset),
                    " > ".join(
                        subset.sort_values("mean_delivery_time", ascending=False)[
                            "weather_category"
                        ]
                    ),
                    " > ".join(
                        subset.sort_values("slow_delivery_rate", ascending=False)[
                            "weather_category"
                        ]
                    ),
                ]
            )

    weather_traffic_order_rows = []
    for weather in weather_categories:
        subset = qualifying.loc[qualifying["weather_category"] == weather]
        if len(subset) >= 2:
            weather_traffic_order_rows.append(
                [
                    weather,
                    len(subset),
                    " > ".join(
                        subset.sort_values("mean_delivery_time", ascending=False)[
                            "traffic_category"
                        ]
                    ),
                    " > ".join(
                        subset.sort_values("slow_delivery_rate", ascending=False)[
                            "traffic_category"
                        ]
                    ),
                ]
            )

    weather_base = standalone.loc[standalone["dimension"] == "weather"].set_index("category")
    traffic_base = standalone.loc[standalone["dimension"] == "traffic"].set_index("category")
    worst_weather_slow = str(weather_base["standalone_slow_rate"].idxmax())
    best_weather_slow = str(weather_base["standalone_slow_rate"].idxmin())
    worst_weather_mean = str(weather_base["standalone_mean"].idxmax())
    best_weather_mean = str(weather_base["standalone_mean"].idxmin())
    strongest_traffic_slow = str(traffic_base["standalone_slow_rate"].idxmax())
    weakest_traffic_slow = str(traffic_base["standalone_slow_rate"].idxmin())
    standalone_slow_weather_gap = float(
        float(weather_base.loc[worst_weather_slow, "standalone_slow_rate"])
        - float(weather_base.loc[best_weather_slow, "standalone_slow_rate"])
    )
    standalone_mean_weather_gap = float(
        float(weather_base.loc[worst_weather_mean, "standalone_mean"])
        - float(weather_base.loc[best_weather_mean, "standalone_mean"])
    )

    weather_signal_rows = []
    weather_gap_values: list[tuple[str, float, float]] = []
    weather_rank_changes = 0
    weather_comparable_count = 0
    weather_worst_stays = 0
    weather_best_stays = 0
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic].set_index(
            "weather_category"
        )
        if worst_weather_slow not in subset.index or best_weather_slow not in subset.index:
            weather_signal_rows.append(
                [
                    traffic,
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "One or both standalone slow-rate endpoint groups do not qualify",
                ]
            )
            continue
        weather_comparable_count += 1
        worst = subset.loc[worst_weather_slow]
        best = subset.loc[best_weather_slow]
        rate_gap = float(worst["slow_delivery_rate"] - best["slow_delivery_rate"])
        mean_gap = float(worst["mean_delivery_time"] - best["mean_delivery_time"])
        weather_gap_values.append((traffic, mean_gap, rate_gap))
        ranked_by_rate = subset["slow_delivery_rate"].rank(method="min", ascending=False)
        weather_worst_stays += int(ranked_by_rate.loc[worst_weather_slow] == 1)
        weather_best_stays += int(ranked_by_rate.loc[best_weather_slow] == subset.shape[0])
        weather_rank_changes += int(
            ranked_by_rate.loc[worst_weather_slow] != 1
            or ranked_by_rate.loc[best_weather_slow] != subset.shape[0]
        )
        gap_relation = (
            "reversed" if rate_gap < -ABS_TOL
            else "unchanged" if close_enough(rate_gap, standalone_slow_weather_gap)
            else "reduced" if rate_gap >= 0 and rate_gap < standalone_slow_weather_gap
            else "increased"
        )
        weather_signal_rows.append(
            [
                traffic,
                f"{int(worst['delivery_count']):,} / {int(best['delivery_count']):,}",
                f"{float(worst['slow_delivery_rate']) * 100:.4f}% / {float(best['slow_delivery_rate']) * 100:.4f}%",
                f"{rate_gap * 100:+.4f} pp",
                f"{mean_gap:+.4f} min",
                f"{gap_relation}; {worst_weather_slow} rank "
                f"{int(ranked_by_rate.loc[worst_weather_slow])}, "
                f"{best_weather_slow} rank {int(ranked_by_rate.loc[best_weather_slow])}",
            ]
        )

    small_high_rate_rows = []
    qualifying_rate_max = float(qualifying["slow_delivery_rate"].max())
    for _, row in subminimum.sort_values(
        ["slow_delivery_rate", "delivery_count"],
        ascending=[False, True],
        na_position="last",
    ).iterrows():
        rate = row["slow_delivery_rate"]
        if pd.notna(rate) and float(rate) > qualifying_rate_max:
            small_high_rate_rows.append(
                [
                    row["weather_category"],
                    row["traffic_category"],
                    f"{int(row['delivery_count']):,}",
                    f"{int(row['slow_delivery_count']):,}",
                    f"{float(rate) * 100:.4f}%",
                    f"Higher than qualifying-cell maximum ({qualifying_rate_max * 100:.4f}%); descriptive only",
                ]
            )

    strongest_traffic_weather_rows = []
    traffic_signal_count = 0
    jam_slow_top_count = 0
    jam_mean_top_count = 0
    standalone_traffic_slow_gap = float(
        float(traffic_base.loc[strongest_traffic_slow, "standalone_slow_rate"])
        - float(traffic_base.loc[weakest_traffic_slow, "standalone_slow_rate"])
    )
    traffic_gap_reduced = traffic_gap_increased = traffic_gap_reversed = 0
    for weather in weather_categories:
        subset = qualifying.loc[qualifying["weather_category"] == weather].set_index(
            "traffic_category"
        )
        if len(subset) > 0:
            jam_slow_top_count += int(
                strongest_traffic_slow in subset.index
                and close_enough(
                    float(subset.loc[strongest_traffic_slow, "slow_delivery_rate"]),
                    float(subset["slow_delivery_rate"].max()),
                )
            )
            jam_mean_top_count += int(
                strongest_traffic_slow in subset.index
                and close_enough(
                    float(subset.loc[strongest_traffic_slow, "mean_delivery_time"]),
                    float(subset["mean_delivery_time"].max()),
                )
            )
        if strongest_traffic_slow not in subset.index or weakest_traffic_slow not in subset.index:
            strongest_traffic_weather_rows.append(
                [weather, "Not comparable", "Not comparable", "Not comparable"]
            )
            continue
        traffic_signal_count += 1
        jam = subset.loc[strongest_traffic_slow]
        low = subset.loc[weakest_traffic_slow]
        rate_delta = float(jam["slow_delivery_rate"] - low["slow_delivery_rate"])
        mean_delta = float(jam["mean_delivery_time"] - low["mean_delivery_time"])
        traffic_gap_reduced += int(
            rate_delta >= 0 and rate_delta < standalone_traffic_slow_gap
        )
        traffic_gap_increased += int(rate_delta > standalone_traffic_slow_gap)
        traffic_gap_reversed += int(rate_delta < 0)
        strongest_traffic_weather_rows.append(
            [
                weather,
                f"{int(jam['delivery_count']):,} / {int(low['delivery_count']):,}",
                f"{float(jam['slow_delivery_rate']) * 100:.4f}% / {float(low['slow_delivery_rate']) * 100:.4f}%",
                f"Jam−Low: {rate_delta * 100:+.4f} pp; "
                f"{rate_delta - standalone_traffic_slow_gap:+.4f} pp vs standalone gap; "
                f"mean {mean_delta:+.4f} min",
            ]
        )

    # Consistency counts for weather ranking by slow rate across traffic strata.
    rate_top_weather_counts = {weather: 0 for weather in weather_categories}
    rate_bottom_weather_counts = {weather: 0 for weather in weather_categories}
    mean_top_weather_counts = {weather: 0 for weather in weather_categories}
    weather_strata_count = 0
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        if len(subset) < 2:
            continue
        weather_strata_count += 1
        max_rate = subset["slow_delivery_rate"].max()
        min_rate = subset["slow_delivery_rate"].min()
        max_mean = subset["mean_delivery_time"].max()
        for weather in subset.loc[
            np.isclose(subset["slow_delivery_rate"], max_rate, atol=ABS_TOL, rtol=REL_TOL),
            "weather_category",
        ]:
            rate_top_weather_counts[str(weather)] += 1
        for weather in subset.loc[
            np.isclose(subset["slow_delivery_rate"], min_rate, atol=ABS_TOL, rtol=REL_TOL),
            "weather_category",
        ]:
            rate_bottom_weather_counts[str(weather)] += 1
        for weather in subset.loc[
            np.isclose(subset["mean_delivery_time"], max_mean, atol=ABS_TOL, rtol=REL_TOL),
            "weather_category",
        ]:
            mean_top_weather_counts[str(weather)] += 1

    top_contributors = qualifying.sort_values(
        ["slow_delivery_count", "slow_delivery_rate", "delivery_count"],
        ascending=[False, False, False],
        kind="stable",
    ).head(5)
    contributor_rows = []
    top_slow = int(top_contributors["slow_delivery_count"].sum())
    for _, row in top_contributors.iterrows():
        n, slow = int(row["delivery_count"]), int(row["slow_delivery_count"])
        contributor_rows.append(
            [
                row["weather_category"],
                row["traffic_category"],
                f"{n:,}",
                f"{slow:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                fmt(float(row["mean_delivery_time"])),
                fmt(float(row["median_delivery_time"])),
                fmt(float(row["p90_delivery_time"])),
                f"{slow:,} / {total_slow:,} ({100 * slow / total_slow:.2f}%)",
            ]
        )

    missing_both = int(
        (
            pd.to_numeric(frame[TARGET], errors="coerce").notna()
            & frame[WEATHER].isna()
            & frame[TRAFFIC].isna()
        ).sum()
    )
    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training source changed during analysis.")

    standalone_rows = []
    for weather in weather_categories:
        row = weather_base.loc[weather]
        standalone_rows.append(
            [
                weather,
                f"{int(row['standalone_count']):,}",
                fmt(float(row["standalone_mean"])),
                f"{int(row['standalone_slow_count']):,} / {int(row['standalone_count']):,}",
                f"{float(row['standalone_slow_rate']) * 100:.4f}%",
            ]
        )
    standalone_traffic_rows = []
    for traffic in sorted(traffic_base.index):
        row = traffic_base.loc[traffic]
        standalone_traffic_rows.append(
            [
                traffic,
                f"{int(row['standalone_count']):,}",
                fmt(float(row["standalone_mean"])),
                f"{int(row['standalone_slow_count']):,} / {int(row['standalone_count']):,}",
                f"{float(row['standalone_slow_rate']) * 100:.4f}%",
            ]
        )
    weather_gap_reduced_count = sum(
        gap >= 0 and gap < standalone_slow_weather_gap
        for _, _, gap in weather_gap_values
    )
    weather_gap_increased_count = sum(
        gap > standalone_slow_weather_gap
        for _, _, gap in weather_gap_values
    )
    weather_gap_reversed_count = sum(gap < 0 for _, _, gap in weather_gap_values)

    lines = [
        "# Weather × Traffic Analysis",
        "",
        "## Objective",
        "",
        "Describe whether observed weather-related delivery-performance differences remain visible within traffic categories, and whether traffic-related differences remain visible within weather categories. This is an observational analysis, not a causal analysis.",
        "",
        "## Analytical Context",
        "",
        f"The standalone Weather Analysis found the highest slow-delivery rate in **{worst_weather_slow}** ({float(weather_base.loc[worst_weather_slow, 'standalone_slow_rate']) * 100:.4f}%) and the lowest in **{best_weather_slow}** ({float(weather_base.loc[best_weather_slow, 'standalone_slow_rate']) * 100:.4f}%). By mean delivery time, the highest category was {worst_weather_mean} ({float(weather_base.loc[worst_weather_mean, 'standalone_mean']):.4f} minutes) and the lowest was {best_weather_mean} ({float(weather_base.loc[best_weather_mean, 'standalone_mean']):.4f} minutes). The standalone Traffic Analysis found the highest slow rate in {strongest_traffic_slow} ({float(traffic_base.loc[strongest_traffic_slow, 'standalone_slow_rate']) * 100:.4f}%) and lowest in {weakest_traffic_slow} ({float(traffic_base.loc[weakest_traffic_slow, 'standalone_slow_rate']) * 100:.4f}%).",
        "",
        "Standalone weather metrics used for context:",
        "",
        *markdown_table(
            ["Weather category", "Count", "Mean (min)", "Slow count / n", "Slow rate"],
            standalone_rows,
        ),
        "",
        "Standalone traffic metrics used for context:",
        "",
        *markdown_table(
            ["Traffic category", "Count", "Mean (min)", "Slow count / n", "Slow rate"],
            standalone_traffic_rows,
        ),
        "",
        "## Data Coverage",
        "",
        f"- Total valid-target records: **{metadata['valid_target_count']:,}** of {metadata['total_train_rows']:,} training rows.",
        f"- Valid-target records with missing weather: **{metadata['missing_weather_count']:,}**.",
        f"- Valid-target records with missing traffic: **{metadata['missing_traffic_count']:,}**.",
        f"- Records with both dimensions available for the combined analysis: **{metadata['eligible_combination_population']:,}**.",
        f"- Records missing either dimension (union; includes {missing_both:,} missing both): **{metadata['excluded_for_missing_either_count']:,}**. Missing weather and traffic counts overlap only for records missing both.",
        "Missing-dimension records remain in the valid-target population and are excluded only from the two-way grouped comparison. No source rows were modified.",
        "",
        "## Two-Way Analysis",
        "",
        f"The fixed slow rule is `Time_taken(min) > 40` minutes. Every observed weather × traffic pair is shown, including empty or subminimum cells. Cells with fewer than {MIN_GROUP_SIZE} records are descriptive only and are not ranked or used for substantive comparison.",
        "",
        "### Weather × Traffic Results",
        "",
        "Median and P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow-delivery rate is slow count / delivery count.",
        "",
        *markdown_table(
            ["Weather", "Traffic", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow count / n", "Slow rate", "Eligibility"],
            combination_rows,
        ),
        "",
        "## Within-Weather Traffic Comparison",
        "",
        "Extremes compare only qualifying traffic cells within each weather category; counts, medians, and P90 accompany values. Where fewer than two traffic cells qualify, the category is not compared.",
        "",
        *markdown_table(
            ["Weather", "Observed traffic cells (counts)", "Qualifying traffic cells", "Lowest mean traffic", "Highest mean traffic", "Lowest slow-rate traffic", "Highest slow-rate traffic"],
            within_weather_rows,
        ),
        "",
        "Traffic orders within each weather category, highest to lowest:",
        "",
        *markdown_table(
            ["Weather", "Qualifying traffic cells", "Mean order", "Slow-rate order"],
            weather_traffic_order_rows,
        ),
        "",
        "## Within-Traffic Weather Comparison",
        "",
        "Only weather × traffic cells with n ≥ 30 are ranked and compared. Rank 1 is the lowest mean or slow rate; ties share ranks.",
        "",
        *markdown_table(
            ["Traffic", "Weather", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_traffic_rows,
        ),
        "",
        "Weather orders within each traffic category, highest to lowest:",
        "",
        *markdown_table(
            ["Traffic", "Qualifying weather categories", "Mean order", "Slow-rate order"],
            traffic_weather_order_rows,
        ),
        "",
        "## Weather Signal Check",
        "",
        f"Standalone slow-rate endpoints: highest {worst_weather_slow} ({float(weather_base.loc[worst_weather_slow, 'standalone_slow_rate']) * 100:.4f}%) and lowest {best_weather_slow} ({float(weather_base.loc[best_weather_slow, 'standalone_slow_rate']) * 100:.4f}%), a difference of {standalone_slow_weather_gap * 100:.4f} percentage points. Standalone mean endpoints are {worst_weather_mean} and {best_weather_mean}, a difference of {standalone_mean_weather_gap:.4f} minutes.",
        "",
        *markdown_table(
            ["Traffic", "Counts: highest-rate weather / lowest-rate weather", "Slow rates: highest / lowest weather", "Within-traffic slow-rate gap", "Within-traffic mean gap", "Assessment / within-traffic ranks"],
            weather_signal_rows,
        ),
        "",
        f"The standalone highest slow-rate category {worst_weather_slow} remains the highest slow-rate category within {weather_worst_stays} of {weather_comparable_count} traffic strata where both weather endpoints qualify; {best_weather_slow} remains lowest within {weather_best_stays}. Endpoint ranking differs from the standalone order in {weather_rank_changes} comparable strata (including ties/rank shifts).",
        "",
        "Strongest standalone traffic signal across weather categories (Jam vs Low):",
        "",
        f"The standalone Jam-minus-Low slow-rate difference was {standalone_traffic_slow_gap * 100:.4f} percentage points.",
        "",
        *markdown_table(
            ["Weather", "Counts: Jam / Low", "Slow rates: Jam / Low", "Conditional gap vs standalone; mean difference"],
            strongest_traffic_weather_rows,
        ),
        "",
        f"Across the {traffic_signal_count} weather strata where both Jam and Low qualify, the Jam–Low slow-rate gap was reduced in {traffic_gap_reduced}, increased in {traffic_gap_increased}, and reversed in {traffic_gap_reversed}. Jam has the highest within-weather slow rate in {jam_slow_top_count} categories and the highest mean in {jam_mean_top_count} categories where its cell qualifies.",
        "",
        "Subminimum cells whose observed slow rate exceeds the maximum slow rate among qualifying cells (high rates remain descriptive only):",
        "",
        *markdown_table(
            ["Weather", "Traffic", "Count", "Slow count", "Slow rate", "Comparison"],
            small_high_rate_rows
            or [["None", "—", "—", "—", "—", "No subminimum cell exceeds the qualifying-cell maximum"]],
        ),
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, **{total_slow:,}** meet the fixed slow rule. Of these, **{qualifying_slow:,}** occur in qualifying weather × traffic cells, **{subminimum_slow:,}** in subminimum cells, and **{metadata['excluded_slow_delivery_count']:,}** in records with at least one missing dimension. The five qualifying cells with the largest slow counts account for **{top_slow:,} ({top_slow / total_slow * 100:.2f}%)** of all slow deliveries.",
        "",
        *markdown_table(
            ["Weather", "Traffic", "Count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            contributor_rows,
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"SQL from `sql/12_weather_traffic_analysis.sql` ran against an in-memory SQLite {sqlite_version} table. Pandas independently grouped the same valid-target records. Counts and ranks were compared exactly; floating-point metrics use `numpy.isclose` with absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Weather × traffic cell metrics and standalone references", metric_checks, "MATCH"],
                ["Within-weather and within-traffic ranks", rank_checks, "MATCH"],
                ["Missing-dimension populations and cell-count reconciliation", "all", "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- The highest standalone slow-rate category, {worst_weather_slow}, remains the highest within-traffic endpoint in {weather_worst_stays}/{weather_comparable_count} comparable strata; the lowest standalone category, {best_weather_slow}, remains lowest in {weather_best_stays}/{weather_comparable_count}.",
        f"- Weather slow-rate endpoint differences were reduced in {weather_gap_reduced_count} comparable traffic categor{'y' if weather_gap_reduced_count == 1 else 'ies'}, increased in {weather_gap_increased_count}, and reversed in {weather_gap_reversed_count}; only strata where both endpoint cells qualify are included.",
        f"- Jam-versus-Low slow-rate differences are directly comparable in {traffic_signal_count} of {len(weather_categories)} weather categories; the conditional gap is smaller than the standalone gap in {traffic_gap_reduced}, larger in {traffic_gap_increased}, and reversed in {traffic_gap_reversed}. Jam has the highest within-weather slow rate in {jam_slow_top_count} categories and highest mean in {jam_mean_top_count}.",
        f"- {len(small_high_rate_rows)} subminimum cell(s) have a slow rate above the largest qualifying-cell rate; each is explicitly labeled descriptive only.",
        "",
        "## Interpretation",
        "",
        "The two-way results show observed weather differences within traffic categories and observed traffic differences within weather categories. Standalone category rankings may shift after stratification, and comparisons are limited to cells meeting the 30-record minimum. This analysis does not establish that weather or traffic causes delivery-time differences.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Combinations with fewer than 30 records are excluded from substantive comparisons and rankings.",
        "- Weather and traffic may be related to other operational factors.",
        "- Missing weather/traffic dimensions reduce the combined-analysis population; their counts are reported separately and the union is reported without double-counting.",
        "- This analysis does not control for city, distance, vehicle, courier, multiple deliveries, or time.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.",
        "- Missing categories were not imputed, and no rows or raw categories were altered.",
        "",
        f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; its schema is unchanged.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(sql_groups)} Weather x traffic cells: "
        f"{metric_checks} metric/population checks and {rank_checks} ranking checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
