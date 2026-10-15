"""Generate member B's five interactive views for the Task 1 similarity analysis.

Each view is written as a self-contained interactive HTML file into
output/views/. The visual encodings (attributes, season colours, colour
scales) are shared via views_common.py so the five views stay consistent.

Views:
  1  time_grid           Time Grid heatmap (day x hour, colour = attribute)
  2  parallel_coords     Parallel Coordinates (colour = season)
  3  splom               Scatterplot Matrix (colour = season)
  4  scatter             Temperature vs pollutant scatter (colour = season)
  5  weekday_heatmap     Weekday x hour mean heatmap (colour = attribute)
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from views_common import (
    ATTR_LABELS,
    NUMERIC_ATTRIBUTES,
    SEASON_COLORS,
    SEASON_ORDER,
    colorscale_for,
    load_data,
    save,
    season_colorscale,
)

WEEKDAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]


# ---------------------------------------------------------------------------
# View 1: Time Grid
# ---------------------------------------------------------------------------
def view_time_grid(df):
    df = df.copy()
    df["Day"] = df["DateTime"].dt.normalize()
    df["Hr"] = df["DateTime"].dt.hour

    # Use a common day grid so every attribute traces the same 391 days and the
    # y-axis stays aligned when the dropdown switches between attributes.
    all_days = sorted(df["Day"].unique())

    traces = []
    for attr in NUMERIC_ATTRIBUTES:
        pivot = (
            df.pivot_table(index="Day", columns="Hr", values=attr, aggfunc="mean")
            .reindex(all_days)
        )
        traces.append(
            go.Heatmap(
                z=pivot.values,
                x=list(pivot.columns),
                y=pivot.index.to_pydatetime(),
                colorscale=colorscale_for(attr),
                colorbar=dict(title=ATTR_LABELS[attr]),
                name=ATTR_LABELS[attr],
                hovertemplate=(
                    "Date: %{y|%Y-%m-%d}<br>Hour: %{x}:00<br>"
                    + ATTR_LABELS[attr]
                    + ": %{z:.2f}<extra></extra>"
                ),
                visible=(attr == "CO(GT)"),
            )
        )

    buttons = [
        dict(
            label=ATTR_LABELS[attr],
            method="update",
            args=[{"visible": [a == attr for a in NUMERIC_ATTRIBUTES]}],
        )
        for attr in NUMERIC_ATTRIBUTES
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="View 1 — Time Grid: hourly pollution & weather across the year",
            font=dict(size=18),
        ),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
            )
        ],
        height=760,
    )
    fig.update_xaxes(title_text="Hour of day", dtick=3)
    fig.update_yaxes(title_text="Date", tickformat="%b %Y")
    return fig


# ---------------------------------------------------------------------------
# View 2: Parallel Coordinates
# ---------------------------------------------------------------------------
def view_parallel_coordinates(df):
    complete = df.dropna(subset=NUMERIC_ATTRIBUTES).copy()
    n_season = len(SEASON_ORDER) - 1

    # Fixed per-axis ranges from the full data, so a season subset still plots
    # on the same scale as "All seasons" and the bundles stay comparable.
    ranges = {c: [complete[c].min(), complete[c].max()] for c in NUMERIC_ATTRIBUTES}

    def dimensions(sub):
        return [
            dict(label=ATTR_LABELS[c], values=sub[c].tolist(), range=ranges[c])
            for c in NUMERIC_ATTRIBUTES
        ]

    def make_trace(sub, alpha):
        return go.Parcoords(
            line=dict(
                color=sub["Season"].cat.codes.tolist(),
                colorscale=season_colorscale(alpha),
                cmin=-0.5,
                cmax=n_season + 0.5,
                showscale=True,
                colorbar=dict(
                    title="Season",
                    tickvals=list(range(len(SEASON_ORDER))),
                    ticktext=SEASON_ORDER,
                    len=0.5,
                ),
            ),
            dimensions=dimensions(sub),
        )

    # One trace per view; the dropdown toggles `visible` so exactly one is shown.
    # (Swapping `dimensions` via method="update" is unreliable for Parcoords,
    #  so each subset gets its own trace instead.)
    subsets = [("All seasons", complete, 0.18)] + [
        (s, complete[complete["Season"] == s], 0.5) for s in SEASON_ORDER
    ]
    traces = [make_trace(sub, alpha) for _, sub, alpha in subsets]
    for i, tr in enumerate(traces):
        tr.visible = i == 0  # show "All seasons" by default

    fig = go.Figure(data=traces)
    buttons = [
        dict(
            label=label,
            method="update",
            args=[{"visible": [j == i for j in range(len(subsets))]}],
        )
        for i, (label, _, _) in enumerate(subsets)
    ]

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"View 2 — Parallel Coordinates coloured by season "
            f"({len(complete):,} complete cases; dropdown isolates a season)",
            font=dict(size=18),
        ),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
            )
        ],
        height=720,
    )
    return fig


# ---------------------------------------------------------------------------
# View 3: SPLOM (Scatterplot Matrix)
# ---------------------------------------------------------------------------
def view_splom(df):
    complete = df.dropna(subset=NUMERIC_ATTRIBUTES).copy()
    season_code = complete["Season"].cat.codes.tolist()
    colorscale = season_colorscale()
    n = len(NUMERIC_ATTRIBUTES)

    def axis_ref(letter: str, idx: int) -> str:
        # First axis is referenced as "x"/"y" (no number); subsequent as "x2", ...
        return letter if idx == 1 else f"{letter}{idx}"

    fig = make_subplots(
        rows=n,
        cols=n,
        shared_xaxes=True,
        shared_yaxes=True,
        horizontal_spacing=0.015,
        vertical_spacing=0.015,
    )

    for i, yattr in enumerate(NUMERIC_ATTRIBUTES):
        for j, xattr in enumerate(NUMERIC_ATTRIBUTES):
            if i == j:
                fig.add_annotation(
                    text=ATTR_LABELS[yattr],
                    x=0.5,
                    y=0.5,
                    xref=f"{axis_ref('x', j + 1)} domain",
                    yref=f"{axis_ref('y', i + 1)} domain",
                    showarrow=False,
                    font=dict(size=13),
                )
            else:
                fig.add_trace(
                    go.Scattergl(
                        x=complete[xattr],
                        y=complete[yattr],
                        mode="markers",
                        marker=dict(
                            color=season_code,
                            colorscale=colorscale,
                            cmin=-0.5,
                            cmax=len(SEASON_ORDER) - 0.5,
                            size=2,
                            opacity=0.55,
                            showscale=(i == 0 and j == 1),
                            colorbar=dict(
                                title="Season",
                                tickvals=list(range(len(SEASON_ORDER))),
                                ticktext=SEASON_ORDER,
                                len=0.7,
                            ),
                        ),
                        showlegend=False,
                    ),
                    row=i + 1,
                    col=j + 1,
                )

    for j, xattr in enumerate(NUMERIC_ATTRIBUTES):
        fig.update_xaxes(title_text=ATTR_LABELS[xattr], row=n, col=j + 1)
    for i, yattr in enumerate(NUMERIC_ATTRIBUTES):
        fig.update_yaxes(title_text=ATTR_LABELS[yattr], row=i + 1, col=1)

    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"View 3 — Scatterplot Matrix coloured by season "
            f"({len(complete):,} complete cases)",
            font=dict(size=18),
        ),
        height=1500,
        width=1500,
    )
    return fig


# ---------------------------------------------------------------------------
# View 4: Scatter Plot (Temperature vs pollutant, colour = season)
# ---------------------------------------------------------------------------
Y_OPTIONS = [
    "CO(GT)",
    "C6H6(GT)",
    "NOx(GT)",
    "NO2(GT)",
    "PT08.S1(CO)",
    "PT08.S2(NMHC)",
    "RH",
    "AH",
]


def view_scatter(df):
    df = df.copy()

    def season_xy(attr):
        xs, ys = [], []
        for s in SEASON_ORDER:
            sub = df[df["Season"] == s].dropna(subset=["T", attr])
            xs.append(sub["T"].tolist())
            ys.append(sub[attr].tolist())
        return xs, ys

    xs, ys = season_xy("CO(GT)")
    traces = [
        go.Scattergl(
            x=xs[i],
            y=ys[i],
            mode="markers",
            name=SEASON_ORDER[i],
            marker=dict(color=SEASON_COLORS[SEASON_ORDER[i]], size=4, opacity=0.7),
        )
        for i in range(len(SEASON_ORDER))
    ]

    buttons = []
    for attr in Y_OPTIONS:
        axs, ays = season_xy(attr)
        buttons.append(
            dict(
                label=ATTR_LABELS[attr],
                method="update",
                args=[
                    {"x": axs, "y": ays},
                    {"yaxis.title.text": ATTR_LABELS[attr]},
                    list(range(len(SEASON_ORDER))),
                ],
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="View 4 — Temperature vs pollutant coloured by season",
            font=dict(size=18),
        ),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
            )
        ],
        height=640,
    )
    fig.update_xaxes(title_text=ATTR_LABELS["T"])
    fig.update_yaxes(title_text=ATTR_LABELS["CO(GT)"])
    return fig


# ---------------------------------------------------------------------------
# View 5: Weekday Heatmap
# ---------------------------------------------------------------------------
def view_weekday_heatmap(df):
    df = df.copy()
    df["WD"] = df["DateTime"].dt.day_name()
    df["Hr"] = df["DateTime"].dt.hour

    traces = []
    for attr in NUMERIC_ATTRIBUTES:
        agg = (
            df.pivot_table(index="WD", columns="Hr", values=attr, aggfunc="mean")
            .reindex(WEEKDAY_ORDER)
        )
        traces.append(
            go.Heatmap(
                z=agg.values,
                x=list(agg.columns),
                y=agg.index.tolist(),
                colorscale=colorscale_for(attr),
                colorbar=dict(title=ATTR_LABELS[attr]),
                name=ATTR_LABELS[attr],
                hovertemplate=(
                    "Weekday: %{y}<br>Hour: %{x}:00<br>"
                    + ATTR_LABELS[attr]
                    + ": %{z:.2f}<extra></extra>"
                ),
                visible=(attr == "CO(GT)"),
            )
        )

    buttons = [
        dict(
            label=ATTR_LABELS[attr],
            method="update",
            args=[{"visible": [a == attr for a in NUMERIC_ATTRIBUTES]}],
        )
        for attr in NUMERIC_ATTRIBUTES
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text="View 5 — Weekday heatmap: mean level by hour of day",
            font=dict(size=18),
        ),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=1.0,
                xanchor="right",
                y=1.15,
                yanchor="top",
            )
        ],
        height=520,
    )
    fig.update_xaxes(title_text="Hour of day", dtick=3)
    fig.update_yaxes(title_text="Weekday")
    return fig


# ---------------------------------------------------------------------------
def main():
    df = load_data()
    views = {
        "1_time_grid": view_time_grid(df),
        "2_parallel_coords": view_parallel_coordinates(df),
        "3_splom": view_splom(df),
        "4_scatter": view_scatter(df),
        "5_weekday_heatmap": view_weekday_heatmap(df),
    }
    for name, fig in views.items():
        path = save(fig, name)
        print(f"Saved {path} ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
