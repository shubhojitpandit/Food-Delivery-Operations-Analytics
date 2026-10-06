"""Clean train/test CSVs using the approved Step 3 transformations."""

from datetime import time
import hashlib
from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_PATH = ROOT / "outputs" / "cleaning_report.md"

TARGET_COLUMN = "Time_taken(min)"
NUMERIC_COLUMNS = (
    "Delivery_person_Age",
    "Delivery_person_Ratings",
    "multiple_deliveries",
)
COORDINATE_COLUMNS = (
    "Delivery_location_latitude",
    "Delivery_location_longitude",
)
DATE_COLUMN = "Order_Date"
TIME_COLUMNS = ("Time_Orderd", "Time_Order_picked")
MISSING_MARKERS_BY_COLUMN = {
    "Delivery_person_Age": {"nan", "null", "none"},
    "Delivery_person_Ratings": {"nan", "null", "none"},
    "Time_Orderd": {"nan", "null", "none"},
    "Road_traffic_density": {"nan", "null", "none"},
    "multiple_deliveries": {"nan", "null", "none"},
    "Festival": {"nan", "null", "none"},
    "City": {"nan", "null", "none"},
    "Weatherconditions": {"conditions nan"},
}
TARGET_PATTERN = re.compile(r"^\(min\)\s*([+-]?\d+(?:\.\d+)?)$")
FLAG_COLUMNS = ("rating_out_of_range", "suspicious_delivery_coordinates")


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 digest for read-only source verification."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    """Format a Markdown table and escape cell delimiters."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [
            str(value).replace("|", r"\|").replace("\n", " ")
            for value in row
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def strip_string_values(frame: pd.DataFrame) -> pd.DataFrame:
    """Strip outer whitespace from string cells without changing internal spaces."""
    cleaned = frame.copy()
    for column in cleaned.columns:
        values = cleaned[column]
        if pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
            cleaned[column] = values.map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
    return cleaned


def convert_confirmed_markers(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Replace only the per-column, Step 2-confirmed marker text with pandas NA."""
    converted = frame.copy()
    counts: dict[str, int] = {}
    for column, markers in MISSING_MARKERS_BY_COLUMN.items():
        if column not in converted.columns:
            continue
        values = converted[column]
        mask = values.map(
            lambda value: isinstance(value, str) and value.strip().casefold() in markers
        )
        counts[column] = int(mask.sum())
        converted.loc[mask, column] = pd.NA
    return converted, counts


def parse_time_column(values: pd.Series, column: str) -> pd.Series:
    """Parse a strict 24-hour time string into Python time values, retaining nulls."""
    result: list[time | None] = []
    for row_number, value in values.items():
        if pd.isna(value):
            result.append(None)
            continue
        text = str(value).strip()
        try:
            parsed = pd.to_datetime(text, format="%H:%M:%S", errors="raise")
        except (ValueError, TypeError) as error:
            raise ValueError(
                f"Malformed clock value {text!r} in {column} at row index {row_number}"
            ) from error
        result.append(parsed.time())
    return pd.Series(result, index=values.index, dtype="object")


def clean_frame(
    raw_frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the approved transformations without modifying the input frame."""
    cleaned = strip_string_values(raw_frame)
    cleaned, marker_counts = convert_confirmed_markers(cleaned)

    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="raise")

    if TARGET_COLUMN in cleaned.columns:
        target_values = cleaned[TARGET_COLUMN]
        target_text = target_values.astype("string").str.strip()
        missing_target = target_values.isna()
        extracted = target_text.str.extract(TARGET_PATTERN, expand=False)
        malformed_target = ~missing_target & extracted.isna()
        if malformed_target.any():
            examples = target_values[malformed_target].head(5).tolist()
            raise ValueError(
                f"Unexpected {TARGET_COLUMN} value(s); expected '(min) <number>': {examples}"
            )
        cleaned[TARGET_COLUMN] = pd.to_numeric(extracted, errors="raise")

    # The data-quality assessment identified day-first dates; strict parsing prevents silent coercion.
    cleaned[DATE_COLUMN] = pd.to_datetime(
        cleaned[DATE_COLUMN], format="%d-%m-%Y", errors="raise"
    )

    for column in TIME_COLUMNS:
        cleaned[column] = parse_time_column(cleaned[column], column)

    if "City" in cleaned.columns:
        cleaned["City"] = cleaned["City"].replace({"Metropolitian": "Metropolitan"})

    if "Delivery_person_Ratings" in cleaned.columns:
        ratings = cleaned["Delivery_person_Ratings"]
        cleaned["rating_out_of_range"] = (
            ratings.notna() & ((ratings < 1) | (ratings > 5))
        ).astype("int8")

    if all(column in cleaned.columns for column in COORDINATE_COLUMNS):
        sentinel_like = cleaned[list(COORDINATE_COLUMNS)].eq(0.01).any(axis=1)
        cleaned["suspicious_delivery_coordinates"] = sentinel_like.astype("int8")

    if "Time_Orderd" in cleaned.columns and "Time_Order_picked" in cleaned.columns:
        order_clock = cleaned["Time_Orderd"]
        pickup_clock = cleaned["Time_Order_picked"]
        earlier = pd.Series(False, index=cleaned.index)
        valid = order_clock.notna() & pickup_clock.notna()
        earlier.loc[valid] = [
            pickup < order
            for order, pickup in zip(order_clock.loc[valid], pickup_clock.loc[valid])
        ]
        cleaned["possible_midnight_crossing"] = earlier.astype("int8")

    return cleaned, marker_counts


def csv_ready_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Serialize date and clock values consistently for CSV output."""
    csv_frame = frame.copy()
    csv_frame[DATE_COLUMN] = csv_frame[DATE_COLUMN].dt.strftime("%Y-%m-%d")
    for column in TIME_COLUMNS:
        csv_frame[column] = csv_frame[column].map(
            lambda value: value.strftime("%H:%M:%S") if isinstance(value, time) else pd.NA
        )
    return csv_frame


def validate_cleaned_data(
    train: pd.DataFrame,
    test: pd.DataFrame,
    train_raw: pd.DataFrame,
    test_raw: pd.DataFrame,
    raw_hashes: dict[str, str],
    raw_paths: dict[str, Path],
    expected_train_columns: list[str],
    expected_test_columns: list[str],
) -> list[str]:
    """Assert row/schema/type/quality invariants before reporting success."""
    checks: list[str] = []
    if len(train) != len(train_raw) or len(train) != 45_593:
        raise AssertionError(f"Unexpected train row count after cleaning: {len(train):,}")
    checks.append(f"Train row count preserved: {len(train):,}.")
    if len(test) != len(test_raw) or len(test) != 11_399:
        raise AssertionError(f"Unexpected test row count after cleaning: {len(test):,}")
    checks.append(f"Test row count preserved: {len(test):,}.")

    if TARGET_COLUMN not in train.columns or TARGET_COLUMN in test.columns:
        raise AssertionError("Target-column placement is incorrect.")
    checks.append("Target is present in train only.")

    for column in (*NUMERIC_COLUMNS, *COORDINATE_COLUMNS, "Vehicle_condition"):
        if not pd.api.types.is_numeric_dtype(train[column]) or not pd.api.types.is_numeric_dtype(
            test[column]
        ):
            raise AssertionError(f"{column} is not numeric in both cleaned datasets.")
    if not pd.api.types.is_numeric_dtype(train[TARGET_COLUMN]):
        raise AssertionError(f"{TARGET_COLUMN} is not numeric in train.")
    checks.append("Required numeric columns and training target have numeric dtypes.")

    if not pd.api.types.is_datetime64_any_dtype(train[DATE_COLUMN]) or not pd.api.types.is_datetime64_any_dtype(
        test[DATE_COLUMN]
    ):
        raise AssertionError("Order_Date is not datetime in both cleaned datasets.")
    for frame in (train, test):
        for column in TIME_COLUMNS:
            nonmissing = frame[column].dropna()
            if not nonmissing.map(lambda value: isinstance(value, time)).all():
                raise AssertionError(f"{column} contains a non-time value.")
    checks.append("Order_Date is datetime; clock columns contain time values or missing values.")

    for frame in (train, test):
        for column in frame.columns:
            values = frame[column]
            if pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
                whitespace = values.map(
                    lambda value: isinstance(value, str) and value != value.strip()
                )
                if whitespace.any():
                    raise AssertionError(f"Unintended whitespace remains in {column}.")
    checks.append("No leading/trailing whitespace remains in string values.")

    for frame in (train, test):
        if "Metropolitian" in set(frame["City"].dropna()):
            raise AssertionError("Metropolitian remains in City after standardization.")
        if not set(frame["City"].dropna()).issubset({"Metropolitan", "Urban", "Semi-Urban"}):
            raise AssertionError("Unexpected City value after standardization.")
    checks.append("City spelling standardization is consistent in train and test.")

    for column in FLAG_COLUMNS + ("possible_midnight_crossing",):
        for frame in (train, test):
            if column not in frame.columns:
                raise AssertionError(f"Expected quality flag {column} is missing.")
            if not set(frame[column].unique()).issubset({0, 1}):
                raise AssertionError(f"{column} contains values other than 0/1.")
    checks.append("All quality flags contain only 0/1.")

    for frame in (train, test):
        if frame.duplicated().any():
            raise AssertionError("Complete duplicate rows found in cleaned data.")
    checks.append("No complete duplicate rows were introduced.")

    if train.columns.tolist() != expected_train_columns + [
        "rating_out_of_range",
        "suspicious_delivery_coordinates",
        "possible_midnight_crossing",
    ]:
        raise AssertionError("Train has unexpected or missing columns.")
    if test.columns.tolist() != expected_test_columns + [
        "rating_out_of_range",
        "suspicious_delivery_coordinates",
        "possible_midnight_crossing",
    ]:
        raise AssertionError("Test has unexpected or missing columns.")
    checks.append("Only the three documented quality flags were added.")

    for filename, path in raw_paths.items():
        if sha256_file(path) != raw_hashes[filename]:
            raise AssertionError(f"Raw input changed during cleaning: {filename}")
    checks.append("SHA-256 checks confirm all raw input files are unchanged.")
    return checks


def build_cleaning_report(
    before_frames: dict[str, pd.DataFrame],
    cleaned_frames: dict[str, pd.DataFrame],
    marker_counts: dict[str, dict[str, int]],
    checks: list[str],
) -> str:
    """Create a report of transformations, type/null changes, and validation."""
    lines = [
        "# Food Delivery Cleaning Report",
        "",
        "## Scope and files",
        "",
        "- **Input files:** `data/raw/train.csv`, `data/raw/test.csv`.",
        "- **Reference file not transformed:** `data/raw/Sample_Submission.csv`.",
        "- **Output files:** `data/processed/train_clean.csv`, "
        "`data/processed/test_clean.csv`.",
        "- **Script:** `python/03_clean.py`.",
        "- No business analysis was performed. The raw input files were read-only.",
        "",
        "## Transformations applied",
        "",
        "- Converted only the confirmed, column-specific missing markers listed below "
        "to pandas missing values.",
        "- Stripped leading/trailing whitespace from string values; internal spaces were "
        "preserved.",
        "- Converted `Delivery_person_Age`, `Delivery_person_Ratings`, and "
        "`multiple_deliveries` to numeric values.",
        "- Parsed `Time_taken(min)` in train by removing its literal `(min)` prefix and "
        "converting only the numeric delivery-time value; retained its column name.",
        "- Parsed `Order_Date` strictly as day-first dates in memory. CSV files serialize "
        "the dates as ISO `YYYY-MM-DD` strings.",
        "- Parsed clock columns strictly as 24-hour times in memory and serialized them "
        "as `HH:MM:SS` strings; missing values remain blank/null.",
        "- Standardized `City` value `Metropolitian` to `Metropolitan` in both datasets.",
        "- Preserved all numeric ratings, including 6; did not modify negative restaurant "
        "coordinates or `0.01` delivery coordinates.",
        "- Did not remove complete rows, repeated order/person IDs, or records with missing "
        "order time. No pickup duration was calculated.",
        "",
        "### Confirmed missing-marker conversions",
        "",
        "Counts show marker strings converted per file; pandas-recognized nulls remain "
        "missing. `conditions NaN` was handled only in `Weatherconditions`; generic null "
        "tokens were handled only in the columns confirmed by Step 2.",
        "",
    ]
    marker_rows = [
        [filename, f"`{column}`", f"{count:,}"]
        for filename, by_column in marker_counts.items()
        for column, count in by_column.items()
    ]
    lines.extend(markdown_table(["File", "Column", "Text markers converted"], marker_rows))

    city_rows = []
    for filename, frame in before_frames.items():
        standardized_count = int(
            frame["City"].map(
                lambda value: isinstance(value, str) and value.strip() == "Metropolitian"
            ).sum()
        )
        city_rows.append([filename, standardized_count])
    lines.extend(
        [
            "",
            "### City spelling standardization",
            "",
        ]
    )
    lines.extend(markdown_table(["File", "City values standardized"], city_rows))

    flag_rows: list[list[object]] = []
    for filename, frame in cleaned_frames.items():
        flag_rows.append(
            [
                filename,
                int(frame["rating_out_of_range"].sum()),
                int(frame["suspicious_delivery_coordinates"].sum()),
                int(frame["possible_midnight_crossing"].sum()),
            ]
        )
    lines.extend(
        [
            "",
            "### Quality flags created",
            "",
            "`rating_out_of_range` is 1 when a non-null rating is outside [1, 5]. "
            "`suspicious_delivery_coordinates` is 1 when either delivery coordinate "
            "equals 0.01. `possible_midnight_crossing` is 1 when both clock values are "
            "present and pickup time is earlier than order time; this does not assert "
            "actual chronology across dates.",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            [
                "File",
                "Rows with rating_out_of_range",
                "Rows with suspicious_delivery_coordinates",
                "Rows with possible_midnight_crossing",
            ],
            flag_rows,
        )
    )

    lines.extend(["", "## Rows and schema", ""])
    row_rows = []
    for filename, raw_frame in before_frames.items():
        clean_frame_data = cleaned_frames[filename]
        row_rows.append(
            [
                filename,
                f"{len(raw_frame):,}",
                f"{len(clean_frame_data):,}",
                f"{len(raw_frame) - len(clean_frame_data):,}",
                f"{int(raw_frame.duplicated().sum()):,}",
                f"{int(clean_frame_data.duplicated().sum()):,}",
            ]
        )
    lines.extend(
        markdown_table(
            [
                "File",
                "Rows before",
                "Rows retained",
                "Rows removed",
                "Complete duplicates before",
                "Complete duplicates after",
            ],
            row_rows,
        )
    )
    lines.extend(
        [
            "",
            "### Before/after dtype and missing-value counts",
            "",
            "The cleaned in-memory date dtype is `datetime64[ns]`; time values are Python "
            "`datetime.time` objects with missing values preserved. CSV has no native date "
            "or time dtype, so those fields are serialized in the documented ISO/clock "
            "formats. Before counts distinguish actual pandas nulls from approved text "
            "markers; after counts are nulls in the cleaned in-memory values.",
            "",
        ]
    )
    schema_rows: list[list[object]] = []
    for filename, raw_frame in before_frames.items():
        cleaned = cleaned_frames[filename]
        # Reconstruct source column order plus the known appended flags for comparison.
        for column in raw_frame.columns:
            before_values = raw_frame[column]
            after_values = cleaned[column]
            marker_set = MISSING_MARKERS_BY_COLUMN.get(column, set())
            marker_mask = before_values.map(
                lambda value: isinstance(value, str)
                and value.strip().casefold() in marker_set
            )
            schema_rows.append(
                [
                    filename,
                    f"`{column}`",
                    str(before_values.dtype),
                    str(after_values.dtype),
                    f"{int(before_values.isna().sum()):,} actual + "
                    f"{int(marker_mask.sum()):,} markers",
                    f"{int(after_values.isna().sum()):,}",
                ]
            )
        for column in ("rating_out_of_range", "suspicious_delivery_coordinates", "possible_midnight_crossing"):
            schema_rows.append([filename, f"`{column}` (added)", "(not present)", str(cleaned[column].dtype), "—", "0"])
    lines.extend(
        markdown_table(
            [
                "File",
                "Column",
                "Before dtype",
                "After in-memory dtype",
                "Before missing count",
                "After missing count",
            ],
            schema_rows,
        )
    )

    lines.extend(["", "## Validation checks performed", ""])
    lines.extend(f"- {check}" for check in checks)
    lines.extend(
        [
            "- Target `Time_taken(min)` is present only in train; it is not added to test.",
            "- Processed CSV outputs were re-read to confirm headers, row counts, numeric "
            "columns, ISO dates, clock format, and binary flags.",
            "",
            "## Unresolved data-quality limitations",
            "",
            "- A clock comparison cannot determine whether an earlier pickup time truly "
            "crossed midnight because no pickup date is supplied; the flag is deliberately "
            "named `possible_midnight_crossing`.",
            "- `0.01` delivery coordinate values are preserved and flagged; the cleaning "
            "does not establish their geographic correctness.",
            "- Ratings equal to 6 are retained and flagged as out of range, not corrected.",
            "- CSV serialization stores date/time columns as formatted text; consumers "
            "should parse the documented formats when loading the files.",
            "- Missing values remain missing; no imputation or row exclusion was performed.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_written_csvs(
    train_path: Path,
    test_path: Path,
    train_expected: pd.DataFrame,
    test_expected: pd.DataFrame,
) -> None:
    """Re-read saved CSVs and check serialized schema and content conventions."""
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    for actual, expected, filename in (
        (train, train_expected, train_path.name),
        (test, test_expected, test_path.name),
    ):
        if len(actual) != len(expected):
            raise AssertionError(f"Saved {filename} has an unexpected row count.")
        if actual.columns.tolist() != expected.columns.tolist():
            raise AssertionError(f"Saved {filename} has an unexpected column layout.")
        if not pd.api.types.is_numeric_dtype(actual["Delivery_person_Age"]):
            raise AssertionError(f"Saved {filename} age is not numeric.")
        if not pd.api.types.is_numeric_dtype(actual["Delivery_person_Ratings"]):
            raise AssertionError(f"Saved {filename} ratings are not numeric.")
        if not pd.api.types.is_numeric_dtype(actual["multiple_deliveries"]):
            raise AssertionError(f"Saved {filename} multiple_deliveries is not numeric.")
        if not pd.api.types.is_numeric_dtype(actual["Vehicle_condition"]):
            raise AssertionError(f"Saved {filename} Vehicle_condition is not numeric.")
        if TARGET_COLUMN in expected.columns and not pd.api.types.is_numeric_dtype(
            actual[TARGET_COLUMN]
        ):
            raise AssertionError(f"Saved {filename} target is not numeric.")
        parsed_dates = pd.to_datetime(actual[DATE_COLUMN], format="%Y-%m-%d", errors="raise")
        if parsed_dates.isna().any():
            raise AssertionError(f"Saved {filename} contains a malformed serialized date.")
        for column in TIME_COLUMNS:
            valid_times = actual[column].dropna()
            parsed_times = pd.to_datetime(valid_times, format="%H:%M:%S", errors="raise")
            if parsed_times.isna().any():
                raise AssertionError(f"Saved {filename} contains a malformed serialized time.")
        for column in FLAG_COLUMNS + ("possible_midnight_crossing",):
            if not set(actual[column].dropna().unique()).issubset({0, 1}):
                raise AssertionError(f"Saved {filename} has invalid values in {column}.")
        if "Metropolitian" in set(actual["City"].dropna()):
            raise AssertionError(f"Saved {filename} has unstandardized City spelling.")
        for column in actual.columns:
            values = actual[column]
            if pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
                if values.map(
                    lambda value: isinstance(value, str) and value != value.strip()
                ).any():
                    raise AssertionError(f"Saved {filename} contains whitespace in {column}.")


def main() -> None:
    """Clean both inputs, validate outputs, and write the cleaning report."""
    raw_paths = {
        "train.csv": RAW_DIR / "train.csv",
        "test.csv": RAW_DIR / "test.csv",
        "Sample_Submission.csv": RAW_DIR / "Sample_Submission.csv",
    }
    raw_hashes = {filename: sha256_file(path) for filename, path in raw_paths.items()}
    raw_frames = {
        filename: pd.read_csv(raw_paths[filename])
        for filename in ("train.csv", "test.csv")
    }
    expected_train_columns = raw_frames["train.csv"].columns.tolist()
    expected_test_columns = raw_frames["test.csv"].columns.tolist()
    if TARGET_COLUMN not in expected_train_columns or TARGET_COLUMN in expected_test_columns:
        raise ValueError("Raw train/test target structure does not match the approved schema.")

    cleaned_frames: dict[str, pd.DataFrame] = {}
    marker_counts: dict[str, dict[str, int]] = {}
    for filename, raw_frame in raw_frames.items():
        cleaned, converted = clean_frame(raw_frame)
        cleaned_frames[filename] = cleaned
        marker_counts[filename] = converted

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "train.csv": PROCESSED_DIR / "train_clean.csv",
        "test.csv": PROCESSED_DIR / "test_clean.csv",
    }
    for filename, cleaned in cleaned_frames.items():
        csv_ready_frame(cleaned).to_csv(output_paths[filename], index=False)

    checks = validate_cleaned_data(
        cleaned_frames["train.csv"],
        cleaned_frames["test.csv"],
        raw_frames["train.csv"],
        raw_frames["test.csv"],
        raw_hashes,
        raw_paths,
        expected_train_columns,
        expected_test_columns,
    )
    validate_written_csvs(
        output_paths["train.csv"],
        output_paths["test.csv"],
        csv_ready_frame(cleaned_frames["train.csv"]),
        csv_ready_frame(cleaned_frames["test.csv"]),
    )
    checks.append("Saved CSVs re-read successfully with expected rows, schema, types, formats, and flag values.")
    report_text = build_cleaning_report(
        raw_frames,
        cleaned_frames,
        marker_counts,
        checks,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_text, encoding="utf-8")

    print(f"Cleaned {len(cleaned_frames)} datasets without removing rows.")
    for filename, output_path in output_paths.items():
        print(f"{output_path.name}: {len(cleaned_frames[filename]):,} rows")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
