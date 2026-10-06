"""Validate approximate geographic-distance metrics against SQLite."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "08_distance_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "distance_analysis.md"

TARGET_COLUMN = "Time_taken(min)"
COORDINATE_COLUMNS = (
    "Restaurant_latitude",
    "Restaurant_longitude",
    "Delivery_location_latitude",
    "Delivery_location_longitude",
)
LATITUDE_COLUMNS = ("Restaurant_latitude", "Delivery_location_latitude")
LONGITUDE_COLUMNS = ("Restaurant_longitude", "Delivery_location_longitude")
CONTEXT_COLUMNS = (
    "ID",
    "City",
    "Road_traffic_density",
    "Weatherconditions",
    "Type_of_vehicle",
)
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
EARTH_RADIUS_KM = 6371.0088
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
DISTANCE_BANDS = (
    "0-1 km",
    "1-2 km",
    "2-3 km",
    "3-5 km",
    "5-10 km",
    "10-15 km",
    "15+ km",
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
    """Compute a streaming SHA-256 digest for source-integrity validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floating-point values with the tolerance from previous steps."""
    return bool(
        np.isclose(
            left,
            right,
            atol=ABSOLUTE_TOLERANCE,
            rtol=RELATIVE_TOLERANCE,
        )
    )


def format_number(value: float, decimals: int = 8) -> str:
    """Format a numeric result compactly for the Markdown report."""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format Markdown rows and escape table delimiters."""
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
    connection: sqlite3.Connection,
    sql_text: str,
) -> list[pd.DataFrame]:
    """Execute the SQL script statement-by-statement and collect result sets."""
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
        raise ValueError("The SQL script ends with an incomplete statement.")
    return results


def numeric_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    """Coerce coordinate fields for validation without changing source values."""
    coordinates = pd.DataFrame(index=frame.index)
    for column in COORDINATE_COLUMNS:
        coordinates[column] = pd.to_numeric(frame[column], errors="coerce")
    return coordinates


def haversine_distance_km(coordinates: pd.DataFrame) -> pd.Series:
    """Calculate great-circle distance with the Haversine formula."""
    restaurant_latitude = np.radians(
        coordinates["Restaurant_latitude"].to_numpy(dtype="float64")
    )
    restaurant_longitude = np.radians(
        coordinates["Restaurant_longitude"].to_numpy(dtype="float64")
    )
    delivery_latitude = np.radians(
        coordinates["Delivery_location_latitude"].to_numpy(dtype="float64")
    )
    delivery_longitude = np.radians(
        coordinates["Delivery_location_longitude"].to_numpy(dtype="float64")
    )

    latitude_delta = delivery_latitude - restaurant_latitude
    longitude_delta = delivery_longitude - restaurant_longitude
    haversine_a = (
        np.sin(latitude_delta / 2.0) ** 2
        + np.cos(restaurant_latitude)
        * np.cos(delivery_latitude)
        * np.sin(longitude_delta / 2.0) ** 2
    )
    haversine_a = np.clip(haversine_a, 0.0, 1.0)
    distance = (
        EARTH_RADIUS_KM
        * 2.0
        * np.arcsin(np.sqrt(haversine_a))
    )
    return pd.Series(distance, index=coordinates.index, dtype="float64")


def coordinate_quality(frame: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    """Measure per-coordinate completeness, numeric validity, and plausibility."""
    numeric = numeric_coordinates(frame)
    missing_masks: dict[str, pd.Series] = {}
    nonnumeric_masks: dict[str, pd.Series] = {}
    out_of_range_masks: dict[str, pd.Series] = {}
    field_rows: list[list[object]] = []
    for column in COORDINATE_COLUMNS:
        raw = frame[column]
        converted = numeric[column]
        missing_masks[column] = raw.isna()
        nonnumeric_masks[column] = raw.notna() & converted.isna()
        bounds = (-90.0, 90.0) if column in LATITUDE_COLUMNS else (-180.0, 180.0)
        out_of_range_masks[column] = (
            converted.notna()
            & ~converted.between(bounds[0], bounds[1], inclusive="both")
        )
        field_rows.append(
            [
                column,
                f"{int(
                    (
                        converted.notna()
                        & converted.between(bounds[0], bounds[1], inclusive="both")
                    ).sum()
                ):,}",
                f"{int(missing_masks[column].sum()):,}",
                "—",
                f"{int(nonnumeric_masks[column].sum()):,}",
                f"{int(out_of_range_masks[column].sum()):,}",
                format_number(float(converted.min())),
                format_number(float(converted.max())),
            ]
        )

    any_missing = pd.DataFrame(missing_masks).any(axis=1)
    any_nonnumeric = pd.DataFrame(nonnumeric_masks).any(axis=1)
    any_out_of_range = pd.DataFrame(out_of_range_masks).any(axis=1)
    all_numeric = numeric.notna().all(axis=1)
    valid = all_numeric.copy()
    for column in LATITUDE_COLUMNS:
        valid &= numeric[column].between(-90.0, 90.0, inclusive="both")
    for column in LONGITUDE_COLUMNS:
        valid &= numeric[column].between(-180.0, 180.0, inclusive="both")

    summary: dict[str, object] = {
        "total_train_rows": len(frame),
        "valid_coordinate_count": int(valid.sum()),
        "rows_with_missing_coordinates": int(any_missing.sum()),
        "rows_with_non_numeric_coordinates": int(any_nonnumeric.sum()),
        "rows_with_out_of_range_coordinates": int(any_out_of_range.sum()),
        "rows_with_invalid_coordinates": int((any_nonnumeric | any_out_of_range).sum()),
        "rows_excluded_for_invalid_or_missing_coordinates": int((~valid).sum()),
        "coordinate_valid_mask": valid,
        "numeric_coordinates": numeric,
        "field_rows": field_rows,
        "suspicious_0_01_counts": {
            column: int(frame[column].eq(0.01).sum())
            for column in COORDINATE_COLUMNS
        },
        "combined_latitude_min": float(
            pd.concat([numeric[column] for column in LATITUDE_COLUMNS]).min()
        ),
        "combined_latitude_max": float(
            pd.concat([numeric[column] for column in LATITUDE_COLUMNS]).max()
        ),
        "combined_longitude_min": float(
            pd.concat([numeric[column] for column in LONGITUDE_COLUMNS]).min()
        ),
        "combined_longitude_max": float(
            pd.concat([numeric[column] for column in LONGITUDE_COLUMNS]).max()
        ),
    }
    return summary, numeric


def distance_band(distance: pd.Series) -> pd.Series:
    """Assign every non-negative distance to one exact half-open band."""
    bins = [0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, np.inf]
    return pd.cut(
        distance,
        bins=bins,
        labels=DISTANCE_BANDS,
        right=False,
        include_lowest=True,
        ordered=False,
    ).astype("object").where(distance.notna(), pd.NA)


def group_distance_metrics(
    valid_records: pd.DataFrame,
    bands: pd.Series,
) -> pd.DataFrame:
    """Calculate performance metrics and SQL-compatible ranks by distance band."""
    included = valid_records.loc[bands.notna(), ["delivery_time"]].copy()
    included["category"] = bands.loc[bands.notna()].astype(str)
    rows = []
    for band in DISTANCE_BANDS:
        group = included.loc[included["category"] == band]
        count = len(group)
        if count == 0:
            rows.append(
                {
                    "category": band,
                    "sort_order": DISTANCE_BANDS.index(band) + 1,
                    "delivery_count": 0,
                    "mean_delivery_time": np.nan,
                    "median_delivery_time": np.nan,
                    "p90_delivery_time": np.nan,
                    "slow_delivery_count": 0,
                    "slow_delivery_rate": np.nan,
                    "sample_size_status": "small_sample",
                }
            )
            continue
        times = group["delivery_time"].to_numpy(dtype="float64")
        slow_count = int((group["delivery_time"] > FIXED_SLOW_THRESHOLD).sum())
        rows.append(
            {
                "category": band,
                "sort_order": DISTANCE_BANDS.index(band) + 1,
                "delivery_count": count,
                "mean_delivery_time": float(np.mean(times)),
                "median_delivery_time": float(np.percentile(times, 50, method="linear")),
                "p90_delivery_time": float(np.percentile(times, 90, method="linear")),
                "slow_delivery_count": slow_count,
                "slow_delivery_rate": slow_count / count,
                "sample_size_status": (
                    "qualifies" if count >= MIN_GROUP_SIZE else "small_sample"
                ),
            }
        )
    result = pd.DataFrame(rows)
    qualifying = result.loc[result["delivery_count"] >= MIN_GROUP_SIZE].copy()
    for rank_name, metric, ascending in RANK_SPECS:
        qualifying[rank_name] = qualifying[metric].rank(
            method="min",
            ascending=ascending,
        ).astype(int)
    return result.merge(
        qualifying[["category", *RANK_METRICS]],
        on="category",
        how="left",
        validate="one_to_one",
    )


def calculate_correlations(
    distance: pd.Series,
    delivery_time: pd.Series,
) -> tuple[float, float, float, float]:
    """Calculate Pearson/Spearman twice with separate implementations."""
    x = distance.to_numpy(dtype="float64")
    y = delivery_time.to_numpy(dtype="float64")
    pearson_numpy = float(np.corrcoef(x, y)[0, 1])
    centered_x = x - np.mean(x)
    centered_y = y - np.mean(y)
    pearson_manual = float(
        np.sum(centered_x * centered_y)
        / np.sqrt(np.sum(centered_x**2) * np.sum(centered_y**2))
    )
    distance_ranks = pd.Series(x).rank(method="average").to_numpy(dtype="float64")
    time_ranks = pd.Series(y).rank(method="average").to_numpy(dtype="float64")
    spearman_rank_pearson = float(np.corrcoef(distance_ranks, time_ranks)[0, 1])
    centered_distance_ranks = distance_ranks - np.mean(distance_ranks)
    centered_time_ranks = time_ranks - np.mean(time_ranks)
    spearman_manual = float(
        np.sum(centered_distance_ranks * centered_time_ranks)
        / np.sqrt(
            np.sum(centered_distance_ranks**2)
            * np.sum(centered_time_ranks**2)
        )
    )
    if not close_enough(pearson_numpy, pearson_manual):
        raise AssertionError("Independent Pearson correlation calculations differ.")
    if not close_enough(spearman_rank_pearson, spearman_manual):
        raise AssertionError("Independent Spearman correlation calculations differ.")
    return pearson_numpy, spearman_rank_pearson, pearson_manual, spearman_manual


def run_sql(
    frame: pd.DataFrame,
    sql_text: str,
    python_distance: pd.Series,
    coordinate_valid: pd.Series,
) -> tuple[list[pd.DataFrame], str]:
    """Execute the SQL artifact against source and temporary Python-reference tables."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        reference = pd.DataFrame(
            {
                "source_row_id": np.arange(1, len(frame) + 1, dtype="int64"),
                "python_distance_km": python_distance.where(coordinate_valid),
            }
        )
        reference.to_sql(
            "python_distance_reference",
            connection,
            index=False,
            if_exists="replace",
        )
        results = parse_sql_script(connection, sql_text)
        if len(results) != 6:
            raise AssertionError(
                f"Expected six SQL result sets, received {len(results)}."
            )
        return results, sqlite3.sqlite_version
    finally:
        connection.close()


def validate_coordinate_summary(
    sql: pd.Series,
    python: dict[str, object],
) -> int:
    """Compare coordinate-quality row counts and each field's missing/range stats."""
    integer_fields = (
        "total_train_rows",
        "valid_coordinate_count",
        "rows_with_missing_coordinates",
        "rows_with_non_numeric_coordinates",
        "rows_with_out_of_range_coordinates",
        "rows_with_invalid_coordinates",
        "rows_excluded_for_invalid_or_missing_coordinates",
        "missing_restaurant_latitude",
        "missing_restaurant_longitude",
        "missing_delivery_latitude",
        "missing_delivery_longitude",
        "non_numeric_restaurant_latitude",
        "non_numeric_restaurant_longitude",
        "non_numeric_delivery_latitude",
        "non_numeric_delivery_longitude",
        "restaurant_latitude_0_01_count",
        "restaurant_longitude_0_01_count",
        "delivery_latitude_0_01_count",
        "delivery_longitude_0_01_count",
        "invalid_restaurant_latitude_range",
        "invalid_restaurant_longitude_range",
        "invalid_delivery_latitude_range",
        "invalid_delivery_longitude_range",
    )
    sql_to_python = {
        "missing_restaurant_latitude": ("Restaurant_latitude", "missing"),
        "missing_restaurant_longitude": ("Restaurant_longitude", "missing"),
        "missing_delivery_latitude": ("Delivery_location_latitude", "missing"),
        "missing_delivery_longitude": ("Delivery_location_longitude", "missing"),
        "non_numeric_restaurant_latitude": ("Restaurant_latitude", "non_numeric"),
        "non_numeric_restaurant_longitude": ("Restaurant_longitude", "non_numeric"),
        "non_numeric_delivery_latitude": ("Delivery_location_latitude", "non_numeric"),
        "non_numeric_delivery_longitude": ("Delivery_location_longitude", "non_numeric"),
        "restaurant_latitude_0_01_count": ("Restaurant_latitude", "0.01"),
        "restaurant_longitude_0_01_count": ("Restaurant_longitude", "0.01"),
        "delivery_latitude_0_01_count": ("Delivery_location_latitude", "0.01"),
        "delivery_longitude_0_01_count": ("Delivery_location_longitude", "0.01"),
    }
    field_range_keys = {
        "invalid_restaurant_latitude_range": "Restaurant_latitude",
        "invalid_restaurant_longitude_range": "Restaurant_longitude",
        "invalid_delivery_latitude_range": "Delivery_location_latitude",
        "invalid_delivery_longitude_range": "Delivery_location_longitude",
    }
    checks = 0
    for field in integer_fields:
        if field in sql_to_python:
            column, kind = sql_to_python[field]
            if kind == "0.01":
                expected = python["suspicious_0_01_counts"][column]
            else:
                expected = int(python["field_quality"][column][kind])
        elif field in field_range_keys:
            expected = int(python["field_quality"][field_range_keys[field]]["out_of_range"])
        else:
            expected = int(python[field])
        if int(sql[field]) != expected:
            raise AssertionError(
                f"SQL/Python coordinate quality differs for {field}: "
                f"{sql[field]} vs {expected}."
            )
        checks += 1

    extrema = {
        "min_restaurant_latitude": "Restaurant_latitude",
        "max_restaurant_latitude": "Restaurant_latitude",
        "min_delivery_latitude": "Delivery_location_latitude",
        "max_delivery_latitude": "Delivery_location_latitude",
        "min_restaurant_longitude": "Restaurant_longitude",
        "max_restaurant_longitude": "Restaurant_longitude",
        "min_delivery_longitude": "Delivery_location_longitude",
        "max_delivery_longitude": "Delivery_location_longitude",
    }
    for sql_field, column in extrema.items():
        expected = (
            python["numeric_coordinates"][column].min()
            if sql_field.startswith("min_")
            else python["numeric_coordinates"][column].max()
        )
        if not close_enough(float(sql[sql_field]), float(expected)):
            raise AssertionError(f"SQL/Python coordinate extrema differ for {sql_field}.")
        checks += 1
    return checks


def validate_distance_summary(sql: pd.Series, python: dict[str, object]) -> int:
    """Compare distribution and distance-quality summary metrics."""
    integer_fields = (
        "distance_count",
        "zero_distance_count",
        "negative_distance_count",
        "distance_over_15_km_count",
        "distance_over_15_with_delivery_0_01_count",
        "missing_derived_distance_count",
    )
    float_fields = (
        "minimum_distance_km",
        "p25_distance_km",
        "median_distance_km",
        "p75_distance_km",
        "p90_distance_km",
        "maximum_distance_km",
        "mean_distance_km",
    )
    checks = 0
    for field in integer_fields:
        if int(sql[field]) != int(python[field]):
            raise AssertionError(f"SQL/Python distance summary differs for {field}.")
        checks += 1
    for field in float_fields:
        if not close_enough(float(sql[field]), float(python[field])):
            raise AssertionError(f"SQL/Python distance summary differs for {field}.")
        checks += 1
    return checks


def validate_groups(sql: pd.DataFrame, python: pd.DataFrame) -> int:
    """Compare band counts, metrics, eligibility, and all six rank columns."""
    sql = sql.set_index("category")
    python = python.set_index("category")
    if set(sql.index) != set(python.index):
        raise AssertionError("SQL and Python distance bands differ.")
    checks = 0
    for band in DISTANCE_BANDS:
        sql_row = sql.loc[band]
        python_row = python.loc[band]
        for field in ("delivery_count", "slow_delivery_count", "sort_order"):
            if int(sql_row[field]) != int(python_row[field]):
                raise AssertionError(f"Distance-band {band} {field} differs.")
            checks += 1
        if str(sql_row["sample_size_status"]) != str(
            python_row["sample_size_status"]
        ):
            raise AssertionError(f"Distance-band {band} sample-size status differs.")
        for field in (
            "mean_delivery_time",
            "median_delivery_time",
            "p90_delivery_time",
            "slow_delivery_rate",
        ):
            left = sql_row[field]
            right = python_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or not close_enough(
                float(left), float(right)
            ):
                raise AssertionError(f"Distance-band {band} {field} differs.")
            checks += 1
        for field in RANK_METRICS:
            left = sql_row[field]
            right = python_row[field]
            if pd.isna(left) and pd.isna(right):
                continue
            if pd.isna(left) or pd.isna(right) or int(left) != int(right):
                raise AssertionError(f"Distance-band {band} {field} differs.")
            checks += 1
    return checks


def metric_table(groups: pd.DataFrame) -> list[list[object]]:
    """Create group results with explicit slow count denominators."""
    output = []
    for _, row in groups.iterrows():
        count = int(row["delivery_count"])
        if count == 0:
            output.append([row["category"], "0", "—", "—", "—", "0 / 0", "—", "No records"])
            continue
        slow_count = int(row["slow_delivery_count"])
        output.append(
            [
                row["category"],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                f"{slow_count:,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                "Meets minimum" if count >= MIN_GROUP_SIZE else "Small sample; descriptive only",
            ]
        )
    return output


def ranking_table(
    groups: pd.DataFrame,
    rank_column: str,
    metric: str,
) -> list[list[object]]:
    """Render eligible distance-band rankings with counts and ties."""
    eligible = groups.loc[
        (groups["delivery_count"] >= MIN_GROUP_SIZE)
        & groups[rank_column].notna()
    ].sort_values([rank_column, "sort_order"], kind="stable")
    rows = []
    for _, row in eligible.iterrows():
        value = float(row[metric])
        text = (
            f"{value * 100:.4f}%"
            if metric == "slow_delivery_rate"
            else format_number(value)
        )
        rows.append(
            [
                int(row[rank_column]),
                row["category"],
                f"{int(row['delivery_count']):,}",
                text,
            ]
        )
    return rows


def append_rankings(lines: list[str], groups: pd.DataFrame) -> None:
    """Append the six requested best/worst metric rankings."""
    specifications = (
        ("Fastest by mean delivery time", "fastest_mean_rank", "mean_delivery_time", "Mean (min)"),
        ("Slowest by mean delivery time", "slowest_mean_rank", "mean_delivery_time", "Mean (min)"),
        ("Fastest by median delivery time", "fastest_median_rank", "median_delivery_time", "Median (min)"),
        ("Slowest by median delivery time", "slowest_median_rank", "median_delivery_time", "Median (min)"),
        ("Lowest slow-delivery rate", "lowest_slow_rate_rank", "slow_delivery_rate", "Slow rate"),
        ("Highest slow-delivery rate", "highest_slow_rate_rank", "slow_delivery_rate", "Slow rate"),
    )
    lines.extend(["### Rankings", ""])
    for title, rank, metric, label in specifications:
        lines.extend([f"#### {title}", ""])
        lines.extend(
            markdown_table(
                ["Rank", "Distance band", "Delivery count", label],
                ranking_table(groups, rank, metric),
            )
        )
        lines.append("")


def main() -> None:
    """Calculate distances, validate SQL/Python metrics, and write the report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [
        TARGET_COLUMN,
        *COORDINATE_COLUMNS,
        *CONTEXT_COLUMNS,
    ]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required distance-analysis columns are missing: {missing_columns}")

    quality, coordinates = coordinate_quality(frame)
    raw_valid = quality["coordinate_valid_mask"]
    distance = pd.Series(np.nan, index=frame.index, dtype="float64")
    if raw_valid.any():
        distance.loc[raw_valid] = haversine_distance_km(
            coordinates.loc[raw_valid]
        )
    if (distance.dropna() < 0).any():
        raise AssertionError("Haversine calculation produced a negative distance.")
    if distance.isna().sum() != len(frame) - int(raw_valid.sum()):
        raise AssertionError("Derived-distance missing count does not match coordinate exclusions.")

    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_target = target.notna()
    valid_distance_mask = valid_target & raw_valid & distance.notna()
    valid_records = pd.DataFrame(
        {
            "delivery_time": target.loc[valid_distance_mask].astype("float64"),
            "distance_km": distance.loc[valid_distance_mask],
        },
        index=frame.index[valid_distance_mask],
    )
    if valid_records.empty:
        raise ValueError("No records have both a valid target and valid coordinates.")
    bands = distance_band(valid_records["distance_km"])
    python_groups = group_distance_metrics(valid_records, bands)

    distance_values = valid_records["distance_km"].to_numpy(dtype="float64")
    distance_summary: dict[str, object] = {
        "distance_count": int(distance_values.size),
        "minimum_distance_km": float(np.min(distance_values)),
        "p25_distance_km": float(np.percentile(distance_values, 25, method="linear")),
        "median_distance_km": float(np.percentile(distance_values, 50, method="linear")),
        "p75_distance_km": float(np.percentile(distance_values, 75, method="linear")),
        "p90_distance_km": float(np.percentile(distance_values, 90, method="linear")),
        "maximum_distance_km": float(np.max(distance_values)),
        "mean_distance_km": float(np.mean(distance_values)),
        "zero_distance_count": int((distance_values == 0).sum()),
        "negative_distance_count": int((distance_values < 0).sum()),
        "distance_over_15_km_count": int((distance_values > 15).sum()),
        "distance_over_15_with_delivery_0_01_count": int(
            (
                valid_records["distance_km"].gt(15)
                & (
                    frame.loc[valid_records.index, "Delivery_location_latitude"].eq(0.01)
                    | frame.loc[valid_records.index, "Delivery_location_longitude"].eq(0.01)
                )
            ).sum()
        ),
        "missing_derived_distance_count": int(
            valid_target.sum() - valid_distance_mask.sum()
        ),
    }

    python_pearson, python_spearman, check_pearson, check_spearman = (
        calculate_correlations(
            valid_records["distance_km"],
            valid_records["delivery_time"],
        )
    )

    quality["field_quality"] = {}
    numeric = quality["numeric_coordinates"]
    for column in COORDINATE_COLUMNS:
        raw = frame[column]
        converted = numeric[column]
        bounds = (-90.0, 90.0) if column in LATITUDE_COLUMNS else (-180.0, 180.0)
        quality["field_quality"][column] = {
            "missing": int(raw.isna().sum()),
            "non_numeric": int((raw.notna() & converted.isna()).sum()),
            "out_of_range": int(
                (
                    converted.notna()
                    & ~converted.between(bounds[0], bounds[1], inclusive="both")
                ).sum()
            ),
        }

    sql_text = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(
        frame,
        sql_text,
        distance,
        raw_valid,
    )
    (
        sql_coordinate_quality,
        sql_distance_summary,
        sql_groups,
        sql_extremes,
        sql_correlations,
        sql_distance_check,
    ) = [result.iloc[0] if len(result) == 1 else result for result in sql_results]

    coordinate_checks = validate_coordinate_summary(
        sql_coordinate_quality,
        quality,
    )
    distance_summary_checks = validate_distance_summary(
        sql_distance_summary,
        distance_summary,
    )
    group_checks = validate_groups(sql_groups, python_groups)
    if (
        int(sql_distance_check["sql_haversine_count"]) != int(raw_valid.sum())
        or int(sql_distance_check["python_haversine_count"]) != int(raw_valid.sum())
    ):
        raise AssertionError("SQL and Python Haversine row counts differ.")
    if int(sql_distance_check["distance_calculation_mismatch_count"]) != 0:
        raise AssertionError("SQL and Python Haversine distances differ beyond tolerance.")
    if not close_enough(
        float(sql_distance_check["maximum_absolute_distance_difference_km"]),
        0.0,
    ):
        raise AssertionError("SQL/Python Haversine maximum distance difference exceeds tolerance.")

    if int(sql_correlations["correlation_pair_count"]) != len(valid_records):
        raise AssertionError("SQL and Python correlation populations differ.")
    sql_pearson = float(sql_correlations["pearson_correlation"])
    sql_spearman = float(sql_correlations["spearman_correlation"])
    correlation_checks = 0
    for label, sql_value, python_value in (
        ("Pearson", sql_pearson, python_pearson),
        ("Spearman", sql_spearman, python_spearman),
        ("Independent Pearson", python_pearson, check_pearson),
        ("Independent Spearman", python_spearman, check_spearman),
    ):
        if not close_enough(sql_value, python_value):
            raise AssertionError(f"{label} correlation validation failed.")
        correlation_checks += 1

    expected_rankings: dict[str, pd.Series] = {}
    qualifying = python_groups.loc[
        python_groups["delivery_count"] >= MIN_GROUP_SIZE
    ]
    for rank_name, metric, ascending in RANK_SPECS:
        expected_rankings[rank_name] = qualifying.set_index("category")[metric].rank(
            method="min",
            ascending=ascending,
        )

    sql_extremes = sql_extremes.copy()
    python_top = (
        valid_records.assign(
            ID=frame.loc[valid_records.index, "ID"],
            City=frame.loc[valid_records.index, "City"],
            Road_traffic_density=frame.loc[
                valid_records.index, "Road_traffic_density"
            ],
            Weatherconditions=frame.loc[
                valid_records.index, "Weatherconditions"
            ],
            Type_of_vehicle=frame.loc[valid_records.index, "Type_of_vehicle"],
            source_row_id=valid_records.index + 1,
        )
        .sort_values(
            ["distance_km", "source_row_id"],
            ascending=[False, True],
            kind="stable",
        )
        .head(10)
        .reset_index(drop=True)
    )
    if sql_extremes["source_row_id"].astype(int).tolist() != python_top[
        "source_row_id"
    ].astype(int).tolist():
        raise AssertionError("SQL/Python top-distance records differ.")
    for sql_distance_value, python_distance_value in zip(
        sql_extremes["distance_km"], python_top["distance_km"]
    ):
        if not close_enough(float(sql_distance_value), float(python_distance_value)):
            raise AssertionError("SQL/Python top-distance values differ.")

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned dataset schema changed during analysis.")

    coordinate_field_rows = quality["field_rows"]
    coordinate_summary_rows = [
        [
            "Any of four coordinates",
            f"{int(quality['valid_coordinate_count']):,}",
            f"{int(quality['rows_with_missing_coordinates']):,}",
            f"{int(quality['rows_with_invalid_coordinates']):,}",
            f"{int(quality['rows_with_non_numeric_coordinates']):,}",
            f"{int(quality['rows_with_out_of_range_coordinates']):,}",
            "—",
            "—",
        ],
        *coordinate_field_rows,
    ]
    distance_distribution_row = [
        f"{distance_summary['distance_count']:,}",
        format_number(float(distance_summary["minimum_distance_km"])),
        format_number(float(distance_summary["p25_distance_km"])),
        format_number(float(distance_summary["median_distance_km"])),
        format_number(float(distance_summary["p75_distance_km"])),
        format_number(float(distance_summary["p90_distance_km"])),
        format_number(float(distance_summary["maximum_distance_km"])),
        format_number(float(distance_summary["mean_distance_km"])),
    ]
    ranking_specs = (
        ("Fastest by mean delivery time", "fastest_mean_rank", "mean_delivery_time", "Mean (min)"),
        ("Slowest by mean delivery time", "slowest_mean_rank", "mean_delivery_time", "Mean (min)"),
        ("Fastest by median delivery time", "fastest_median_rank", "median_delivery_time", "Median (min)"),
        ("Slowest by median delivery time", "slowest_median_rank", "median_delivery_time", "Median (min)"),
        ("Lowest slow-delivery rate", "lowest_slow_rate_rank", "slow_delivery_rate", "Slow rate"),
        ("Highest slow-delivery rate", "highest_slow_rate_rank", "slow_delivery_rate", "Slow rate"),
    )

    lines = [
        "# Distance / Geographic Analysis",
        "",
        "## Objective",
        "",
        "Describe the observed association between approximate straight-line geographic "
        "distance and delivery performance. Distance is not route, road-network, driving, "
        "or travelled distance.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only.",
        f"- **Target population:** non-null numeric `{TARGET_COLUMN}` records.",
        "- **Coordinates:** restaurant and delivery latitude/longitude fields only.",
        "- **Slow threshold:** fixed at 40 minutes; slow means strictly "
        "`Time_taken(min) > 40`.",
        "- **Percentiles:** continuous linear interpolation at rank "
        "`1 + (n - 1) × p`.",
        f"- **Minimum band size:** {MIN_GROUP_SIZE} records for ranking or substantive "
        "comparison; smaller bands are descriptive.",
        f"- Total train rows: **{len(frame):,}**; valid numeric targets: "
        f"**{int(valid_target.sum()):,}**.",
        "",
        "## Coordinate Data Quality",
        "",
        "A row is coordinate-valid only if all four values are numeric and satisfy "
        "latitude [-90, 90] and longitude [-180, 180]. The counts below are row-level "
        "exclusions where noted; per-field counts are also shown.",
        "",
    ]
    lines.extend(
        markdown_table(
            [
                "Coordinate field / row set",
                "Valid coordinate rows / values",
                "Missing rows / values",
                "Invalid coordinate rows",
                "Non-numeric rows / values",
                "Out-of-range rows / values",
                "Minimum",
                "Maximum",
            ],
            coordinate_summary_rows,
        )
    )
    lines.extend(
        [
            "",
            f"- Rows excluded from distance calculation for missing or implausible "
            f"coordinates: **{int(quality['rows_excluded_for_invalid_or_missing_coordinates']):,}**.",
            f"- Valid coordinates: **{int(quality['valid_coordinate_count']):,}**; missing "
            f"coordinate rows: **{int(quality['rows_with_missing_coordinates']):,}**; "
            f"non-numeric coordinate rows: "
            f"**{int(quality['rows_with_non_numeric_coordinates']):,}**; out-of-range "
            f"coordinate rows: **{int(quality['rows_with_out_of_range_coordinates']):,}**.",
            "- Combined numeric latitude range: "
            f"{format_number(quality['combined_latitude_min'])} to "
            f"{format_number(quality['combined_latitude_max'])}; combined numeric "
            "longitude range: "
            f"{format_number(quality['combined_longitude_min'])} to "
            f"{format_number(quality['combined_longitude_max'])}.",
            "- No coordinates were repaired or silently removed. A value of 0.01 is "
            "within the broad geographic bounds but is reported as a suspicious pattern.",
            "",
            "Exact `0.01` values by coordinate field:",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Coordinate field", "Values equal to 0.01"],
            [
                [column, f"{count:,}"]
                for column, count in quality["suspicious_0_01_counts"].items()
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Haversine Distance Method",
            "",
            "For latitude/longitude in radians, let `Δφ` be the latitude difference and "
            "`Δλ` the longitude difference. The Haversine term is "
            "`a = sin²(Δφ/2) + cos(φ₁) cos(φ₂) sin²(Δλ/2)`; central angle is "
            "`c = 2 asin(√a)`; distance is `R × c`.",
            f"- Mean Earth radius assumption: **{EARTH_RADIUS_KM:,.4f} km**.",
            "- Haversine is calculated in Python for every coordinate-valid row; the SQL "
            "independently recalculates it for validation. Values are held only in memory "
            "and are not written to the cleaned CSV.",
            "- The result approximates straight-line distance over a spherical Earth; it "
            "is not actual road/network or travelled distance.",
            "",
            "## Distance Distribution",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Count", "Minimum (km)", "P25 (km)", "Median (km)", "P75 (km)", "P90 (km)", "Maximum (km)", "Mean (km)"],
            [distance_distribution_row],
        )
    )
    lines.extend(
        [
            "",
            f"- Zero-distance records: **{int(distance_summary['zero_distance_count']):,}**.",
            f"- Negative distances: **{int(distance_summary['negative_distance_count']):,}** "
            "(must be zero).",
            f"- Missing derived distances among valid targets: "
            f"**{int(distance_summary['missing_derived_distance_count']):,}**.",
            f"- Distances greater than 15 km (the predeclared top band): "
            f"**{int(distance_summary['distance_over_15_km_count']):,}**; retained and "
            "flagged for context rather than removed.",
            f"- Of those, rows with a delivery latitude or longitude equal to 0.01: "
            f"**{int(distance_summary['distance_over_15_with_delivery_0_01_count']):,}**.",
            "",
            "## Distance-Band Analysis",
            "",
            "Bands are exhaustive, mutually exclusive half-open ranges: **[0,1), [1,2), "
            "[2,3), [3,5), [5,10), [10,15), and [15,∞) km**. Exact boundary values enter "
            "the band beginning at that boundary. Each coordinate-valid target is assigned "
            "to exactly one band.",
            "",
            "### Results",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Distance band", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / denominator", "Slow rate", "Sample-size status"],
            metric_table(sql_groups.sort_values("sort_order")),
        )
    )
    lines.extend(["", "### Rankings", ""])
    for title, rank_column, metric, label in ranking_specs:
        lines.extend([f"#### {title}", ""])
        lines.extend(
            markdown_table(
                ["Rank", "Distance band", "Delivery count", label],
                ranking_table(sql_groups, rank_column, metric),
            )
        )
        lines.append("")
    lines.extend(
        [
            "### Slow-Delivery Analysis",
            "",
            "Slow rate = slow deliveries in the distance band / all valid deliveries in "
            "that band. Classification uses the unchanged global rule `Time_taken(min) > 40`.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Distance band", "Slow count (numerator)", "Delivery count (denominator)", "Rate calculation", "Slow rate", "Sample-size status"],
            [
                [
                    row["category"],
                    f"{int(row['slow_delivery_count']):,}",
                    f"{int(row['delivery_count']):,}",
                    (
                        f"{int(row['slow_delivery_count']):,} / "
                        f"{int(row['delivery_count']):,}"
                    )
                    if int(row["delivery_count"])
                    else "Not defined",
                    (
                        f"{float(row['slow_delivery_rate']) * 100:.4f}%"
                        if pd.notna(row["slow_delivery_rate"])
                        else "—"
                    ),
                    (
                        "Meets minimum; ranked"
                        if int(row["delivery_count"]) >= MIN_GROUP_SIZE
                        else (
                            "Small sample; descriptive only"
                            if int(row["delivery_count"])
                            else "No records"
                        )
                    ),
                ]
                for _, row in sql_groups.sort_values("sort_order").iterrows()
            ],
        )
    )

    lines.extend(
        [
            "",
            "## Distance vs Delivery Time",
            "",
            "Correlations use valid targets with four plausible numeric coordinates and "
            "a calculable Haversine distance. Both are descriptive association measures.",
            "",
            "### Pearson Correlation",
            "",
            f"- Pearson correlation between approximate straight-line distance and "
            f"delivery time: **{python_pearson:.8f}**.",
            "- Independently checked with NumPy's correlation matrix and a direct "
            "centered-covariance calculation.",
            "",
            "### Spearman Correlation",
            "",
            f"- Spearman rank correlation: **{python_spearman:.8f}**.",
            "- Independently checked by correlating average ranks with NumPy and a direct "
            "centered-rank covariance calculation.",
            "",
            "Neither coefficient is causal. Straight-line distance does not account for "
            "road network, route choice, traffic, road conditions, pickup delay, or "
            "geographic barriers, and is only an approximation of actual travel conditions.",
            "",
            "## Extreme Distance Check",
            "",
            "The following are the 10 largest coordinate-valid distances, shown only for "
            "context/data inspection. No records are excluded because of large distance.",
            "",
        ]
    )
    top_rows = []
    for _, row in sql_extremes.iterrows():
        top_rows.append(
            [
                row["ID"],
                format_number(float(row["distance_km"])),
                format_number(float(row["Time_taken(min)"])),
                row["City"] if pd.notna(row["City"]) else "NULL",
                row["Road_traffic_density"]
                if pd.notna(row["Road_traffic_density"])
                else "NULL",
                row["Weatherconditions"]
                if pd.notna(row["Weatherconditions"])
                else "NULL",
                row["Type_of_vehicle"]
                if pd.notna(row["Type_of_vehicle"])
                else "NULL",
            ]
        )
    lines.extend(
        markdown_table(
            [
                "ID",
                "Approx. straight-line distance (km)",
                "Time_taken(min)",
                "City",
                "Road_traffic_density",
                "Weatherconditions",
                "Type_of_vehicle",
            ],
            top_rows,
        )
    )
    lines.extend(
        [
            "",
            "The context columns are reproduced for these top-distance records only; they "
            "are not used to form combined-factor groups or draw causal conclusions.",
            "",
            "## SQL vs Python Validation",
            "",
            f"SQL was executed from `sql/08_distance_analysis.sql` against an in-memory "
            f"SQLite table (version `{sqlite_version}`). Python independently calculated "
            "the Haversine distances and distance bands; SQL recalculated the same "
            "Haversine values from source coordinates for row-level verification.",
            "",
            f"Counts and ranks were compared exactly. Floating-point metrics use "
            f"`numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and relative "
            f"tolerance `{RELATIVE_TOLERANCE:g}`.",
            "",
        ]
    )
    validation_rows = [
        ["Coordinate quality fields", coordinate_checks, "MATCH"],
        [
            "Haversine row-level values",
            f"{int(sql_distance_check['sql_haversine_count']):,} distances; "
            f"max abs diff {float(sql_distance_check['maximum_absolute_distance_difference_km']):.3g} km",
            "MATCH",
        ],
        ["Distance distribution", distance_summary_checks, "MATCH"],
        ["Distance-band metrics and rankings", group_checks, "MATCH"],
        ["Pearson/Spearman correlations", correlation_checks, "MATCH"],
        ["Top-10 records and ordering", 10, "MATCH"],
    ]
    lines.extend(
        markdown_table(
            ["Validation area", "Checks", "Result"],
            validation_rows,
        )
    )
    lines.extend(
        [
            "",
            "SQL and Python agreed on coordinate filtering, all seven distance-band "
            "counts and metrics, ranks, distance-distribution percentiles, both "
            "correlations, and top-10 row order. Negative and missing derived distances "
            "were checked explicitly; no negative values occurred.",
            "",
            "## Interpretation",
            "",
            "The band summaries and correlation coefficients describe observed "
            "associations between approximate straight-line geographic distance and "
            "delivery time. They do not show that distance causes slower delivery or "
            "explain delivery performance on its own. The distance measure is not actual "
            "road/network or travelled distance.",
            "",
            "## Limitations",
            "",
            "- Haversine distance assumes a spherical Earth and measures straight-line "
            "separation, not a route.",
            "- Straight-line distance does not account for road network, route choice, "
            "traffic, road conditions, pickup delay, or geographic barriers.",
            "- Coordinate plausibility bounds are broad. A value may fall inside those "
            "bounds yet remain suspicious; exact 0.01 values are reported but not repaired.",
            "- Distances above 15 km are retained in the predeclared upper band and "
            "highlighted; the analysis does not classify them as errors or delete them.",
            "- Correlation is descriptive and unadjusted; this step does not combine "
            "distance with other explanatory dimensions or establish causation.",
            "- Findings are limited to valid numeric targets and valid coordinate rows in "
            "the cleaned training data.",
            "",
            f"Read-only validation: `data/processed/train_clean.csv` SHA-256 is "
            f"`{source_hash_before}` before and after; the input schema is unchanged and "
            "no derived distance column was persisted.",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Validated {int(valid_records.shape[0]):,} distances, "
        f"{group_checks} distance-band metric/rank checks, "
        f"{coordinate_checks} coordinate checks, and {correlation_checks} "
        "correlation checks."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
