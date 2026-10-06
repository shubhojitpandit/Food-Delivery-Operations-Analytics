"""Generate the six SUPPORTING visualizations from validated definitions."""

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
CITY_ORDER = ("Metropolitan", "Semi-Urban", "Urban")
VEHICLE_ORDER = ("bicycle", "electric_scooter", "motorcycle", "scooter")
MULTIPLE_ORDER = ("0", "1", "2", "3")
TIME_BANDS = ("Night", "Morning", "Afternoon", "Evening", "Late Night")
DELAY_BANDS = (
    "0-5 minutes",
    "6-10 minutes",
    "11-15 minutes",
    "16-20 minutes",
    "21-30 minutes",
    "31+ minutes",
)
COLOR = "#287271"
DARK = "#264653"
GRID = "#d9e2e7"


def read_source() -> pd.DataFrame:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Cleaned training data not found: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    required = {
        TARGET,
        "Type_of_vehicle",
        "Vehicle_condition",
        "City",
        "Road_traffic_density",
        "Time_Orderd",
        "Time_Order_picked",
        "multiple_deliveries",
    }
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Required source columns are missing: {sorted(missing_columns)}")
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce")
    valid = frame.loc[frame[TARGET].notna()].copy()
    if len(valid) != 45_593 or int(valid[TARGET].gt(SLOW_THRESHOLD).sum()) != 4_037:
        raise AssertionError("Valid targets or fixed slow count differ from Step 5.1.")
    return valid


def category_label(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    number = pd.to_numeric(value, errors="coerce")
    if pd.notna(number) and float(number).is_integer():
        return str(int(number))
    return str(value)


def grouped_pairs(
    frame: pd.DataFrame,
    dimension: str,
    order: tuple[str, ...],
) -> dict[str, tuple[int, int]]:
    values = frame[dimension].map(category_label)
    eligible = values.notna() & frame[TARGET].notna()
    result: dict[str, tuple[int, int]] = {}
    for category in order:
        mask = eligible & values.eq(category)
        result[category] = (
            int(mask.sum()),
            int(frame.loc[mask, TARGET].gt(SLOW_THRESHOLD).sum()),
        )
    return result


def two_way_pairs(
    frame: pd.DataFrame,
    row_dimension: str,
    row_order: tuple[str, ...],
    column_dimension: str,
    column_order: tuple[str, ...],
) -> dict[tuple[str, str], tuple[int, int]]:
    row_values = frame[row_dimension].map(category_label)
    column_values = frame[column_dimension].map(category_label)
    eligible = row_values.notna() & column_values.notna() & frame[TARGET].notna()
    result: dict[tuple[str, str], tuple[int, int]] = {}
    for row in row_order:
        for column in column_order:
            mask = eligible & row_values.eq(row) & column_values.eq(column)
            result[(row, column)] = (
                int(mask.sum()),
                int(frame.loc[mask, TARGET].gt(SLOW_THRESHOLD).sum()),
            )
    return result


def verify(
    actual: dict[object, tuple[int, int]],
    expected: dict[object, tuple[int, int]],
    visualization_id: str,
) -> None:
    if actual != expected:
        mismatches = {
            key: (expected.get(key), actual.get(key))
            for key in expected.keys() | actual.keys()
            if expected.get(key) != actual.get(key)
        }
        raise AssertionError(
            f"{visualization_id} source metrics differ from its report: {mismatches}"
        )


def strict_time_band(value: object) -> str | None:
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


def prepare_supporting_data(
    frame: pd.DataFrame,
) -> tuple[dict[str, dict[object, tuple[int, int]]], dict[str, object]]:
    expected: dict[str, dict[object, tuple[int, int]]] = {
        "V09": {
            "bicycle": (68, 4),
            "electric_scooter": (3814, 181),
            "motorcycle": (26435, 3111),
            "scooter": (15276, 741),
        },
        "V10": {
            "0": (15009, 2556),
            "1": (15030, 724),
            "2": (15034, 712),
            "3": (520, 45),
        },
        "V14": {
            "0-5 minutes": (14564, 1338),
            "6-10 minutes": (14288, 1284),
            "11-15 minutes": (14179, 1227),
            "16-20 minutes": (0, 0),
            "21-30 minutes": (0, 0),
            "31+ minutes": (0, 0),
        },
    }
    actual: dict[str, dict[object, tuple[int, int]]] = {
        "V09": grouped_pairs(frame, "Type_of_vehicle", VEHICLE_ORDER),
        "V10": grouped_pairs(frame, "Vehicle_condition", ("0", "1", "2", "3")),
    }
    actual["V11"] = two_way_pairs(
        frame, "City", CITY_ORDER, "Road_traffic_density", TRAFFIC_ORDER
    )
    expected["V11"] = {
        ("Metropolitan", "High"): (3365, 231),
        ("Metropolitan", "Jam"): (11090, 2321),
        ("Metropolitan", "Low"): (10852, 193),
        ("Metropolitan", "Medium"): (8322, 558),
        ("Semi-Urban", "High"): (17, 17),
        ("Semi-Urban", "Jam"): (135, 135),
        ("Semi-Urban", "Low"): (0, 0),
        ("Semi-Urban", "Medium"): (11, 11),
        ("Urban", "High"): (945, 30),
        ("Urban", "Jam"): (2627, 351),
        ("Urban", "Low"): (4093, 18),
        ("Urban", "Medium"): (2356, 81),
    }
    actual["V12"] = time_traffic_pairs(frame)
    expected["V12"] = {
        ("Night", "High"): (0, 0),
        ("Night", "Jam"): (0, 0),
        ("Night", "Low"): (430, 11),
        ("Night", "Medium"): (0, 0),
        ("Morning", "High"): (1769, 104),
        ("Morning", "Jam"): (0, 0),
        ("Morning", "Low"): (5949, 0),
        ("Morning", "Medium"): (0, 0),
        ("Afternoon", "High"): (2553, 164),
        ("Afternoon", "Jam"): (0, 0),
        ("Afternoon", "Low"): (0, 0),
        ("Afternoon", "Medium"): (1496, 0),
        ("Evening", "High"): (0, 0),
        ("Evening", "Jam"): (8710, 1722),
        ("Evening", "Low"): (0, 0),
        ("Evening", "Medium"): (9182, 645),
        ("Late Night", "High"): (0, 0),
        ("Late Night", "Jam"): (5090, 1026),
        ("Late Night", "Low"): (8683, 201),
        ("Late Night", "Medium"): (0, 0),
    }
    actual["V13"] = two_way_pairs(
        frame, "Type_of_vehicle", VEHICLE_ORDER,
        "multiple_deliveries", MULTIPLE_ORDER,
    )
    expected["V13"] = {
        ("bicycle", "0"): (20, 0),
        ("bicycle", "1"): (43, 3),
        ("bicycle", "2"): (4, 1),
        ("bicycle", "3"): (0, 0),
        ("electric_scooter", "0"): (1262, 31),
        ("electric_scooter", "1"): (2333, 93),
        ("electric_scooter", "2"): (130, 47),
        ("electric_scooter", "3"): (8, 8),
        ("motorcycle", "0"): (7700, 480),
        ("motorcycle", "1"): (16508, 1587),
        ("motorcycle", "2"): (1361, 690),
        ("motorcycle", "3"): (322, 322),
        ("scooter", "0"): (5113, 129),
        ("scooter", "1"): (9275, 401),
        ("scooter", "2"): (490, 170),
        ("scooter", "3"): (31, 31),
    }

    # Exact elapsed delays are fractional minutes; negative direct differences remain excluded.
    order_clock = pd.to_datetime(
        frame["Time_Orderd"].where(
            frame["Time_Orderd"].astype(str).str.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d"
            )
        ),
        format="%H:%M:%S",
        errors="coerce",
    )
    pickup_clock = pd.to_datetime(
        frame["Time_Order_picked"].where(
            frame["Time_Order_picked"].astype(str).str.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d"
            )
        ),
        format="%H:%M:%S",
        errors="coerce",
    )
    delay = (
        (pickup_clock.dt.hour - order_clock.dt.hour) * 60
        + pickup_clock.dt.minute - order_clock.dt.minute
        + (pickup_clock.dt.second - order_clock.dt.second) / 60
    )
    delay = delay.where(order_clock.notna() & pickup_clock.notna() & delay.ge(0))
    labels = pd.cut(
        delay,
        bins=[-np.inf, 5, 10, 15, 20, 30, np.inf],
        labels=DELAY_BANDS,
        right=True,
        ordered=False,
    )
    delay_frame = frame.assign(_delay_band=labels.astype("object"))
    actual["V14"] = grouped_pairs(delay_frame, "_delay_band", DELAY_BANDS)

    for visualization_id, pairs in actual.items():
        verify(pairs, expected[visualization_id], visualization_id)
    return actual, {
        "time_traffic": actual["V12"],
        "vehicle_multiple": actual["V13"],
        "delay_frame": delay_frame,
        "delay": delay,
    }


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
    values = [pairs[category] for category in order]
    rates = [slow / count * 100 for count, slow in values]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    positions = np.arange(len(order))
    bars = ax.barh(positions, rates, color=COLOR, height=0.64)
    ax.set_yticks(positions, labels=order)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Slow-delivery rate (%)")
    ax.set_title(title, loc="left", color=DARK, weight="bold", pad=15)
    style_axis(ax)
    for bar, (count, slow) in zip(bars, values, strict=True):
        ax.text(
            min(bar.get_width() + 1, 78),
            bar.get_y() + bar.get_height() / 2,
            f"{(slow / count if count else 0):.2%}  ({slow:,}/{count:,})",
            va="center",
            ha="left",
            fontsize=9,
            color=DARK,
        )
    fig.text(
        0.12, 0.025,
        "Slow means delivery time strictly greater than the fixed 40-minute threshold.",
        fontsize=8.5, color="#52636b",
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
    qualifying_only: bool = False,
    count_panel: bool = False,
    small_labels: bool = False,
) -> str:
    rates = np.full((len(rows), len(columns)), np.nan, dtype="float64")
    counts = np.zeros((len(rows), len(columns)), dtype="float64")
    labels: list[list[str]] = [["" for _ in columns] for _ in rows]
    for i, row in enumerate(rows):
        for j, column in enumerate(columns):
            count, slow = pairs[(row, column)]
            counts[i, j] = count
            if count >= MIN_GROUP_SIZE:
                rates[i, j] = slow / count * 100
                labels[i][j] = f"{100 * slow / count:.1f}%\nn={count:,}"
            elif count and small_labels:
                labels[i][j] = f"<30\nn={count:,}"
            elif not count:
                labels[i][j] = "—" if qualifying_only else "n=0"

    panels = 2 if count_panel else 1
    fig, axes = plt.subplots(
        1,
        panels,
        figsize=(10, max(5.8, 0.72 * len(rows) + 1.7)),
        squeeze=False,
    )
    rate_ax = axes[0, -1]
    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#e9eef1")
    image = rate_ax.imshow(
        np.ma.masked_invalid(rates),
        aspect="auto",
        cmap=cmap,
        norm=Normalize(vmin=0, vmax=100),
    )
    rate_ax.set_xticks(np.arange(len(columns)), labels=columns)
    rate_ax.set_yticks(np.arange(len(rows)), labels=rows)
    rate_ax.set_title(
        "Slow-delivery rate (%)" if count_panel else "",
        color=DARK,
        weight="bold",
    )
    for i, row_labels in enumerate(labels):
        for j, label in enumerate(row_labels):
            if label:
                cell_rate = rates[i, j]
                text_color = "white" if np.isfinite(cell_rate) and cell_rate >= 75 else DARK
                rate_ax.text(
                    j, i, label, ha="center", va="center", fontsize=8, color=text_color
                )
    for ax in axes[0]:
        ax.tick_params(length=0)
        ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=2)
        ax.tick_params(which="minor", bottom=False, left=False)

    if count_panel:
        count_ax = axes[0, 0]
        count_cmap = plt.get_cmap("Blues").copy()
        count_cmap.set_bad("#e9eef1")
        count_image = count_ax.imshow(counts, aspect="auto", cmap=count_cmap)
        count_ax.set_xticks(np.arange(len(columns)), labels=columns)
        count_ax.set_yticks(np.arange(len(rows)), labels=rows)
        count_ax.set_title("Delivery count", color=DARK, weight="bold")
        for i in range(len(rows)):
            for j in range(len(columns)):
                count_ax.text(
                    j, i, f"{int(counts[i, j]):,}", ha="center", va="center",
                    fontsize=8,
                    color="white" if counts[i, j] > float(np.max(counts)) * 0.55 else DARK,
                )
        fig.colorbar(count_image, ax=count_ax, fraction=0.035, pad=0.03)
    fig.colorbar(image, ax=rate_ax, fraction=0.035, pad=0.03)
    fig.suptitle(title, x=0.08, ha="left", color=DARK, weight="bold", fontsize=14, y=0.98)
    fig.text(
        0.08, 0.025,
        "Only cells with n>=30 are used for rate comparisons. Observational association; no causal inference.",
        fontsize=8.2, color="#52636b",
    )
    fig.tight_layout(rect=(0.04, 0.06, 0.98, 0.94))
    return save_figure(fig, filename)


def append_validation(rows: list[list[str]]) -> None:
    if not VALIDATION_PATH.is_file():
        raise FileNotFoundError(
            "Run python/19_visualize_core.py before the supporting visualizations."
        )
    lines = VALIDATION_PATH.read_text(encoding="utf-8").rstrip().splitlines()
    existing_ids = {line.split("|")[1].strip() for line in lines if line.startswith("| V")}
    for row in rows:
        if row[0] in existing_ids:
            raise ValueError(f"Validation already contains {row[0]}; rerun CORE first.")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    VALIDATION_PATH.write_text("\n".join(lines), encoding="utf-8")


def make_supporting_charts(
    frame: pd.DataFrame,
    actual: dict[str, dict[object, tuple[int, int]]],
) -> list[list[str]]:
    validation: list[list[str]] = []
    bar_charts = (
        ("V09", VEHICLE_ORDER, "Slow-Delivery Rate by Vehicle Type",
         "V09_vehicle_type.png", "Step 5.5 vehicle", "Slow rate; slow count / n",
         "Bicycle n=68; all standalone vehicle categories meet n>=30."),
        ("V10", ("0", "1", "2", "3"), "Slow-Delivery Rate by Vehicle Condition",
         "V10_vehicle_condition.png", "Step 5.5 vehicle condition",
         "Slow rate; slow count / n", "Vehicle-condition labels are categorical, not a quality scale."),
    )
    for visualization_id, order, title, filename, source, metric, caveat in bar_charts:
        path = draw_rate_bars(actual[visualization_id], order, title, filename)
        validation.append(
            [visualization_id, Path(path).name, source, metric, "VALIDATED", caveat]
        )

    city_matrix = actual["V11"]
    city_mean_path = draw_city_mean_heatmap(frame, city_matrix)
    validation.append(
        ["V11", Path(city_mean_path).name, "Step 6.2 City × Traffic",
         "Mean delivery time in qualifying cells", "VALIDATED",
         "Only cells with n>=30 are shaded; subminimum Semi-Urban cells are not compared."]
    )
    time_path = draw_heatmap(
        actual["V12"], TIME_BANDS, TRAFFIC_ORDER,
        "Time × Traffic: Cell Coverage and Slow-Delivery Rate",
        "V12_time_traffic.png",
        count_panel=True,
    )
    validation.append(
        ["V12", Path(time_path).name, "Step 6.7 Time × Traffic",
         "Cell count and qualifying-cell slow rate", "VALIDATED",
         "Exact Step 5.7 time bands; empty combinations are shown as zero, not inferred categories."]
    )
    vehicle_path = draw_heatmap(
        actual["V13"], VEHICLE_ORDER, MULTIPLE_ORDER,
        "Vehicle × Multiple Deliveries: Slow-Delivery Rate",
        "V13_vehicle_multiple_deliveries.png",
        qualifying_only=True,
        small_labels=True,
    )
    validation.append(
        ["V13", Path(vehicle_path).name, "Step 6.5 Vehicle × Multiple Deliveries",
         "Slow rate for cells meeting n>=30", "VALIDATED",
         "Subminimum cells are shown only as counts, not rate comparisons; category labels remain categorical."]
    )

    delay_pairs = actual["V14"]
    delay_path = draw_count_bars(
        delay_pairs,
        DELAY_BANDS,
        "Valid Non-Negative Order-to-Pickup Delay Distribution",
        "V14_pickup_delay_bands.png",
    )
    validation.append(
        ["V14", Path(delay_path).name, "Step 5.7 pickup delay",
         "Delivery count by established delay band", "VALIDATED",
         "Only valid non-negative direct same-day differences; 831 ambiguous negative differences excluded."]
    )
    return validation


def draw_city_mean_heatmap(
    frame: pd.DataFrame,
    pairs: dict[tuple[str, str], tuple[int, int]],
) -> str:
    """Plot validated mean minutes only in the qualifying City × Traffic cells."""
    city_values = {
        ("Metropolitan", "High"): (3365, 28.10846954),
        ("Metropolitan", "Jam"): (11090, 31.91009919),
        ("Metropolitan", "Low"): (10852, 22.12965352),
        ("Metropolitan", "Medium"): (8322, 27.611031),
        ("Semi-Urban", "Jam"): (135, 49.88888889),
        ("Urban", "High"): (945, 24.12592593),
        ("Urban", "Jam"): (2627, 27.74343357),
        ("Urban", "Low"): (4093, 19.24407525),
        ("Urban", "Medium"): (2356, 23.73089983),
    }
    means = np.full((len(CITY_ORDER), len(TRAFFIC_ORDER)), np.nan, dtype="float64")
    counts = np.full_like(means, np.nan)
    city_labels = frame["City"].map(category_label)
    traffic_labels = frame["Road_traffic_density"].map(category_label)
    for i, city in enumerate(CITY_ORDER):
        for j, traffic in enumerate(TRAFFIC_ORDER):
            key = (city, traffic)
            count, _ = pairs[key]
            if key in city_values:
                expected_count, expected_mean = city_values[key]
                if count != expected_count:
                    raise AssertionError(f"V11 count mismatch in {key}.")
                mask = city_labels.eq(city) & traffic_labels.eq(traffic)
                mean = float(frame.loc[mask, TARGET].mean())
                if not np.isclose(mean, expected_mean, atol=1e-8, rtol=1e-10):
                    raise AssertionError(
                        f"V11 mean differs from Step 6.2 in {key}: "
                        f"{mean} != {expected_mean}"
                    )
                means[i, j] = mean
                counts[i, j] = count
            elif count >= MIN_GROUP_SIZE:
                raise AssertionError(f"Unlisted qualifying V11 cell: {key}.")

    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#e9eef1")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    image = ax.imshow(np.ma.masked_invalid(means), aspect="auto", cmap=cmap, vmin=0)
    ax.set_xticks(np.arange(len(TRAFFIC_ORDER)), labels=TRAFFIC_ORDER)
    ax.set_yticks(np.arange(len(CITY_ORDER)), labels=CITY_ORDER)
    ax.set_title("City × Traffic: Mean Delivery Time", loc="left", color=DARK, weight="bold", pad=15)
    ax.tick_params(length=0)
    for i in range(len(CITY_ORDER)):
        for j in range(len(TRAFFIC_ORDER)):
            if np.isfinite(means[i, j]):
                ax.text(
                    j, i, f"{means[i, j]:.1f} min\nn={int(counts[i, j]):,}",
                    ha="center", va="center", fontsize=8.5, color=DARK,
                )
            else:
                ax.text(j, i, "not compared", ha="center", va="center", fontsize=7.5, color="#52636b")
    ax.set_xticks(np.arange(-0.5, len(TRAFFIC_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(CITY_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.035)
    colorbar.set_label("Mean delivery time (minutes)")
    fig.text(
        0.1, 0.025,
        "Only observed cells with n>=30 are shown; blank cells are not compared.",
        fontsize=8.3, color="#52636b",
    )
    fig.tight_layout(rect=(0.05, 0.06, 0.98, 1))
    path = CHART_DIR / "V11_city_traffic.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if not path.is_file() or path.stat().st_size < 10_000:
        raise AssertionError(f"V11 chart output is missing or unexpectedly small: {path}")
    return f"outputs/charts/{path.name}"


def draw_count_bars(
    pairs: dict[str, tuple[int, int]],
    order: tuple[str, ...],
    title: str,
    filename: str,
) -> str:
    counts = [pairs[category][0] for category in order]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    positions = np.arange(len(order))
    bars = ax.barh(positions, counts, color=COLOR, height=0.64)
    ax.set_yticks(positions, labels=order)
    ax.invert_yaxis()
    ax.set_xlabel("Delivery count")
    ax.set_title(title, loc="left", color=DARK, weight="bold", pad=15)
    style_axis(ax)
    ax.set_xlim(0, max(counts) * 1.18 if max(counts) else 1)
    for bar, count in zip(bars, counts, strict=True):
        ax.text(
            max(bar.get_width() + max(counts) * 0.015, max(counts) * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{count:,}",
            va="center",
            fontsize=9,
            color=DARK,
        )
    fig.text(
        0.12, 0.025,
        "Only valid, non-negative direct same-day pickup delays are included; no midnight rollover is assumed.",
        fontsize=8.1, color="#52636b",
    )
    fig.tight_layout(rect=(0.08, 0.06, 1, 1))
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / filename
    fig.savefig(path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if not path.is_file() or path.stat().st_size < 10_000:
        raise AssertionError(f"Chart output is missing or unexpectedly small: {path}")
    return f"outputs/charts/{filename}"


def append_validation(rows: list[list[str]]) -> None:
    if not VALIDATION_PATH.is_file():
        raise FileNotFoundError(
            "Run python/19_visualize_core.py before the supporting visualizations."
        )
    lines = VALIDATION_PATH.read_text(encoding="utf-8").rstrip().splitlines()
    existing_ids = {line.split("|")[1].strip() for line in lines if line.startswith("| V")}
    for row in rows:
        if row[0] in existing_ids:
            raise ValueError(f"Validation already contains {row[0]}; rerun CORE first.")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    VALIDATION_PATH.write_text("\n".join(lines), encoding="utf-8")


def time_traffic_pairs(frame: pd.DataFrame) -> dict[tuple[str, str], tuple[int, int]]:
    bands = frame["Time_Orderd"].map(strict_time_band)
    categorized = frame.assign(_time_band=bands)
    return two_way_pairs(
        categorized, "_time_band", TIME_BANDS, "Road_traffic_density", TRAFFIC_ORDER
    )


def main() -> None:
    frame = read_source()
    actual, _ = prepare_supporting_data(frame)
    validation = make_supporting_charts(frame, actual)
    append_validation(validation)
    print(f"Generated {len(validation)} SUPPORTING charts in {CHART_DIR}.")
    print(f"Appended validation results to {VALIDATION_PATH}.")


if __name__ == "__main__":
    main()
