#!/usr/bin/env python3
"""
generate_figures.py

Generate the paper's VOD figures from csd_analysis.py / perturbation_detection.py
output. The multi-catchment figures (ac1_var_graphs, ac1_var_combined_graphs,
ac1_changepoint_analysis, var_changepoint_analysis, pre_post_analysis) read the
per-site CSVs in SITE_CSVS below rather than csd_analysis_output.csv, since the
single-CSV pipeline only ever covers one VOD site. SITE_CSVS are placeholders
 — update them as needed. The perturbations figure needs the underlying smoothed-derivative
curve, which perturbation_detection_output.csv does not store (only the detected
events), so it is recomputed here from the original VOD CSV.

Usage:
  python generate_figures.py path/to/vod.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from csd_analysis import load_vod, compute_residuals, phase_surrogate_test
from perturbation_detection import moving_average_derivative, savgol_smooth

plt.rcParams.update({
    "font.family":     "sans-serif",
    "font.sans-serif": ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size":       8,
    "axes.titlesize":  8,
    "axes.labelsize":  8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi":      300,
    "savefig.dpi":     300,
})

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parents[3]
FIG_DIR = Path(__file__).parent / "figures"
PERTURBATION_OUTPUT_CSV = Path(__file__).parent / "perturbation_detection_output.csv"

SPLIT_DATE = pd.Timestamp("2000-01-01")  # changepoint used to produce the SITE_CSVS below

# Multi-site AC-1/variance CSVs (one per VOD water-supply catchment), each produced
# by the full multi-site csd_analysis.py (data_processing/resiliency/csd_analysis/)
# with --changepoint 2000-01. Placeholders pointing at that existing run — replace
# with new paths if the multi-site analysis is re-run.
_VOD_ALL_DIR = REPO_ROOT / "data_processing" / "resiliency" / "csd_analysis" / "output" / "VOD_all"
_SPLIT_TAG = "win10y_step12_climatology_split200001_nsurr1000"
SITE_CSVS = {
    "Hinckley_NY":      _VOD_ALL_DIR / "Hinckley_NY" / f"Hinckley_NY_{_SPLIT_TAG}.csv",
    "Cannonsville_NY": _VOD_ALL_DIR / "Cannonsville_NY" / f"Cannonsville_NY_{_SPLIT_TAG}.csv",
    "Sebago_ME":        _VOD_ALL_DIR / "Sebago_ME" / f"Sebago_ME_{_SPLIT_TAG}.csv",
    "Alcove_NY":        _VOD_ALL_DIR / "Alcove_NY" / f"Alcove_NY_{_SPLIT_TAG}.csv",
    "Scituate_RI":      _VOD_ALL_DIR / "Scituate_RI" / f"Scituate_RI_{_SPLIT_TAG}.csv",
    "Hemlock_NY":       _VOD_ALL_DIR / "Hemlock_NY" / f"Hemlock_NY_{_SPLIT_TAG}.csv",
    "Barkhamsted_CT":   _VOD_ALL_DIR / "Barkhamsted_CT" / f"Barkhamsted_CT_{_SPLIT_TAG}.csv",
    "Quabbin_MA":       _VOD_ALL_DIR / "Quabbin_MA" / f"Quabbin_MA_{_SPLIT_TAG}.csv",
    "Wachusett_MA":     _VOD_ALL_DIR / "Wachusett_MA" / f"Wachusett_MA_{_SPLIT_TAG}.csv",
    "Massabesic_NH":    _VOD_ALL_DIR / "Massabesic_NH" / f"Massabesic_NH_{_SPLIT_TAG}.csv",
}

_magma = plt.cm.magma
SITE_COLORS = {k: _magma(t) for k, t in zip(SITE_CSVS, np.linspace(0.15, 0.88, len(SITE_CSVS)))}
TAC_COLOR = _magma(0.25)
VAR_COLOR = _magma(0.65)
PRE_COLOR = _magma(0.25)
POST_COLOR = _magma(0.68)
DERIVATIVE_COLOR = _magma(0.68)
POSITIVE_COLOR = _magma(0.80)
NEGATIVE_COLOR = _magma(0.22)


def display_site(site: str) -> str:
    """'City_ST' -> 'City, ST' for panel titles/labels."""
    city, state = site.rsplit("_", 1)
    return f"{city}, {state}"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_site_csvs() -> dict[str, pd.DataFrame]:
    return {
        site: pd.read_csv(path, parse_dates=["centre_date"], index_col="centre_date")
        for site, path in SITE_CSVS.items()
    }


def _pre_post_split(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    series = series.dropna()
    return series[series.index < SPLIT_DATE], series[series.index >= SPLIT_DATE]

# ---------------------------------------------------------------------------
# Figure 1: perturbations (smoothed derivative + detected events)
# ---------------------------------------------------------------------------

def _event_color(peak_value: float):
    return POSITIVE_COLOR if peak_value > 0 else NEGATIVE_COLOR


def plot_perturbations(vod_csv: Path, out_path: Path) -> None:
    """
    Recompute the smoothed derivative curve (moving_average method, matching
    perturbation_detection.py's default) and overlay the events already
    detected in perturbation_detection_output.csv.
    """
    residual = compute_residuals(load_vod(vod_csv))
    residual_filled = residual.interpolate(method="linear", limit_direction="both")
    smoothed = savgol_smooth(moving_average_derivative(residual_filled))
    events = pd.read_csv(PERTURBATION_OUTPUT_CSV, parse_dates=["start", "end", "peak_date"])

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(smoothed.index, smoothed.values, color=DERIVATIVE_COLOR, lw=1)
    ax.margins(y=0.15)
    ax.set_ylabel("Smoothed derivative")
    ax.set_xlabel("Date")

    if not events.empty:
        threshold = events["threshold"].iloc[0]
        ax.axhline(threshold, color=POSITIVE_COLOR, lw=0.8, ls=":")
        ax.axhline(-threshold, color=NEGATIVE_COLOR, lw=0.8, ls=":")
        for _, ev in events.iterrows():
            color = _event_color(ev["peak_value"])
            ax.scatter(ev["peak_date"], ev["peak_value"], color=color, zorder=5)
            dy = 10 if ev["peak_value"] > 0 else -10
            va = "bottom" if ev["peak_value"] > 0 else "top"
            ax.annotate(ev["peak_date"].strftime("%b %Y"), xy=(ev["peak_date"], ev["peak_value"]),
                        xytext=(8, dy), textcoords="offset points", ha="left", va=va,
                        color=color, fontsize=8)

    ax.xaxis.set_minor_locator(mdates.YearLocator())
    ax.tick_params(axis="x", which="minor", length=4)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

# ---------------------------------------------------------------------------
# Figure 2: AC-1 and variance overlaid across all catchments
# ---------------------------------------------------------------------------

def plot_ac1_var_graphs(site_data: dict[str, pd.DataFrame], out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    ylabels = {"TAC": "AC-1", "Var": "Normalized variance"}
    for row_i, metric in enumerate(["TAC", "Var"]):
        ax = axes[row_i]
        for site, df in site_data.items():
            ax.plot(df.index, df[metric], color=SITE_COLORS[site], linewidth=1.6,
                    marker="o", markersize=3, label=display_site(site), alpha=0.85)
        ax.axvline(SPLIT_DATE, color="black", linewidth=1, linestyle="--", alpha=0.5)
        ax.set_ylabel(ylabels[metric])
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(ncol=3, loc="best")
    axes[-1].set_xlabel("Centre date")
    fig.suptitle("CSD indicators - all VOD catchments", fontsize=9, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

# ---------------------------------------------------------------------------
# Figure 3: AC-1 and variance combined, one panel per catchment
# ---------------------------------------------------------------------------

def plot_ac1_var_combined_graphs(site_data: dict[str, pd.DataFrame], out_path: Path) -> None:
    sites = list(site_data)
    nrows, ncols = 5, 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.5 * nrows), sharex=True)
    axes_flat = axes.flatten()

    for i, site in enumerate(sites):
        ax = axes_flat[i]
        df = site_data[site]
        ax.plot(df.index, df["TAC"], color=TAC_COLOR, linewidth=1.5,
                marker="o", markersize=3.5, alpha=0.9)
        ax.set_ylabel("AC-1", color=TAC_COLOR)
        ax.tick_params(axis="y", labelcolor=TAC_COLOR)

        ax_var = ax.twinx()
        ax_var.plot(df.index, df["Var"], color=VAR_COLOR, linewidth=1.5,
                    linestyle="--", marker="s", markersize=3.5, alpha=0.9)
        ax_var.set_ylabel("Normalized variance", color=VAR_COLOR)
        ax_var.tick_params(axis="y", labelcolor=VAR_COLOR)
        ax_var.grid(False)

        ax.set_title(display_site(site), pad=3)
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.tick_params(axis="x", labelbottom=True)

    for ax in axes_flat[len(sites):]:
        ax.set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("Centre date")

    fig.suptitle("AC-1 and Variance by catchment", fontsize=9, y=0.978)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

# ---------------------------------------------------------------------------
# Figures 4-5: per-catchment changepoint grids (AC-1, variance)
# ---------------------------------------------------------------------------

def plot_changepoint_grid(site_data: dict[str, pd.DataFrame], metric: str, ylabel: str, out_path: Path) -> None:
    """
    5x2 grid, one panel per catchment: `metric` over time, changepoint at
    SPLIT_DATE, background shaded red/blue where a segment's phase-surrogate
    trend is significantly increasing/decreasing, tau/p annotated per segment.
    """
    sites = list(site_data)
    nrows, ncols = 5, 2
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 3.8 * nrows))
    axes_flat = axes.flatten()

    for i, site in enumerate(sites):
        ax = axes_flat[i]
        df = site_data[site]
        series = df[metric]
        color = TAC_COLOR if metric == "TAC" else SITE_COLORS[site]

        pre, post = _pre_post_split(series)
        seg_results = [
            ("pre", phase_surrogate_test(pre) if len(pre) >= 4 else None, series.index.min(), SPLIT_DATE),
            ("post", phase_surrogate_test(post) if len(post) >= 4 else None, SPLIT_DATE, series.index.max()),
        ]
        for _, res, lo, hi in seg_results:
            if res is not None and not np.isnan(res["tau"]) and res["p"] < 0.05:
                c = "#ffe8e8" if res["tau"] > 0 else "#e8eeff"
                ax.axvspan(lo, hi, color=c, alpha=0.45, zorder=0, lw=0)
        ax.axvline(SPLIT_DATE, color="dimgray", linewidth=1.2, linestyle="--", alpha=0.7)

        ax.plot(df.index, series, color=color, linewidth=1.5, marker="o", markersize=3, alpha=0.9)
        ax.set_title(display_site(site), pad=3)
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", rotation=90)

        parts = []
        for name, res, _, _ in seg_results:
            if res is None or np.isnan(res["tau"]):
                parts.append(f"{name}: n<4")
            else:
                parts.append(f"{name}: τ={res['tau']:+.2f} p={res['p']:.2f}{'*' if res['p'] < 0.05 else ''}")
        ax.annotate("   ".join(parts), xy=(0.98, 0.04), xycoords="axes fraction", va="bottom", ha="right",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.65, lw=0))

    for ax in axes_flat[len(sites):]:
        ax.set_visible(False)

    fig.suptitle(f"{ylabel} by catchment - changepoint {SPLIT_DATE.strftime('%Y-%m')}\n"
                 "background: red = sig. increasing post-split, blue = sig. decreasing (phase-surrogate p<0.05)",
                 fontsize=9, y=0.978)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

# ---------------------------------------------------------------------------
# Figure 6: pre/post-2000 regime-shift analysis (scatter + arrow chart)
# ---------------------------------------------------------------------------

def _site_pre_post_tau(site_data: dict[str, pd.DataFrame], metric: str = "TAC") -> dict[str, tuple]:
    results = {}
    for site, df in site_data.items():
        pre, post = _pre_post_split(df[metric])
        if len(pre) < 4 or len(post) < 4:
            continue
        pre_res, post_res = phase_surrogate_test(pre), phase_surrogate_test(post)
        results[site] = (pre_res["tau"], post_res["tau"], pre_res["p"] < 0.05, post_res["p"] < 0.05)
    return results


def plot_pre_post_analysis(site_data: dict[str, pd.DataFrame], out_path: Path) -> None:
    """(a) pre- vs. post-2000 Kendall tau scatter, (b) dot-and-arrow chart of the same
    transition per catchment, for AC-1."""
    pp = _site_pre_post_tau(site_data, "TAC")
    sites = list(pp)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, max(6.5, 0.55 * len(sites) + 1.8)),
                              gridspec_kw={"width_ratios": [1.0, 1.15]})

    ax = axes[0]
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.6)
    ax.axvline(0, color="black", linewidth=0.8, alpha=0.6)

    qpad = 0.15
    for qx, qy, label in [(-qpad, qpad, r"dec $\rightarrow$ inc"), (qpad, qpad, r"inc $\rightarrow$ inc"),
                           (-qpad, -qpad, r"dec $\rightarrow$ dec"), (qpad, -qpad, r"inc $\rightarrow$ dec")]:
        ax.text(qx, qy, label, ha="center", va="center", color="grey",
                bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))

    # Nearby labels (e.g. two catchments with similar pre/post tau) land on top
    # of each other since each is placed at a fixed offset from its dot. A
    # small vertical-only repulsion — nudge labels whose dots are close in
    # both x and y apart in y — declutters those without moving labels far
    # from their dot.
    text_y = {site: pp[site][1] for site in sites}
    min_sep, x_thresh = 0.06, 0.2
    for _ in range(50):
        moved = False
        for site_i in sites:
            for site_j in sites:
                if site_i >= site_j or abs(pp[site_i][0] - pp[site_j][0]) > x_thresh:
                    continue
                gap = text_y[site_j] - text_y[site_i]
                if abs(gap) < min_sep:
                    push = (min_sep - abs(gap)) / 2
                    sign = 1 if gap >= 0 else -1
                    text_y[site_i] -= sign * push
                    text_y[site_j] += sign * push
                    moved = True
        if not moved:
            break

    for site in sites:
        pre_tau, post_tau, _, post_sig = pp[site]
        ax.scatter(pre_tau, post_tau, s=110, zorder=4,
                   color=POST_COLOR if post_sig else "none",
                   edgecolors=POST_COLOR, linewidths=2.0)
        ax.annotate(display_site(site), (pre_tau, post_tau), xytext=(9, text_y[site]),
                    textcoords=("offset points", "data"), ha="left", va="center", zorder=5)
    ax.set_xlabel("Pre-2000 Kendall τ (AC-1)")
    ax.set_ylabel("Post-2000 Kendall τ (AC-1)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(handles=[
        Line2D([0], [0], marker="o", color="w", markerfacecolor=POST_COLOR,
               markeredgecolor=POST_COLOR, markeredgewidth=1.5, markersize=10,
               label="Significant post-2000 (phase-surrogate p < 0.05)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="none",
               markeredgecolor=POST_COLOR, markeredgewidth=1.5, markersize=10,
               label="Not significant post-2000 (phase-surrogate p ≥ 0.05)"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, frameon=False, labelspacing=1.2)

    ax2 = axes[1]
    y = np.arange(len(sites))
    ax2.set_xlim(-1, 1); ax2.set_ylim(y.min() - 0.6, y.max() + 0.6)
    ax2.axvspan(-1, 0, color="#e8eeff", alpha=0.45, zorder=0, lw=0)
    ax2.axvspan(0, 1, color="#ffe8e8", alpha=0.45, zorder=0, lw=0)
    ax2.text(0.25, 0.985, "Decreasing autocorrelation", transform=ax2.transAxes,
              ha="center", va="top", fontsize=8, bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))
    ax2.text(0.75, 0.985, "Increasing autocorrelation", transform=ax2.transAxes,
              ha="center", va="top", fontsize=8, bbox=dict(fc="white", alpha=0.6, lw=0, pad=2))
    for i, site in enumerate(sites):
        pre_tau, post_tau, pre_sig, post_sig = pp[site]
        both_sig = pre_sig and post_sig
        ax2.annotate("", xy=(post_tau, y[i]), xytext=(pre_tau, y[i]), zorder=3,
                     arrowprops=dict(arrowstyle="-|>", color="black",
                                      alpha=0.75 if both_sig else 0.30,
                                      linestyle="solid" if both_sig else "dotted",
                                      linewidth=1.3, shrinkA=6, shrinkB=6))
        ax2.scatter(pre_tau, y[i], s=70, zorder=4,
                    facecolor=PRE_COLOR if pre_sig else "none", edgecolor=PRE_COLOR, linewidth=1.5)
        ax2.scatter(post_tau, y[i], s=70, zorder=4,
                    facecolor=POST_COLOR if post_sig else "none", edgecolor=POST_COLOR, linewidth=1.5)
    ax2.axvline(0, color="black", linewidth=0.8, alpha=0.6)
    ax2.set_yticks(y)
    ax2.set_yticklabels([display_site(s) for s in sites])
    ax2.set_xlabel("Kendall τ (AC-1)")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.35, zorder=0)
    ax2.legend(handles=[
        Line2D([0], [0], marker="o", color="w", markerfacecolor=PRE_COLOR,
               markeredgecolor=PRE_COLOR, markersize=9, label="pre-2000"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=POST_COLOR,
               markeredgecolor=POST_COLOR, markersize=9, label="post-2000"),
        Line2D([0, 1], [0, 0], color="black", alpha=0.75, linestyle="solid",
               linewidth=1.3, label="Significant trend both pre- and post-2000"),
        Line2D([0, 1], [0, 0], color="black", alpha=0.30, linestyle="dotted",
               linewidth=1.3, label="Not significant pre- and/or post-2000"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)

    for letter, a in zip("ab", axes):
        a.text(-0.02, 1.03, letter, transform=a.transAxes, fontsize=11,
               fontweight="bold", va="bottom", ha="left")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_path}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "vod_csv", type=Path,
        help="Path to the VOD CSV used to produce perturbation_detection_output.csv "
             "(needed to recompute the smoothed derivative curve for the perturbations figure).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    print("Perturbations figure...")
    plot_perturbations(args.vod_csv, FIG_DIR / "perturbations.png")

    print("Loading multi-site AC-1/variance CSVs...")
    site_data = load_site_csvs()

    print("AC-1 + variance overlay (all catchments)...")
    plot_ac1_var_graphs(site_data, FIG_DIR / "ac1_var_graphs.png")

    print("AC-1 + variance combined grid (one panel per catchment)...")
    plot_ac1_var_combined_graphs(site_data, FIG_DIR / "ac1_var_combined_graphs.png")

    print("AC-1 changepoint grid...")
    plot_changepoint_grid(site_data, "TAC", "AC-1", FIG_DIR / "ac1_changepoint_analysis.png")

    print("Variance changepoint grid...")
    plot_changepoint_grid(site_data, "Var", "Normalized variance", FIG_DIR / "var_changepoint_analysis.png")

    print("Pre/post-2000 regime-shift analysis...")
    plot_pre_post_analysis(site_data, FIG_DIR / "pre_post_analysis.png")

    print(f"\nAll figures saved to {FIG_DIR}")


if __name__ == "__main__":
    main()
