"""Interactive visual-analytic tool with linked brushing (cross-filtering).

Run with:  python app.py   then open http://127.0.0.1:8050

Select time periods in the Scatter plot or the SPLOM (box/lasso select), or
brush an axis in the Parallel Coordinates view. The selected time periods are
highlighted across the other views, so a group of hours can be traced from one
attribute space to another and to the Time Grid / Weekday Heatmap.

Selection model
---------------
* "selection" store  : list of selected row ids (from brushing). Empty = none.
* "seasons" checklist : filter (removes seasons from every view).
* Parallel-coordinates brush : native plotly brush, converted to row ids.
"""
import re

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
from plotly.subplots import make_subplots

from views_common import (
    ATTR_LABELS,
    NUMERIC_ATTRIBUTES,
    SEASON_COLORS,
    SEASON_ORDER,
    colorscale_for,
    load_data,
    season_colorscale,
    season_highlight_colorscale,
)

WEEKDAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

Y_OPTIONS = [
    "CO(GT)", "C6H6(GT)", "NOx(GT)", "NO2(GT)",
    "PT08.S1(CO)", "PT08.S2(NMHC)", "RH", "AH",
]

SPLOM_SAMPLE_N = 2000  # down-sample the SPLOM for responsive interaction

# Core variables shown by default in the SPLOM (a readable subset; the rest
# remain selectable in the dropdown — still the same 9 attributes).
SPLOM_DEFAULT_ATTRS = ["CO(GT)", "C6H6(GT)", "NOx(GT)", "NO2(GT)", "T"]

# ---------------------------------------------------------------------------
# Data preparation (done once at import)
# ---------------------------------------------------------------------------
df = load_data()
df["_id"] = range(len(df))
df["Day"] = df["DateTime"].dt.normalize()
df["Hr"] = df["DateTime"].dt.hour
df["WD"] = df["DateTime"].dt.day_name()

complete = df.dropna(subset=NUMERIC_ATTRIBUTES).copy()
splom_sample = complete.sample(n=SPLOM_SAMPLE_N, random_state=42)

GRAY = "#d9d9d9"


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------
def extract_ids(selected_data):
    """Map plotly selectedData -> list of global row ids (via customdata)."""
    ids = []
    if not selected_data:
        return ids
    for p in selected_data.get("points", []):
        cd = p.get("customdata")
        if isinstance(cd, (list, tuple)):
            ids.append(cd[0] if cd else None)
        else:
            ids.append(cd)
    return [i for i in ids if i is not None]


def parse_parcoords_constraints(restyle_data, current):
    """Merge a parcoords brush event into the accumulated constraint dict."""
    constraints = dict(current or {})
    if not restyle_data:
        return constraints
    update = restyle_data[0] if isinstance(restyle_data, list) else restyle_data
    if not isinstance(update, dict):
        return constraints
    for key, val in update.items():
        m = re.match(r"dimensions\[(\d+)\]\.constraintrange", key)
        if not m:
            continue
        dim = int(m.group(1))
        if isinstance(val, (list, tuple)) and len(val) == 2 and all(v is not None for v in val):
            constraints[dim] = [float(val[0]), float(val[1])]
        else:
            constraints.pop(dim, None)
    return constraints


def apply_constraints(data, constraints):
    """Return the set of _ids whose rows satisfy every parcoords constraint."""
    mask = pd.Series(True, index=data.index)
    for dim, (lo, hi) in (constraints or {}).items():
        attr = NUMERIC_ATTRIBUTES[dim]
        mask &= data[attr].between(lo, hi)
    return set(data.loc[mask, "_id"])


# ---------------------------------------------------------------------------
# Render functions (each returns a go.Figure given the current selection)
# ---------------------------------------------------------------------------
def render_scatter(highlight_ids, seasons, x_attr, y_attr):
    data = complete[complete["Season"].isin(seasons)]
    sel = set(highlight_ids or [])
    traces = []
    for s in SEASON_ORDER:
        sub = data[data["Season"] == s]
        if not len(sub):
            continue
        if sel:
            traces.append(go.Scattergl(
                x=sub[x_attr], y=sub[y_attr], mode="markers",
                marker=dict(color=GRAY, size=4, opacity=0.45),
                customdata=sub["_id"].tolist(), name=f"{s} (rest)", showlegend=False,
                hoverinfo="skip",
            ))
            sub_sel = sub[sub["_id"].isin(sel)]
            if len(sub_sel):
                traces.append(go.Scattergl(
                    x=sub_sel[x_attr], y=sub_sel[y_attr], mode="markers",
                    marker=dict(color=SEASON_COLORS[s], size=4, opacity=0.9),
                    customdata=sub_sel["_id"].tolist(), name=s,
                ))
        else:
            traces.append(go.Scattergl(
                x=sub[x_attr], y=sub[y_attr], mode="markers",
                marker=dict(color=SEASON_COLORS[s], size=4, opacity=0.6),
                customdata=sub["_id"].tolist(), name=s,
            ))

    fig = go.Figure(data=traces)
    n_sel = len(sel)
    fig.update_layout(
        template="plotly_white",
        title=dict(text=(
            f"Scatter — {ATTR_LABELS[x_attr]} vs {ATTR_LABELS[y_attr]} "
            f"({'highlighting ' + str(n_sel) + ' selected' if n_sel else 'box/lasso to select'})"
        )),
        dragmode="select",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_xaxes(title_text=ATTR_LABELS[x_attr])
    fig.update_yaxes(title_text=ATTR_LABELS[y_attr])
    return fig


def render_parcoords(highlight_ids, seasons):
    data = complete[complete["Season"].isin(seasons)]
    sel = set(highlight_ids or [])

    if sel:
        # Faded grey context lines + full-opacity season-coloured selected lines,
        # mirroring the Scatter / SPLOM highlight treatment.
        color = data["Season"].cat.codes.astype(float).copy()
        color[~data["_id"].isin(sel)] = -1.0
        line = dict(
            color=color.tolist(),
            colorscale=season_highlight_colorscale(),
            cmin=-1.0,
            cmax=len(SEASON_ORDER) - 1.0,
            showscale=False,
        )
        n_shown = int(data["_id"].isin(sel).sum())
        title = (f"Parallel Coordinates — highlighting {n_shown:,} selected "
                 f"(grey = unselected)")
    else:
        line = dict(
            color=data["Season"].cat.codes.tolist(),
            colorscale=season_colorscale(0.18),
            cmin=-0.5,
            cmax=len(SEASON_ORDER) - 0.5,
            showscale=True,
            colorbar=dict(
                title="Season",
                tickvals=list(range(len(SEASON_ORDER))),
                ticktext=SEASON_ORDER,
                len=0.5,
            ),
        )
        title = (f"Parallel Coordinates — brush an axis to select "
                 f"({len(data):,} complete cases)")

    fig = go.Figure(go.Parcoords(
        line=line,
        dimensions=[
            dict(label=ATTR_LABELS[c], values=data[c].tolist(),
                 range=[data[c].min(), data[c].max()])
            for c in NUMERIC_ATTRIBUTES
        ],
    ))
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title),
        height=480,
    )
    return fig


def render_splom(highlight_ids, seasons, splom_attrs):
    splom_attrs = list(splom_attrs or SPLOM_DEFAULT_ATTRS)
    data = splom_sample[splom_sample["Season"].isin(seasons)]
    sel = set(highlight_ids or [])
    if sel:
        # Keep the down-sampled baseline for speed, but force the currently
        # selected points in so brushing in the Scatter/Parcoords always
        # highlights here even when a point is outside the sample.
        extra = complete[complete["_id"].isin(sel) & complete["Season"].isin(seasons)]
        data = pd.concat([data, extra]).drop_duplicates(subset="_id")
    code = data["Season"].cat.codes.tolist()
    cs = season_colorscale()
    n = len(splom_attrs)

    def axis_ref(letter, idx):
        return letter if idx == 1 else f"{letter}{idx}"

    fig = make_subplots(
        rows=n, cols=n, shared_xaxes=True, shared_yaxes=True,
        horizontal_spacing=0.015, vertical_spacing=0.015,
    )
    for i, yattr in enumerate(splom_attrs):
        for j, xattr in enumerate(splom_attrs):
            if i == j:
                fig.add_annotation(
                    text=ATTR_LABELS[yattr], x=0.5, y=0.5,
                    xref=f"{axis_ref('x', j + 1)} domain",
                    yref=f"{axis_ref('y', i + 1)} domain",
                    showarrow=False, font=dict(size=12),
                )
                continue
            if sel:
                fig.add_trace(go.Scattergl(
                    x=data[xattr], y=data[yattr], mode="markers",
                    marker=dict(color=GRAY, size=2, opacity=0.4),
                    customdata=data["_id"].tolist(), showlegend=False, hoverinfo="skip",
                ), row=i + 1, col=j + 1)
                sub_sel = data[data["_id"].isin(sel)]
                if len(sub_sel):
                    fig.add_trace(go.Scattergl(
                        x=sub_sel[xattr], y=sub_sel[yattr], mode="markers",
                        marker=dict(
                            color=sub_sel["Season"].cat.codes.tolist(), colorscale=cs,
                            cmin=-0.5, cmax=len(SEASON_ORDER) - 0.5,
                            size=2.5, opacity=0.9,
                            showscale=(i == 0 and j == 1),
                            colorbar=dict(
                                title="Season",
                                tickvals=list(range(len(SEASON_ORDER))),
                                ticktext=SEASON_ORDER, len=0.7,
                            ),
                        ),
                        customdata=sub_sel["_id"].tolist(), showlegend=False,
                    ), row=i + 1, col=j + 1)
            else:
                fig.add_trace(go.Scattergl(
                    x=data[xattr], y=data[yattr], mode="markers",
                    marker=dict(
                        color=code, colorscale=cs,
                        cmin=-0.5, cmax=len(SEASON_ORDER) - 0.5,
                        size=2, opacity=0.55,
                        showscale=(i == 0 and j == 1),
                        colorbar=dict(
                            title="Season",
                            tickvals=list(range(len(SEASON_ORDER))),
                            ticktext=SEASON_ORDER, len=0.7,
                        ),
                    ),
                    customdata=data["_id"].tolist(), showlegend=False,
                ), row=i + 1, col=j + 1)

    for j, xattr in enumerate(splom_attrs):
        fig.update_xaxes(title_text=ATTR_LABELS[xattr], row=n, col=j + 1)
    for i, yattr in enumerate(splom_attrs):
        fig.update_yaxes(title_text=ATTR_LABELS[yattr], row=i + 1, col=1)

    n_sel = len(sel)
    fig.update_layout(
        template="plotly_white",
        title=dict(text=(
            f"SPLOM — {'highlighting ' + str(n_sel) + ' selected' if n_sel else 'box/lasso to select'} "
            f"({n} variables, {len(data):,} sampled points)"
        )),
        dragmode="select",
        height=300 * n,
    )
    return fig


def _pivot_heatmap(data, attr):
    return data.pivot_table(index="Day", columns="Hr", values=attr, aggfunc="mean")


def render_time_grid(highlight_ids, seasons, attr):
    base = df[df["Season"].isin(seasons)]
    all_days = sorted(base["Day"].unique())
    pivot = _pivot_heatmap(base, attr).reindex(all_days)
    traces = [
        go.Heatmap(
            z=pivot.values, x=list(pivot.columns),
            y=pivot.index.to_pydatetime(),
            colorscale=colorscale_for(attr),
            colorbar=dict(title=ATTR_LABELS[attr]),
            hovertemplate="Date: %{y|%Y-%m-%d}<br>Hour: %{x}:00<br>"
            + ATTR_LABELS[attr] + ": %{z:.2f}<extra></extra>",
        )
    ]
    sel = set(highlight_ids or [])
    if sel:
        traces[0].opacity = 0.25
        sel_rows = base[base["_id"].isin(sel)]
        pivot_sel = _pivot_heatmap(sel_rows, attr).reindex(index=pivot.index, columns=pivot.columns)
        traces.append(go.Heatmap(
            z=pivot_sel.values, x=list(pivot_sel.columns),
            y=pivot_sel.index.to_pydatetime(),
            colorscale=colorscale_for(attr),
            showscale=False,
            hovertemplate="Date: %{y|%Y-%m-%d}<br>Hour: %{x}:00<br>"
            + ATTR_LABELS[attr] + ": %{z:.2f}<extra></extra>",
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_white",
        title=dict(text=f"Time Grid — {ATTR_LABELS[attr]} "
                        f"({'selected cells highlighted' if sel else 'full year'})"),
        height=560,
    )
    fig.update_xaxes(title_text="Hour of day", dtick=3)
    fig.update_yaxes(title_text="Date", tickformat="%b %Y")
    return fig


def render_weekday(highlight_ids, seasons, attr, mode="mean"):
    base = df[df["Season"].isin(seasons)]
    sel = set(highlight_ids or [])

    if mode == "count":
        sub = base[base["_id"].isin(sel)] if sel else base
        cnt = (sub.assign(_n=1.0)
                  .pivot_table(index="WD", columns="Hr", values="_n", aggfunc="sum")
                  .reindex(WEEKDAY_ORDER)
                  .fillna(0))
        fig = go.Figure(go.Heatmap(
            z=cnt.values, x=list(cnt.columns), y=cnt.index.tolist(),
            colorscale="Reds", zmin=0,
            colorbar=dict(title="selected records"),
            hovertemplate="Weekday: %{y}<br>Hour: %{x}:00<br>Selected records: %{z:.0f}<extra></extra>",
        ))
        title = (f"Weekday Heatmap — selected-record count ({len(sel):,} selected)"
                 if sel else "Weekday Heatmap — record count (no selection)")
    else:
        data = base[base["_id"].isin(sel)] if sel else base
        agg = data.pivot_table(index="WD", columns="Hr", values=attr, aggfunc="mean").reindex(WEEKDAY_ORDER)
        fig = go.Figure(go.Heatmap(
            z=agg.values, x=list(agg.columns), y=agg.index.tolist(),
            colorscale=colorscale_for(attr),
            colorbar=dict(title=ATTR_LABELS[attr]),
            hovertemplate="Weekday: %{y}<br>Hour: %{x}:00<br>"
            + ATTR_LABELS[attr] + ": %{z:.2f}<extra></extra>",
        ))
        title = (f"Weekday Heatmap — {ATTR_LABELS[attr]} "
                 f"({'mean of selected ' + str(len(sel)) + ' points' if sel else 'mean of all points'})")

    fig.update_layout(
        template="plotly_white",
        title=dict(text=title),
        height=560,
    )
    fig.update_xaxes(title_text="Hour of day", dtick=3)
    fig.update_yaxes(title_text="Weekday")
    return fig


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------
app = Dash(__name__)

season_options = [{"label": s, "value": s} for s in SEASON_ORDER]
attr_options = [{"label": ATTR_LABELS[a], "value": a} for a in NUMERIC_ATTRIBUTES]
y_options = [{"label": ATTR_LABELS[a], "value": a} for a in Y_OPTIONS]

app.layout = html.Div(
    style={"fontFamily": "Helvetica, Arial, sans-serif", "margin": "20px", "maxWidth": "1500px"},
    children=[
        html.H2("Air Quality — Linked-Brushing Visual Analytics", style={"marginBottom": "4px"}),
        html.Div(
            "Select time periods in the Scatter plot or SPLOM (box/lasso), or brush an axis "
            "in the Parallel Coordinates view. The selection is highlighted across all other views.",
            style={"color": "#555", "marginBottom": "12px"},
        ),
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "24px", "flexWrap": "wrap",
                   "marginBottom": "12px"},
            children=[
                html.Div([
                    html.Label("Seasons (filter):", style={"fontWeight": "bold"}),
                    dcc.Checklist(
                        id="seasons", options=season_options, value=SEASON_ORDER,
                        inline=True, style={"marginLeft": "8px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("Heatmap attribute:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="heatmap-attr", options=attr_options, value="CO(GT)",
                                 clearable=False, style={"width": "200px", "marginLeft": "8px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("Weekday heatmap:", style={"fontWeight": "bold"}),
                    dcc.RadioItems(
                        id="weekday-mode",
                        options=[
                            {"label": "Attribute mean", "value": "mean"},
                            {"label": "Selected count", "value": "count"},
                        ],
                        value="mean",
                        inline=True,
                        labelStyle={"marginLeft": "8px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("Scatter x-axis:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="scatter-x", options=attr_options, value="T",
                                 clearable=False, style={"width": "200px", "marginLeft": "8px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("Scatter y-axis:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="scatter-y", options=y_options, value="CO(GT)",
                                 clearable=False, style={"width": "200px", "marginLeft": "8px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Label("SPLOM variables:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="splom-attr", options=attr_options,
                                 value=SPLOM_DEFAULT_ATTRS, multi=True, clearable=False,
                                 style={"width": "340px", "marginLeft": "8px"}),
                ], style={"display": "flex", "alignItems": "center"}),
                html.Button("Reset selection", id="reset-btn", n_clicks=0,
                            style={"padding": "8px 16px", "cursor": "pointer"}),
            ],
        ),
        dcc.Store(id="selection", data=[]),
        dcc.Store(id="parcoords-constraints", data={}),

        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[
                dcc.Graph(id="scatter-graph", config={"displaylogo": False}),
                dcc.Graph(id="parcoords-graph", config={"displaylogo": False}),
            ],
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginTop": "16px"},
            children=[
                dcc.Graph(id="timegrid-graph", config={"displaylogo": False}),
                dcc.Graph(id="weekday-graph", config={"displaylogo": False}),
            ],
        ),
        dcc.Graph(id="splom-graph", config={"displaylogo": False},
                  style={"marginTop": "16px"}),
    ],
)


# ---------------------------------------------------------------------------
# Selection callbacks (sources -> selection store)
# ---------------------------------------------------------------------------
@app.callback(
    Output("selection", "data", allow_duplicate=True),
    Input("scatter-graph", "selectedData"),
    prevent_initial_call=True,
)
def select_from_scatter(selected_data):
    return extract_ids(selected_data)


@app.callback(
    Output("selection", "data", allow_duplicate=True),
    Input("splom-graph", "selectedData"),
    prevent_initial_call=True,
)
def select_from_splom(selected_data):
    return extract_ids(selected_data)


@app.callback(
    Output("parcoords-constraints", "data", allow_duplicate=True),
    Output("selection", "data", allow_duplicate=True),
    Input("parcoords-graph", "restyleData"),
    State("parcoords-constraints", "data"),
    State("seasons", "value"),
    prevent_initial_call=True,
)
def select_from_parcoords(restyle_data, current_constraints, seasons):
    seasons = seasons or SEASON_ORDER
    data = complete[complete["Season"].isin(seasons)]
    constraints = parse_parcoords_constraints(restyle_data, current_constraints)
    ids = sorted(apply_constraints(data, constraints))
    return constraints, ids


@app.callback(
    Output("selection", "data", allow_duplicate=True),
    Output("parcoords-constraints", "data", allow_duplicate=True),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_selection(_n_clicks):
    return [], {}


# ---------------------------------------------------------------------------
# Render callbacks
# ---------------------------------------------------------------------------
@app.callback(
    Output("scatter-graph", "figure"),
    Output("timegrid-graph", "figure"),
    Output("weekday-graph", "figure"),
    Output("splom-graph", "figure"),
    Input("selection", "data"),
    Input("seasons", "value"),
    Input("heatmap-attr", "value"),
    Input("scatter-x", "value"),
    Input("scatter-y", "value"),
    Input("splom-attr", "value"),
    Input("weekday-mode", "value"),
)
def render_views(selection, seasons, heatmap_attr, scatter_x, scatter_y, splom_attr, weekday_mode):
    seasons = seasons or SEASON_ORDER
    return (
        render_scatter(selection, seasons, scatter_x, scatter_y),
        render_time_grid(selection, seasons, heatmap_attr),
        render_weekday(selection, seasons, heatmap_attr, weekday_mode),
        render_splom(selection, seasons, splom_attr),
    )


@app.callback(
    Output("parcoords-graph", "figure"),
    Input("selection", "data"),
    Input("seasons", "value"),
)
def render_parcoords_view(selection, seasons):
    return render_parcoords(selection, seasons or SEASON_ORDER)


if __name__ == "__main__":
    app.run(debug=True, port=8050)
