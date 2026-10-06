"""Profile the raw food-delivery CSV files and write a Markdown report."""

from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "outputs" / "profiling_report.md"
FILES = ("train.csv", "test.csv", "Sample_Submission.csv")
MAX_DISPLAYED_VALUES = 20


def show_values(values: list[object], limit: int = MAX_DISPLAYED_VALUES) -> str:
    """Format exact values for a readable Markdown list."""
    displayed = ", ".join(repr(value) for value in values[:limit])
    if len(values) > limit:
        displayed += f", ... ({len(values) - limit} more)"
    return displayed or "(none)"


def is_missing_like_text(value: object) -> bool:
    """Identify common null-like words that were read as literal text."""
    if not isinstance(value, str):
        return False
    return bool(re.search(r"(?:^|\s)(?:nan|null|none)(?:$|\s)", value.strip(), re.IGNORECASE))


def add_iqr_warning(issues: list[str], column: object, numeric_values: pd.Series) -> None:
    """Flag extreme values for review without treating them as confirmed errors."""
    if len(numeric_values) < 4:
        return
    first_quartile = numeric_values.quantile(0.25)
    third_quartile = numeric_values.quantile(0.75)
    spread = third_quartile - first_quartile
    if spread <= 0:
        return
    lower_fence = first_quartile - 3 * spread
    upper_fence = third_quartile + 3 * spread
    outlier_count = int(
        ((numeric_values < lower_fence) | (numeric_values > upper_fence)).sum()
    )
    if outlier_count:
        issues.append(
            f"- `{column}` has {outlier_count:,} value(s) beyond a 3×IQR screening "
            "fence; these are candidates for review, not confirmed errors."
        )


def profile_frame(name: str, frame: pd.DataFrame) -> list[str]:
    """Build one file's profile without changing the source DataFrame."""
    lines = [
        f"## {name}",
        "",
        f"- **Rows:** {len(frame):,}",
        f"- **Columns:** {len(frame.columns):,}",
        f"- **Completely duplicated rows:** {int(frame.duplicated().sum()):,}",
        "",
        "### Column-by-column profile",
        "",
    ]

    issues: list[str] = []
    for column in frame.columns:
        values = frame[column]
        missing = int(values.isna().sum())
        missing_percent = (missing / len(frame) * 100) if len(frame) else 0.0
        missing_like_text = values.map(is_missing_like_text)
        missing_like_count = int(missing_like_text.sum())
        unique_count = int(values.nunique(dropna=True))
        lower_name = str(column).lower()

        lines.extend(
            [
                f"#### `{column}`",
                "",
                f"- **Pandas dtype:** `{values.dtype}`",
                f"- **Pandas missing values:** {missing:,} ({missing_percent:.2f}%)",
                f"- **Unique non-missing values:** {unique_count:,}",
            ]
        )

        if missing:
            issues.append(
                f"- `{column}` contains {missing:,} missing value(s) "
                f"({missing_percent:.2f}%)."
            )
        if missing_like_count:
            marker_percent = (missing_like_count / len(frame) * 100) if len(frame) else 0.0
            lines.append(
                f"- **Missing-like text markers (not parsed as missing):** "
                f"{missing_like_count:,} ({marker_percent:.2f}%)"
            )
            examples = values[missing_like_text].dropna().unique().tolist()
            issues.append(
                f"- `{column}` contains {missing_like_count:,} literal text value(s) "
                f"that look like missing markers: {show_values(examples, limit=5)}."
            )

        if pd.api.types.is_numeric_dtype(values):
            numeric_values = values.dropna()
            if not numeric_values.empty:
                stats = numeric_values.describe()
                lines.extend(
                    [
                        "- **Numerical statistics:**",
                        "",
                        "  ```text",
                        stats.to_string().replace("\n", "\n  "),
                        "  ```",
                        f"- **Minimum / maximum:** {numeric_values.min()} / "
                        f"{numeric_values.max()}",
                    ]
                )

                if "latitude" in str(column).lower() or "longitude" in str(column).lower():
                    lower, upper = (-90, 90) if "latitude" in str(column).lower() else (-180, 180)
                    outside = numeric_values[(numeric_values < lower) | (numeric_values > upper)]
                    if not outside.empty:
                        issues.append(
                            f"- `{column}` has {len(outside):,} coordinate value(s) "
                            f"outside the valid range [{lower}, {upper}]."
                        )
                    else:
                        lines.append(
                            f"- **Coordinate bound check:** all numeric values are within "
                            f"[{lower}, {upper}]."
                        )

                # IQR screening is not useful for geographic coordinates spanning regions.
                is_coordinate = "latitude" in str(column).lower() or "longitude" in str(column).lower()
                spread = stats["75%"] - stats["25%"]
                if not is_coordinate and spread > 0:
                    add_iqr_warning(issues, column, numeric_values)
        elif pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
            unique_values = values.dropna().unique().tolist()
            lines.append(
                f"- **Distinct values:** {show_values(unique_values)}"
            )

            # Detect whitespace/case variants without normalizing stored values.
            normalized: dict[str, set[str]] = {}
            whitespace_values: list[str] = []
            for value in unique_values:
                if isinstance(value, str):
                    if value != value.strip():
                        whitespace_values.append(value)
                    normalized.setdefault(value.strip().casefold(), set()).add(value)
            if whitespace_values:
                issues.append(
                    f"- `{column}` has leading/trailing whitespace in categorical "
                    f"value(s), for example {show_values(whitespace_values, limit=5)}."
                )
            variants = [sorted(raw_values) for raw_values in normalized.values() if len(raw_values) > 1]
            if variants:
                examples = "; ".join(show_values(group, limit=6) for group in variants[:5])
                issues.append(
                    f"- `{column}` contains categorical values that differ only by "
                    f"whitespace and/or letter case: {examples}."
                )

            non_missing_text = values[values.notna() & ~missing_like_text].astype(str).str.strip()
            numeric_conversion = pd.to_numeric(non_missing_text, errors="coerce")
            if len(non_missing_text) and numeric_conversion.notna().all():
                lines.extend(
                    [
                        "- **Numeric-looking text statistics (diagnostic only):**",
                        "",
                        "  ```text",
                        numeric_conversion.describe().to_string().replace("\n", "\n  "),
                        "  ```",
                        f"- **Numeric-looking minimum / maximum:** "
                        f"{numeric_conversion.min()} / {numeric_conversion.max()}",
                    ]
                )
                add_iqr_warning(issues, column, numeric_conversion)
                issues.append(
                    f"- `{column}` is stored as `{values.dtype}` although every "
                    "non-missing, non-marker value can be parsed as numeric."
                )
            elif "taken" in lower_name and "(min)" in lower_name:
                duration_text = non_missing_text.str.extract(
                    r"^\(min\)\s*([+-]?\d+(?:\.\d+)?)$",
                    expand=False,
                )
                duration_values = pd.to_numeric(duration_text, errors="coerce")
                if len(non_missing_text) and duration_values.notna().all():
                    lines.extend(
                        [
                            "- **Numeric-looking duration statistics (diagnostic only):**",
                            "",
                            "  ```text",
                            duration_values.describe().to_string().replace("\n", "\n  "),
                            "  ```",
                            f"- **Numeric-looking minimum / maximum:** "
                            f"{duration_values.min()} / {duration_values.max()}",
                        ]
                    )
                    add_iqr_warning(issues, column, duration_values)
                    issues.append(
                        f"- `{column}` is stored as `{values.dtype}` using text values "
                        "with a unit prefix rather than a numeric dtype."
                    )

        if "date" in lower_name or pd.api.types.is_datetime64_any_dtype(values):
            date_values = values[values.notna() & ~missing_like_text]
            parsed_dates = pd.to_datetime(date_values, errors="coerce", dayfirst=True)
            invalid_dates = parsed_dates.isna()
            if parsed_dates.notna().any():
                lines.append(
                    f"- **Parsed date range:** {parsed_dates.min().date()} to "
                    f"{parsed_dates.max().date()}"
                )
            invalid_count = int(invalid_dates.sum())
            if invalid_count:
                examples = date_values[invalid_dates].astype(str).head(5).tolist()
                issues.append(
                    f"- `{column}` has {invalid_count:,} malformed date value(s), "
                    f"for example {show_values(examples, limit=5)}."
                )
            if not pd.api.types.is_datetime64_any_dtype(values) and values.notna().any():
                issues.append(
                    f"- `{column}` appears date-related but is stored as `{values.dtype}`."
                )

        if "time" in lower_name:
            nonmissing = values[values.notna() & ~missing_like_text]
            is_duration = "taken" in lower_name or "(min)" in lower_name
            examples = nonmissing.astype(str).head(5).tolist()
            lines.append(
                f"- **Time-related inspection:** {len(nonmissing):,} non-missing value(s); "
                f"sample {show_values(examples, limit=5)}"
            )
            if is_duration:
                lines.append(
                    "- Treated as a duration-like field for inspection; no conversion "
                    "or derived duration was created."
                )
            else:
                parsed_times = pd.to_datetime(
                    nonmissing.astype(str).str.strip(),
                    format="mixed",
                    errors="coerce",
                )
                invalid_times = parsed_times.isna()
                valid_times = parsed_times.dropna()
                if not valid_times.empty:
                    clock_values = valid_times.dt.strftime("%H:%M:%S")
                    lines.append(
                        f"- **Clock-time range:** {clock_values.min()} to {clock_values.max()}"
                    )
                invalid_count = int(invalid_times.sum())
                if invalid_count:
                    bad_examples = nonmissing[invalid_times].astype(str).head(5).tolist()
                    issues.append(
                        f"- `{column}` has {invalid_count:,} malformed clock-time value(s), "
                        f"for example {show_values(bad_examples, limit=5)}."
                    )
                if not pd.api.types.is_object_dtype(values) and not pd.api.types.is_string_dtype(values):
                    issues.append(
                        f"- `{column}` appears time-related but is stored as `{values.dtype}`."
                    )

        if "latitude" in lower_name or "longitude" in lower_name:
            if not pd.api.types.is_numeric_dtype(values):
                issues.append(
                    f"- `{column}` is coordinate-related but is not stored as a numeric dtype."
                )

        if lower_name == "id":
            duplicate_ids = int(values.duplicated(keep=False).sum())
            if duplicate_ids:
                issues.append(
                    f"- Identifier-like column `{column}` has {duplicate_ids:,} "
                    "row(s) whose identifier occurs more than once."
                )

        lines.append("")

    lines.extend(["### Potential data-quality issues", ""])
    lines.extend(issues or ["- No potential issues detected by these basic checks."])
    lines.append("")
    return lines


def compare_train_test(train: pd.DataFrame, test: pd.DataFrame) -> list[str]:
    """Summarize schema differences and report whether train-only fields occur in test."""
    train_columns = list(train.columns)
    test_columns = list(test.columns)
    train_only = [column for column in train_columns if column not in test_columns]
    test_only = [column for column in test_columns if column not in train_columns]
    shared = [column for column in train_columns if column in test_columns]

    lines = [
        "## Train / test structure comparison",
        "",
        f"- **Columns in train but not test:** {show_values(train_only)}",
        f"- **Columns in test but not train:** {show_values(test_only)}",
        "",
        "### Shared-column pandas dtypes",
        "",
        "| Column | train.csv dtype | test.csv dtype | Match |",
        "|---|---|---|---|",
    ]
    for column in shared:
        train_dtype = str(train[column].dtype)
        test_dtype = str(test[column].dtype)
        match = "Yes" if train_dtype == test_dtype else "No"
        lines.append(f"| `{column}` | `{train_dtype}` | `{test_dtype}` | {match} |")

    lines.extend(["", "### Target-column presence", ""])
    if train_only:
        lines.append(
            "- Train-only column(s), and therefore target candidate(s) based on "
            f"structure: {show_values(train_only)}."
        )
        for column in train_only:
            lines.append(
                f"- `{column}` exists in train.csv and "
                f"{'is present' if column in test_columns else 'is absent'} in test.csv."
            )
    else:
        lines.append(
            "- No train-only column was found; this structural comparison does not "
            "identify a target column."
        )
    lines.append("")
    return lines


def main() -> None:
    """Read the raw CSVs, produce profiles, and write the requested report."""
    frames = {
        filename: pd.read_csv(RAW_DIR / filename)
        for filename in FILES
    }

    report = [
        "# Food Delivery Dataset Profiling Report",
        "",
        "This report describes the supplied raw CSV files only. It does not clean, "
        "overwrite, or add columns to the source data, and it contains no business "
        "analysis or derived variables.",
        "",
        "Pandas-missing percentages use the number of rows in the corresponding file. "
        "Null-like words read as literal text are reported separately. Unique counts "
        "exclude pandas-recognized missing values. Numeric-looking statistics use "
        "temporary diagnostic parsing only; source values are not changed. The 3×IQR "
        "screening is a potential outlier check, not a data-validity conclusion.",
        "",
    ]
    for filename, frame in frames.items():
        report.extend(profile_frame(filename, frame))

    report.extend(compare_train_test(frames["train.csv"], frames["test.csv"]))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    print(f"Profiled {len(frames)} files.")
    for filename, frame in frames.items():
        print(f"{filename}: {len(frame):,} rows x {len(frame.columns):,} columns")
    print(f"Report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
