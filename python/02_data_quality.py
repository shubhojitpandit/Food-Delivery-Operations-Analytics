"""Quantitatively assess data-quality concerns in the raw train and test CSVs."""

from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "outputs" / "data_quality_report.md"
DATA_FILES = ("train.csv", "test.csv")
NULL_MARKER_PATTERN = re.compile(r"\b(?:nan|null|none)\b", re.IGNORECASE)
CATEGORICAL_COLUMNS = (
    "Weatherconditions",
    "Road_traffic_density",
    "Type_of_order",
    "Type_of_vehicle",
    "multiple_deliveries",
    "Festival",
    "City",
)
NUMERIC_COLUMN_CANDIDATES = (
    "Delivery_person_Age",
    "Delivery_person_Ratings",
    "multiple_deliveries",
)
COORDINATE_COLUMNS = (
    "Restaurant_latitude",
    "Restaurant_longitude",
    "Delivery_location_latitude",
    "Delivery_location_longitude",
)
DATE_COLUMNS = ("Order_Date",)
TIME_COLUMNS = ("Time_Orderd", "Time_Order_picked")


def is_missing_marker(value: object) -> bool:
    """Return true for null-like words embedded in literal text values."""
    return isinstance(value, str) and bool(NULL_MARKER_PATTERN.search(value))


def missing_masks(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Separate parser-recognized nulls from text that resembles a null marker."""
    actual_missing = values.isna()
    text_markers = values.map(is_missing_marker) & ~actual_missing
    return actual_missing, text_markers


def percentage(count: int, total: int) -> str:
    """Format a percentage using the full dataset row count as the denominator."""
    return f"{count / total * 100:.2f}%" if total else "0.00%"


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format table cells safely for Markdown."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", r"\|").replace("\n", " ") for value in row) + " |"
        for row in rows
    )
    return lines


def raw_categories(frame: pd.DataFrame, column: str) -> list[object]:
    """Return the exact non-null raw categories in stable sorted order."""
    values = frame[column].dropna().unique().tolist()
    return sorted(values, key=lambda value: str(value).casefold())


def profile_missing_values(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 1. Missing values",
        "",
        "Actual missing means pandas parsed the cell as null. Missing-like text remains "
        "a literal string in the source and is counted separately. Percentages use all "
        "rows in that file as the denominator.",
        "",
    ]
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        for column in frame.columns:
            actual, marker = missing_masks(frame[column])
            actual_count = int(actual.sum())
            marker_count = int(marker.sum())
            if actual_count or marker_count:
                rows.append(
                    [
                        filename,
                        f"`{column}`",
                        f"{actual_count:,} ({percentage(actual_count, len(frame))})",
                        f"{marker_count:,} ({percentage(marker_count, len(frame))})",
                        ", ".join(repr(item) for item in frame.loc[marker, column].unique()),
                    ]
                )
    if rows:
        lines.extend(
            markdown_table(
                ["File", "Column", "Actual missing", "Missing-like text", "Exact marker text"],
                rows,
            )
        )
    else:
        lines.append("No actual or missing-like values detected.")
    lines.append("")
    return lines


def profile_whitespace(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 2. Leading/trailing whitespace",
        "",
        "Counts are rows whose string value starts or ends with whitespace; raw values "
        "are not stripped. Exact whitespace-bearing values are shown (up to 20 per cell).",
        "",
    ]
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        for column in frame.columns:
            values = frame[column]
            if not (pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values)):
                continue
            has_whitespace = values.map(
                lambda value: isinstance(value, str) and value != value.strip()
            )
            count = int(has_whitespace.sum())
            if count:
                distinct = values[has_whitespace].dropna().unique().tolist()
                shown = ", ".join(repr(value) for value in distinct[:20])
                if len(distinct) > 20:
                    shown += f", ... ({len(distinct) - 20} more)"
                rows.append(
                    [filename, f"`{column}`", f"{count:,}", percentage(count, len(frame)), shown]
                )
    if rows:
        lines.extend(markdown_table(["File", "Column", "Rows affected", "Percent", "Raw values"], rows))
    else:
        lines.append("No leading/trailing whitespace detected in string columns.")
    lines.append("")
    return lines


def numeric_text_values(values: pd.Series) -> tuple[pd.Series, pd.Series]:
    actual, marker = missing_masks(values)
    cleaned_for_inspection = values[~actual & ~marker].astype("string").str.strip()
    parsed = pd.to_numeric(cleaned_for_inspection, errors="coerce")
    return parsed, parsed.notna()


def profile_types(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 3. String columns with date, time, or numeric-looking content",
        "",
        "Parsing below is temporary diagnostic inspection only; source columns are "
        "unchanged. Numeric candidates list how many non-null, non-marker cells parsed.",
        "",
    ]
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        for column in frame.columns:
            values = frame[column]
            if not (pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values)):
                continue
            name = str(column)
            if name in DATE_COLUMNS:
                parsed = pd.to_datetime(values, format="%d-%m-%Y", errors="coerce")
                actual, markers = missing_masks(values)
                eligible = ~actual & ~markers
                invalid = int((eligible & parsed.isna()).sum())
                range_text = (
                    f"{parsed.min().date()} to {parsed.max().date()}"
                    if parsed.notna().any()
                    else "no valid dates"
                )
                rows.append(
                    [filename, f"`{column}`", f"`{values.dtype}`", "Date string", range_text, f"{invalid:,}"]
                )
            elif name in TIME_COLUMNS:
                actual, markers = missing_masks(values)
                eligible = ~actual & ~markers
                parsed = pd.to_datetime(
                    values[eligible].astype("string").str.strip(),
                    format="%H:%M:%S",
                    errors="coerce",
                )
                invalid = int(parsed.isna().sum())
                clock_range = (
                    f"{parsed.dt.strftime('%H:%M:%S').min()} to "
                    f"{parsed.dt.strftime('%H:%M:%S').max()}"
                    if parsed.notna().any()
                    else "no valid clock times"
                )
                rows.append(
                    [filename, f"`{column}`", f"`{values.dtype}`", "Clock-time string", clock_range, f"{invalid:,}"]
                )
            elif name == "Time_taken(min)":
                actual, markers = missing_masks(values)
                eligible_values = values[~actual & ~markers].astype("string").str.strip()
                duration_text = eligible_values.str.extract(
                    r"^\(min\)\s*([+-]?\d+(?:\.\d+)?)$", expand=False
                )
                parsed = pd.to_numeric(duration_text, errors="coerce")
                rows.append(
                    [
                        filename,
                        f"`{column}`",
                        f"`{values.dtype}`",
                        "Target with `(min)` prefix",
                        f"prefix values: {int(eligible_values.str.startswith('(min)').sum()):,}; "
                        f"numeric range: {parsed.min()} to {parsed.max()}",
                        f"{int(parsed.isna().sum()):,}",
                    ]
                )
            else:
                parsed, valid = numeric_text_values(values)
                eligible_count = int((~values.isna() & ~values.map(is_missing_marker)).sum())
                if eligible_count and int(valid.sum()) == eligible_count:
                    rows.append(
                        [
                            filename,
                            f"`{column}`",
                            f"`{values.dtype}`",
                            "Numeric-looking string",
                            f"{int(valid.sum()):,} parsed; range {parsed.min()} to {parsed.max()}",
                            "0",
                        ]
                    )
    if rows:
        lines.extend(
            markdown_table(
                ["File", "Column", "Current dtype", "Content type", "Inspection", "Unparsed"],
                rows,
            )
        )
    else:
        lines.append("No matching string columns found.")
    lines.append("")
    return lines


def profile_ratings(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 4. Delivery person ratings",
        "",
        "Exact numeric values are parsed from non-missing, non-marker rating strings "
        "for comparison only. The raw data is not corrected or filtered.",
        "",
    ]
    numeric_by_file: dict[str, pd.Series] = {}
    all_values: set[float] = set()
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        parsed, valid = numeric_text_values(frame["Delivery_person_Ratings"])
        numeric = parsed[valid]
        numeric_by_file[filename] = numeric
        all_values.update(float(value) for value in numeric.unique())
        below = int((numeric < 1).sum())
        above = int((numeric > 5).sum())
        six = int((numeric == 6).sum())
        rows.append(
            [
                filename,
                ", ".join(f"{value:g}" for value in sorted(numeric.unique())),
                f"{below:,}",
                f"{above:,}",
                f"{six:,}",
            ]
        )
    lines.extend(
        markdown_table(
            ["File", "Distinct numeric-looking values", "Below 1", "Above 5", "Equal to 6"],
            rows,
        )
    )
    six_files = [name for name, values in numeric_by_file.items() if bool((values == 6).any())]
    six_total = sum(int((values == 6).sum()) for values in numeric_by_file.values())
    lines.extend(
        [
            "",
            f"- **Equal to 6 across train/test:** {six_total:,}; occurs in "
            f"{', '.join(six_files) if six_files else 'neither file'}.",
            f"- **Exact distinct numeric-looking values across both files:** "
            f"{', '.join(f'{value:g}' for value in sorted(all_values)) or '(none)'}.",
            "",
        ]
    )
    return lines


def profile_coordinates(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 5. Geographic coordinates",
        "",
        "Geographic bounds are checked against the universal latitude/longitude limits. "
        "The value `0.01` is counted exactly as stored. Because datasets may span multiple "
        "regions, a globally valid coordinate is not by itself evidence of correctness.",
        "",
    ]
    rows: list[list[object]] = []
    structure_rows: list[list[object]] = []
    for filename, frame in frames.items():
        for column in COORDINATE_COLUMNS:
            values = frame[column]
            numeric = pd.to_numeric(values, errors="coerce")
            is_latitude = "latitude" in column.lower()
            lower_bound, upper_bound = (-90, 90) if is_latitude else (-180, 180)
            rows.append(
                [
                    filename,
                    f"`{column}`",
                    str(values.dtype),
                    f"{numeric.min()} / {numeric.max()}",
                    f"{int(numeric.eq(0.01).sum()):,}",
                    f"{int(numeric.eq(0).sum()):,}",
                    f"{int((numeric < 0).sum()):,}",
                    f"{int(((numeric < lower_bound) | (numeric > upper_bound)).sum()):,}",
                ]
            )

        complete = frame[list(COORDINATE_COLUMNS)].notna().all(axis=1)
        restaurant_lat = pd.to_numeric(frame["Restaurant_latitude"], errors="coerce")
        restaurant_lon = pd.to_numeric(frame["Restaurant_longitude"], errors="coerce")
        delivery_lat = pd.to_numeric(frame["Delivery_location_latitude"], errors="coerce")
        delivery_lon = pd.to_numeric(frame["Delivery_location_longitude"], errors="coerce")
        exact_same = complete & restaurant_lat.eq(delivery_lat) & restaurant_lon.eq(delivery_lon)
        any_001 = pd.concat(
            [restaurant_lat, restaurant_lon, delivery_lat, delivery_lon], axis=1
        ).eq(0.01).any(axis=1)
        all_zero = (
            restaurant_lat.eq(0)
            & restaurant_lon.eq(0)
            & delivery_lat.eq(0)
            & delivery_lon.eq(0)
        )
        paired_001 = (
            restaurant_lat.eq(0.01)
            & restaurant_lon.eq(0.01)
            & delivery_lat.eq(0.01)
            & delivery_lon.eq(0.01)
        )
        structure_rows.append(
            [
                filename,
                f"{int(complete.sum()):,}",
                f"{int(exact_same.sum()):,}",
                f"{int(any_001.sum()):,}",
                f"{int(paired_001.sum()):,}",
                f"{int(all_zero.sum()):,}",
                f"{int((restaurant_lat < 0).sum()):,}",
                f"{int((restaurant_lon < 0).sum()):,}",
            ]
        )

    lines.extend(
        markdown_table(
            [
                "File",
                "Coordinate",
                "dtype",
                "Min / max",
                "Count = 0.01",
                "Count = 0",
                "Count < 0",
                "Outside global bounds",
            ],
            rows,
        )
    )
    lines.extend(["", "### Restaurant/delivery coordinate pairing", ""])
    lines.extend(
        markdown_table(
            [
                "File",
                "Complete coordinate rows",
                "Exact same restaurant/delivery pair",
                "Rows with any coordinate = 0.01",
                "All four coordinates = 0.01",
                "All four coordinates = 0",
                "Negative restaurant latitudes",
                "Negative restaurant longitudes",
            ],
            structure_rows,
        )
    )
    lines.extend(
        [
            "",
            "This pairing check compares row-wise values only. Non-identical location pairs "
            "are not treated as errors; source locations or a geographic reference would "
            "be needed to validate actual places.",
            "",
        ]
    )
    return lines


def profile_dates_and_times(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 6. Date and time quality",
        "",
        "Order/pickup comparisons use clock-time values on the same 24-hour clock because "
        "the files provide no pickup date. A pickup time earlier than an order time is "
        "therefore reported as a possible midnight crossing, not a proven chronology error.",
        "",
    ]
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        raw_dates = frame["Order_Date"]
        date_actual, date_markers = missing_masks(raw_dates)
        valid_date_text = raw_dates[~date_actual & ~date_markers]
        parsed_dates = pd.to_datetime(valid_date_text, format="%d-%m-%Y", errors="coerce")
        rows.append(
            [
                filename,
                "`Order_Date`",
                str(raw_dates.dtype),
                f"{int(date_actual.sum()):,}",
                f"{int(date_markers.sum()):,}",
                f"{int(parsed_dates.isna().sum()):,}",
                (
                    f"{parsed_dates.min().date()} to {parsed_dates.max().date()}"
                    if parsed_dates.notna().any()
                    else "no valid date range"
                ),
            ]
        )

        parsed_clocks: dict[str, pd.Series] = {}
        for column in TIME_COLUMNS:
            raw_times = frame[column]
            actual, markers = missing_masks(raw_times)
            valid_text = raw_times[~actual & ~markers].astype("string").str.strip()
            parsed = pd.to_datetime(valid_text, format="%H:%M:%S", errors="coerce")
            parsed_clocks[column] = parsed
            rows.append(
                [
                    filename,
                    f"`{column}`",
                    str(raw_times.dtype),
                    f"{int(actual.sum()):,}",
                    f"{int(markers.sum()):,}",
                    f"{int(parsed.isna().sum()):,}",
                    (
                        f"{parsed.dt.strftime('%H:%M:%S').min()} to "
                        f"{parsed.dt.strftime('%H:%M:%S').max()}"
                        if parsed.notna().any()
                        else "no valid time range"
                    ),
                ]
            )

        order = pd.to_datetime(
            frame["Time_Orderd"][~missing_masks(frame["Time_Orderd"])[0] & ~missing_masks(frame["Time_Orderd"])[1]]
            .astype("string")
            .str.strip(),
            format="%H:%M:%S",
            errors="coerce",
        )
        pickup = pd.to_datetime(
            frame["Time_Order_picked"][
                ~missing_masks(frame["Time_Order_picked"])[0]
                & ~missing_masks(frame["Time_Order_picked"])[1]
            ]
            .astype("string")
            .str.strip(),
            format="%H:%M:%S",
            errors="coerce",
        )
        order_clock = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
        pickup_clock = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
        order_clock.loc[order.index] = order
        pickup_clock.loc[pickup.index] = pickup
        comparable = order_clock.notna() & pickup_clock.notna()
        earlier = comparable & (pickup_clock < order_clock)
        possible_midnight = earlier & (order_clock.dt.hour >= 18) & (pickup_clock.dt.hour <= 6)
        ordinary_order_before_pickup = comparable & (pickup_clock >= order_clock)
        lines.extend(
            [
                f"### {filename} order/pickup clock comparison",
                "",
                f"- Rows with both valid clock values: {int(comparable.sum()):,}.",
                f"- Pickup earlier than order by same-day clock comparison: "
                f"{int(earlier.sum()):,} (possible midnight-crossing records).",
                f"- Of those, order at/after 18:00 and pickup at/before 06:00: "
                f"{int(possible_midnight.sum()):,} (more plausible overnight-clock pattern).",
                f"- Order and pickup comparisons that are not earlier: "
                f"{int(ordinary_order_before_pickup.sum()):,}.",
                "",
            ]
        )

    lines.extend(
        markdown_table(
            [
                "File",
                "Column",
                "dtype",
                "Actual missing",
                "Missing-like text",
                "Malformed non-marker values",
                "Valid range",
            ],
            rows,
        )
    )
    lines.append("")
    return lines


def profile_categories(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 7. Categorical consistency",
        "",
        "Category labels and counts are displayed exactly as read, including padding. "
        "Whitespace-normalized groups are diagnostic comparisons only. The known "
        "`Metropolitian` label is called out for verification against an authoritative "
        "category spelling; no correction is applied.",
        "",
    ]
    for column in CATEGORICAL_COLUMNS:
        lines.extend([f"### `{column}`", ""])
        for filename, frame in frames.items():
            if column not in frame.columns:
                continue
            values = frame[column]
            actual, markers = missing_masks(values)
            category_counts = values[~actual & ~markers].value_counts(dropna=False)
            marker_counts = values[markers].value_counts(dropna=False)
            raw_parts = [
                f"{value!r} ({int(count):,})"
                for value, count in category_counts.items()
            ]
            marker_parts = [
                f"{value!r} ({int(count):,})"
                for value, count in marker_counts.items()
            ]
            lines.append(f"- **{filename} raw valid categories:** " + (", ".join(raw_parts) or "(none)"))
            lines.append(
                f"- **{filename} missing-like categories:** "
                + (", ".join(marker_parts) or "(none)")
            )

            normalized_groups: dict[str, set[str]] = {}
            for value in category_counts.index:
                if isinstance(value, str):
                    normalized_groups.setdefault(value.strip().casefold(), set()).add(value)
            whitespace_values = [
                value
                for group in normalized_groups.values()
                for value in group
                if value != value.strip()
            ]
            variants = [sorted(group) for group in normalized_groups.values() if len(group) > 1]
            lines.append(
                f"- **{filename} categories with leading/trailing whitespace:** "
                + (", ".join(repr(value) for value in sorted(whitespace_values)) or "none")
            )
            if variants:
                lines.append(
                    f"- **{filename} labels that collapse after whitespace/case normalization:** "
                    + "; ".join(", ".join(repr(value) for value in group) for group in variants)
                )
            else:
                lines.append(
                    f"- **{filename} labels that collapse after whitespace/case normalization:** none"
                )
        if column == "City":
            all_values = {
                value
                for frame in frames.values()
                for value in raw_categories(frame, column)
            }
            spelling_present = any(
                isinstance(value, str) and value.strip().casefold() == "metropolitian"
                for value in all_values
            )
            lines.append(
                "- **Possible spelling issue:** "
                "`Metropolitian` occurs in the raw categories and resembles the standard "
                "spelling `Metropolitan`; verify the intended label before any standardization."
                if spelling_present
                else "- **Possible spelling issue:** no `Metropolitian` value observed."
            )
        lines.append("")
    return lines


def profile_duplicates(frames: dict[str, pd.DataFrame]) -> list[str]:
    lines = [
        "## 8. Duplicates",
        "",
        "Complete duplicates count rows identical across all columns. Duplicate-ID rows "
        "count every row whose order ID appears more than once, not just extra occurrences. "
        "Repeated delivery-person IDs are reported separately because a person may be "
        "associated with multiple records.",
        "",
    ]
    rows: list[list[object]] = []
    for filename, frame in frames.items():
        id_values = frame["ID"]
        duplicate_id_rows = int(id_values.duplicated(keep=False).sum())
        person_ids = frame["Delivery_person_ID"]
        rows.append(
            [
                filename,
                f"{int(frame.duplicated().sum()):,}",
                f"{int(id_values.nunique(dropna=True)):,}",
                f"{duplicate_id_rows:,}",
                f"{int(id_values.duplicated().sum()):,}",
                f"{int(person_ids.nunique(dropna=True)):,}",
                f"{int(person_ids.duplicated(keep=False).sum()):,}",
            ]
        )
    lines.extend(
        markdown_table(
            [
                "File",
                "Completely duplicated rows",
                "Unique IDs",
                "Rows with repeated ID",
                "Repeated ID occurrences after first",
                "Unique delivery-person IDs",
                "Rows with repeated delivery-person ID",
            ],
            rows,
        )
    )
    train_ids = set(frames["train.csv"]["ID"].dropna())
    test_ids = set(frames["test.csv"]["ID"].dropna())
    lines.extend(
        [
            "",
            f"- **IDs shared between train and test:** {len(train_ids & test_ids):,}.",
            f"- **IDs unique to train:** {len(train_ids - test_ids):,}; "
            f"**unique to test:** {len(test_ids - train_ids):,}.",
            "",
        ]
    )
    return lines


def profile_train_test(frames: dict[str, pd.DataFrame]) -> list[str]:
    train = frames["train.csv"]
    test = frames["test.csv"]
    shared = [column for column in train.columns if column in test.columns]
    train_only = [column for column in train.columns if column not in test.columns]
    test_only = [column for column in test.columns if column not in train.columns]
    lines = [
        "## 9. Train/test consistency",
        "",
        f"- **Shared columns:** {', '.join(f'`{column}`' for column in shared)}.",
        f"- **Train-only columns:** {', '.join(f'`{column}`' for column in train_only) or '(none)'}.",
        f"- **Test-only columns:** {', '.join(f'`{column}`' for column in test_only) or '(none)'}.",
        "",
        "### Shared-column dtype comparison",
        "",
    ]
    dtype_rows = [
        [
            f"`{column}`",
            str(train[column].dtype),
            str(test[column].dtype),
            "Yes" if train[column].dtype == test[column].dtype else "No",
        ]
        for column in shared
    ]
    lines.extend(markdown_table(["Column", "Train dtype", "Test dtype", "Match"], dtype_rows))
    lines.extend(["", "### Category/value-pattern comparison", ""])
    rows: list[list[object]] = []
    for column in CATEGORICAL_COLUMNS:
        train_values = set(raw_categories(train, column))
        test_values = set(raw_categories(test, column))
        train_markers = set(
            train.loc[train[column].map(is_missing_marker), column].dropna().unique()
        )
        test_markers = set(
            test.loc[test[column].map(is_missing_marker), column].dropna().unique()
        )
        rows.append(
            [
                f"`{column}`",
                len(train_values),
                len(test_values),
                ", ".join(repr(v) for v in sorted(test_values - train_values, key=str)) or "(none)",
                ", ".join(repr(v) for v in sorted(train_values - test_values, key=str)) or "(none)",
                ", ".join(repr(v) for v in sorted(train_markers | test_markers, key=str)) or "(none)",
            ]
        )
    lines.extend(
        markdown_table(
            [
                "Column",
                "Train raw categories",
                "Test raw categories",
                "Test-only categories",
                "Train-only categories",
                "Missing-like markers",
            ],
            rows,
        )
    )
    lines.extend(["", "### Numeric-like range comparison", ""])
    pattern_rows: list[list[object]] = []
    for column in (*NUMERIC_COLUMN_CANDIDATES, *COORDINATE_COLUMNS):
        if column not in train.columns or column not in test.columns:
            continue
        train_values, train_valid = numeric_text_values(train[column])
        test_values, test_valid = numeric_text_values(test[column])
        pattern_rows.append(
            [
                f"`{column}`",
                f"{train_values[train_valid].min()} to {train_values[train_valid].max()}",
                f"{test_values[test_valid].min()} to {test_values[test_valid].max()}",
                f"{int(train_valid.sum()):,} / {int(test_valid.sum()):,}",
            ]
        )
    lines.extend(
        markdown_table(
            ["Column", "Train range", "Test range", "Parsed valid cells (train / test)"],
            pattern_rows,
        )
    )
    lines.extend(
        [
            "",
            "The train-only `Time_taken(min)` field is the target candidate identified by "
            "structure. It contains text-prefixed minute values in this file and is absent "
            "from test. Category-set differences are shown exactly, including text markers "
            "where relevant; they are not automatically treated as schema errors.",
            "",
        ]
    )
    return lines


def recommended_treatment(frames: dict[str, pd.DataFrame]) -> list[str]:
    train = frames["train.csv"]
    test = frames["test.csv"]
    rows = [
        [
            "Text missing markers",
            "Convert to NULL",
            "Literal `NaN`, `NaN `, and embedded forms such as `conditions NaN` represent "
            "missing-like text, not pandas nulls; confirm marker rules per column first.",
        ],
        [
            "Leading/trailing whitespace",
            "normalize/strip",
            "Padding appears in identifiers and categories and can create false category "
            "differences. Preserve a raw copy and validate identifiers before matching.",
        ],
        [
            "Numeric-looking string columns",
            "convert type",
            "Age, ratings, and multiple_deliveries parse numerically after excluding "
            "missing-like text; check invalid values and expected domains before conversion.",
        ],
        [
            "Order_Date",
            "convert type",
            "The observed date strings parse with day-first format; retain malformed values "
            "for review rather than silently coercing them.",
        ],
        [
            "Order/pickup clock columns",
            "convert type",
            "Valid cells parse as `%H:%M:%S`; preserve missing markers and consider midnight "
            "semantics before later timeline calculations.",
        ],
        [
            "Time_taken(min)",
            "convert type",
            "Remove the `(min)` prefix only as an explicit parsed representation in a later "
            "cleaning step; preserve the raw target and validate all conversions.",
        ],
        [
            "Ratings outside 1–5, including 6",
            "investigate further",
            "Out-of-range ratings are observed. Confirm the source convention before "
            "correcting or excluding them; do not infer a replacement.",
        ],
        [
            "Coordinate values equal to 0.01, negative values, and extreme patterns",
            "investigate further",
            "Counts flag potential sentinel or geographic anomalies, but raw locations "
            "cannot be verified without authoritative geography/source metadata.",
        ],
        [
            "Categorical spelling `Metropolitian`",
            "correct/standardize",
            "It resembles `Metropolitan`, but confirm the intended canonical label and "
            "apply consistently across train and test only after validation.",
        ],
        [
            "Other categorical differences",
            "retain",
            "Keep distinct values unless they are confirmed missing markers or verified "
            "spelling/format variants; report unseen labels during later validation.",
        ],
        [
            "Repeated IDs / complete duplicates",
            "exclude only if justified",
            "Do not discard automatically. Establish ID-key semantics and investigate "
            "whether repeated records are legitimate before exclusion.",
        ],
        [
            "Pandas-recognized nulls",
            "retain",
            "Keep missingness explicit during assessment; choose any imputation or exclusion "
            "policy only after the intended downstream use is defined.",
        ],
        [
            "Pickup clock earlier than order clock",
            "investigate further",
            "Some records may cross midnight, but no pickup date is supplied to establish "
            "the correct chronology. Validate source semantics before deriving elapsed time.",
        ],
    ]
    lines = [
        "## 10. Recommended Data Treatment",
        "",
        "These are decision-support recommendations only. No treatment below has been "
        "applied to the raw files.",
        "",
    ]
    lines.extend(markdown_table(["Issue", "Recommendation", "Reason"], rows))
    lines.extend(
        [
            "",
            f"Assessment evidence includes {int(train.duplicated().sum()):,} complete train "
            f"duplicates and {int(test.duplicated().sum()):,} complete test duplicates. "
            f"ID duplicate-row counts are reported in Section 8. The target "
            f"`Time_taken(min)` is present in train: {'yes' if 'Time_taken(min)' in train else 'no'}; "
            f"present in test: {'yes' if 'Time_taken(min)' in test else 'no'}.",
            "",
        ]
    )
    return lines


def main() -> None:
    """Load the original train/test CSVs and write the quantitative assessment."""
    frames = {filename: pd.read_csv(RAW_DIR / filename) for filename in DATA_FILES}
    report = [
        "# Food Delivery Data Quality Assessment",
        "",
        "This assessment investigates potential issues in raw `train.csv` and `test.csv`. "
        "It does not clean, overwrite, or create replacement data, and it does not perform "
        "business analysis. All diagnostic parsing uses temporary in-memory values only.",
        "",
        "Pandas default CSV parsing is used to match the Step 1 inspection. Consequently, "
        "pandas-recognized nulls and null-like strings (including padded or embedded "
        "markers) are reported separately.",
        "",
    ]
    report.extend(profile_missing_values(frames))
    report.extend(profile_whitespace(frames))
    report.extend(profile_types(frames))
    report.extend(profile_ratings(frames))
    report.extend(profile_coordinates(frames))
    report.extend(profile_dates_and_times(frames))
    report.extend(profile_categories(frames))
    report.extend(profile_duplicates(frames))
    report.extend(profile_train_test(frames))
    report.extend(recommended_treatment(frames))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    print(f"Assessed {len(frames)} files.")
    for filename, frame in frames.items():
        print(f"{filename}: {len(frame):,} rows x {len(frame.columns):,} columns")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
