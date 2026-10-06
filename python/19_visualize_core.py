"""Generate the eight CORE visualizations from validated analysis definitions."""

from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "train_clean.csv"
CHART_DIR = ROOT / "outputs" / "charts"
VALIDATION_PATH = ROOT / "outputs" / "visualization_validation.md"

TARGET = "Time_taken(min)"
SLOW_THRESHOLD = 40.0
MIN_GROUP_SIZE = 30
TRAFFIC_ORDER = ("High", "Jam", "Low", "Medium")
WEATHER_ORDER = (
    "conditions Cloudy",
    "conditions Fog",
    "conditions Sandstorms",
    "conditions Stormy",
    "conditions Sunny",
    "conditions Windy",
)
TIME_BANDS = ("Night", "Morning", "Afternoon", "Evening", "Late Night")
DISTANCE_BANDS = (
    "0-1 km",
    "1-2 km",
    "2-3 km",
    "3-5 km",
    "5-10 km",
    "10-15 km",
    "15+ km",
)
EARTH_RADIUS_KM = 6371.0088
COLOR = "#287271"
ACCENT = "#e76f51"
DARK = "#264653"
GRID = "#d9e2e7"


def read_source() -> pd.DataFrame:
    """Load only the cleaned training data and validate its target population."""
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Cleaned training data not found: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    required = {
        TARGET,
        "Road_traffic_density",
        "multiple_deliveries",
        "City",
        "Time_Orderd",
        "Weatherconditions",
        "Restaurant_latitude",
        "Restaurant_longitude",
        "Delivery_location_latitude",
        "Delivery_location_longitude",
    }
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Required source columns are missing: {sorted(missing_columns)}")
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce")
    valid = frame.loc[frame[TARGET].notna()].copy()
    if len(valid) != 45_593:
        raise AssertionError(f"Expected 45,593 valid targets, found {len(valid):,}.")
    if int(valid[TARGET].gt(SLOW_THRESHOLD).sum()) != 4_037:
        raise AssertionError("The fixed >40-minute slow count differs from Step 5.1.")
    return valid


def category_label(value: object) -> object:
    """Render numeric categorical labels without a trailing decimal."""
    if pd.isna(value):
        return pd.NA
    number = pd.to_numeric(value, errors="coerce")
    if pd.notna(number) and float(number).is_integer():
        return str(int(number))
    return str(value)


def group_counts(
    frame: pd.DataFrame,
    dimension: str,
    order: tuple[str, ...],
) -> dict[str, tuple[int, int]]:
    """Return ordered category count and slow-count pairs."""
    values = frame[dimension].map(category_label)
    eligible = values.notna() & frame[TARGET].notna()
    result: dict[str, tuple[int, int]] = {}
    for category in order:
        mask = eligible & values.eq(category)
        count = int(mask.sum())
        result[category] = (count, int(frame.loc[mask, TARGET].gt(SLOW_THRESHOLD).sum()))
    return result


def two_way_counts(
    frame: pd.DataFrame,
    row_dimension: str,
    row_order: tuple[str, ...],
    column_dimension: str,
    column_order: tuple[str, ...],
) -> dict[tuple[str, str], tuple[int, int]]:
    """Return observed two-way cell count and slow-count pairs."""
    rows = frame[row_dimension].map(category_label)
    columns = frame[column_dimension].map(category_label)
    eligible = rows.notna() & columns.notna() & frame[TARGET].notna()
    result: dict[tuple[str, str], tuple[int, int]] = {}
    for row in row_order:
        for column in column_order:
            mask = eligible & rows.eq(row) & columns.eq(column)
            count = int(mask.sum())
            result[(row, column)] = (
                count,
                int(frame.loc[mask, TARGET].gt(SLOW_THRESHOLD).sum()),
            )
    return result


def validate_pairs(
    actual: dict[object, tuple[int, int]],
    expected: dict[object, tuple[int, int]],
    visualization_id: str,
) -> None:
    """Stop before charting if any plotted denominator or numerator differs."""
    if actual != expected:
        mismatches = {
            key: (expected.get(key), actual.get(key))
            for key in expected.keys() | actual.keys()
            if expected.get(key) != actual.get(key)
        }
        raise AssertionError(
            f"{visualization_id} source metrics differ from its report: {mismatches}"
        )


def percent_table(
    pairs: dict[str, tuple[int, int]],
) -> pd.DataFrame:
    rows = [
        {
            "category": category,
            "count": count,
            "slow": slow,
            "rate": slow / count if count else np.nan,
        }
        for category, (count, slow) in pairs.items()
    ]
    return pd.DataFrame(rows)


def haversine_km(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Use the validated Step 5.8 coordinate bounds and Haversine formula."""
    columns = (
        "Restaurant_latitude",
        "Restaurant_longitude",
        "Delivery_location_latitude",
        "Delivery_location_longitude",
    )
    coordinates = frame.loc[:, columns].apply(pd.to_numeric, errors="coerce")
    valid = coordinates.notna().all(axis=1)
    valid &= coordinates["Restaurant_latitude"].between(-90, 90)
    valid &= coordinates["Delivery_location_latitude"].between(-90, 90)
    valid &= coordinates["Restaurant_longitude"].between(-180, 180)
    valid &= coordinates["Delivery_location_longitude"].between(-180, 180)
    radians = np.radians(coordinates)
    lat_delta = radians["Delivery_location_latitude"] - radians["Restaurant_latitude"]
    lon_delta = radians["Delivery_location_longitude"] - radians["Restaurant_longitude"]
    haversine_a = (
        np.sin(lat_delta / 2.0) ** 2
        + np.cos(radians["Restaurant_latitude"])
        * np.cos(radians["Delivery_location_latitude"])
        * np.sin(lon_delta / 2.0) ** 2
    ).clip(0.0, 1.0)
    distance = EARTH_RADIUS_KM * 2.0 * np.arcsin(np.sqrt(haversine_a))
    return pd.Series(distance, index=frame.index), valid


def strict_time_band(value: object) -> str | None:
    """Apply the validated strict HH:MM:SS parser and Step 5.7 boundaries."""
    if pd.isna(value):
        return None
    text = str(value)
    if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d", text) is None:
        return None
    hour = int(text[:2])
    if hour <= 5:
        return "Night"
    if hour <= 11:
        return "Morning"
    if hour <= 16:
        return "Afternoon"
    if hour <= 20:
        return "Evening"
    return "Late Night"


def prepare_core_data(
    frame: pd.DataFrame,
) -> dict[str, dict[object, tuple[int, int]]]:
    """Calculate chart-driving values and compare them with report values."""
    expected: dict[str, dict[object, tuple[int, int]]] = {
        "V02": {
            "High": (4425, 280),
            "Jam": (14143, 2830),
            "Low": (15477, 214),
            "Medium": (10947, 659),
        },
        "V03": {
            "0": (14095, 640),
            "1": (28159, 2084),
            "2": (1985, 908),
            "3": (361, 361),
        },
        "V04": {
            "Urban": (10136, 483),
            "Metropolitan": (34093, 3353),
            "Semi-Urban": (164, 164),
        },
        "V05": {
            "Night": (430, 11),
            "Morning": (7718, 104),
            "Afternoon": (4049, 164),
            "Evening": (17892, 2367),
            "Late Night": (13773, 1227),
        },
        "V06": {
            "0-1 km": (0, 0),
            "1-2 km": (4074, 67),
            "2-3 km": (526, 8),
            "3-5 km": (7564, 140),
            "5-10 km": (12186, 371),
            "10-15 km": (12178, 1974),
            "15+ km": (9065, 1477),
        },
    }
    actual: dict[str, dict[object, tuple[int, int]]] = {
        "V02": group_counts(frame, "Road_traffic_density", TRAFFIC_ORDER),
        "V03": group_counts(
            frame,
            "multiple_deliveries",
            ("0", "1", "2", "3"),
        ),
        "V04": group_counts(
            frame,
            "City",
            ("Urban", "Metropolitan", "Semi-Urban"),
        ),
    }

    time_bands = frame["Time_Orderd"].map(strict_time_band)
    time_frame = frame.assign(_time_band=time_bands)
    actual["V05"] = group_counts(time_frame, "_time_band", TIME_BANDS)

    distances, coordinate_valid = haversine_km(frame)
    distance_band = pd.cut(
        distances,
        bins=[0, 1, 2, 3, 5, 10, 15, np.inf],
        labels=DISTANCE_BANDS,
        right=False,
        include_lowest=True,
        ordered=False,
    ).astype("object")
    distance_frame = frame.loc[coordinate_valid].assign(
        _distance_band=distance_band.loc[coordinate_valid]
    )
    actual["V06"] = group_counts(distance_frame, "_distance_band", DISTANCE_BANDS)

    actual["V07"] = two_way_counts(
        frame,
        "Weatherconditions",
        WEATHER_ORDER,
        "Road_traffic_density",
        TRAFFIC_ORDER,
    )
    expected["V07"] = {
        ("conditions Cloudy", "High"): (744, 0),
        ("conditions Cloudy", "Jam"): (2349, 821),
        ("conditions Cloudy", "Low"): (2605, 72),
        ("conditions Cloudy", "Medium"): (1838, 225),
        ("conditions Fog", "High"): (776, 0),
        ("conditions Fog", "Jam"): (2429, 860),
        ("conditions Fog", "Low"): (2597, 77),
        ("conditions Fog", "Medium"): (1852, 214),
        ("conditions Sandstorms", "High"): (701, 57),
        ("conditions Sandstorms", "Jam"): (2399, 339),
        ("conditions Sandstorms", "Low"): (2609, 0),
        ("conditions Sandstorms", "Medium"): (1786, 78),
        ("conditions Stormy", "High"): (733, 52),
        ("conditions Stormy", "Jam"): (2323, 306),
        ("conditions Stormy", "Low"): (2699, 0),
        ("conditions Stormy", "Medium"): (1831, 67),
        ("conditions Sunny", "High"): (735, 120),
        ("conditions Sunny", "Jam"): (2289, 152),
        ("conditions Sunny", "Low"): (2475, 65),
        ("conditions Sunny", "Medium"): (1785, 0),
        ("conditions Windy", "High"): (735, 50),
        ("conditions Windy", "Jam"): (2351, 351),
        ("conditions Windy", "Low"): (2484, 0),
        ("conditions Windy", "Medium"): (1852, 75),
    }
    distance_traffic = two_way_counts(
        distance_frame,
        "_distance_band",
        DISTANCE_BANDS,
        "Road_traffic_density",
        TRAFFIC_ORDER,
    )
    actual["V08"] = distance_traffic
    expected["V08"] = {
        ("0-1 km", "High"): (0, 0),
        ("0-1 km", "Jam"): (0, 0),
        ("0-1 km", "Low"): (0, 0),
        ("0-1 km", "Medium"): (0, 0),
        ("1-2 km", "High"): (972, 67),
        ("1-2 km", "Jam"): (0, 0),
        ("1-2 km", "Low"): (3058, 0),
        ("1-2 km", "Medium"): (0, 0),
        ("2-3 km", "High"): (128, 8),
        ("2-3 km", "Jam"): (0, 0),
        ("2-3 km", "Low"): (396, 0),
        ("2-3 km", "Medium"): (0, 0),
        ("3-5 km", "High"): (885, 47),
        ("3-5 km", "Jam"): (1642, 92),
        ("3-5 km", "Low"): (3773, 0),
        ("3-5 km", "Medium"): (1185, 0),
        ("5-10 km", "High"): (2415, 155),
        ("5-10 km", "Jam"): (3484, 210),
        ("5-10 km", "Low"): (2273, 0),
        ("5-10 km", "Medium"): (3890, 0),
        ("10-15 km", "High"): (0, 0),
        ("10-15 km", "Jam"): (5213, 1435),
        ("10-15 km", "Low"): (3412, 121),
        ("10-15 km", "Medium"): (3440, 401),
        ("15+ km", "High"): (25, 3),
        ("15+ km", "Jam"): (3804, 1093),
        ("15+ km", "Low"): (2565, 93),
        ("15+ km", "Medium"): (2432, 258),
    }
    for visualization_id, pairs in actual.items():
        validate_pairs(pairs, expected[visualization_id], visualization_id)

    if int(frame[TARGET].min()) != 10 or int(frame[TARGET].max()) != 54:
        raise AssertionError("V01 target range differs from the overall report.")
    return actual


def style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)


def save_figure(fig: plt.Figure, filename: str) -> str:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / filename
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if not path.is_file() or path.stat().st_size < 10_000:
        raise AssertionError(f"Chart output is missing or unexpectedly small: {path}")
    return f"outputs/charts/{filename}"


def draw_rate_bars(
    pairs: dict[str, tuple[int, int]],
    order: tuple[str, ...],
    title: str,
    filename: str,
) -> str:
    stats = percent_table(pairs).set_index("category").loc[list(order)]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    positions = np.arange(len(order))
    bars = ax.barh(
        positions,
        stats["rate"].to_numpy() * 100,
        color=COLOR,
        height=0.64,
    )
    ax.set_yticks(positions, labels=order)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Slow-delivery rate (%)")
    ax.set_title(title, loc="left", color=DARK, weight="bold", pad=15)
    style_axis(ax)
    for bar, (_, row) in zip(bars, stats.iterrows(), strict=True):
        label = f'{row["rate"]:.2%}  ({int(row["slow"]):,}/{int(row["count"]):,})'
        if bar.get_width() >= 85:
            x_position = bar.get_width() - 1
            alignment = "right"
            color = "white"
        else:
            x_position = bar.get_width() + 1
            alignment = "left"
            color = DARK
        ax.text(
            x_position,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha=alignment,
            fontsize=9,
            color=color,
        )
    fig.text(
        0.12,
        0.025,
        "Slow means delivery time strictly greater than the fixed 40-minute threshold.",
        fontsize=8.5,
        color="#52636b",
    )
    fig.tight_layout(rect=(0.08, 0.06, 1, 1))
    return save_figure(fig, filename)


def draw_heatmap(
    pairs: dict[tuple[str, str], tuple[int, int]],
    rows: tuple[str, ...],
    columns: tuple[str, ...],
    title: str,
    filename: str,
    *,
    mask_below_minimum: bool = False,
    annotate_small: bool = False,
) -> str:
    rates = np.full((len(rows), len(columns)), np.nan, dtype="float64")
    labels: list[list[str]] = [["" for _ in columns] for _ in rows]
    for row_index, row in enumerate(rows):
        for column_index, column in enumerate(columns):
            count, slow = pairs[(row, column)]
            if count:
                if not mask_below_minimum or count >= MIN_GROUP_SIZE:
                    rates[row_index, column_index] = 100 * slow / count
                    labels[row_index][column_index] = (
                        f"{100 * slow / count:.1f}%\nn={count:,}"
                    )
                elif annotate_small:
                    labels[row_index][column_index] = f"n={count:,}\n<30"
            else:
                labels[row_index][column_index] = "n=0"
    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#e9eef1")
    fig, ax = plt.subplots(figsize=(10, max(5.8, 0.72 * len(rows) + 1.7)))
    image = ax.imshow(
        np.ma.masked_invalid(rates),
        aspect="auto",
        cmap=cmap,
        norm=Normalize(vmin=0, vmax=100),
    )
    ax.set_xticks(np.arange(len(columns)), labels=columns)
    ax.set_yticks(np.arange(len(rows)), labels=rows)
    ax.set_title(title, loc="left", color=DARK, weight="bold", pad=15)
    ax.set_xlabel("Road traffic density" if "traffic" in filename else "")
    ax.tick_params(length=0)
    ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for row_index, row_labels in enumerate(labels):
        for column_index, label in enumerate(row_labels):
            if label:
                ax.text(
                    column_index,
                    row_index,
                    label,
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=DARK,
                )
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.035)
    colorbar.set_label("Slow-delivery rate (%)")
    fig.text(
        0.1,
        0.025,
        "Observational association. Slow means delivery time >40 minutes; cells below n=30 are not compared."
        if mask_below_minimum
        else "Observational association. Slow means delivery time >40 minutes.",
        fontsize=8.2,
        color="#52636b",
    )
    fig.tight_layout(rect=(0.06, 0.06, 0.98, 1))
    return save_figure(fig, filename)


def write_validation(rows: list[list[str]]) -> None:
    lines = [
        "# Visualization Validation",
        "",
        "Charts are generated from `data/processed/train_clean.csv` with Pandas and Matplotlib. "
        "The fixed slow rule is `Time_taken(min) > 40`; the established minimum is 30 records.",
        "",
        "| Visualization ID | Chart filename | Source analysis | Metric used | Validation status | Caveat |",
        "|---|---|---|---|---|---|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.append("")
    VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text("\n".join(lines), encoding="utf-8")


def make_core_charts(
    frame: pd.DataFrame,
    actual: dict[str, dict[object, tuple[int, int]]],
) -> list[list[str]]:
    validation: list[list[str]] = []

    fig, ax = plt.subplots(figsize=(10, 5.8))
    times = frame[TARGET].to_numpy(dtype="float64")
    ax.hist(
        times,
        bins=np.arange(9.5, 55.5, 1),
        color=COLOR,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.axvline(
        26,
        color=DARK,
        linewidth=1.5,
        linestyle=":",
        label="Median: 26 min",
    )
    ax.axvline(
        SLOW_THRESHOLD,
        color=ACCENT,
        linewidth=2,
        linestyle="--",
        label="Fixed threshold: slow if >40 min",
    )
    ax.set_xlabel("Delivery time (minutes)")
    ax.set_ylabel("Delivery count")
    ax.set_title("Distribution of Delivery Times", loc="left", color=DARK, weight="bold", pad=15)
    ax.legend(frameon=False, loc="upper right")
    style_axis(ax)
    ax.text(
        0.99,
        0.86,
        f"n={len(times):,}  |  median={np.median(times):.0f} min  |  P90=40 min",
        transform=ax.transAxes,
        ha="right",
        color=DARK,
        fontsize=9,
    )
    fig.tight_layout()
    filename = "V01_delivery_time_distribution.png"
    save_figure(fig, filename)
    validation.append(
        ["V01", filename, "Step 5.1 overall", "Delivery-time count distribution", "VALIDATED",
         "45,593 targets; 10–54 min; fixed line at 40; slow is strictly >40."]
    )

    chart_sources = (
        ("V02", TRAFFIC_ORDER, "Slow-Delivery Rate by Traffic Category",
         "V02_traffic_performance.png", "Step 5.2 traffic", "Slow rate; slow count / n",
         "601 valid targets have missing traffic."),
        ("V03", ("0", "1", "2", "3"), "Slow-Delivery Rate by Multiple-Delivery Category",
         "V03_multiple_deliveries.png", "Step 5.6 courier / multiple deliveries",
         "Slow rate; slow count / n", "Category labels are categorical; no continuous trend is fitted."),
        ("V04", ("Urban", "Metropolitan", "Semi-Urban"), "Slow-Delivery Rate by City",
         "V04_city_performance.png", "Step 5.4 city", "Slow rate; slow count / n",
         "Semi-Urban has n=164; all included city groups meet n>=30."),
        ("V05", TIME_BANDS, "Slow-Delivery Rate by Order-Time Band",
         "V05_order_time_bands.png", "Step 5.7 time", "Slow rate; slow count / n",
         "Strict HH:MM:SS parsing; 1,731 order times are missing or invalid."),
        ("V06", DISTANCE_BANDS, "Slow-Delivery Rate by Approximate Distance Band",
         "V06_distance_bands.png", "Step 5.8 distance", "Slow rate; slow count / n",
         "Haversine straight-line distance; extreme 15+ km records are retained."),
    )
    for visualization_id, order, title, filename, source, metric, caveat in chart_sources:
        saved = draw_rate_bars(actual[visualization_id], order, title, filename)
        validation.append(
            [visualization_id, Path(saved).name, source, metric, "VALIDATED", caveat]
        )

    weather_saved = draw_heatmap(
        actual["V07"],
        WEATHER_ORDER,
        TRAFFIC_ORDER,
        "Weather × Traffic: Slow-Delivery Rate",
        "V07_weather_traffic.png",
    )
    validation.append(
        ["V07", Path(weather_saved).name, "Step 6.4 Weather × Traffic",
         "Slow-delivery rate by observed cell", "VALIDATED",
         "All 24 cells meet n>=30; observational association, not causation."]
    )
    distance_saved = draw_heatmap(
        actual["V08"],
        DISTANCE_BANDS,
        TRAFFIC_ORDER,
        "Distance × Traffic: Slow-Delivery Rate",
        "V08_distance_traffic.png",
        mask_below_minimum=True,
        annotate_small=True,
    )
    validation.append(
        ["V08", Path(distance_saved).name, "Step 6.3 Distance × Traffic",
         "Slow-delivery rate by qualifying cell", "VALIDATED",
         "Cells below n=30 are uncolored; distance is Haversine straight-line and observational."]
    )
    return validation


def main() -> None:
    frame = read_source()
    actual = prepare_core_data(frame)
    validation = make_core_charts(frame, actual)
    write_validation(validation)
    print(f"Generated {len(validation)} CORE charts in {CHART_DIR}.")
    print(f"Wrote validation results to {VALIDATION_PATH}.")


if __name__ == "__main__":
    main()
