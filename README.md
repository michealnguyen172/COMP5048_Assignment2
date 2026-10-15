# COMP5048 Assignment 2: Air Quality Sensor Data Analysis

Group visual analytics project on the UCI Air Quality dataset (hourly, Mar 2004 to Apr 2005).

## Main file
`AirQuality_Group.ipynb`: one notebook with Section 0 (data processing + data quality) and Tasks 1 to 4 in order. Outputs are saved in the notebook, so charts are visible without re-running.

## Supporting code
| File | Purpose | Owner |
|---|---|---|
| `data_processing.py` | Load CSV, convert -200 to missing (no imputation), build DateTime, save `output/air_quality_clean.csv` | B |
| `data_quality.py` | -200 verification, missingness by month, 03:00 NOx/NO2 gap → `output/data_quality/` | B |
| `views_common.py` | Shared attribute list, labels, colours, data loader | B |
| `generate_views.py` | Exports the five Task 1 views as standalone HTML | B |
| `app.py` | Linked-brushing Dash dashboard for Task 1 | B |
| `figure_registry.md` | Registry of every figure (ID, encoding, interaction, file) | B |

## How to run
```bash
pip install pandas numpy plotly dash ipywidgets jupyter
jupyter notebook AirQuality_Group.ipynb      # run all cells top to bottom
python app.py                                # optional: dashboard at http://127.0.0.1:8050
```

## Rules
- Same attributes in every task (defined once in `views_common.py`).
- `-200` values are missing and never imputed.
- No clustering algorithms; groups are found from visual evidence only.

## Members
| | Member | Section |
|---|---|---|
| A | Wang Yuyao | Task 3 Prediction |
| B | Lian Fengyu | Task 1 Similarity, data quality, figure registry |
| C | Nguyen Huu Hoang Duc | Task 2 Trend, literature survey |
| D | Tang Yaqing | Task 4 Evaluation, data section, report assembly |
