"""Shared helpers for generating member B's five interactive views.

Loads the clean dataset, derives the Season field, and provides the shared
attribute/colour definitions used across all five views so the visual encodings
remain consistent (a requirement for the Task 1 similarity analysis).
"""
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
CLEAN_FILE = PROJECT_DIR / "output" / "air_quality_clean.csv"
VIEWS_DIR = PROJECT_DIR / "output" / "views"

# The 9 analysis attributes agreed by the group (see data_processing.py).
NUMERIC_ATTRIBUTES = [
    "CO(GT)",
    "PT08.S1(CO)",
    "C6H6(GT)",
    "PT08.S2(NMHC)",
    "NOx(GT)",
    "NO2(GT)",
    "T",
    "RH",
    "AH",
]

# Display labels (with units) used as axis titles in every view.
ATTR_LABELS = {
    "CO(GT)": "CO (mg/m³)",
    "PT08.S1(CO)": "CO sensor response",
    "C6H6(GT)": "Benzene (µg/m³)",
    "PT08.S2(NMHC)": "NMHC sensor response",
    "NOx(GT)": "NOx (ppb)",
    "NO2(GT)": "NO₂ (µg/m³)",
    "T": "Temperature (°C)",
    "RH": "Relative Humidity (%)",
    "AH": "Absolute Humidity (g/m³)",
}

# Season mapping from month number (meteorological seasons).
_SEASON_MAP = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}

SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]
SEASON_COLORS = {
    "Winter": "#4C78A8",   # blue
    "Spring": "#54A24B",   # green
    "Summer": "#F58518",   # orange
    "Autumn": "#B279A2",   # purple
}

# Heatmap colour scales per attribute. Pollutants default to Inferno;
# temperature and humidity use scales that match their intuitive semantics.
_COLORSCALE = {
    "T": "RdBu_r",
    "RH": "Blues",
    "AH": "Blues",
}


def colorscale_for(attr: str) -> str:
    return _COLORSCALE.get(attr, "Inferno")


def load_data() -> pd.DataFrame:
    """Load the clean dataset and add the ordered Season field."""
    df = pd.read_csv(CLEAN_FILE, parse_dates=["DateTime"])
    df["Season"] = df["Month"].map(_SEASON_MAP)
    df["Season"] = pd.Categorical(df["Season"], categories=SEASON_ORDER, ordered=True)
    return df


def save(fig, name: str) -> Path:
    """Write a Plotly figure as a self-contained interactive HTML file."""
    VIEWS_DIR.mkdir(exist_ok=True)
    path = VIEWS_DIR / f"{name}.html"
    fig.write_html(path, include_plotlyjs=True, full_html=True)
    return path


def season_colorscale(alpha: float = 1.0) -> list:
    """Discrete colour scale for season-coded numeric colour arrays.

    Returns a *stepped* scale: each season occupies a solid band with hard
    edges (duplicate colours at the band boundaries), so the colourbar reads as
    categorical instead of a continuous gradient. ``alpha`` < 1 makes
    overlapping lines/points blend, so dense regions read as density instead of
    an opaque tangle (used for the Parallel Coordinates view).
    """
    n = len(SEASON_ORDER)

    def _rgba(hexc, a):
        h = hexc.lstrip("#")
        return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"

    colors = [_rgba(SEASON_COLORS[s], alpha) for s in SEASON_ORDER]
    scale = []
    for i in range(n):
        scale.append([i / n, colors[i]])
        scale.append([(i + 1) / n, colors[i]])
    return scale


def season_highlight_colorscale(rest_opacity: float = 0.18) -> list:
    """Colour scale for the Parallel Coordinates selection highlight.

    Maps -1 (unselected) to a dim grey and 0..n-1 (season codes) to the
    full-opacity season colours. Used with ``cmin=-1`` / ``cmax=n-1`` so a
    single Parcoords trace can draw faded context lines and season-coloured
    selected lines at once.
    """
    n = len(SEASON_ORDER)

    def _rgba(hexc, a):
        h = hexc.lstrip("#")
        return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"

    scale = [[0.0, f"rgba(180, 180, 180, {rest_opacity})"]]
    for i in range(n):
        scale.append([(i + 1) / n, _rgba(SEASON_COLORS[SEASON_ORDER[i]], 1.0)])
    return scale
