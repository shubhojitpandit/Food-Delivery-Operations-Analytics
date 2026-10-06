"""Validate courier-related delivery-time summaries against SQLite."""

import hashlib
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "processed" / "train_clean.csv"
SQL_PATH = ROOT / "sql" / "06_courier_analysis.sql"
REPORT_PATH = ROOT / "outputs" / "courier_analysis.md"
TARGET_COLUMN = "Time_taken(min)"
RATING_COLUMN = "Delivery_person_Ratings"
AGE_COLUMN = "Delivery_person_Age"
MULTIPLE_COLUMN = "multiple_deliveries"
RATING_FLAG_COLUMN = "rating_out_of_range"
FIXED_SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
ABSOLUTE_TOLERANCE = 1e-9
RELATIVE_TOLERANCE = 1e-12
GROUP_DIMENSIONS = (
    "rating_primary",
    "rating_all",
    "age_band",
    "multiple_deliveries",
    "rating_sensitivity",
)
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
AGE_BANDS = ("Under 20", "20-29", "30-39", "40-49", "50+")
def sha256_file(path: Path) -> str:
    """Compute a streaming SHA-256 digest for read-only source validation."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close_enough(left: float, right: float) -> bool:
    """Compare floats with the tolerance used in prior analysis steps."""
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


def category_text(value: object) -> str:
    """Format numeric categories consistently with SQLite printf('%g')."""
    return format(float(value), "g")


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Create a Markdown table while escaping separators in cell text."""
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


def build_age_bands(ages: pd.Series) -> pd.Series:
    """Assign the five fixed descriptive age bands."""
    return pd.cut(
        ages,
        bins=[-np.inf, 20, 30, 40, 50, np.inf],
        labels=AGE_BANDS,
        right=False,
        ordered=False,
    )


def calculate_metrics(
    group: pd.DataFrame,
    dimension: str,
    category: str,
) -> dict[str, object]:
    """Calculate one group's metrics using continuous linear percentiles."""
    values = group[TARGET_COLUMN].to_numpy(dtype="float64")
    slow_count = int((group[TARGET_COLUMN] > FIXED_SLOW_THRESHOLD).sum())
    count = len(group)
    return {
        "dimension_name": dimension,
        "category": category,
        "delivery_count": count,
        "mean_delivery_time": float(np.mean(values)),
        "median_delivery_time": float(np.percentile(values, 50, method="linear")),
        "p90_delivery_time": float(np.percentile(values, 90, method="linear")),
        "slow_delivery_count": slow_count,
        "slow_delivery_rate": slow_count / count,
    }


def calculate_grouped_results(
    valid: pd.DataFrame,
    dimension: str,
    values: pd.Series,
    include_empty_age_bands: bool = False,
) -> pd.DataFrame:
    """Independently calculate grouped metrics and eligible group rankings."""
    categorized = valid.loc[values.notna(), [TARGET_COLUMN]].copy()
    categorized["category"] = values.loc[values.notna()].astype(str)
    results = [
        calculate_metrics(group, dimension, category)
        for category, group in categorized.groupby("category", sort=True)
    ]
    result_frame = pd.DataFrame(results)

    if include_empty_age_bands:
        present = set(result_frame["category"]) if not result_frame.empty else set()
        for band in AGE_BANDS:
            if band not in present:
                result_frame.loc[len(result_frame)] = {
                    "dimension_name": dimension,
                    "category": band,
                    "delivery_count": 0,
                    "mean_delivery_time": np.nan,
                    "median_delivery_time": np.nan,
                    "p90_delivery_time": np.nan,
                    "slow_delivery_count": 0,
                    "slow_delivery_rate": np.nan,
                }

    if result_frame.empty:
        return result_frame

    qualifying = result_frame.loc[
        result_frame["delivery_count"] >= MIN_GROUP_SIZE
    ].copy()
    if dimension != "rating_sensitivity":
        for rank_name, metric, ascending in RANK_SPECS:
            qualifying[rank_name] = qualifying[metric].rank(
                method="min",
                ascending=ascending,
            ).astype(int)
    else:
        for rank_name in RANK_METRICS:
            qualifying[rank_name] = np.nan

    result_frame = result_frame.merge(
        qualifying[["category", *RANK_METRICS]],
        on="category",
        how="left",
        validate="one_to_one",
    )
    result_frame["sample_size_status"] = np.where(
        result_frame["delivery_count"] >= MIN_GROUP_SIZE,
        "qualifies",
        "small_sample",
    )
    return result_frame


def calculate_python_results(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int], int, int]:
    """Compute all courier groups, rating sensitivity, and age distribution."""
    targets = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    valid_mask = targets.notna()
    valid = frame.loc[valid_mask].copy()
    valid[TARGET_COLUMN] = targets.loc[valid_mask]

    ratings = pd.to_numeric(valid[RATING_COLUMN], errors="coerce")
    ages = pd.to_numeric(valid[AGE_COLUMN], errors="coerce")
    multiple = pd.to_numeric(valid[MULTIPLE_COLUMN], errors="coerce")
    flag = pd.to_numeric(valid[RATING_FLAG_COLUMN], errors="coerce")
    expected_flag = (ratings.notna() & ((ratings < 1) | (ratings > 5))).astype(int)
    if flag.isna().any() or not flag.astype(int).equals(expected_flag.astype(int)):
        raise AssertionError(
            "rating_out_of_range does not match the established [1, 5] rating rule."
        )

    missing_counts = {
        RATING_COLUMN: int(ratings.isna().sum()),
        AGE_COLUMN: int(ages.isna().sum()),
        MULTIPLE_COLUMN: int(multiple.isna().sum()),
    }
    out_of_range_count = int(expected_flag.sum())

    rating_primary_mask = (
        ratings.notna()
        & expected_flag.eq(0)
        & ratings.between(1, 5, inclusive="both")
    )
    rating_primary = ratings.where(rating_primary_mask).map(
        lambda value: category_text(value) if pd.notna(value) else pd.NA
    )
    rating_all = ratings.map(
        lambda value: category_text(value) if pd.notna(value) else pd.NA
    )
    age_bands = build_age_bands(ages)
    multiple_categories = multiple.map(
        lambda value: category_text(value) if pd.notna(value) else pd.NA
    )

    sensitivity_rows = []
    sensitivity_populations = (
        (
            "Primary: in-range ratings (1-5)",
            valid.loc[rating_primary_mask, [TARGET_COLUMN]],
        ),
        (
            "Sensitivity: all ratings (non-missing; includes out-of-range)",
            valid.loc[ratings.notna(), [TARGET_COLUMN]],
        ),
    )
    for label, population in sensitivity_populations:
        if population.empty:
            raise ValueError(f"Rating sensitivity population is empty: {label}.")
        sensitivity_rows.append(
            calculate_metrics(population, "rating_sensitivity", label)
        )
    sensitivity_results = pd.DataFrame(sensitivity_rows)
    for rank_name in RANK_METRICS:
        sensitivity_results[rank_name] = np.nan
    sensitivity_results["sample_size_status"] = np.where(
        sensitivity_results["delivery_count"] >= MIN_GROUP_SIZE,
        "qualifies",
        "small_sample",
    )

    groups = [
        calculate_grouped_results(valid, "rating_primary", rating_primary),
        calculate_grouped_results(valid, "rating_all", rating_all),
        calculate_grouped_results(
            valid,
            "age_band",
            age_bands,
            include_empty_age_bands=True,
        ),
        calculate_grouped_results(
            valid,
            "multiple_deliveries",
            multiple_categories,
        ),
        sensitivity_results,
    ]
    python_results = pd.concat(groups, ignore_index=True)

    valid_ages = ages.dropna()
    age_summary = pd.Series(
        {
            "valid_age_count": int(valid_ages.count()),
            "valid_targets_missing_age": int(len(valid) - valid_ages.count()),
            "minimum_age": float(valid_ages.min()),
            "maximum_age": float(valid_ages.max()),
            "median_age": float(valid_ages.quantile(0.5, interpolation="linear")),
            "p25_age": float(valid_ages.quantile(0.25, interpolation="linear")),
            "p75_age": float(valid_ages.quantile(0.75, interpolation="linear")),
        }
    )
    return (
        python_results,
        age_summary,
        missing_counts,
        out_of_range_count,
        int(valid_mask.sum()),
    )


def run_sql(frame: pd.DataFrame, query: str) -> tuple[pd.DataFrame, str]:
    """Execute the SQL artifact against an in-memory SQLite table."""
    connection = sqlite3.connect(":memory:")
    try:
        frame.to_sql("train_clean", connection, index=False, if_exists="replace")
        results = pd.read_sql_query(query, connection)
        return results, sqlite3.sqlite_version
    finally:
        connection.close()


def validate_group_results(
    sql_results: pd.DataFrame,
    python_results: pd.DataFrame,
) -> dict[str, dict[str, int]]:
    """Compare every metric and eligible ranking from SQL with Pandas."""
    validation: dict[str, dict[str, int]] = {}
    for dimension in GROUP_DIMENSIONS:
        sql_subset = (
            sql_results.loc[sql_results["dimension_name"] == dimension]
            .set_index("category")
        )
        python_subset = (
            python_results.loc[python_results["dimension_name"] == dimension]
            .set_index("category")
        )
        if set(sql_subset.index) != set(python_subset.index):
            raise AssertionError(f"SQL and Python categories differ for {dimension}.")

        group_count = len(sql_subset)
        metric_checks = rank_checks = 0
        for category in sorted(sql_subset.index):
            sql_row = sql_subset.loc[category]
            python_row = python_subset.loc[category]
            for metric in COUNT_METRICS:
                if int(sql_row[metric]) != int(python_row[metric]):
                    raise AssertionError(
                        f"{dimension} {category} {metric} differs."
                    )
                metric_checks += 1
            for metric in FLOAT_METRICS:
                sql_value = sql_row[metric]
                python_value = python_row[metric]
                if pd.isna(sql_value) and pd.isna(python_value):
                    continue
                if pd.isna(sql_value) or pd.isna(python_value) or not close_enough(
                    float(sql_value), float(python_value)
                ):
                    raise AssertionError(
                        f"{dimension} {category} {metric} differs: "
                        f"{sql_value} vs {python_value}."
                    )
                metric_checks += 1

            if dimension == "rating_sensitivity":
                continue
            for metric in RANK_METRICS:
                sql_rank = sql_row[metric]
                python_rank = python_row[metric]
                if pd.isna(sql_rank) and pd.isna(python_rank):
                    continue
                if (
                    pd.isna(sql_rank)
                    or pd.isna(python_rank)
                    or int(sql_rank) != int(python_rank)
                ):
                    raise AssertionError(
                        f"{dimension} {category} {metric} differs."
                    )
                rank_checks += 1
        validation[dimension] = {
            "groups": group_count,
            "metric_checks": metric_checks,
            "rank_checks": rank_checks,
        }
    return validation


def validate_age_summary(
    sql_results: pd.DataFrame,
    python_summary: pd.Series,
) -> int:
    """Check SQL/Python valid-age distribution statistics."""
    sql_row = sql_results.iloc[0]
    count_fields = ("valid_age_count", "valid_targets_missing_age")
    float_fields = (
        "minimum_age",
        "maximum_age",
        "median_age",
        "p25_age",
        "p75_age",
    )
    checks = 0
    for field in count_fields:
        if int(sql_row[field]) != int(python_summary[field]):
            raise AssertionError(f"SQL and Python age summary differ for {field}.")
        checks += 1
    for field in float_fields:
        if not close_enough(float(sql_row[field]), float(python_summary[field])):
            raise AssertionError(f"SQL and Python age summary differ for {field}.")
        checks += 1
    return checks


def rank_table(
    rows: pd.DataFrame,
    metric: str,
    rank_column: str,
) -> list[list[object]]:
    """Render a ranking with ties and category counts."""
    ranked = rows.loc[
        (rows["delivery_count"] >= MIN_GROUP_SIZE) & rows[rank_column].notna()
    ].sort_values([rank_column, "category"], kind="stable")
    output = []
    for _, row in ranked.iterrows():
        value = float(row[metric])
        display = (
            f"{value * 100:.4f}%"
            if metric == "slow_delivery_rate"
            else format_number(value)
        )
        output.append(
            [int(row[rank_column]), row["category"], f"{int(row['delivery_count']):,}", display]
        )
    return output


def grouped_result_table(rows: pd.DataFrame) -> list[list[object]]:
    """Render grouped metrics and sample-size eligibility."""
    output = []
    for _, row in rows.iterrows():
        count = int(row["delivery_count"])
        if count == 0:
            output.append([row["category"], "0", "—", "—", "—", "No valid records"])
            continue
        status = (
            "Meets minimum; ranked"
            if count >= MIN_GROUP_SIZE
            else "Small sample; descriptive only"
        )
        output.append(
            [
                row["category"],
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                status,
            ]
        )
    return output


def slow_delivery_table(rows: pd.DataFrame) -> list[list[object]]:
    """Render slow counts and explicit denominators."""
    output = []
    for _, row in rows.iterrows():
        count = int(row["delivery_count"])
        if count == 0:
            output.append([row["category"], "0", "0", "Not defined", "—"])
            continue
        slow_count = int(row["slow_delivery_count"])
        output.append(
            [
                row["category"],
                f"{slow_count:,}",
                f"{count:,}",
                f"{slow_count:,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
            ]
        )
    return output


def append_rankings(lines: list[str], rows: pd.DataFrame) -> None:
    """Append mean, median, and slow-rate rankings for qualifying groups."""
    rankings = (
        ("Fastest by mean delivery time", "mean_delivery_time", "fastest_mean_rank", "Minutes"),
        ("Slowest by mean delivery time", "mean_delivery_time", "slowest_mean_rank", "Minutes"),
        ("Fastest by median delivery time", "median_delivery_time", "fastest_median_rank", "Minutes"),
        ("Slowest by median delivery time", "median_delivery_time", "slowest_median_rank", "Minutes"),
        ("Lowest slow-delivery rate", "slow_delivery_rate", "lowest_slow_rate_rank", "Rate"),
        ("Highest slow-delivery rate", "slow_delivery_rate", "highest_slow_rate_rank", "Rate"),
    )
    lines.extend(["### Rankings", ""])
    for title, metric, rank_column, label in rankings:
        lines.extend([f"#### {title}", ""])
        lines.extend(
            markdown_table(
                ["Rank", "Category", "Delivery count", label],
                rank_table(rows, metric, rank_column),
            )
        )
        lines.append("")


def main() -> None:
    """Run SQL/Python validation and write the courier analysis report."""
    source_hash_before = sha256_file(TRAIN_PATH)
    frame = pd.read_csv(TRAIN_PATH)
    original_columns = frame.columns.tolist()
    required = [
        TARGET_COLUMN,
        RATING_COLUMN,
        RATING_FLAG_COLUMN,
        AGE_COLUMN,
        MULTIPLE_COLUMN,
    ]
    missing_columns = [column for column in required if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Required analysis columns are missing: {missing_columns}")

    (
        python_results,
        python_age_summary,
        missing_counts,
        out_of_range_count,
        valid_count,
    ) = calculate_python_results(frame)
    total_rows = len(frame)
    if valid_count == 0:
        raise ValueError("No valid numeric delivery targets were found.")

    query = SQL_PATH.read_text(encoding="utf-8")
    sql_results, sqlite_version = run_sql(frame, query)
    if sql_results.empty:
        raise AssertionError("The SQL query returned no courier analysis results.")

    population_row = sql_results.iloc[0]
    if int(population_row["total_train_rows"]) != total_rows:
        raise AssertionError("SQL and Python total train-row counts differ.")
    if int(population_row["valid_target_rows"]) != valid_count:
        raise AssertionError("SQL and Python valid-target counts differ.")

    sql_missing_fields = {
        RATING_COLUMN: "rating_all",
        AGE_COLUMN: "age_band",
        MULTIPLE_COLUMN: "multiple_deliveries",
    }
    for field, dimension in sql_missing_fields.items():
        sql_count = int(
            sql_results.loc[
                sql_results["dimension_name"] == dimension,
                "valid_targets_missing_dimension",
            ].iloc[0]
        )
        if sql_count != missing_counts[field]:
            raise AssertionError(f"SQL and Python missing counts differ for {field}.")

    sql_out_of_range = int(
        sql_results.loc[
            sql_results["dimension_name"] == "rating_primary",
            "valid_targets_excluded_out_of_range",
        ].iloc[0]
    )
    if sql_out_of_range != out_of_range_count:
        raise AssertionError("SQL and Python out-of-range rating counts differ.")

    for dimension in GROUP_DIMENSIONS:
        subset = sql_results.loc[sql_results["dimension_name"] == dimension]
        python_subset = python_results.loc[
            python_results["dimension_name"] == dimension
        ]
        expected_count = {
            "rating_primary": (
                valid_count
                - missing_counts[RATING_COLUMN]
                - out_of_range_count
            ),
            "rating_all": valid_count - missing_counts[RATING_COLUMN],
            "age_band": valid_count - missing_counts[AGE_COLUMN],
            "multiple_deliveries": valid_count - missing_counts[MULTIPLE_COLUMN],
            "rating_sensitivity": (
                valid_count
                - missing_counts[RATING_COLUMN]
                - out_of_range_count
                + valid_count
                - missing_counts[RATING_COLUMN]
            ),
        }[dimension]
        # The rating sensitivity rows intentionally summarize two overlapping populations.
        if dimension == "rating_sensitivity":
            if int(subset["delivery_count"].sum()) != expected_count:
                raise AssertionError("Rating sensitivity scenario counts do not reconcile.")
        elif int(subset["delivery_count"].sum()) != expected_count:
            raise AssertionError(f"SQL group counts do not reconcile for {dimension}.")
        if int(python_subset["delivery_count"].sum()) != expected_count:
            raise AssertionError(f"Python group counts do not reconcile for {dimension}.")

    validation = validate_group_results(sql_results, python_results)
    age_summary_checks = validate_age_summary(sql_results, python_age_summary)

    # The overlapping in-range groups must be identical in both rating scenarios.
    primary = (
        sql_results.loc[sql_results["dimension_name"] == "rating_primary"]
        .set_index("category")
    )
    all_ratings = (
        sql_results.loc[sql_results["dimension_name"] == "rating_all"]
        .set_index("category")
    )
    common_ratings = set(primary.index) & set(all_ratings.index)
    if not common_ratings:
        raise AssertionError("No in-range rating categories are available to compare.")
    shared_rating_checks = 0
    for category in common_ratings:
        for metric in (*COUNT_METRICS, *FLOAT_METRICS):
            left = primary.loc[category, metric]
            right = all_ratings.loc[category, metric]
            if metric in COUNT_METRICS:
                if int(left) != int(right):
                    raise AssertionError(
                        f"Rating sensitivity changed in-range category {category}."
                    )
            elif not close_enough(float(left), float(right)):
                raise AssertionError(
                    f"Rating sensitivity changed in-range category {category}."
                )
            shared_rating_checks += 1

    # Sensitivity summaries compare the complete rated population in each scenario.
    rating_population = (
        sql_results.loc[sql_results["dimension_name"] == "rating_sensitivity"]
        .set_index("category")
    )
    primary_population = rating_population.loc[
        "Primary: in-range ratings (1-5)"
    ]
    all_population = rating_population.loc[
        "Sensitivity: all ratings (non-missing; includes out-of-range)"
    ]
    scenario_deltas = {
        metric: float(all_population[metric]) - float(primary_population[metric])
        for metric in (
            "mean_delivery_time",
            "median_delivery_time",
            "p90_delivery_time",
            "slow_delivery_rate",
        )
    }

    source_hash_after = sha256_file(TRAIN_PATH)
    if source_hash_after != source_hash_before:
        raise AssertionError("The cleaned training dataset changed during analysis.")
    if pd.read_csv(TRAIN_PATH, nrows=0).columns.tolist() != original_columns:
        raise AssertionError("The cleaned dataset schema changed during analysis.")

    rating_primary_rows = sql_results.loc[
        sql_results["dimension_name"] == "rating_primary"
    ].sort_values("category", key=lambda values: values.map(float))
    rating_all_rows = sql_results.loc[
        sql_results["dimension_name"] == "rating_all"
    ].sort_values("category", key=lambda values: values.map(float))
    age_rows = sql_results.loc[sql_results["dimension_name"] == "age_band"].copy()
    age_rows["category"] = pd.Categorical(
        age_rows["category"], categories=AGE_BANDS, ordered=True
    )
    age_rows = age_rows.sort_values("category")
    valid_ratings = pd.to_numeric(
        frame.loc[pd.to_numeric(frame[TARGET_COLUMN], errors="coerce").notna(), RATING_COLUMN],
        errors="coerce",
    ).dropna()
    rating_category_counts = valid_ratings.value_counts().sort_index()
    age_summary_sql = sql_results.iloc[0]

    lines = [
        "# Courier Analysis",
        "",
        "## Objective",
        "",
        "Describe observed delivery-performance differences across delivery-person "
        "ratings, delivery-person age bands, and multiple-delivery categories as "
        "separate dimensions. No causal interpretation is made.",
        "",
        "## Data Scope",
        "",
        "- **Source:** `data/processed/train_clean.csv` only.",
        f"- **Target:** `{TARGET_COLUMN}`, included only when non-null and numeric.",
        "- **Slow threshold:** fixed at 40 minutes from Step 5.1; slow means strictly "
        "`Time_taken(min) > 40`.",
        "- Median, P25, P75, and P90 use continuous linear interpolation at rank "
        "`1 + (n - 1) × p`.",
        f"- A group must contain at least {MIN_GROUP_SIZE} valid targets to be ranked "
        "or substantively compared; smaller groups are descriptive only.",
        f"- Total train rows: **{total_rows:,}**; valid numeric targets: "
        f"**{valid_count:,}**; missing/invalid targets: **{total_rows - valid_count:,}**.",
        "- Missing courier values remain in the overall valid-target population and "
        "are excluded only from the corresponding grouped comparison.",
        "",
        "## Delivery Person Ratings",
        "",
        "### Data Quality",
        "",
        f"- Valid-target records with a missing rating: **{missing_counts[RATING_COLUMN]:,}**.",
        f"- Valid-target records with an out-of-range rating: **{out_of_range_count:,}** "
        "(outside the expected inclusive 1–5 range).",
        f"- Primary in-range comparison population: **{int(primary_population['delivery_count']):,}**.",
        f"- All-ratings sensitivity population, including out-of-range values: "
        f"**{int(all_population['delivery_count']):,}**.",
        "- Primary analysis uses the established `rating_out_of_range` flag and the "
        "inclusive 1–5 rule; out-of-range values are excluded, not corrected or recoded.",
        "",
        "Exact observed non-missing numeric rating values and their valid-target counts:",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Rating value", "Valid-target records"],
            [
                [category_text(category), f"{int(count):,}"]
                for category, count in rating_category_counts.items()
            ],
        )
    )
    lines.extend(
        [
            "",
            "### Primary Results",
            "",
            "Only exact numeric rating values within 1–5 are included. Values with "
            "fewer than 30 records are listed descriptively and are not ranked.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Rating", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Sample-size status"],
            grouped_result_table(rating_primary_rows),
        )
    )
    append_rankings(lines, rating_primary_rows)
    lines.extend(
        [
            "### Slow-Delivery Analysis",
            "",
            "Slow rate = slow deliveries in the rating group / all valid deliveries "
            "in that rating group. The same strict global threshold (> 40 minutes) is used.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Rating", "Slow count (numerator)", "Delivery count (denominator)", "Rate calculation", "Slow rate"],
            slow_delivery_table(rating_primary_rows),
        )
    )

    lines.extend(
        [
            "",
            "### Rating Sensitivity Analysis",
            "",
            "The sensitivity scenario includes every non-missing numeric rating, including "
            "out-of-range values as their original distinct categories. No value is recoded.",
            "",
        ]
    )
    sensitivity_rows: list[list[object]] = []
    for category in (
        "Primary: in-range ratings (1-5)",
        "Sensitivity: all ratings (non-missing; includes out-of-range)",
    ):
        row = rating_population.loc[category]
        count = int(row["delivery_count"])
        slow_count = int(row["slow_delivery_count"])
        sensitivity_rows.append(
            [
                category,
                f"{count:,}",
                format_number(float(row["mean_delivery_time"])),
                format_number(float(row["median_delivery_time"])),
                format_number(float(row["p90_delivery_time"])),
                f"{slow_count:,} / {count:,}",
                f"{float(row['slow_delivery_rate']) * 100:.4f}%",
            ]
        )
    lines.extend(
        markdown_table(
            ["Scenario", "Rated deliveries", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / denominator", "Slow rate"],
            sensitivity_rows,
        )
    )
    out_of_range_rows = rating_all_rows.loc[
        ~rating_all_rows["category"].map(float).between(1, 5, inclusive="both")
    ]
    if not out_of_range_rows.empty:
        lines.extend(
            [
                "",
                "Out-of-range categories in the all-ratings scenario (descriptive only "
                "when below the 30-record minimum):",
                "",
            ]
        )
        lines.extend(
            markdown_table(
                ["Original rating value", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Slow count / denominator", "Slow rate", "Sample-size status"],
                [
                    [
                        row["category"],
                        f"{int(row['delivery_count']):,}",
                        format_number(float(row["mean_delivery_time"])),
                        format_number(float(row["median_delivery_time"])),
                        format_number(float(row["p90_delivery_time"])),
                        f"{int(row['slow_delivery_count']):,} / {int(row['delivery_count']):,}",
                        f"{float(row['slow_delivery_rate']) * 100:.4f}%",
                        "Meets minimum; sensitivity only"
                        if int(row["delivery_count"]) >= MIN_GROUP_SIZE
                        else "Small sample; descriptive only",
                    ]
                    for _, row in out_of_range_rows.iterrows()
                ],
            )
        )
    lines.extend(
        [
            "",
            f"The {len(common_ratings)} shared in-range rating categories have identical "
            "group counts and delivery metrics in both scenarios; adding out-of-range "
            "ratings changes the rated-population aggregate, not the membership of "
            "ratings 1–5.",
            "",
            "Aggregate change (all non-missing ratings minus primary in-range population): "
            + "; ".join(
                [
                    f"mean {scenario_deltas['mean_delivery_time']:+.8f} min",
                    f"median {scenario_deltas['median_delivery_time']:+.8f} min",
                    f"P90 {scenario_deltas['p90_delivery_time']:+.8f} min",
                    f"slow rate {scenario_deltas['slow_delivery_rate'] * 100:+.6f} percentage points",
                ]
            )
            + ".",
        ]
    )

    age_stats = [
        [
            f"{int(age_summary_sql['valid_age_count']):,}",
            f"{int(age_summary_sql['valid_targets_missing_age']):,}",
            format_number(float(age_summary_sql["minimum_age"])),
            format_number(float(age_summary_sql["maximum_age"])),
            format_number(float(age_summary_sql["median_age"])),
            format_number(float(age_summary_sql["p25_age"])),
            format_number(float(age_summary_sql["p75_age"])),
        ]
    ]
    lines.extend(
        [
            "",
            "## Delivery Person Age",
            "",
            "### Data Distribution",
            "",
            "Age distribution statistics use valid-target records with a non-missing "
            "numeric age. The missing count is within the valid-target population.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Valid age count", "Missing age count", "Minimum", "Maximum", "Median", "P25", "P75"],
            age_stats,
        )
    )
    lines.extend(
        [
            "",
            "### Age-Band Results",
            "",
            "The predefined bands are Under 20, 20–29, 30–39, 40–49, and 50+. Empty "
            "bands are shown with zero records; no additional bands were created.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Age band", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Sample-size status"],
            grouped_result_table(age_rows),
        )
    )
    append_rankings(lines, age_rows)
    lines.extend(
        [
            "### Slow-Delivery Analysis",
            "",
            "Slow rate = slow deliveries in the age band / all valid deliveries in that "
            "age band; the fixed threshold remains strictly > 40 minutes.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Age band", "Slow count (numerator)", "Delivery count (denominator)", "Rate calculation", "Slow rate"],
            slow_delivery_table(age_rows),
        )
    )

    multiple_distribution = sql_results.loc[
        sql_results["dimension_name"] == "multiple_deliveries"
    ].sort_values("category", key=lambda values: values.map(float))
    lines.extend(
        [
            "",
            "## Multiple Deliveries",
            "",
            "### Category Distribution",
            "",
            f"Valid-target records with missing `multiple_deliveries`: "
            f"**{missing_counts[MULTIPLE_COLUMN]:,}**. Distinct observed non-missing values:",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Category label", "Delivery count"],
            [
                [row["category"], f"{int(row['delivery_count']):,}"]
                for _, row in multiple_distribution.iterrows()
            ],
        )
    )
    lines.extend(["", "### Results", ""])
    lines.extend(
        markdown_table(
            ["Category", "Delivery count", "Mean (min)", "Median (min)", "P90 (min)", "Sample-size status"],
            grouped_result_table(multiple_distribution),
        )
    )
    append_rankings(lines, multiple_distribution)
    lines.extend(
        [
            "### Slow-Delivery Analysis",
            "",
            "Slow rate = slow deliveries in the category / all valid deliveries in that "
            "category; slow remains strictly > 40 minutes.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Category", "Slow count (numerator)", "Delivery count (denominator)", "Rate calculation", "Slow rate"],
            slow_delivery_table(multiple_distribution),
        )
    )

    validation_rows = []
    for dimension, summary in validation.items():
        validation_rows.append(
            [
                dimension,
                summary["groups"],
                summary["metric_checks"],
                summary["rank_checks"],
                "MATCH",
            ]
        )
    validation_rows.extend(
        [
            [
                "Age distribution",
                1,
                age_summary_checks,
                0,
                "MATCH",
            ],
            [
                "Shared in-range rating pattern",
                len(common_ratings),
                shared_rating_checks,
                0,
                "MATCH",
            ],
        ]
    )
    lines.extend(
        [
            "",
            "## SQL vs Python Validation",
            "",
            f"SQL was executed from `sql/06_courier_analysis.sql` against an in-memory "
            f"SQLite table (version `{sqlite_version}`). Python independently grouped "
            "the same valid-target population with Pandas and NumPy's "
            "`percentile(method='linear')`. SQLite's query implements equivalent "
            "continuous rank interpolation.",
            "",
            f"Counts and rankings were compared exactly. Floating-point statistics use "
            f"`numpy.isclose` with absolute tolerance `{ABSOLUTE_TOLERANCE:g}` and "
            f"relative tolerance `{RELATIVE_TOLERANCE:g}`. All category-level metrics, "
            "eligible-group ranks, the age distribution summary, and both rating "
            "sensitivity populations matched.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            ["Analysis", "Groups / scenarios", "Metric checks", "Ranking checks", "Result"],
            validation_rows,
        )
    )
    lines.extend(
        [
            "",
            "For rating sensitivity, both the 1–5 primary population and the all-non-missing "
            "rating population were independently validated. The out-of-range values were "
            "kept as observed and were not recoded. Group counts reconcile to each "
            "dimension's eligible population; the two rating sensitivity rows are separate "
            "overlapping populations, not additive categories. Missing values are excluded "
            "only from their own dimension's comparison.",
            "",
            "## Interpretation",
            "",
            "The tables describe observed delivery-time differences across rating values, "
            "fixed age bands, and multiple-delivery categories separately. Rating values "
            "outside 1–5 are excluded from the primary comparison and shown unchanged in "
            "the sensitivity scenario. These descriptive associations do not show that "
            "ratings, age, or multiple deliveries cause faster or slower deliveries.",
            "",
            "## Limitations",
            "",
            "- The comparisons are observational and unadjusted; traffic, weather, city, "
            "vehicle, distance, and time dimensions are not analyzed here.",
            "- The 30-record rule is a reporting guardrail, not a guarantee of statistical "
            "precision; smaller categories remain descriptive only.",
            "- Missing rating, age, and multiple-delivery values are excluded separately "
            "from their own comparisons and are not inferred.",
            "- Ratings outside the expected 1–5 range remain anomalous values; sensitivity "
            "analysis includes them without assigning a valid-rating meaning.",
            "- The age bands are the fixed descriptive bands requested and do not imply a "
            "causal or ordinal model.",
            "- `multiple_deliveries` values are treated as categorical labels; the numeric "
            "labels are not interpreted as an ordered scale.",
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
    total_metric_checks = sum(
        summary["metric_checks"] for summary in validation.values()
    ) + age_summary_checks + shared_rating_checks
    total_rank_checks = sum(
        summary["rank_checks"] for summary in validation.values()
    )
    print(
        f"Validated {len(GROUP_DIMENSIONS)} grouped analyses; "
        f"{total_metric_checks} metric and {total_rank_checks} ranking checks matched."
    )
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
