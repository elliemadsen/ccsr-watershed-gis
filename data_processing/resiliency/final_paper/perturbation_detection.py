#!/usr/bin/env python3
"""
perturbation_detection.py

Detect discrete perturbations in a VOD residual time series. VOD is deseasonalized by
subtracting each calendar month's climatological mean (see csd_analysis.py's
compute_residuals). A WINDOW_POINTS-point moving window is passed over the residual
series. Within each window we compute either moving_average (default, mean of the
second half of the window minus the mean of the first half) or linear_fit (the slope
of an OLS line fit through the window) and assign to the window's centre time step,
producing a derivative series. The derivative series is smoothed with a first-order
Savitzky-Golay filter to remove high-frequency noise. Time steps where |smoothed
derivative| exceeds the PERCENTILE threshold (default 95) are flagged; consecutive
flagged steps are grouped into one disturbance event, and the step with the largest
|derivative| in each event is taken as the perturbation date. Because both derivative
methods require every point in their window to be valid, missing months in the
residual series are linearly interpolated before the moving window is applied.


Usage:
  python perturbation_detection.py path/to/vod.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from csd_analysis import load_vod, compute_residuals

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOW_POINTS = 18       # 9-month moving window
SAVGOL_WINDOW = 7        # Savitzky-Golay filter window length
SAVGOL_POLYORDER = 1     # Savitzky-Golay polynomial order
PERCENTILE = 95.0        # perturbation threshold

OUT_CSV = Path(__file__).parent / "perturbation_detection_output.csv"

# ---------------------------------------------------------------------------
# Derivative methods
# ---------------------------------------------------------------------------

def moving_average_derivative(residual: pd.Series) -> pd.Series:
    """
    For each WINDOW_POINTS-point window, the mean of the second half minus
    the mean of the first half, assigned to the window's centre time step.
    NaN wherever the window contains any missing value.
    """
    half = WINDOW_POINTS // 2
    values = residual.to_numpy(dtype=float)
    n = len(values)
    out = np.full(n, np.nan)
    for end in range(WINDOW_POINTS - 1, n):
        start = end - WINDOW_POINTS + 1
        chunk = values[start:end + 1]
        if np.isnan(chunk).any():
            continue
        out[start + half] = chunk[half:].mean() - chunk[:half].mean()
    return pd.Series(out, index=residual.index, name="deriv_moving_average")


def linear_fit_derivative(residual: pd.Series) -> pd.Series:
    """
    For each WINDOW_POINTS-point window, the slope of an OLS line fit
    through the window, assigned to the window's centre time step. NaN
    wherever the window contains any missing value.
    """
    half = WINDOW_POINTS // 2
    values = residual.to_numpy(dtype=float)
    n = len(values)
    out = np.full(n, np.nan)
    x = np.arange(WINDOW_POINTS, dtype=float)
    for end in range(WINDOW_POINTS - 1, n):
        start = end - WINDOW_POINTS + 1
        chunk = values[start:end + 1]
        if np.isnan(chunk).any():
            continue
        slope, _ = np.polyfit(x, chunk, 1)
        out[start + half] = slope
    return pd.Series(out, index=residual.index, name="deriv_linear_fit")

# ---------------------------------------------------------------------------
# Smoothing and event detection
# ---------------------------------------------------------------------------

def savgol_smooth(series: pd.Series) -> pd.Series:
    """
    Apply a Savitzky-Golay filter to `series`. NaNs (window warm-up at the
    series edges, or gaps in the source data) are linearly interpolated
    before filtering and re-masked to NaN afterward.
    """
    nan_mask = series.isna()
    filled = series.interpolate(method="linear", limit_direction="both")
    smoothed = savgol_filter(filled.to_numpy(dtype=float), SAVGOL_WINDOW, SAVGOL_POLYORDER)
    result = pd.Series(smoothed, index=series.index, name=series.name + "_savgol")
    result[nan_mask] = np.nan
    return result


def detect_perturbations(deriv_smoothed: pd.Series) -> pd.DataFrame:
    """
    Flag time steps where |deriv_smoothed| exceeds the PERCENTILE threshold,
    group consecutive flagged steps into disturbance events, and take the
    largest |value| within each event as the perturbation date.

    Returns a DataFrame with one row per event:
      start, end, peak_date, peak_value, threshold, n_points
    """
    abs_vals = deriv_smoothed.abs()
    threshold = float(np.percentile(abs_vals.dropna().to_numpy(), PERCENTILE))
    flagged_idx = np.where((abs_vals > threshold).to_numpy())[0]

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
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vod_csv", type=Path, help="Path to a VODCA daily CSV (columns: date, VOD_mean).")
    parser.add_argument(
        "--method", choices=["moving_average", "linear_fit"], default="moving_average",
        help="Derivative method (default: moving_average, the primary method).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Loading {args.vod_csv} ...")
    monthly = load_vod(args.vod_csv)
    residual = compute_residuals(monthly)

    n_missing = int(residual.isna().sum())
    if n_missing:
        print(f"Note: {n_missing}/{len(residual)} months missing; linearly interpolated "
              "before the moving window is applied.")
    residual_filled = residual.interpolate(method="linear", limit_direction="both")

    deriv = (moving_average_derivative(residual_filled) if args.method == "moving_average"
             else linear_fit_derivative(residual_filled))
    smoothed = savgol_smooth(deriv)
    events = detect_perturbations(smoothed)

    if events.empty:
        print("No perturbations detected.")
    else:
        print(f"{len(events)} perturbation(s) detected "
              f"(threshold = {events['threshold'].iloc[0]:.4g} at the {PERCENTILE:g}th percentile)")
        print(events[["start", "end", "peak_date", "peak_value", "n_points"]].to_string(index=False))

    events.to_csv(OUT_CSV, index=False)
    print(f"\nSaved: {OUT_CSV}")


if __name__ == "__main__":
    main()
