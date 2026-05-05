"""
gcm_results_chart.py
--------------------
Reads gcm_change_factors.json and produces a 5-row × 4-column chart.
  Rows    : one per GCM model
  Columns : one per season  (DJF, MAM, JJA, SON)
  Each cell shows four diverging vertical bars:
    • Temperature  (ΔK,  diverging from 0)
    • Precipitation (% change from 1.0, diverging from 0)
    • ET           (% change from 1.0, diverging from 0)
    • LAI          (% change from 1.0, diverging from 0)

Each variable is scaled to its own global axis range so relative magnitudes
within one variable are comparable across seasons and models.
DJF ET change factors are fixed at 1.0 for all models (dormant-season
baseline < 2 mm/month — too small for a reliable multiplicative ratio).
"""

import json
import os
import textwrap
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(SCRIPT_DIR, "gcm_change_factors.json")
OUT_PATH   = os.path.join(SCRIPT_DIR, "output", "gcm_results_chart.png")

# Visual properties for each variable
VAR_CONFIG = {
    "temp":   {"label": "Temp",   "color": "#d73027", "unit": "ΔK"},
    "precip": {"label": "Precip", "color": "#4575b4", "unit": "% Δ"},
    "et":     {"label": "ET",     "color": "#ff7f00", "unit": "% Δ"},
    "lai":    {"label": "LAI",    "color": "#33a02c", "unit": "% Δ"},
}
VARIABLES = list(VAR_CONFIG.keys())   # order of bars within each cell

# Bar layout inside each Axes
BAR_WIDTH  = 0.55
BAR_SPACING = 1.0          # spacing between bar centres
BAR_X_POSITIONS = np.arange(len(VARIABLES)) * BAR_SPACING   # [0, 1, 2, 3]

# Cap ET bars at this abs-pct-change to avoid one outlier dominating
ET_DISPLAY_CAP_PCT = 100.0   # bars capped at ±100 %; outliers annotated


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def ratio_to_pct(v: float) -> float:
    """Convert a change-factor ratio to percent change (e.g. 1.07 → +7)."""
    return (v - 1.0) * 100.0


def load_data(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def compute_global_scales(data: dict) -> dict:
    """
    For each variable compute the global maximum absolute value
    (after converting ratios to % change) across all model × season combinations.
    These become the axis half-widths so every subplot shares the same scale.
    """
    maxabs = {v: 0.0 for v in VARIABLES}
    for model in data["models"]:
        for season, vals in model["seasons"].items():
            maxabs["temp"]   = max(maxabs["temp"],   abs(vals["temp"]))
            maxabs["precip"] = max(maxabs["precip"],  abs(ratio_to_pct(vals["precip"])))
            # ET: use capped value for scale so the outlier doesn't crush others
            maxabs["et"]     = max(maxabs["et"],
                                   min(abs(ratio_to_pct(vals["et"])), ET_DISPLAY_CAP_PCT))
            maxabs["lai"]    = max(maxabs["lai"],     abs(ratio_to_pct(vals["lai"])))

    # Round up to a clean number for axis limits
    def ceil_nice(x):
        for step in [0.5, 1, 2, 5, 10, 15, 20, 25, 50, 100]:
            if step >= x:
                return step
        return round(x * 1.1, 0)

    return {v: ceil_nice(maxabs[v]) for v in VARIABLES}


def draw_cell(ax, vals: dict, scales: dict):
    """
    Draw four diverging vertical bars in a single Axes `ax`.

    Parameters
    ----------
    vals   : dict with keys temp, precip, et, lai
    scales : dict with per-variable half-width for the y-axis
    """
    # Light grey horizontal grid lines
    for y_grid in [-1.0, -0.5, 0.5, 1.0]:
        ax.axhline(y_grid, color="#cccccc", linewidth=0.4, zorder=1)
    ax.axhline(0, color="black", linewidth=0.6, zorder=2)

    val_map = {
        "temp":   vals["temp"],                     # already ΔK
        "precip": ratio_to_pct(vals["precip"]),
        "et":     ratio_to_pct(vals["et"]),
        "lai":    ratio_to_pct(vals["lai"]),
    }

    for i, var in enumerate(VARIABLES):
        raw_val  = val_map[var]
        cfg      = VAR_CONFIG[var]
        scale    = scales[var]
        x        = BAR_X_POSITIONS[i]

        # For ET apply display cap
        display_val = raw_val
        clipped     = False
        if var == "et" and abs(raw_val) > ET_DISPLAY_CAP_PCT:
            display_val = ET_DISPLAY_CAP_PCT * np.sign(raw_val)
            clipped     = True

        # Normalise to [-1, +1] relative to this variable's global scale
        norm = display_val / scale if scale != 0 else 0.0

        color = cfg["color"]
        ax.bar(x, norm, width=BAR_WIDTH, color=color,
               alpha=0.82, zorder=3, linewidth=0)

        # Annotate value above (positive) or below (negative) the bar
        if var == "temp":
            label_str = f"{raw_val:+.2f} K"
        else:
            label_str = f"{raw_val:+.1f}%"
            if clipped:
                label_str += " ▶"   # indicate truncation

        # Place text just beyond the bar tip
        y_text = norm + 0.06 * np.sign(norm) if norm != 0 else 0.06
        va = "bottom" if norm >= 0 else "top"
        ax.text(x, y_text, label_str, va=va, ha="center",
                fontsize=5.5, color=color, zorder=4)

    # Axes formatting
    ax.set_ylim(-1.45, 1.45)
    ax.set_xlim(-0.65, (len(VARIABLES) - 1) * BAR_SPACING + 0.65)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    data   = load_data(JSON_PATH)
    scales = compute_global_scales(data)

    seasons = data["seasons"]       # ['DJF', 'MAM', 'JJA', 'SON']
    models  = data["models"]        # 5 models
    n_rows  = len(models)
    n_cols  = len(seasons)

    fig = plt.figure(figsize=(13, 10))

    # Top-level title
    fig.suptitle(
        "GCM Change Factors by Model and Season",
        fontsize=14, y=0.98
    )

    # Build a GridSpec with extra rows/cols for labels
    # Layout: row 0 = season headers, rows 1–5 = data, col 0 = model labels, cols 1–4 = data
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(
        n_rows + 2, n_cols + 1,
        figure=fig,
        top=0.93, bottom=0.22, left=0.08, right=0.97,
        hspace=0.30, wspace=0.15,
        height_ratios=[0.35, 0.20] + [1.0] * n_rows,
        width_ratios=[0.20] + [1.0] * n_cols,
    )

    SEASON_LABELS = {
        "DJF": "Winter (DJF)",
        "MAM": "Spring (MAM)",
        "JJA": "Summer (JJA)",
        "SON": "Fall (SON)",
    }

    # Season header row (row 0, cols 1–4)
    for j, season in enumerate(seasons):
        ax_hdr = fig.add_subplot(gs[0, j + 1])
        ax_hdr.text(0.5, 0.5, SEASON_LABELS[season],
                    ha="center", va="center",
                    fontsize=10,
                    transform=ax_hdr.transAxes)
        ax_hdr.axis("off")

    # Corner cell (row 0, col 0) — blank
    ax_corner = fig.add_subplot(gs[0, 0])
    ax_corner.axis("off")

    # Var-name sub-header row (row 1, cols 1–4)
    ax_blank1 = fig.add_subplot(gs[1, 0])
    ax_blank1.axis("off")
    for j in range(n_cols):
        ax_vhdr = fig.add_subplot(gs[1, j + 1])
        ax_vhdr.set_xlim(-0.65, (len(VARIABLES) - 1) * BAR_SPACING + 0.65)
        ax_vhdr.set_ylim(0, 1)
        for k, var in enumerate(VARIABLES):
            ax_vhdr.text(BAR_X_POSITIONS[k], 0.5, VAR_CONFIG[var]["label"],
                         ha="center", va="center",
                         fontsize=6.5, color=VAR_CONFIG[var]["color"])
        ax_vhdr.axis("off")

    # Data cells
    for i, model in enumerate(models):
        # Model label in col 0
        ax_lbl = fig.add_subplot(gs[i + 2, 0])
        label_text = f"{model['name']}\n({model['quadrant']})"
        ax_lbl.text(0.95, 0.5, label_text,
                    ha="right", va="center",
                    fontsize=9.5,
                    transform=ax_lbl.transAxes)
        ax_lbl.axis("off")

        for j, season in enumerate(seasons):
            ax = fig.add_subplot(gs[i + 2, j + 1])
            vals = model["seasons"][season]
            draw_cell(ax, vals, scales)

    # ---------------------------------------------------------------------------
    # Legend
    # ---------------------------------------------------------------------------
    legend_elements = [
        mpatches.Patch(color=VAR_CONFIG[v]["color"],
                       label=f"{VAR_CONFIG[v]['label']}  ({VAR_CONFIG[v]['unit']})")
        for v in VARIABLES
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=4,
        fontsize=10,
        frameon=True,
        framealpha=0.9,
        bbox_to_anchor=(0.5, 0.145),
    )

    # Subtitle / note — split into two wrapped lines
    line1 = "All values are watershed averages.\n" + \
        "Temperature: max daily temp seasonal mean, mean ΔK\n" + \
        "Precipitation: total seasonal precip, mean % change\n" + \
        "ET: seasonal mean, median % change\n" + \
        "LAI: seasonal mean, median % change\n" + \
        "Bars normalised per variable."
    
    # line2 = textwrap.fill(
    #     f"Bars normalised per variable — global max: "
    #     f"Temp {scales['temp']:.1f} K | Precip {scales['precip']:.0f}% | "
    #     f"ET {ET_DISPLAY_CAP_PCT:.0f}% (display cap) | LAI {scales['lai']:.0f}%.  "
    #     "DJF ET set to no-change (CF = 1.0) for all models: dormant-season baseline < 2 mm/month.",
    #     width=110,
    # )
    fig.text(0.5, 0.10, line1, ha="center", va="top",
             fontsize=7, style="italic", color="#555555")
    # fig.text(0.5, 0.06, line2, ha="center", va="top",
    #          fontsize=7, style="italic", color="#555555")

    # Save
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fig.savefig(OUT_PATH, dpi=180, bbox_inches="tight")
    print(f"Chart saved to: {OUT_PATH}")
    plt.show()


if __name__ == "__main__":
    main()
