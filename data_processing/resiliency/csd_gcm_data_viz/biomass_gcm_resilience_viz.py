#!/usr/bin/env python3
"""
biomass_gcm_resilience_viz.py

Improved, multi-figure visualization of the Biomass_GCM critical-slowing-down
(CSD) resilience analysis, built from the per-GCM outputs already produced by
csd_analysis.py (window=10y, step=12mo, climatology detrend, fisher-p 3-segment
split, n_surrogates=1000):

    csd_analysis/output/Biomass_GCM/Biomass_GCM_<MODEL>_win10y_step12_climatology_fisherpn3_nsurr1000.csv
    csd_analysis/output/Biomass_GCM/Biomass_GCM_<MODEL>_win10y_step12_climatology_fisherpn3_nsurr1000.md

The ensemble mean (GCM_mean) is intentionally excluded — only the five
individual GCMs (ACCESS, CMCC, CNRM, INM, IPSL) are shown.

This script does not re-run any analysis; it parses the existing CSVs (TAC/Var
time series) and Markdown reports (fisher-p 3-segment trend tables) and turns
them into a focused set of comparison figures and tables centred on shifts in
resilience — i.e. periods where AC1 (lag-1 autocorrelation) and/or Variance
are significantly increasing (resilience loss / destabilizing) or decreasing
(resilience gain / stabilizing).

Outputs (written to ./outputs/):
    01_overlay_timeseries.png      - raw TAC/Var lines, all 5 models overlaid
    02_trend_segments_timeline.png - per-model/metric trend-segment bands on a shared timeline
    03_trend_heatmap_matrix.png    - segment-order x model x metric trend matrix
    04_model_timeseries_grid.png   - small multiples: one row per model, shaded by segment trend
    trend_summary_table.csv/.png   - full detail table (period, n, tau, p, trend) per model/metric
    summary.md                     - textual synthesis of cross-model agreement/disagreement
"""

import re
from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR  = SCRIPT_DIR.parent / "csd_analysis" / "output" / "Biomass_GCM"
OUT_DIR    = SCRIPT_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_TAG = "win10y_step12_climatology_fisherpn3_nsurr1000"

MODELS = ["ACCESS", "CMCC", "CNRM", "IPSL", "INM"]
MODEL_DESC = {
    "ACCESS": "hot/wet",
    "CMCC":   "warm/wet",
    "CNRM":   "warm/dry",
    "IPSL":   "hot/dry",
    "INM":    "median",
}
MODEL_LABEL = {m: f"{m} ({MODEL_DESC[m]})" for m in MODELS}
MODEL_COLORS = {
    "ACCESS": "#1b9e77", "CMCC": "#e6ab02", "CNRM": "#66a61e",
    "IPSL": "#e7298a", "INM": "#a6761d",
}
METRICS = ["TAC", "Var"]
METRIC_LABEL = {"TAC": "Lag-1 AC1", "Var": "Variance"}

TREND_COLOR = {"increasing": "#d6604d", "decreasing": "#4393c3", "no trend": "#dddddd"}
TREND_TEXT_COLOR = {"increasing": "#67001f", "decreasing": "#053061", "no trend": "#555555"}

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

PERIOD_ROW_RE = re.compile(
    r"\|\s*(?P<period>[^|]+?)\s*\|\s*(?P<n>\d+)\s*\|\s*Surrogate\s*\|\s*"
    r"(?P<tau>[+-][\d.]+)\s*\|\s*(?P<p>[\d.]+)\s*(?P<sig>\*)?\s*\|\s*(?P<trend>[\w\s]+?)\s*\|"
)


def _parse_period_bounds(period: str, series_start: pd.Timestamp, series_end: pd.Timestamp):
    """Turn a Period column string into (start, end) timestamps."""
    period = period.strip()
    if period == "Full record":
        return series_start, series_end
    m = re.match(r"Before (\d{4}-\d{2})", period)
    if m:
        return series_start, pd.Timestamp(m.group(1))
    m = re.match(r"From (\d{4}-\d{2})", period)
    if m:
        return pd.Timestamp(m.group(1)), series_end
    m = re.match(r"(\d{4}-\d{2})\s*[–-]+\s*(\d{4}-\d{2})", period)
    if m:
        return pd.Timestamp(m.group(1)), pd.Timestamp(m.group(2))
    raise ValueError(f"Could not parse period label: {period!r}")


def load_model(model: str) -> tuple[pd.DataFrame, dict]:
    """
    Load a single model's CSV (centre_date, TAC, Var) and parse its Markdown
    report into {metric: [rows]} where each row is a dict with keys:
    period, start, end, n, tau, p, trend, is_full_record.
    """
    base = f"Biomass_GCM_{model}_{FILE_TAG}"
    csv_path = INPUT_DIR / f"{base}.csv"
    md_path = INPUT_DIR / f"{base}.md"

    df = pd.read_csv(csv_path, parse_dates=["centre_date"], index_col="centre_date")
    series_start, series_end = df.index.min(), df.index.max()

    text = md_path.read_text(encoding="utf-8")
    sections = {}
    for metric in METRICS:
        m = re.search(rf"### {metric}\n\n(.*?)(?:\n\n|\Z)", text, re.DOTALL)
        if not m:
            raise ValueError(f"{md_path}: could not find ### {metric} section")
        rows = []
        for row_m in PERIOD_ROW_RE.finditer(m.group(1)):
            period = row_m.group("period")
            start, end = _parse_period_bounds(period, series_start, series_end)
            rows.append({
                "period": period,
                "start": start,
                "end": end,
                "n": int(row_m.group("n")),
                "tau": float(row_m.group("tau")),
                "p": float(row_m.group("p")),
                "trend": row_m.group("trend").strip(),
                "is_full_record": period.strip() == "Full record",
            })
        sections[metric] = rows

    return df, sections


def load_all_models():
    data = {}
    for model in MODELS:
        df, sections = load_model(model)
        data[model] = {"df": df, "trends": sections}
    return data


# ---------------------------------------------------------------------------
# Figure 1: clean raw overlay
# ---------------------------------------------------------------------------

def fig_overlay_timeseries(data: dict) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for ax, metric in zip(axes, METRICS):
        for model in MODELS:
            df = data[model]["df"]
            ax.plot(
                df.index, df[metric],
                color=MODEL_COLORS[model], linewidth=1.7, marker="o", markersize=3,
                label=MODEL_LABEL[model],
            )
        ax.set_ylabel(f"{METRIC_LABEL[metric]}" + (" coefficient" if metric == "TAC" else " (normalized)"))
        ax.set_title(f"Biomass_GCM — {METRIC_LABEL[metric]}")
        ax.grid(True, linestyle="--", alpha=0.4)
    axes[0].legend(fontsize=9, ncol=1, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    axes[-1].set_xlabel("Centre date of 10-year window")
    fig.suptitle("Biomass critical-slowing-down indicators across 5 GCMs (SSP3-7.0)", y=1.0)
    fig.tight_layout()
    out = OUT_DIR / "01_overlay_timeseries.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Figure 2: trend-segment bands on a shared timeline
# ---------------------------------------------------------------------------

def fig_trend_segments_timeline(data: dict) -> None:
    rows = [(model, metric) for model in MODELS for metric in METRICS]
    fig, ax = plt.subplots(figsize=(13, 0.6 * len(rows) + 1.5))

    all_starts, all_ends = [], []
    for i, (model, metric) in enumerate(rows):
        y = len(rows) - i
        segs = [r for r in data[model]["trends"][metric] if not r["is_full_record"]]
        for seg in segs:
            start_num = seg["start"].toordinal()
            end_num = seg["end"].toordinal()
            color = TREND_COLOR[seg["trend"]]
            ax.barh(y, end_num - start_num, left=start_num, height=0.8,
                    color=color, edgecolor="white", linewidth=0.5)
            mid = (start_num + end_num) / 2
            label = f"τ={seg['tau']:+.2f}" + ("*" if seg["p"] < 0.05 else "")
            ax.text(mid, y, label, ha="center", va="center", fontsize=7,
                     color=TREND_TEXT_COLOR[seg["trend"]])
            all_starts.append(start_num)
            all_ends.append(end_num)
        model_box = TextArea(MODEL_LABEL[model], textprops=dict(
            color=MODEL_COLORS[model], fontsize=9, ha="right"))
        metric_box = TextArea(f" — {METRIC_LABEL[metric]}", textprops=dict(
            color="black", fontsize=9, ha="right"))
        label_box = HPacker(children=[model_box, metric_box], align="center", pad=0, sep=0)
        ab = AnnotationBbox(
            label_box, (min(all_starts) - 200, y), xycoords="data",
            box_alignment=(1, 0.5), frameon=False, annotation_clip=False,
        )
        ax.add_artist(ab)

    ax.set_yticks([])
    ax.set_ylim(0, len(rows) + 1)
    xticks_years = list(range(1995, 2066, 5))
    ax.set_xticks([pd.Timestamp(year=y, month=1, day=1).toordinal() for y in xticks_years])
    ax.set_xticklabels(xticks_years, rotation=45)
    ax.set_xlabel("Year")
    ax.set_title(
        "Biomass_GCM resilience trend segments by model (fisher-p 3-segment split)\n"
        "red = increasing AC1/Var (resilience loss)   blue = decreasing (resilience gain)   "
        "gray = no significant trend   * p<0.05"
    )

    # group separators between models
    for i in range(1, len(MODELS)):
        ax.axhline(len(rows) - (i * len(METRICS)) + 0.5, color="black", linewidth=0.6, alpha=0.3)

    fig.tight_layout()
    out = OUT_DIR / "02_trend_segments_timeline.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Figure 3: segment-order x model x metric trend matrix
# ---------------------------------------------------------------------------

HEATMAP_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "trend_diverging",
    [TREND_COLOR["decreasing"], TREND_COLOR["no trend"], TREND_COLOR["increasing"]],
)


def fig_trend_heatmap_matrix(data: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 0.7 * len(MODELS) + 2))
    for ax, metric in zip(axes, METRICS):
        n_seg = 3
        grid = np.zeros((len(MODELS), n_seg))
        annot = np.empty((len(MODELS), n_seg), dtype=object)
        for r, model in enumerate(MODELS):
            segs = [s for s in data[model]["trends"][metric] if not s["is_full_record"]]
            for c, seg in enumerate(segs):
                grid[r, c] = {"increasing": 1, "decreasing": -1, "no trend": 0}[seg["trend"]]
                sig = "*" if seg["p"] < 0.05 else ""
                date_range = f"{seg['start'].strftime('%Y')}–{seg['end'].strftime('%Y')}"
                annot[r, c] = f"{date_range}\nτ={seg['tau']:+.2f}{sig}"

        ax.imshow(grid, cmap=HEATMAP_CMAP, vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(n_seg))
        ax.set_xticklabels(["Segment 1\n(early)", "Segment 2\n(mid)", "Segment 3\n(late)"])
        ax.set_yticks(range(len(MODELS)))
        ax.set_yticklabels([MODEL_LABEL[m] for m in MODELS])
        for tick, model in zip(ax.get_yticklabels(), MODELS):
            tick.set_color(MODEL_COLORS[model])
        ax.set_title(f"{METRIC_LABEL[metric]}")
        for r in range(len(MODELS)):
            for c in range(n_seg):
                ax.text(c, r, annot[r, c] or "", ha="center", va="center", fontsize=7.5)
        ax.set_xticks(np.arange(-0.5, n_seg, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(MODELS), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.5)
        ax.tick_params(which="minor", length=0)

    fig.suptitle(
        "Biomass_GCM trend direction by segment order, model, metric\n"
        "blue = decreasing (resilience gain), red = increasing (resilience loss), white = no trend",
        y=1.04,
    )
    fig.tight_layout()
    out = OUT_DIR / "03_trend_heatmap_matrix.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Figure 4: small multiples, one row per model, shaded by segment trend
# ---------------------------------------------------------------------------

def fig_model_timeseries_grid(data: dict) -> None:
    fig, axes = plt.subplots(len(MODELS), 2, figsize=(12, 2.6 * len(MODELS)), sharex="col")
    for r, model in enumerate(MODELS):
        df = data[model]["df"]
        for c, metric in enumerate(METRICS):
            ax = axes[r, c]
            for seg in data[model]["trends"][metric]:
                if seg["is_full_record"]:
                    continue
                ax.axvspan(seg["start"], seg["end"], color=TREND_COLOR[seg["trend"]], alpha=0.35, lw=0)
            ax.plot(df.index, df[metric], color="black", linewidth=1.3, marker="o", markersize=2.5)
            if r == 0:
                ax.set_title(METRIC_LABEL[metric])
            if c == 0:
                ax.set_ylabel(MODEL_LABEL[model], fontsize=9, color=MODEL_COLORS[model], fontweight="bold")
            ax.grid(True, linestyle="--", alpha=0.3)
    for c in range(2):
        axes[-1, c].set_xlabel("Centre date")

    handles = [plt.Rectangle((0, 0), 1, 1, color=TREND_COLOR[t], alpha=0.35) for t in
               ["increasing", "decreasing", "no trend"]]
    fig.legend(handles, ["increasing (resilience loss)", "decreasing (resilience gain)", "no significant trend"],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.01), fontsize=9)
    fig.suptitle("Biomass_GCM per-model AC1/Variance with significant trend segments shaded", y=1.0)
    fig.tight_layout(rect=(0, 0.02, 1, 0.98))
    out = OUT_DIR / "04_model_timeseries_grid.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Table: full detail
# ---------------------------------------------------------------------------

def make_summary_table(data: dict) -> pd.DataFrame:
    records = []
    for model in MODELS:
        for metric in METRICS:
            for seg in data[model]["trends"][metric]:
                records.append({
                    "model": model,
                    "description": MODEL_DESC[model],
                    "metric": metric,
                    "period": seg["period"],
                    "start": seg["start"].strftime("%Y-%m"),
                    "end": seg["end"].strftime("%Y-%m"),
                    "n": seg["n"],
                    "tau": seg["tau"],
                    "p": seg["p"],
                    "significant": seg["p"] < 0.05,
                    "trend": seg["trend"],
                })
    return pd.DataFrame.from_records(records)


def fig_summary_table(table: pd.DataFrame) -> None:
    cols = ["model", "description", "metric", "period", "n", "tau", "p", "trend"]
    display = table[cols].copy()
    display["tau"] = display["tau"].map(lambda v: f"{v:+.3f}")
    display["p"] = table.apply(lambda r: f"{r['p']:.3f}{'*' if r['p'] < 0.05 else ''}", axis=1)

    fig, ax = plt.subplots(figsize=(11, 0.32 * len(display) + 1))
    ax.axis("off")
    tbl = ax.table(
        cellText=display.values,
        colLabels=[c.replace("_", " ").title() for c in cols],
        loc="center", cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.3)

    for j in range(len(cols)):
        tbl[0, j].set_facecolor("#404040")
        tbl[0, j].set_text_props(color="white", weight="bold")

    trend_col = cols.index("trend")
    full_record_rows = table["period"].eq("Full record").values
    for i, (_, row) in enumerate(table.iterrows(), start=1):
        color = TREND_COLOR[row["trend"]]
        tbl[i, trend_col].set_facecolor(color)
        if full_record_rows[i - 1]:
            for j in range(len(cols)):
                tbl[i, j].set_facecolor("#f0f0f0" if j != trend_col else color)

    ax.set_title("Biomass_GCM resilience trend summary (fisher-p 3-segment split, surrogate test)", pad=14)
    fig.tight_layout()
    out = OUT_DIR / "trend_summary_table.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Markdown synthesis
# ---------------------------------------------------------------------------

def write_summary_md(data: dict, table: pd.DataFrame) -> None:
    lines = ["# Biomass_GCM resilience shift summary (5-GCM comparison)", ""]
    lines.append(
        "Source: `csd_analysis` output, Biomass_GCM, 10-year window / 12-month step / "
        "climatology detrend / fisher-p 3-segment split / 1000 surrogates. Ensemble mean excluded."
    )
    lines.append("")
    lines.append("Models: " + ", ".join(f"**{m}** ({MODEL_DESC[m]})" for m in MODELS))
    lines.append("")

    lines.append("## Full-record trend (any model significant?)")
    lines.append("")
    lines.append("| Model | TAC tau (p) | TAC trend | Var tau (p) | Var trend |")
    lines.append("| --- | --- | --- | --- | --- |")
    for model in MODELS:
        row = {}
        for metric in METRICS:
            full = next(s for s in data[model]["trends"][metric] if s["is_full_record"])
            row[metric] = full
        lines.append(
            f"| {MODEL_LABEL[model]} "
            f"| {row['TAC']['tau']:+.3f} ({row['TAC']['p']:.3f}) | {row['TAC']['trend']} "
            f"| {row['Var']['tau']:+.3f} ({row['Var']['p']:.3f}) | {row['Var']['trend']} |"
        )
    lines.append("")
    lines.append(
        "No model shows a significant full-record trend in either AC1 or Variance — "
        "the signal only emerges once the record is split into segments (below)."
    )
    lines.append("")

    lines.append("## Cross-model pattern in segmented trends")
    lines.append("")
    seg_table = table[~table["period"].eq("Full record")]
    inc_sig = seg_table[(seg_table.trend == "increasing") & seg_table.significant]
    dec_sig = seg_table[(seg_table.trend == "decreasing") & seg_table.significant]

    lines.append(
        f"- {len(inc_sig)} of {len(seg_table)} segment-trends across all models/metrics are "
        f"**significantly increasing** (resilience loss): "
        + ", ".join(f"{r.model}/{r.metric} {r.start}–{r.end}" for r in inc_sig.itertuples())
        + "."
    )
    lines.append(
        f"- {len(dec_sig)} are **significantly decreasing** (resilience gain): "
        + ", ".join(f"{r.model}/{r.metric} {r.start}–{r.end}" for r in dec_sig.itertuples())
        + "."
    )
    lines.append("")
    lines.append(
        "- **ACCESS, CMCC, CNRM** all show the same qualitative shape for TAC: a significant "
        "*decreasing* early segment followed by a significant *increasing* middle segment — "
        "i.e. resilience first improves, then erodes, in the early-to-mid 21st century, before "
        "leveling off (ACCESS, CNRM) or reversing again (CMCC, whose late segment swings back to "
        "significantly decreasing)."
    )
    lines.append(
        "- **INM and IPSL diverge** from that pattern: INM shows *increasing* TAC early "
        "(2007-12 and earlier) then *decreasing* through the 2007–2028 segment — the reverse "
        "ordering from the other three models. IPSL shows no significant TAC trend until a "
        "*decreasing* middle segment (2025–2054); it never shows a significant increasing "
        "(resilience-loss) TAC segment."
    )
    lines.append(
        "- For **Variance**, ACCESS/CNRM/CMCC again largely agree: an early significant decrease "
        "followed by a later significant increase (CMCC's increase is delayed to its final "
        "segment, 2023-12 onward). INM's variance instead decreases sharply after an early "
        "increase, and IPSL shows two consecutive significant decreases with no increasing "
        "segment at all."
    )
    lines.append(
        "- Net read: **3 of 5 models (ACCESS, CMCC, CNRM)** — the hot/wet, warm/wet, and "
        "warm/dry scenarios — agree on a multi-decadal pattern of early resilience gain "
        "followed by resilience loss in both AC1 and Variance. **IPSL (hot/dry)** shows only "
        "resilience gain (no loss signal), and **INM (median)** shows the pattern reversed "
        "in time relative to the other four."
    )
    lines.append("")

    lines.append("## Detail tables")
    lines.append("")
    for model in MODELS:
        lines.append(f"### {MODEL_LABEL[model]}")
        lines.append("")
        for metric in METRICS:
            lines.append(f"**{METRIC_LABEL[metric]}**")
            lines.append("")
            lines.append("| Period | n | tau | p | Trend |")
            lines.append("| --- | --- | --- | --- | --- |")
            for seg in data[model]["trends"][metric]:
                sig = " *" if seg["p"] < 0.05 else ""
                lines.append(f"| {seg['period']} | {seg['n']} | {seg['tau']:+.3f} | {seg['p']:.3f}{sig} | {seg['trend']} |")
            lines.append("")

    out = OUT_DIR / "summary.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    data = load_all_models()

    fig_overlay_timeseries(data)
    fig_trend_segments_timeline(data)
    fig_trend_heatmap_matrix(data)
    fig_model_timeseries_grid(data)

    table = make_summary_table(data)
    table.to_csv(OUT_DIR / "trend_summary_table.csv", index=False)
    print(f"Saved {OUT_DIR / 'trend_summary_table.csv'}")
    fig_summary_table(table)

    write_summary_md(data, table)
    print("\nDone.")


if __name__ == "__main__":
    main()
