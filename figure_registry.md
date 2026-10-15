# Figure Registry — Air Quality Visualisation (Group Assignment)

Maintained by: **Member B**

This registry documents every interactive visualisation produced for the
assignment. Each figure has a stable ID used across the report, the code
(`generate_views.py` / `app.py`) and the HTML files in `output/views/`.

## 0. Primary interactive tool (linked brushing)

The five views are integrated into a single **Dash application** (`app.py`)
that provides **cross-view linked brushing**: selecting time periods in the
Scatter plot or SPLOM (box/lasso), or brushing an axis in the Parallel
Coordinates view, highlights the same time periods across all other views.
This lets a group of hours be traced from one attribute space to another and
to the Time Grid / Weekday Heatmap.

| Item | Value |
|------|-------|
| File | `app.py` |
| Run | `python app.py` → open http://127.0.0.1:8050 |
| Shared selection | `dcc.Store` holds the selected row ids |
| Selection sources | Scatter (box/lasso), SPLOM (box/lasso), Parallel Coordinates (axis brush) |
| Filters | Season checklist |
| Reset | "Reset selection" button clears the selection |

The standalone `*.html` files below are single-view exports of the same five
views (same encodings), kept for reference and for embedding in the report.

## 1. Overview

| Figure ID | View | Chart type | Primary encoding | Interaction | Supports | File |
|-----------|------|------------|------------------|-------------|----------|------|
| V1 | Time Grid | Heatmap | day × hour → colour (attribute) | attribute dropdown, hover | Task 1 grouping / temporal | `1_time_grid.html` |
| V2 | Parallel Coordinates | Parallel coordinates | 9 axes → line; colour = season | axis brushing | Task 1 grouping attributes | `2_parallel_coords.html` |
| V3 | SPLOM | Scatterplot matrix | pairwise scatter over 5 default variables; colour = season | box/lasso select, hover, variable selector | Task 1 visual group discovery / correlation | `3_splom.html` |
| V4 | Scatter Plot | Scatter | x vs y (both selectable; default T vs CO(GT)); colour = season | x/y-attribute dropdowns, legend toggle | Task 1 environmental vs pollutant | `4_scatter.html` |
| V5 | Weekday Heatmap | Heatmap | weekday × hour → colour (attribute mean or selected count) | attribute dropdown, mean/count toggle, hover | Task 1 daily/weekly pattern | `5_weekday_heatmap.html` |

## 2. Shared visual encodings (used consistently across all views)

**Attributes (9 numeric + DateTime):**

| Attribute | Label | Missing (%) |
|-----------|-------|-------------|
| CO(GT) | CO (mg/m³) | 18.0 |
| PT08.S1(CO) | CO sensor response | 3.9 |
| C6H6(GT) | Benzene (µg/m³) | 3.9 |
| PT08.S2(NMHC) | NMHC sensor response | 3.9 |
| NOx(GT) | NOx (ppb) | 17.5 |
| NO2(GT) | NO₂ (µg/m³) | 17.6 |
| T | Temperature (°C) | 3.9 |
| RH | Relative Humidity (%) | 3.9 |
| AH | Absolute Humidity (g/m³) | 3.9 |

**Season colour scale** (meteorological seasons, used for all colour-by-season views):

| Season | Months | Colour |
|--------|--------|--------|
| Winter | Dec–Feb | `#4C78A8` (blue) |
| Spring | Mar–May | `#54A24B` (green) |
| Summer | Jun–Aug | `#F58518` (orange) |
| Autumn | Sep–Nov | `#B279A2` (purple) |

**Heatmap colour scales:** pollutants use `Inferno`; Temperature uses `RdBu_r`
(cold → hot); RH and AH use `Blues`.

## 3. Per-figure detail

### V1 — Time Grid
- **Purpose:** reveal hourly/daily/seasonal pollution regimes as horizontal
  (season) and vertical (rush-hour) bands.
- **Encoding:** x = hour of day (0–23), y = date (391 days), colour = value of
  the selected attribute. Missing values appear as gaps (white), which also
  surfaces data-quality issues (e.g. the 03:00 NOx gap).
- **Interaction:** dropdown switches the coloured attribute among all 9.
- **Notes:** a common 391-day grid is used for every attribute so the y-axis
  stays aligned when switching.

### V2 — Parallel Coordinates
- **Purpose:** identify which attributes separate the seasonal pollution groups.
- **Encoding:** one polyline per complete case (6,941 rows with no missing
  value across all 9 attributes); line colour = season.
- **Interaction:** drag along any axis to brush a value range and highlight the
  corresponding polylines.

### V3 — SPLOM (Scatterplot Matrix)
- **Purpose:** visually discover tight groupings of time periods and pairwise
  correlations (e.g. CO vs Benzene vs Temperature).
- **Encoding:** pairwise scatter matrix over a selectable subset of the 9
  attributes, defaulting to 5 (CO, Benzene, NOx, NO2, Temperature); off-diagonal
  cells are pairwise scatterplots coloured by season; diagonal cells show the
  attribute name. The matrix is down-sampled to 2,000 points for responsive
  WebGL (`Scattergl`) interaction, with currently selected points force-included
  so a selection made elsewhere is never invisible.
- **Interaction:** box/lasso select, hover, per-plot zoom, variable selector.

### V4 — Scatter Plot
- **Purpose:** show how pollutants relate to each other and to temperature across
  seasons, supporting both the "winter high-NOx" seasonal grouping (T vs NOx)
  and the "elevated CO-NOx" rush-hour grouping (CO vs NOx).
- **Encoding:** x = selectable attribute (default T); y = selectable attribute
  (default CO(GT)); colour = season.
- **Interaction:** dropdowns switch the x attribute (any of the 9) and the y
  attribute (any of the remaining 8 — all but Temperature); legend toggles
  seasons.

### V5 — Weekday Heatmap
- **Purpose:** reveal the weekly cycle (weekday rush hours vs weekend) for each
  attribute, and — in count mode — where a brushed/lassoed group of hours falls
  across the week.
- **Encoding:** x = hour of day, y = weekday (Mon–Sun); colour = either the mean
  of the selected attribute (means skip missing values, not imputed) or the
  selected-record count, chosen by a mode toggle.
- **Interaction:** dropdown switches the coloured attribute; a radio toggles
  between "Attribute mean" (default) and "Selected count". With no selection,
  mean mode shows the mean over all records; with a selection it shows the mean
  over the selected records, and count mode shows how many selected records fall
  in each weekday × hour cell.
- **Note:** hour-3 cells for NOx/NO₂ are based on few observations (93.3% of
  03:00 readings are missing) and should be interpreted cautiously.

## 4. Data-quality notes relevant to all figures
- The `-200` missing-value code is converted to true missing values and is
  **never imputed**. Figures therefore either drop incomplete rows (V2, V3,
  V4) or leave gaps (V1) / aggregate over available values (V5).
- The 03:00 NOx(GT)/NO₂(GT) reference-analyzer gap (93.3% missing) is visible
  in V1 as a near-vertical white stripe when those attributes are selected.
- See `output/data_quality/data_quality_report.md` for the full data-quality
  evidence.

## 5. Files
- Code: `app.py` (linked-brushing Dash app), `data_processing.py`,
  `data_quality.py`, `views_common.py`, `generate_views.py`
- Outputs: `output/views/*.html` (single-view interactive exports),
  `output/views/previews/*.png` (static previews),
  `output/data_quality/*` (quality reports)
