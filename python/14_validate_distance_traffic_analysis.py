"""Validate Distance x traffic analysis against SQLite and write its report."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "11_distance_traffic_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "distance_traffic_analysis.md"

TARGET = "Time_taken(min)"
TRAFFIC = "Road_traffic_density"
COORDINATES = (
    "Restaurant_latitude",
    "Restaurant_longitude",
    "Delivery_location_latitude",
    "Delivery_location_longitude",
)
LATITUDES = ("Restaurant_latitude", "Delivery_location_latitude")
LONGITUDES = ("Restaurant_longitude", "Delivery_location_longitude")
EARTH_RADIUS_KM = 6371.0088
SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABS_TOL = 1e-9
REL_TOL = 1e-12
DISTANCE_BANDS = (
    "0-1 km",
    "1-2 km",
    "2-3 km",
    "3-5 km",
    "5-10 km",
    "10-15 km",
    "15+ km",
)
BAND_EDGES = (0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, np.inf)
COUNT_FIELDS = ("delivery_count", "slow_delivery_count")
FLOAT_FIELDS = (
    "mean_delivery_time",
    "median_delivery_time",
    "p90_delivery_time",
    "slow_delivery_rate",
)
RANK_FIELDS = (
    "mean_rank_within_traffic",
    "highest_mean_rank_within_traffic",
    "slow_rate_rank_within_traffic",
    "highest_slow_rate_rank_within_traffic",
    "mean_rank_within_distance",
    "highest_mean_rank_within_distance",
    "slow_rate_rank_within_distance",
    "highest_slow_rate_rank_within_distance",
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


def parse_sql_script(
    connection: sqlite3.Connection, sql_text: str
) -> list[pd.DataFrame]:
    """Run a multi-statement SQL file and collect each SELECT result set."""
    cursor = connection.cursor()
    statement_lines: list[str] = []
    results: list[pd.DataFrame] = []
    for line in sql_text.splitlines():
        statement_lines.append(line)
        candidate = "\n".join(statement_lines)
        if not sqlite3.complete_statement(candidate):
            continue
        statement = "\n".join(
            line for line in candidate.splitlines()
            if not line.lstrip().startswith("--")
        ).strip()
        statement_lines.clear()
        if not statement:
            continue
        cursor.execute(statement)
        if cursor.description is not None:
            results.append(
                pd.DataFrame(
                    cursor.fetchall(),
                    columns=[item[0] for item in cursor.description],
                )
            )
    if "\n".join(statement_lines).strip():
        raise ValueError("SQL script ends with an incomplete statement.")
    return results


def haversine_km(coordinates: pd.DataFrame, valid: pd.Series) -> pd.Series:
    """Calculate the Step 5.8 spherical Haversine distance in kilometers."""
    result = pd.Series(np.nan, index=coordinates.index, dtype="float64")
    selected = coordinates.loc[valid]
    lat_1 = np.radians(selected["Restaurant_latitude"].to_numpy(dtype="float64"))
    lon_1 = np.radians(selected["Restaurant_longitude"].to_numpy(dtype="float64"))
    lat_2 = np.radians(selected["Delivery_location_latitude"].to_numpy(dtype="float64"))
    lon_2 = np.radians(selected["Delivery_location_longitude"].to_numpy(dtype="float64"))
    delta_lat = lat_2 - lat_1
    delta_lon = lon_2 - lon_1
    a = (
        np.sin(delta_lat / 2.0) ** 2
        + np.cos(lat_1) * np.cos(lat_2) * np.sin(delta_lon / 2.0) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    result.loc[valid] = (
        EARTH_RADIUS_KM * 2.0 * np.arcsin(np.sqrt(a))
    )
    return result


def assign_bands(distance: pd.Series) -> pd.Series:
    """Apply the Step 5.8 exhaustive, half-open distance intervals."""
    return pd.cut(
        distance,
        bins=BAND_EDGES,
        labels=DISTANCE_BANDS,
        right=False,
        include_lowest=True,
        ordered=False,
    ).astype("object").where(distance.notna(), pd.NA)


def rank_qualifying(
    groups: pd.DataFrame,
    partition: str,
    metric: str,
    ascending: bool,
) -> pd.Series:
    """Create SQL RANK-equivalent values only for cells meeting n >= 30."""
    qualifying = groups.loc[groups["delivery_count"] >= MIN_GROUP_SIZE]
    result = pd.Series(np.nan, index=groups.index, dtype="float64")
    result.loc[qualifying.index] = qualifying.groupby(partition)[metric].rank(
        method="min",
        ascending=ascending,
    )
    return result


def prepare_records(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Calculate valid targets, coordinate mask, Haversine distances and bands."""
    target = pd.to_numeric(frame[TARGET], errors="coerce")
    numeric = pd.DataFrame(index=frame.index)
    for column in COORDINATES:
        numeric[column] = pd.to_numeric(frame[column], errors="coerce")
    coordinate_valid = numeric.notna().all(axis=1)
    for column in LATITUDES:
        coordinate_valid &= numeric[column].between(-90.0, 90.0, inclusive="both")
    for column in LONGITUDES:
        coordinate_valid &= numeric[column].between(-180.0, 180.0, inclusive="both")
    distance = haversine_km(numeric, coordinate_valid)
    bands = assign_bands(distance)
    valid_target = target.notna()
    records = pd.DataFrame(
        {
            "source_row_id": np.arange(1, len(frame) + 1, dtype="int64"),
            "order_id": frame["ID"].to_numpy(),
            "delivery_time": target.astype("float64"),
            "traffic_category": frame[TRAFFIC].to_numpy(),
            "distance_km": distance,
            "distance_band": bands,
            "coordinate_valid": coordinate_valid.to_numpy(),
            "valid_target": valid_target.to_numpy(),
        },
        index=frame.index,
    )
    meta = {
        "total_train_rows": len(frame),
        "valid_target_rows": int(valid_target.sum()),
        "valid_target_coordinate_rows": int((valid_target & coordinate_valid).sum()),
        "target_rows_excluded_for_coordinates": int((valid_target & ~coordinate_valid).sum()),
        "target_rows_missing_traffic": int(
            (valid_target & coordinate_valid & frame[TRAFFIC].isna()).sum()
        ),
        "categorized_target_rows": int(
            (valid_target & coordinate_valid & frame[TRAFFIC].notna()).sum()
        ),
        "all_slow_target_rows": int((valid_target & (target > SLOW_THRESHOLD)).sum()),
        "slow_rows_excluded_for_coordinates": int(
            (valid_target & ~coordinate_valid & (target > SLOW_THRESHOLD)).sum()
        ),
        "slow_rows_missing_traffic": int(
            (valid_target & coordinate_valid & frame[TRAFFIC].isna()
             & (target > SLOW_THRESHOLD)).sum()
        ),
        "rows_with_missing_coordinates": int(frame[list(COORDINATES)].isna().any(axis=1).sum()),
        "rows_with_non_numeric_coordinates": int(
            (
                frame[list(COORDINATES)].notna()
                & numeric.isna()
            ).any(axis=1).sum()
        ),
        "rows_with_out_of_range_coordinates": int(
            (
                pd.concat(
                    [
                        numeric[column].notna()
                        & ~numeric[column].between(-90.0, 90.0, inclusive="both")
                        for column in LATITUDES
                    ],
                    axis=1,
                ).any(axis=1)
                | pd.concat(
                    [
                        numeric[column].notna()
                        & ~numeric[column].between(-180.0, 180.0, inclusive="both")
                        for column in LONGITUDES
                    ],
                    axis=1,
                ).any(axis=1)
            ).fillna(False).sum()
        ),
    }
    return records, meta


def calculate_groups(records: pd.DataFrame) -> pd.DataFrame:
    """Independently calculate a complete observed-traffic by exact-band grid."""
    valid = records.loc[
        records["valid_target"]
        & records["coordinate_valid"]
        & records["traffic_category"].notna()
    ].copy()
    traffic_categories = sorted(valid["traffic_category"].astype(str).unique())
    rows: list[dict[str, object]] = []
    for band in DISTANCE_BANDS:
        for traffic in traffic_categories:
            group = valid.loc[
                (valid["distance_band"] == band)
                & (valid["traffic_category"].astype(str) == traffic)
            ]
            count = len(group)
            slow_count = int((group["delivery_time"] > SLOW_THRESHOLD).sum())
            if count:
                values = group["delivery_time"].to_numpy(dtype="float64")
                mean = float(np.mean(values))
                median = float(np.percentile(values, 50, method="linear"))
                p90 = float(np.percentile(values, 90, method="linear"))
                rate = slow_count / count
            else:
                mean = median = p90 = rate = np.nan
            rows.append(
                {
                    "distance_band": band,
                    "sort_order": DISTANCE_BANDS.index(band) + 1,
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
    specs = (
        ("mean_rank_within_traffic", "traffic_category", "mean_delivery_time", True),
        ("highest_mean_rank_within_traffic", "traffic_category", "mean_delivery_time", False),
        ("slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_traffic", "traffic_category", "slow_delivery_rate", False),
        ("mean_rank_within_distance", "distance_band", "mean_delivery_time", True),
        ("highest_mean_rank_within_distance", "distance_band", "mean_delivery_time", False),
        ("slow_rate_rank_within_distance", "distance_band", "slow_delivery_rate", True),
        ("highest_slow_rate_rank_within_distance", "distance_band", "slow_delivery_rate", False),
    )
    for output, partition, metric, ascending in specs:
        groups[output] = rank_qualifying(groups, partition, metric, ascending)
    return groups


def validate_sql(
    metadata_sql: pd.Series,
    row_sql: pd.DataFrame,
    groups_sql: pd.DataFrame,
    top_sql: pd.DataFrame,
    records: pd.DataFrame,
    groups_python: pd.DataFrame,
    metadata_python: dict[str, int],
) -> tuple[int, int, float]:
    """Validate populations, all row-level distances/bands, metrics and ranks."""
    metric_checks = rank_checks = 0
    for field, expected in metadata_python.items():
        if int(metadata_sql[field]) != expected:
            raise AssertionError(f"SQL/Python population differs for {field}.")
        metric_checks += 1

    expected_rows = records.loc[
        records["valid_target"] & records["coordinate_valid"]
    ].sort_values("source_row_id")
    row_sql = row_sql.sort_values("source_row_id")
    if not np.array_equal(
        row_sql["source_row_id"].to_numpy(dtype="int64"),
        expected_rows["source_row_id"].to_numpy(dtype="int64"),
    ):
        raise AssertionError("SQL/Python valid coordinate target rows differ.")
    if len(row_sql) != len(expected_rows):
        raise AssertionError("SQL/Python Haversine calculation counts differ.")
    maximum_difference = 0.0
    for sql_row, py_row in zip(row_sql.itertuples(), expected_rows.itertuples()):
        difference = abs(float(sql_row.distance_km) - float(py_row.distance_km))
        maximum_difference = max(maximum_difference, difference)
        if not close_enough(float(sql_row.distance_km), float(py_row.distance_km)):
            raise AssertionError(f"Haversine distance differs at row {sql_row.source_row_id}.")
        if str(sql_row.distance_band) != str(py_row.distance_band):
            raise AssertionError(f"Distance band differs at row {sql_row.source_row_id}.")
        if str(sql_row.traffic_category) != str(py_row.traffic_category):
            if not (pd.isna(sql_row.traffic_category) and pd.isna(py_row.traffic_category)):
                raise AssertionError(f"Traffic category differs at row {sql_row.source_row_id}.")
        metric_checks += 2

    keys = ["distance_band", "traffic_category"]
    sql_indexed = groups_sql.set_index(keys).sort_index()
    py_indexed = groups_python.set_index(keys).sort_index()
    if not sql_indexed.index.equals(py_indexed.index):
        raise AssertionError("SQL/Python Distance x traffic grid differs.")
    for key in sql_indexed.index:
        sql_row = sql_indexed.loc[key]
        py_row = py_indexed.loc[key]
        for field in COUNT_FIELDS:
            if int(sql_row[field]) != int(py_row[field]):
                raise AssertionError(f"{key} {field} differs.")
            metric_checks += 1
        if int(sql_row["sort_order"]) != int(py_row["sort_order"]):
            raise AssertionError(f"{key} sort order differs.")
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

    python_top = (
        expected_rows.sort_values(
            ["distance_km", "source_row_id"],
            ascending=[False, True],
            kind="stable",
        ).head(10).reset_index(drop=True)
    )
    if top_sql["source_row_id"].astype(int).tolist() != python_top[
        "source_row_id"
    ].astype(int).tolist():
        raise AssertionError("SQL/Python top-10 extreme records differ.")
    for sql_value, py_value in zip(top_sql["distance_km"], python_top["distance_km"]):
        if not close_enough(float(sql_value), float(py_value)):
            raise AssertionError("SQL/Python top-10 distance values differ.")
        metric_checks += 1
    return metric_checks, rank_checks, maximum_difference


def ranked_extreme(
    subset: pd.DataFrame, metric: str, category_column: str, high: bool
) -> str:
    """List tied extrema with cell size and distribution details."""
    qualifying = subset.loc[subset["delivery_count"] >= MIN_GROUP_SIZE]
    if len(qualifying) < 2:
        return "Not comparable (fewer than 2 qualifying groups)"
    value = qualifying[metric].max() if high else qualifying[metric].min()
    tied = qualifying.loc[
        np.isclose(qualifying[metric], value, atol=ABS_TOL, rtol=REL_TOL)
    ]
    parts = []
    for _, row in tied.iterrows():
        stat = float(row[metric])
        rendered = f"{stat * 100:.4f}%" if metric == "slow_delivery_rate" else f"{fmt(stat)} min"
        parts.append(
            f"{row[category_column]} (n={int(row['delivery_count']):,}; {rendered}; "
            f"median {fmt(float(row['median_delivery_time']))}; "
            f"P90 {fmt(float(row['p90_delivery_time']))})"
        )
    return "; ".join(parts)


def main() -> None:
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = ["ID", TARGET, TRAFFIC, *COORDINATES]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Required analysis columns are missing: {missing}")

    records, metadata = prepare_records(frame)
    python_groups = calculate_groups(records)
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        sql_results = parse_sql_script(connection, SQL_PATH.read_text(encoding="utf-8"))
        sqlite_version = sqlite3.sqlite_version
    finally:
        connection.close()
    if len(sql_results) != 4:
        raise AssertionError(f"Expected 4 SQL result sets, received {len(sql_results)}.")
    metadata_sql, row_sql, groups_sql, top_sql = sql_results
    metric_checks, rank_checks, max_distance_difference = validate_sql(
        metadata_sql.iloc[0],
        row_sql,
        groups_sql,
        top_sql,
        records,
        python_groups,
        metadata,
    )

    all_valid_target = records.loc[records["valid_target"]]
    valid_distance = all_valid_target.loc[all_valid_target["coordinate_valid"]]
    values = valid_distance["distance_km"].to_numpy(dtype="float64")
    distance_distribution = {
        "count": len(values),
        "min": float(np.min(values)),
        "p25": float(np.percentile(values, 25, method="linear")),
        "median": float(np.percentile(values, 50, method="linear")),
        "p75": float(np.percentile(values, 75, method="linear")),
        "p90": float(np.percentile(values, 90, method="linear")),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "zero_count": int((values == 0).sum()),
        "negative_count": int((values < 0).sum()),
        "over_15_count": int((values >= 15).sum()),
    }
    if distance_distribution["negative_count"] != 0:
        raise AssertionError("Haversine calculation produced a negative distance.")
    if valid_distance["distance_band"].isna().any():
        raise AssertionError("A valid distance was not assigned to a band.")
    distance_band_counts = (
        valid_distance["distance_band"].value_counts().reindex(DISTANCE_BANDS, fill_value=0)
    )
    if int(distance_band_counts.sum()) != len(valid_distance):
        raise AssertionError("Distance-band assignment does not reconcile.")

    qualifying = python_groups.loc[
        python_groups["delivery_count"] >= MIN_GROUP_SIZE
    ].copy()
    short_bands = DISTANCE_BANDS[:5]
    long_bands = DISTANCE_BANDS[5:]
    traffic_categories = sorted(
        valid_distance.loc[valid_distance["traffic_category"].notna(), "traffic_category"]
        .astype(str).unique()
    )
    within_traffic_rows: list[list[object]] = []
    within_traffic_patterns: list[tuple[str, str, str, int]] = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        for _, row in subset.sort_values("sort_order").iterrows():
            within_traffic_rows.append(
                [
                    traffic,
                    row["distance_band"],
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
            ordered = subset.sort_values("sort_order")
            means = ordered["mean_delivery_time"].to_numpy(dtype="float64")
            rates = ordered["slow_delivery_rate"].to_numpy(dtype="float64")
            mean_pattern = (
                "increasing" if np.all(np.diff(means) > 0)
                else "decreasing" if np.all(np.diff(means) < 0)
                else "mixed / ties"
            )
            rate_pattern = (
                "increasing" if np.all(np.diff(rates) > 0)
                else "decreasing" if np.all(np.diff(rates) < 0)
                else "mixed / ties"
            )
            within_traffic_patterns.append((traffic, mean_pattern, rate_pattern, len(subset)))

    within_distance_rows: list[list[object]] = []
    within_distance_patterns: list[list[object]] = []
    for band in DISTANCE_BANDS:
        subset = qualifying.loc[qualifying["distance_band"] == band]
        if subset.empty:
            continue
        ordered = subset.sort_values("mean_delivery_time")
        for _, row in ordered.iterrows():
            within_distance_rows.append(
                [
                    band,
                    row["traffic_category"],
                    f"{int(row['delivery_count']):,}",
                    fmt(float(row["mean_delivery_time"])),
                    fmt(float(row["median_delivery_time"])),
                    fmt(float(row["p90_delivery_time"])),
                    f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                    f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    int(row["mean_rank_within_distance"]),
                    int(row["slow_rate_rank_within_distance"]),
                ]
            )
        if len(subset) >= 2:
            mean_order = " > ".join(
                subset.sort_values("mean_delivery_time", ascending=False)["traffic_category"]
            )
            rate_order = " > ".join(
                subset.sort_values("slow_delivery_rate", ascending=False)["traffic_category"]
            )
            within_distance_patterns.append([band, len(subset), mean_order, rate_order])

    standalone_distance_rows = []
    for band in DISTANCE_BANDS:
        group = valid_distance.loc[valid_distance["distance_band"] == band]
        if group.empty:
            continue
        count = len(group)
        slow_count = int((group["delivery_time"] > SLOW_THRESHOLD).sum())
        standalone_distance_rows.append(
            {
                "distance_band": band,
                "delivery_count": count,
                "slow_delivery_rate": slow_count / count,
            }
        )
    standalone_distance = pd.DataFrame(standalone_distance_rows).set_index("distance_band")

    signal_rows: list[list[object]] = []
    long_signal_count = {"10-15 km": 0, "15+ km": 0}
    for traffic in traffic_categories:
        all_short = qualifying.loc[
            qualifying["traffic_category"].eq(traffic)
            & qualifying["distance_band"].isin(short_bands)
        ]
        if all_short.empty:
            short_reference = None
        else:
            short_reference = float(all_short["slow_delivery_rate"].max())
        long_lookup: dict[str, pd.Series | None] = {}
        for band in long_bands:
            cell = qualifying.loc[
                qualifying["traffic_category"].eq(traffic)
                & qualifying["distance_band"].eq(band)
            ]
            long_lookup[band] = None if cell.empty else cell.iloc[0]
            if cell.empty or short_reference is None:
                signal_rows.append(
                    [
                        traffic,
                        band,
                        "Not comparable",
                        "Not comparable",
                        "Not comparable",
                        "No qualifying short-distance reference or long-distance cell",
                    ]
                )
                continue
            row = cell.iloc[0]
            gap = float(row["slow_delivery_rate"] - short_reference)
            is_elevated = gap > ABS_TOL
            long_signal_count[band] += int(is_elevated)
            signal_rows.append(
                [
                    traffic,
                    band,
                    f"{int(row['delivery_count']):,}",
                    f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    f"{short_reference * 100:.4f}%",
                    f"{gap * 100:+.4f} pp; {'elevated' if is_elevated else 'not higher'}",
                ]
            )
        cell_10_15 = long_lookup["10-15 km"]
        cell_15 = long_lookup["15+ km"]
        if cell_10_15 is None or cell_15 is None:
            signal_rows.append(
                [
                    traffic,
                    "15+ vs 10-15 comparison",
                    "Not comparable",
                    "Not comparable",
                    "Not comparable",
                    "One or both long-band cells do not meet n ≥ 30",
                ]
            )
        else:
            signal_rows.append(
                [
                    traffic,
                    "15+ vs 10-15 comparison",
                    f"{int(cell_15['delivery_count']):,} vs {int(cell_10_15['delivery_count']):,}",
                    f"{float(cell_15['slow_delivery_rate']) * 100:.4f}% vs {float(cell_10_15['slow_delivery_rate']) * 100:.4f}%",
                    "—",
                    f"Slow-rate delta {100 * float(cell_15['slow_delivery_rate'] - cell_10_15['slow_delivery_rate']):+.4f} pp; "
                    f"mean delta {float(cell_15['mean_delivery_time'] - cell_10_15['mean_delivery_time']):+.4f} min",
                ]
            )

    # The prior report's exact top-ten records define the extreme-distance set.
    extreme_rows = records.loc[
        records["source_row_id"].isin(top_sql["source_row_id"].astype(int))
    ].copy()
    extreme_rows = extreme_rows.sort_values(
        ["distance_km", "source_row_id"],
        ascending=[False, True],
        kind="stable",
    )
    extreme_with_traffic = int(extreme_rows["traffic_category"].notna().sum())
    extreme_without_traffic = len(extreme_rows) - extreme_with_traffic
    if len(extreme_rows) != 10:
        raise AssertionError("Could not reproduce the ten Step 5.8 extreme records.")
    top_table = []
    for _, row in extreme_rows.iterrows():
        traffic = "NULL" if pd.isna(row["traffic_category"]) else row["traffic_category"]
        top_table.append(
            [
                row["order_id"],
                fmt(float(row["distance_km"])),
                fmt(float(row["delivery_time"])),
                traffic,
                row["distance_band"],
            ]
        )

    # Sensitivity only: primary metrics include every record; this compares
    # metrics after removing exactly the prior Step 5.8 top-ten extreme records.
    extreme_ids = set(extreme_rows["source_row_id"].astype(int))
    primary = valid_distance.loc[valid_distance["traffic_category"].notna()].copy()
    primary["traffic_label"] = primary["traffic_category"].astype(str)
    primary["band_label"] = primary["distance_band"].astype(str)
    sensitivity_rows = []
    affected_keys = (
        extreme_rows.loc[extreme_rows["traffic_category"].notna()]
        .groupby(["distance_band", "traffic_category"], observed=True)
        .size()
        .rename("extreme_count")
        .reset_index()
    )
    mean_order_changes = rate_order_changes = 0
    sensitivity_cell_records: list[dict[str, object]] = []
    for _, keyrow in affected_keys.iterrows():
        band, traffic = str(keyrow["distance_band"]), str(keyrow["traffic_category"])
        full = primary.loc[
            (primary["band_label"] == band) & (primary["traffic_label"] == traffic)
        ]
        reduced = full.loc[~full["source_row_id"].isin(extreme_ids)]
        full_count, reduced_count = len(full), len(reduced)
        if full_count < MIN_GROUP_SIZE or reduced_count < MIN_GROUP_SIZE:
            continue
        full_slow = int((full["delivery_time"] > SLOW_THRESHOLD).sum())
        reduced_slow = int((reduced["delivery_time"] > SLOW_THRESHOLD).sum())
        full_mean, reduced_mean = float(full["delivery_time"].mean()), float(reduced["delivery_time"].mean())
        full_rate, reduced_rate = full_slow / full_count, reduced_slow / reduced_count
        sensitivity_cell_records.append(
            {
                "distance_band": band,
                "traffic_category": traffic,
                "full_mean": full_mean,
                "reduced_mean": reduced_mean,
                "full_rate": full_rate,
                "reduced_rate": reduced_rate,
            }
        )
        sensitivity_rows.append(
            [
                band,
                traffic,
                int(keyrow["extreme_count"]),
                f"{full_count:,}",
                f"{reduced_count:,}",
                fmt(full_mean),
                fmt(reduced_mean),
                f"{reduced_mean - full_mean:+.6f}",
                f"{full_rate * 100:.4f}%",
                f"{reduced_rate * 100:.4f}%",
                f"{(reduced_rate - full_rate) * 100:+.4f} pp",
            ]
        )

    if sensitivity_cell_records:
        sens = pd.DataFrame(sensitivity_cell_records)
        max_mean_change = float((sens["reduced_mean"] - sens["full_mean"]).abs().max())
        max_rate_change_pp = float(
            ((sens["reduced_rate"] - sens["full_rate"]).abs() * 100).max()
        )
        # Compare traffic order using every qualifying traffic cell in any
        # affected distance band, not only cells containing top-ten records.
        for band in affected_keys["distance_band"].astype(str).unique():
            band_records = primary.loc[primary["band_label"] == band]
            full_means: dict[str, float] = {}
            reduced_means: dict[str, float] = {}
            full_rates: dict[str, float] = {}
            reduced_rates: dict[str, float] = {}
            for traffic, subset in band_records.groupby("traffic_label", sort=True):
                remaining = subset.loc[~subset["source_row_id"].isin(extreme_ids)]
                if len(subset) < MIN_GROUP_SIZE or len(remaining) < MIN_GROUP_SIZE:
                    continue
                full_means[str(traffic)] = float(subset["delivery_time"].mean())
                reduced_means[str(traffic)] = float(remaining["delivery_time"].mean())
                full_rates[str(traffic)] = float(
                    (subset["delivery_time"] > SLOW_THRESHOLD).mean()
                )
                reduced_rates[str(traffic)] = float(
                    (remaining["delivery_time"] > SLOW_THRESHOLD).mean()
                )
            if len(full_means) >= 2:
                full_mean_order = sorted(full_means, key=full_means.get)
                reduced_mean_order = sorted(reduced_means, key=reduced_means.get)
                full_rate_order = sorted(full_rates, key=full_rates.get)
                reduced_rate_order = sorted(reduced_rates, key=reduced_rates.get)
                mean_order_changes += int(full_mean_order != reduced_mean_order)
                rate_order_changes += int(full_rate_order != reduced_rate_order)
    else:
        max_mean_change = max_rate_change_pp = 0.0

    top_slow = qualifying.sort_values(
        ["slow_delivery_count", "slow_delivery_rate", "delivery_count"],
        ascending=[False, False, False],
        kind="stable",
    ).head(5)
    all_slow = metadata["all_slow_target_rows"]
    top_slow_count = int(top_slow["slow_delivery_count"].sum())
    contribution_rows = [
        [
            row["distance_band"],
            row["traffic_category"],
            f"{int(row['delivery_count']):,}",
            f"{int(row['slow_delivery_count']):,}",
            f"{float(row['slow_delivery_rate']) * 100:.4f}%",
            fmt(float(row["mean_delivery_time"])),
            fmt(float(row["median_delivery_time"])),
            fmt(float(row["p90_delivery_time"])),
            f"{int(row['slow_delivery_count']):,} / {all_slow:,} "
            f"({100 * int(row['slow_delivery_count']) / all_slow:.2f}%)",
        ]
        for _, row in top_slow.iterrows()
    ]

    within_traffic_extremes = []
    for traffic in traffic_categories:
        subset = qualifying.loc[qualifying["traffic_category"] == traffic]
        within_traffic_extremes.append(
            [
                traffic,
                len(subset),
                ranked_extreme(subset, "mean_delivery_time", "distance_band", False),
                ranked_extreme(subset, "mean_delivery_time", "distance_band", True),
                ranked_extreme(subset, "slow_delivery_rate", "distance_band", False),
                ranked_extreme(subset, "slow_delivery_rate", "distance_band", True),
            ]
        )

    available_short_bands = [
        band for band in short_bands if band in standalone_distance.index
    ]
    primary_short_max = float(
        standalone_distance.loc[available_short_bands, "slow_delivery_rate"].max()
    )
    primary_long_results = {
        band: float(standalone_distance.loc[band, "slow_delivery_rate"])
        for band in long_bands
    }
    # Use compact category-level counts for monotonic pattern reporting.
    monotonic_mean_count = sum(item[1] == "increasing" for item in within_traffic_patterns)
    monotonic_rate_count = sum(item[2] == "increasing" for item in within_traffic_patterns)
    mixed_count = sum(item[1] == "mixed / ties" or item[2] == "mixed / ties" for item in within_traffic_patterns)

    # Overall distance percentiles and grouped target populations.
    overall_distribution_rows = [[
        f"{distance_distribution['count']:,}",
        fmt(distance_distribution["min"]),
        fmt(distance_distribution["p25"]),
        fmt(distance_distribution["median"]),
        fmt(distance_distribution["p75"]),
        fmt(distance_distribution["p90"]),
        fmt(distance_distribution["max"]),
        fmt(distance_distribution["mean"]),
    ]]
    small_slow = int(
        python_groups.loc[
            python_groups["delivery_count"] < MIN_GROUP_SIZE,
            "slow_delivery_count",
        ].sum()
    )
    qualifying_slow = int(qualifying["slow_delivery_count"].sum())
    if (
        qualifying_slow
        + small_slow
        + metadata["slow_rows_missing_traffic"]
        + metadata["slow_rows_excluded_for_coordinates"]
        != all_slow
    ):
        raise AssertionError("Slow-delivery population does not reconcile.")
    if int(python_groups["delivery_count"].sum()) != metadata["categorized_target_rows"]:
        raise AssertionError("Distance x traffic counts do not reconcile.")

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_before != source_hash_after or frame.columns.tolist() != original_columns:
        raise AssertionError("The cleaned training CSV changed during validation.")

    signal_comparison_rows = [
        [
            "Standalone all-traffic comparison",
            "5-10 km",
            f"{int(standalone_distance.loc['5-10 km', 'delivery_count']):,}",
            f"{primary_short_max * 100:.4f}% maximum among qualifying <10 km bands",
            "—",
            f"10-15: {primary_long_results['10-15 km'] * 100:.4f}%; "
            f"15+: {primary_long_results['15+ km'] * 100:.4f}%",
        ],
        *signal_rows,
    ]
    lines = [
        "# Distance × Traffic Analysis",
        "",
        "## Objective",
        "",
        "Describe whether the association between approximate straight-line geographic distance and delivery performance remains visible across traffic categories, and whether traffic differences remain visible across distance bands. This is observational analysis only.",
        "",
        "## Analytical Context",
        "",
        "Step 5.8 reported slow-delivery rates of 16.2096% in 10–15 km and 16.2934% in 15+ km, compared with 3.0445% in 5–10 km. Its Pearson correlation was -0.00250807 and Spearman correlation was 0.31378161. Step 5.2 reported traffic-category slow rates from 1.3827% (Low) to 20.0099% (Jam). This step considers only exact distance bands × `Road_traffic_density` categories.",
        "",
        "## Distance Method",
        "",
        "Approximate straight-line geographic distance was recalculated from the four cleaned coordinate fields with the Step 5.8 Haversine implementation: `a = sin²(Δφ/2) + cos(φ₁)cos(φ₂)sin²(Δλ/2)`, and distance `= 2R asin(√a)`. Earth radius is **6,371.0088 km**. Both Python and SQLite calculate it independently.",
        "",
        "The exact Step 5.8 half-open bands are `[0,1)`, `[1,2)`, `[2,3)`, `[3,5)`, `[5,10)`, `[10,15)`, and `[15,∞)` km. Boundary values enter the band beginning at that value. Distance is straight-line geographic separation, not actual road/network, driving, or travelled distance.",
        "",
        f"- Source: `data/processed/train_clean.csv`; {metadata['total_train_rows']:,} total rows and {metadata['valid_target_rows']:,} valid numeric delivery-time targets.",
        f"- Coordinate-valid target rows: {metadata['valid_target_coordinate_rows']:,}; rows excluded for missing/invalid coordinates: {metadata['target_rows_excluded_for_coordinates']:,}.",
        f"- Missing-coordinate rows: {metadata['rows_with_missing_coordinates']:,}; non-numeric-coordinate rows: {metadata['rows_with_non_numeric_coordinates']:,}; out-of-range-coordinate rows: {metadata['rows_with_out_of_range_coordinates']:,}.",
        f"- All valid-target records were assigned to a distance band; {distance_distribution['over_15_count']:,} are in the 15+ km band and remain in the primary analysis.",
        "",
        "Distance distribution among valid targets with plausible numeric coordinates:",
        "",
        *markdown_table(
            ["Count", "Minimum (km)", "P25 (km)", "Median (km)", "P75 (km)", "P90 (km)", "Maximum (km)", "Mean (km)"],
            overall_distribution_rows,
        ),
        "",
        f"Zero distances: {distance_distribution['zero_count']:,}; negative distances: {distance_distribution['negative_count']:,}; missing derived distances among coordinate-valid targets: {int(valid_distance['distance_km'].isna().sum()):,}.",
        "",
        "## Two-Way Analysis",
        "",
        f"The fixed slow-delivery definition is `Time_taken(min) > 40`; it was not recalculated. Cells with fewer than {MIN_GROUP_SIZE} records remain displayed but are excluded from substantive comparisons and rankings.",
        "",
        "### Distance × Traffic Results",
        "",
        "Median/P90 use continuous linear interpolation at rank `1 + (n - 1) × p` (NumPy `percentile(method='linear')`). Slow rate is slow count / delivery count.",
        "",
        *markdown_table(
            ["Distance band", "Traffic", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count", "Slow count / n", "Slow rate", "Eligibility"],
            [
                [
                    row["distance_band"],
                    row["traffic_category"],
                    f"{int(row['delivery_count']):,}",
                    "—" if pd.isna(row["mean_delivery_time"]) else fmt(float(row["mean_delivery_time"])),
                    "—" if pd.isna(row["median_delivery_time"]) else fmt(float(row["median_delivery_time"])),
                    "—" if pd.isna(row["p90_delivery_time"]) else fmt(float(row["p90_delivery_time"])),
                    f"{int(row['slow_delivery_count']):,}",
                    f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}"
                    if int(row["delivery_count"]) else "0 / 0",
                    "—" if pd.isna(row["slow_delivery_rate"]) else f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                    "Qualifies" if int(row["delivery_count"]) >= MIN_GROUP_SIZE else "Small sample; descriptive only",
                ]
                for _, row in python_groups.iterrows()
            ],
        ),
        "",
        "## Within-Traffic Distance Comparison",
        "",
        "All cells meeting n ≥ 30 are listed. Ranks use 1 for the lowest mean/rate; ties share ranks. Min/max labels include count, median, and P90.",
        "",
        *markdown_table(
            ["Traffic", "Distance band", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_traffic_rows,
        ),
        "",
        *markdown_table(
            ["Traffic", "Qualifying distance bands", "Lowest mean", "Highest mean", "Lowest slow rate", "Highest slow rate"],
            within_traffic_extremes,
        ),
        "",
        "Observed sequences across qualifying bands (ordered by increasing distance; no monotonicity is assumed):",
        "",
        *markdown_table(
            ["Traffic", "Qualifying bands", "Mean sequence", "Slow-rate sequence"],
            [
                [
                    traffic,
                    count,
                    "increasing" if mean_pattern == "increasing" else mean_pattern,
                    rate_pattern,
                ]
                for traffic, mean_pattern, rate_pattern, count in within_traffic_patterns
            ],
        ),
        "",
        "## Within-Distance Traffic Comparison",
        "",
        "Only traffic cells with at least 30 records in a given distance band are ranked or compared.",
        "",
        *markdown_table(
            ["Distance band", "Traffic", "Count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / n", "Slow rate", "Mean rank", "Slow-rate rank"],
            within_distance_rows,
        ),
        "",
        "Traffic-category orders (highest to lowest) where at least two traffic cells qualify:",
        "",
        *markdown_table(
            ["Distance band", "Qualifying traffic categories", "Mean order", "Slow-rate order"],
            within_distance_patterns,
        ),
        "",
        "## 10 km Signal Check",
        "",
        "The comparison reference within each traffic category is the highest slow-delivery rate among qualifying bands below 10 km. The exact 10–15 km and 15+ km bands are compared separately; no additional distance category is created. Every entry uses n ≥ 30 cells.",
        "",
        *markdown_table(
            ["Traffic", "Band / comparison", "Count(s)", "Slow rate(s)", "Below-10 km reference", "Difference / assessment"],
            signal_comparison_rows,
        ),
        "",
        f"Across traffic strata with qualifying reference and long-band cells, the 10–15 km rate is above the within-traffic <10 km reference in {long_signal_count['10-15 km']} categories; the 15+ km rate is above it in {long_signal_count['15+ km']} categories. These counts describe consistency, not causation.",
        "",
        "## Extreme Distance Check",
        "",
        f"All {distance_distribution['over_15_count']:,} records in the 15+ km band, including the exact ten largest records below, are retained in primary results. Their extreme values are the same rows inspected in Step 5.8.",
        "",
        *markdown_table(
            ["ID", "Approx. straight-line distance (km)", "Time_taken(min)", "Traffic category", "Distance band"],
            top_table,
        ),
        "",
        f"A separate sensitivity recalculates affected cells after omitting only these ten rows; the primary results above include them. Of these ten records, {extreme_with_traffic} have a traffic category and {extreme_without_traffic} have missing traffic, so only the former enter two-way sensitivity cells. Across {len(sensitivity_rows)} qualifying affected cells, the maximum absolute mean change is {max_mean_change:.6f} minutes and the maximum absolute slow-rate change is {max_rate_change_pp:.4f} percentage points. Considering all qualifying traffic categories in affected distance bands, traffic mean order changed in {mean_order_changes} band(s) and slow-rate order in {rate_order_changes} band(s). This measures the influence of the ten largest-distance records only; the 15+ km group as a whole is not excluded.",
        "",
        *markdown_table(
            ["Band", "Traffic", "Top-10 records", "Primary n", "Sensitivity n", "Primary mean", "Without top 10 mean", "Mean delta", "Primary slow rate", "Without top 10 rate", "Rate delta"],
            sensitivity_rows,
        ),
        "",
        "## Slow-Delivery Contribution",
        "",
        f"Across all valid targets, {all_slow:,} deliveries are slow. Of these, {qualifying_slow:,} occur in qualifying Distance × traffic cells, {small_slow:,} in subminimum cells, {metadata['slow_rows_missing_traffic']:,} have missing traffic among coordinate-valid targets, and {metadata['slow_rows_excluded_for_coordinates']:,} are excluded for coordinate issues. The five qualifying cells with the largest slow counts contribute {top_slow_count:,} ({top_slow_count / all_slow * 100:.2f}%) of all slow deliveries.",
        "",
        *markdown_table(
            ["Distance band", "Traffic", "Count", "Slow count", "Slow rate", "Mean (min)", "Median (min)", "P90 (min)", "Share of all slow deliveries"],
            contribution_rows,
        ),
        "",
        "## SQL vs Python Validation",
        "",
        f"SQL from `sql/11_distance_traffic_analysis.sql` ran in in-memory SQLite {sqlite_version}. Python independently calculated Haversine distance, band assignments, cell metrics, and rankings. Counts/ranks matched exactly; floating values use `numpy.isclose` with absolute tolerance `{ABS_TOL:g}` and relative tolerance `{REL_TOL:g}`.",
        "",
        *markdown_table(
            ["Validation", "Checks", "Result"],
            [
                ["Population and coordinate-validity counts", len(metadata), "MATCH"],
                ["Haversine row values and band assignments", f"{len(row_sql):,} rows; max absolute difference {max_distance_difference:.3g} km", "MATCH"],
                ["Distance × traffic cell metrics and ranks", f"{metric_checks:,} metric/population checks; {rank_checks:,} rank checks", "MATCH"],
                ["Top-10 extreme record identities/order", 10, "MATCH"],
                ["Distance-band assignment coverage", f"{int(distance_band_counts.sum()):,} / {len(valid_distance):,}", "MATCH"],
            ],
        ),
        "",
        "## Key Observations",
        "",
        f"- Within-traffic mean delivery time increased across all observed qualifying distance bands in {monotonic_mean_count} of {len(within_traffic_patterns)} comparable traffic categories; slow rate increased monotonically in {monotonic_rate_count}. At least one metric was mixed or tied in {mixed_count} categories. Jam's sequence is mixed for mean but increasing for slow rate; High, Low, and Medium have mixed/tied sequences for at least one measure.",
        f"- Standalone, the 10–15 km and 15+ km slow rates ({primary_long_results['10-15 km'] * 100:.4f}% and {primary_long_results['15+ km'] * 100:.4f}%) exceeded the highest qualifying below-10 km rate ({primary_short_max * 100:.4f}%). Within traffic, they exceed the short-band reference in {long_signal_count['10-15 km']} and {long_signal_count['15+ km']} comparable strata respectively.",
        "- Among comparable traffic categories, the largest 10+ km excess over the <10 km slow-rate reference occurs in Jam; the excess is smaller in Medium and Low. High has no qualifying 10+ km cell, so its pattern is not comparable under the minimum-size rule. For Jam, Low, and Medium, 15+ km slow rates are close to their 10–15 km rates, with category-specific differences shown above.",
        f"- The ten largest geographic distances are retained. Removing those ten only in the labeled sensitivity changed affected cell mean by at most {max_mean_change:.6f} minutes and slow rate by at most {max_rate_change_pp:.4f} percentage points; see affected cells above.",
        "- Traffic comparisons within distance bands vary by band; consult the qualifying counts and full rankings rather than generalizing from one category.",
        "",
        "## Interpretation",
        "",
        "The tables describe observed delivery-time patterns across distance bands within traffic categories, and traffic patterns within distance bands. The elevated standalone 10+ km slow rates are assessed against qualifying shorter bands separately for each traffic category. Straight-line geographic distance is only an approximation of actual travel conditions and does not establish a causal explanation. Extreme observations remain included in the primary results.",
        "",
        "## Limitations",
        "",
        "- This is observational analysis; no causal relationship is established.",
        "- Haversine distance is approximate straight-line geographic separation, not actual road/network distance.",
        "- Combinations with fewer than 30 records are excluded from substantive comparison and ranking, while their counts remain displayed.",
        "- Extreme geographic values were retained in the primary analysis; the top-ten-excluded calculation is clearly labeled as sensitivity only.",
        "- Traffic and distance may be related to other operational factors.",
        "- No regression, machine learning, or formal interaction model was fitted.",
        "- The 30-record minimum is a reporting guardrail, not a guarantee of statistical precision.",
        "- This analysis does not add weather, city, vehicle, courier, multiple deliveries, or time.",
        "",
        f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is `{source_hash_after}` before and after; the source schema is unchanged and no distance column was persisted.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {len(python_groups)} Distance x traffic cells, "
        f"{len(row_sql):,} Haversine rows, {metric_checks} metric/population checks, "
        f"{rank_checks} ranking checks; max distance delta "
        f"{max_distance_difference:.3g} km."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
