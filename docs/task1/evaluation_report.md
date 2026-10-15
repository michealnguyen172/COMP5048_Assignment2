# Heuristic Evaluation Report — Air Quality Visual Analytics Tool

Maintained by: **Member B**

This report documents the evaluation of the interactive visual-analytic tool produced for Task 1 (Similarity Analysis). It records the evaluation method, the problems identified against a set of visualisation design principles, and — critically — the before/after comparison and rationale for each modification, so the improvement cycle is traceable.

## 1. Overview

| Item | Value |
|------|-------|
| Tool evaluated | Linked-brushing dashboard (`app.py`) + 5 standalone views (`output/views/*.html`) |
| Method | Heuristic evaluation — a structured expert inspection against visualisation design principles |
| Evaluator | Member B |
| Scope | The 5 views, the dashboard, and the accompanying report / registry / data-quality claims |
| Date | 2026-10-14 |
| Outcome | 11 problems identified; all fixed (see §5) |

## 2. Evaluation method and justification

The tool's purpose is to let an analyst **discover** groupings of time periods purely through visual evidence — no clustering algorithm, no pre-computed labels. The evaluation therefore has to answer a single question: **does the tool make that visual evidence legible, trustworthy, and traceable across views?**

A **heuristic evaluation** was chosen because it is the evaluation best *designed for this particular tool*:

- The tool's risk points are known and specific — encoding correctness (categorical vs continuous colour), over-plotting in the 6,941-line Parallel Coordinates, and whether cross-view linking is genuine shared state rather than per-chart. A targeted, principle-by-principle inspection covers these directly and completely.
- Each Task 1 requirement maps to a concrete visualisation principle (§3), so the evaluation is verifiable rather than subjective: every problem is traced to a violated principle and to a fix.
- Because the fixes were re-inspected against the same principles, the evaluation closes a full "violation → fix → re-check" loop.

The evaluation proceeded as a **cognitive walkthrough** of the five analytic questions (identify seasonal groups; trace a group of hours across views; isolate one season; read the weekday × hour pattern; box-select a SPLOM cluster), applying the principles at each step.

## 3. Principles applied (heuristics)

| # | Principle | Source | What it checks here |
|---|-----------|--------|---------------------|
| H1 | Expressiveness — the visual channel must match the data type | Munzner | Season is categorical → stepped/discrete colour, not a continuous gradient |
| H2 | Effectiveness / no over-plotting — structure must stay legible at density | Tufte, Few | 6,941 parcoords lines; 9×9 SPLOM axis labels |
| H3 | Interactivity is architecture — cross-view linking must be shared state | — | Selecting in one view must highlight the same hours in every other |
| H4 | Completeness vs responsiveness — down-sampling must never hide the selection | — | SPLOM 2,000-row sample must force-include selected points |
| H5 | Data integrity — missing values never imputed; filters must respect the analyst's choice | — | `-200` → true missing; the season filter must constrain brushing |
| H6 | Honesty & traceability — wording and counts must not overstate the evidence | — | no "clustering"; accurate instance counts; month-resolved missingness |

## 4. Findings (problems)

Each row is a violation of a principle, with severity and the affected view(s).

| ID | Problem | Principle | Severity | Affected view(s) |
|----|---------|-----------|----------|------------------|
| P1 | Standalone HTML views are isolated; selecting in one does not affect the others, so "trace hours across views" is unsupported | H3 | High | All (before `app.py`) |
| P2 | Parallel Coordinates draws all 6,941 complete-case lines at once — severe over-plotting, no visible bundles | H2 | High | V2 Parcoords |
| P3 | Season encoded with a continuous-looking colour bar although it is categorical | H1 | Medium | V2, V3 |
| P4 | V4 dropdown did not update the y-axis title when switching the variable | H6 | Medium | V4 Scatter |
| P5 | SPLOM down-samples to 2,000 rows, so small selections made elsewhere are sometimes not highlighted | H4 | Medium | V3 SPLOM |
| P6 | Report used "clustering", implying the grouping was algorithmic, contradicting the no-clustering constraint | H6 | Low | Report / registry |
| P7 | Data-quality claim "9,357 rows match the 9,357 documented UCI instances" was inaccurate (UCI lists 9,358) | H6 | Low | Data-quality report |
| P8 | `monthly_missing.csv` merged March 2004 and March 2005, so offline blocks could not be located in time | H6 | Low | Data-quality report |
| P9 | Selecting hours in the Scatter or SPLOM did **not** highlight them in the Parallel Coordinates view — the parcoords callback ignored the shared selection | H3 | High | V2 Parcoords |
| P10 | The 9×9 SPLOM axis-label matrix is unreadable; labels overlap and the panel is too crowded to scan | H2 | Medium | V3 SPLOM |
| P11 | Brushing the Parallel Coordinates with a single season selected still selected matching hours from **all** seasons, silently ignoring the filter | H5 | High | V2 Parcoords |

## 5. Before / after comparison

| ID | Before | After |
|----|--------|-------|
| P1 | Five independent `*.html` files; no cross-view selection | `app.py` linked-brushing dashboard: shared `dcc.Store` selection + callbacks, so box/lasso/brush selections highlight the same hours across all views |
| P2 | Parcoords rendered all 6,941 lines as an opaque tangle | Alpha-blended (density) colours + a season dropdown that isolates one season honestly, with axes fixed to the full-data range for comparability |
| P3 | Season colour bar was a smooth blue→green→orange→purple gradient | Stepped (discrete) colour scale with hard boundaries and `cmin`/`cmax` shifted to `[-0.5, 3.5]` so the four category labels sit centred in their blocks |
| P4 | `yaxis.title.text` was inside the trace-update dict, so the title never changed | Moved `yaxis.title.text` into the layout-update dict (standard 3-element `args`) |
| P5 | SPLOM plotted only a fixed 2,000-row sample | SPLOM still samples 2,000 for speed, but currently-selected points are force-included, so any selection is always highlighted |
| P6 | "clustering" / "Task 1 clustering" wording | "visual grouping discovery" / "visual group discovery" |
| P7 | Claim of exact match with UCI instance count | "The downloaded CSV contained 9,357 valid timestamped records after blank trailing rows were removed." |
| P8 | Missingness aggregated only by calendar month | Added a `YearMonth` (`2004-03`) aggregation (`yearmonth_missing.csv`), locating offline blocks in time |
| P9 | Parcoords callback took only the season filter + reset button, never the selection | Added `selection` as an input and a grey-context + season-coloured highlight (`season_highlight_colorscale`), so Scatter/SPLOM selections light up the same lines |
| P10 | 9×9 SPLOM with all nine attributes | Default to 5 core attributes (CO, C6H6, NOx, NO2, T) with a multi-select dropdown; height scales with the attribute count; the remaining 4 attributes stay selectable |
| P11 | Parcoords brushing applied `apply_constraints` to all seasons | Added the season filter as a `State` and constrained brushing to the filtered subset, so "Summer only" + a T-range brush returns Summer-only hours |

## 6. Modification rationale

- **P1 — build a real dashboard instead of independent files.** Single-chart interactions (hover, zoom, in-chart select) cannot demonstrate the "trace a group of hours from one attribute space to another" requirement. Only a server-side, shared-selection architecture (Dash callbacks + a `Store` of selected row ids) makes the cross-view link real and verifiable.
- **P2 — density + filtering rather than raw down-sampling.** Dropping lines would lose the "all 6,941 complete cases" claim, so the default view uses alpha blending to turn over-plotting into density, and a season dropdown provides an honest, lossless way to inspect each bundle. Axes are kept on the full-data range so subsets stay comparable.
- **P3 — discrete colour bar, not a legend.** Parcoords and SPLOM use a single colour-coded trace, so Plotly exposes a colour bar rather than a legend. The correct categorical treatment is a stepped scale with centred category labels, which reads as a legend while keeping the encoding consistent.
- **P4 — fix the dropdown contract.** Plotly's `updatemenus` `method="update"` takes `args = [trace_update, layout_update, trace_indices]`; the y-axis title is a layout property and must live in the second element.
- **P5 — force-include the selection.** The SPLOM sample exists only for responsiveness; guaranteeing the selected points are always drawn removes the only case where linked brushing appeared to break, at negligible cost.
- **P9 — a selection must be an input to every view.** Cross-view highlighting is only "linked" if *every* view subscribes to the shared selection; the Parallel Coordinates view had been left out, so selections made elsewhere never reached it. Wiring the selection in restores the symmetry the dashboard claims.
- **P10 — "show everything" is not "reveal structure".** A 9×9 matrix of axis labels is unreadable; a readable default subset (still drawn from the same 9 attributes) is the honest fix, with the full set kept one click away.
- **P11 — a filter that does not constrain the brush silently fabricates evidence.** Brushing "Summer only" must return Summer hours; otherwise a cross-season trace would contradict the group the analyst just isolated. The brush is now computed on the filtered subset only.
- **P6–P8 — reporting correctness.** Terminology and data-quality claims must not overstate the evidence; a categorical encoding must not look continuous; and missing-block analysis must resolve to the actual month, not a merged calendar month.

## 7. How the improvements enhanced discovery

- **P1 + P9 + P11 together make linked brushing trustworthy.** A group selected anywhere is the *same* hours everywhere, and the season filter is honoured during brushing. This is what lets Grouping 1 (seasonal) and Grouping 2 (rush-hour) be traced across attribute spaces without contradiction.
- **P2 + P10 make the bundles and clusters legible.** The density display exposes the four season bundles in the Parallel Coordinates, and a readable SPLOM subset lets tight point clusters be box-selected without drowning in overlapping axis labels.
- **P3 (H1) lets season read as four categories.** The Winter-high / Summer-low NOx split is visible as distinct bundles rather than misread as a gradient "range".
- **P5 guarantees a selection is never invisible.** The rush-hour group — small relative to the full year — still shows up in the SPLOM when selected, so no cross-view trace silently drops it.
- **P6–P8 keep the evidence honest.** The report's claims (9,357 records, `-200` treated as missing, no clustering) survive scrutiny, so the visual findings stand on their own.

## Appendix — files changed in this cycle

| File | Change |
|------|--------|
| `app.py` | Linked-brushing dashboard; parcoords selection input + highlight colourscale; SPLOM 5-attribute default + selector; season-filtered brushing |
| `generate_views.py` | V2 season dropdown + density; V4 y-axis fix; discrete season scale |
| `views_common.py` | `season_colorscale(alpha=...)` stepped discrete scale; `season_highlight_colorscale()` |
| `data_quality.py` | UCI count wording; `YearMonth` aggregation |
| `figure_registry.md` | "visual grouping discovery" wording; linked-brushing section |
| `output/data_quality/*` | `yearmonth_missing.csv`; regenerated report |
| `output/views/*` | regenerated HTML + previews; interaction-evidence composites |
