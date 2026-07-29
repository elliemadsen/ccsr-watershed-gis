#!/usr/bin/env python3
"""
detect_events.py

Detect perturbations ("disturbance events") in a Cannonsville vegetation/
moisture residual time series, following the method of Smith et al. (2022,
Nat. Clim. Change), Methods section "Perturbation detection and recovery
analysis": https://www.nature.com/articles/s41558-022-01352-2#Sec6

Supported datasets (--data, default VOD):
  VOD         — VODCA daily CSV (data/VOD/VODCA_CXKu_Cannonsville.csv),
                resampled to monthly means
  LAI_GIMMS   — GIMMS LAI3g monthly rasters
                (data/LAI/raw_data/processed_monthly/)
  LAI_MODIS   — MODIS LAI monthly rasters
                (data/L-Range/MODIS_baseline_obs/LAI/)

Pipeline:
  1. The monthly series for the chosen dataset is de-trended (STL by default,
     matching csd_analysis.py) to obtain a residual series.
  2. An 18-point (9-month) moving window is passed over the residual series.
     Within each window we compute either:
       - method 1 ("moving_average"): the mean of the second half of the
         window minus the mean of the first half, or
       - method 2 ("linear_fit"): the slope of an OLS line fit through the
         window.
     The result is assigned to the window's center time step, producing a
     derivative time series.
  3. The derivative series is smoothed with a Savitzky-Golay filter
     (7 points, first-order polynomial) to remove high-frequency noise.
  4. Any |derivative| above the 99th percentile is flagged; consecutive
     flagged time steps are grouped into a single disturbance period, and the
     time step with the largest |derivative| within each period is taken as
     the perturbation date.

The paper notes results are nearly identical between the two methods, so
method 1 (moving_average) is the default; method 2 is provided for
comparison via --method.

Output is written to events/{data}/, so runs on different datasets don't
overwrite each other.

Usage:
  python detect_events.py
  python detect_events.py --data LAI_GIMMS
  python detect_events.py --data LAI_MODIS --method both
  python detect_events.py --detrend climatology --percentile 97.5
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

plt.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size":          8,
    "axes.titlesize":     8,
    "axes.labelsize":     8,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.fontsize":    8,
    "figure.dpi":         300,
    "savefig.dpi":        300,
})

sys.path.insert(0, str(Path(__file__).parent.parent / "csd_analysis"))
import csd_analysis as csd  # reuses load_vod / load_lai_gimms / load_lai_modis / detrend / STL conventions

OUT_DIR = Path(__file__).parent / "events"

# Cannonsville, NY — smaller sub-basins-bbox boundary (data/sub-basins/Subbasins.shp
# extent), distinct from csd_analysis.py's VOD_CSV/load_vod(), which uses the larger
# Cannonsville_NY catchment rectangle. csd_analysis.py is left untouched; this loader
# reuses its CSV-reading logic but points at the smaller-boundary file directly.
CANNONSVILLE_SMALL_CSV = csd.VOD_DIR / "VODCA_CXKu_Cannonsville.csv"


def load_vod_cannonsville_small() -> pd.Series:
    return csd._load_vod_csv(CANNONSVILLE_SMALL_CSV, "VOD", csd.MIN_OBS_MONTHLY)


DATA_LOADERS = {
    "VOD": load_vod_cannonsville_small,
    "LAI_GIMMS": csd.load_lai_gimms,
    "LAI_MODIS": csd.load_lai_modis,
}

WINDOW_POINTS = 18      # 18-point (9-month) moving window, per paper
SAVGOL_WINDOW = 7       # Savitzky-Golay window length, per paper
SAVGOL_POLYORDER = 1    # Savitzky-Golay polynomial order, per paper
PERCENTILE = 99.0       # perturbation threshold, per paper


# ---------------------------------------------------------------------------
# Derivative methods
# ---------------------------------------------------------------------------

def moving_average_derivative(residual: pd.Series, window: int = WINDOW_POINTS) -> pd.Series:
    """
    Method 1: for each `window`-point window, take the mean of the second
    half minus the mean of the first half. Assigned to the window's center
    time step. NaN wherever the window contains any missing value.
    """
    half = window // 2
    values = residual.to_numpy(dtype=float)
    n = len(values)
    out = np.full(n, np.nan)

    for end in range(window - 1, n):
        start = end - window + 1
        chunk = values[start:end + 1]
        if np.isnan(chunk).any():
            continue
        first_half = chunk[:half]
        second_half = chunk[half:]
        center = start + half
        out[center] = second_half.mean() - first_half.mean()

    return pd.Series(out, index=residual.index, name="deriv_moving_average")


def linear_fit_derivative(residual: pd.Series, window: int = WINDOW_POINTS) -> pd.Series:
    """
    Method 2: for each `window`-point window, fit an OLS line and take the
    slope. Assigned to the window's center time step. NaN wherever the
    window contains any missing value.
    """
    half = window // 2
    values = residual.to_numpy(dtype=float)
    n = len(values)
    out = np.full(n, np.nan)
    x = np.arange(window, dtype=float)

    for end in range(window - 1, n):
        start = end - window + 1
        chunk = values[start:end + 1]
        if np.isnan(chunk).any():
            continue
        slope, _ = np.polyfit(x, chunk, 1)
        center = start + half
        out[center] = slope

    return pd.Series(out, index=residual.index, name="deriv_linear_fit")


# ---------------------------------------------------------------------------
# Smoothing and event detection
# ---------------------------------------------------------------------------

def savgol_smooth(series: pd.Series, window_length: int = SAVGOL_WINDOW,
                   polyorder: int = SAVGOL_POLYORDER) -> pd.Series:
    """
    Apply a Savitzky-Golay filter to `series`. NaNs (window warm-up at the
    series edges, or gaps from missing VOD months) are linearly interpolated
    before filtering and re-masked to NaN afterward, so missing data is never
    fabricated into the output.
    """
    nan_mask = series.isna()
    filled = series.interpolate(method="linear", limit_direction="both")
    smoothed = savgol_filter(filled.to_numpy(dtype=float), window_length, polyorder)
    result = pd.Series(smoothed, index=series.index, name=series.name + "_savgol")
    result[nan_mask] = np.nan
    return result


def detect_perturbations(deriv_smoothed: pd.Series, percentile: float = PERCENTILE) -> pd.DataFrame:
    """
    Flag time steps where |deriv_smoothed| exceeds the given percentile,
    group consecutive flagged steps into disturbance periods, and take the
    largest |value| within each period as the perturbation date.

    Returns a DataFrame with one row per disturbance period:
      start, end, peak_date, peak_value, threshold, n_points
    """
    abs_vals = deriv_smoothed.abs()
    valid = abs_vals.dropna()
    threshold = float(np.percentile(valid.to_numpy(), percentile))

    flagged = (abs_vals > threshold).to_numpy()
    flagged_idx = np.where(flagged)[0]

    if len(flagged_idx) == 0:
        return pd.DataFrame(columns=["start", "end", "peak_date", "peak_value", "threshold", "n_points"])

    breaks = np.where(np.diff(flagged_idx) != 1)[0] + 1
    groups = np.split(flagged_idx, breaks)

    rows = []
    for group in groups:
        group_vals = abs_vals.iloc[group]
        peak_pos = group[np.argmax(group_vals.to_numpy())]
        rows.append({
            "start": deriv_smoothed.index[group[0]],
            "end": deriv_smoothed.index[group[-1]],
            "peak_date": deriv_smoothed.index[peak_pos],
            "peak_value": deriv_smoothed.iloc[peak_pos],
            "threshold": threshold,
            "n_points": len(group),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

# Style guide palette: magma colormap, sampled at fixed points for consistency
# with the other figures in this project (see csd_analysis.py VOD_SITE_COLORS).
_magma = plt.cm.magma
RESIDUAL_COLOR   = _magma(0.42)
DERIVATIVE_COLOR = _magma(0.68)
POSITIVE_COLOR   = _magma(0.80)   # greening (positive) perturbation
NEGATIVE_COLOR   = _magma(0.22)   # browning (negative) perturbation
EVENT_LABEL_FMT = "%b %Y"           # e.g. "Jul 1994"


def _event_color(peak_value: float):
    """Magma high sample for a positive (greening) perturbation, low sample for negative (browning)."""
    return POSITIVE_COLOR if peak_value > 0 else NEGATIVE_COLOR


def _annotate_event(ax: plt.Axes, ev: pd.Series, color: str) -> None:
    """Offset the label away from the dot/line, above for peaks, below for troughs."""
    dy = 10 if ev["peak_value"] > 0 else -10
    va = "bottom" if ev["peak_value"] > 0 else "top"
    ax.annotate(ev["peak_date"].strftime(EVENT_LABEL_FMT), xy=(ev["peak_date"], ev["peak_value"]),
                xytext=(8, dy), textcoords="offset points", ha="left", va=va,
                color=color, fontsize=8)


def _add_yearly_ticks(ax: plt.Axes) -> None:
    """Major ticks/labels as chosen by matplotlib, plus an unlabeled minor tick mark every year."""
    ax.xaxis.set_minor_locator(mdates.YearLocator())
    ax.tick_params(axis="x", which="minor", length=4)


def plot_results(residual: pd.Series, deriv_smoothed: pd.Series,
                  events: pd.DataFrame, out_path: Path,
                  data_name: str = "VOD") -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    axes[0].plot(residual.index, residual.values, color=RESIDUAL_COLOR, lw=1)
    axes[0].set_ylabel(f"{data_name} residual")
    axes[0].text(0.01, 0.97, "a", transform=axes[0].transAxes,
                 fontsize=11, fontweight="bold", va="top", ha="left")
    for _, ev in events.iterrows():
        color = _event_color(ev["peak_value"])
        axes[0].axvspan(ev["start"], ev["end"], color=color, alpha=0.2)
        axes[0].axvline(ev["peak_date"], color=color, lw=1, ls="--")
        axes[0].annotate(ev["peak_date"].strftime(EVENT_LABEL_FMT), xy=(ev["peak_date"], 1),
                          xycoords=("data", "axes fraction"),
                          xytext=(4, -2), textcoords="offset points", ha="left", va="top",
                          color=color, fontsize=8)

    axes[1].plot(deriv_smoothed.index, deriv_smoothed.values, color=DERIVATIVE_COLOR, lw=1)
    axes[1].margins(y=0.15)
    if not events.empty:
        thresh = events["threshold"].iloc[0]
        axes[1].axhline(thresh, color=POSITIVE_COLOR, lw=0.8, ls=":")
        axes[1].axhline(-thresh, color=NEGATIVE_COLOR, lw=0.8, ls=":")
        for _, ev in events.iterrows():
            color = _event_color(ev["peak_value"])
            axes[1].scatter(ev["peak_date"], ev["peak_value"], color=color, zorder=5)
            _annotate_event(axes[1], ev, color)
    axes[1].set_ylabel("Smoothed derivative")
    axes[1].set_xlabel("Date")
    axes[1].text(0.01, 0.97, "b", transform=axes[1].transAxes,
                 fontsize=11, fontweight="bold", va="top", ha="left")
    for ax in axes:
        _add_yearly_ticks(ax)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def plot_derivative_only(deriv_smoothed: pd.Series, events: pd.DataFrame,
                          out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(deriv_smoothed.index, deriv_smoothed.values, color=DERIVATIVE_COLOR, lw=1)
    ax.margins(y=0.15)
    ax.set_ylabel("Smoothed derivative")
    ax.set_xlabel("Date")
    if not events.empty:
        thresh = events["threshold"].iloc[0]
        ax.axhline(thresh, color=POSITIVE_COLOR, lw=0.8, ls=":")
        ax.axhline(-thresh, color=NEGATIVE_COLOR, lw=0.8, ls=":")
        for _, ev in events.iterrows():
            color = _event_color(ev["peak_value"])
            ax.scatter(ev["peak_date"], ev["peak_value"], color=color, zorder=5)
            _annotate_event(ax, ev, color)
    _add_yearly_ticks(ax)

    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", choices=list(DATA_LOADERS.keys()), default="VOD",
                         help="Dataset to detect perturbations in (default: VOD).")
    parser.add_argument("--detrend", choices=["stl", "climatology"], default="stl",
                         help="De-trending method used to obtain the residual series (default: stl).")
    parser.add_argument("--method", choices=["moving_average", "linear_fit", "both"], default="moving_average",
                         help="Derivative method (default: moving_average, per the paper's primary method).")
    parser.add_argument("--window-points", type=int, default=WINDOW_POINTS,
                         help=f"Moving window length in months (default: {WINDOW_POINTS}).")
    parser.add_argument("--savgol-window", type=int, default=SAVGOL_WINDOW,
                         help=f"Savitzky-Golay filter window length (default: {SAVGOL_WINDOW}).")
    parser.add_argument("--savgol-polyorder", type=int, default=SAVGOL_POLYORDER,
                         help=f"Savitzky-Golay polynomial order (default: {SAVGOL_POLYORDER}).")
    parser.add_argument("--percentile", type=float, default=PERCENTILE,
                         help=f"Percentile threshold for flagging perturbations (default: {PERCENTILE}).")
    parser.add_argument("--no-plot", action="store_true", help="Skip generating plots.")
    return parser.parse_args()


def run_method(residual: pd.Series, method: str, args: argparse.Namespace) -> tuple[pd.Series, pd.DataFrame]:
    if method == "moving_average":
        deriv = moving_average_derivative(residual, args.window_points)
    else:
        deriv = linear_fit_derivative(residual, args.window_points)

    smoothed = savgol_smooth(deriv, args.savgol_window, args.savgol_polyorder)
    events = detect_perturbations(smoothed, args.percentile)
    return smoothed, events


def main() -> None:
    args = parse_args()
    data_name = args.data
    data_out_dir = OUT_DIR / data_name
    data_out_dir.mkdir(parents=True, exist_ok=True)

    monthly_series = DATA_LOADERS[data_name]()
    clim_start, clim_end = csd.CLIM_PERIODS[data_name]
    residual = csd.detrend(monthly_series, args.detrend, clim_start, clim_end)

    n_missing = int(residual.isna().sum())
    if n_missing:
        print(f"Note: {n_missing}/{len(residual)} months of the {data_name} residual are missing. "
              "These are linearly interpolated before the moving window is applied — with this "
              f"dataset's gaps, requiring all {args.window_points} points in every window to be "
              "observed leaves zero valid windows.")
    residual_filled = residual.interpolate(method="linear", limit_direction="both")

    methods = ["moving_average", "linear_fit"] if args.method == "both" else [args.method]

    for method in methods:
        smoothed, events = run_method(residual_filled, method, args)

        print(f"\n=== {method} ===")
        print(f"{len(events)} perturbation(s) detected (threshold = "
              f"{events['threshold'].iloc[0]:.4g} at the {args.percentile}th percentile)"
              if not events.empty else "No perturbations detected.")
        if not events.empty:
            print(events[["start", "end", "peak_date", "peak_value", "n_points"]]
                  .to_string(index=False))

        tag = f"{method}_{args.detrend}_p{args.percentile:g}"
        csv_path = data_out_dir / f"{data_name}_perturbations_{tag}.csv"
        events.to_csv(csv_path, index=False)
        print(f"Saved: {csv_path}")

        if not args.no_plot:
            plot_path = data_out_dir / f"{data_name}_perturbations_{tag}.png"
            plot_results(residual, smoothed, events, plot_path, data_name=data_name)
            print(f"Saved: {plot_path}")

            deriv_plot_path = data_out_dir / f"{data_name}_perturbations_{tag}_derivative_only.png"
            plot_derivative_only(smoothed, events, deriv_plot_path)
            print(f"Saved: {deriv_plot_path}")


if __name__ == "__main__":
    main()
