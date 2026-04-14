"""
Delta Change Downscaling for L-Range LAI and ET
================================================

Computes multiplicative seasonal change factors from L-Range model output
(historical vs future) and applies them to MODIS observational baselines
to produce bias-corrected future projections.

Processes all GCM model directories found in GCM_future_historical/.

Usage:
    python process_delta_change.py [--variable {et,lai,both}]

Options:
    --variable    Variable(s) to process: et, lai, or both (default: both)

All paths are resolved relative to the repository root.  Edit the
CONFIG section below if your directory layout differs.
"""

import argparse
import os
import sys
import warnings
from datetime import datetime

import numpy as np

# ---------------------------------------------------------------------------
# Resolve paths — this script lives in data_processing/climate_models/L-range/
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir, os.pardir))

sys.path.insert(0, SCRIPT_DIR)
from utils import (
    read_asc_header,
    read_asc,
    write_asc,
    read_mask,
    load_model_et,
    load_model_lai_total,
    load_obs_et,
    load_obs_lai,
)

# ===================================================================
# CONFIG — edit these if paths or periods change
# ===================================================================
DATA_DIR   = os.path.join(REPO_ROOT, "data", "L-range")
GCM_DIR    = os.path.join(DATA_DIR, "GCM_future_historical")
OBS_DIR    = os.path.join(DATA_DIR, "MODIS_baseline_obs")
MASK_PATH  = os.path.join(DATA_DIR, "watershed-mask", "watershed_mask.asc")
OUTPUT_DIRS = {
    "et":  os.path.join(DATA_DIR, "downscaled_output_ET"),
    "lai": os.path.join(DATA_DIR, "downscaled_output_LAI"),
}

HIST_YEARS = range(1990, 2020)       # 30-year historical window
FUTURE_YEARS = range(2035, 2065)     # 30-year future window
OBS_YEARS = range(2006, 2021)        # MODIS baseline (2006–2020 inclusive)

# Season definitions: name -> list of (month, year_offset)
# year_offset = -1 means "December of the previous year"
SEASONS = {
    "DJF": [(12, -1), (1, 0), (2, 0)],
    "MAM": [(3, 0), (4, 0), (5, 0)],
    "JJA": [(6, 0), (7, 0), (8, 0)],
    "SON": [(9, 0), (10, 0), (11, 0)],
}

NODATA = -9999.0
ZERO_THRESHOLD = 1e-6   # treat values below this as zero for CF computation


# ===================================================================
# ARGUMENT PARSING
# ===================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description="Delta change downscaling for L-Range LAI and ET."
    )
    parser.add_argument(
        "--variable",
        choices=["et", "lai", "both"],
        default="both",
        help="Variable(s) to process: et, lai, or both (default: both)",
    )
    return parser.parse_args()


def get_variables(variable_arg):
    if variable_arg == "both":
        return ["et", "lai"]
    return [variable_arg]


# ===================================================================
# CORE FUNCTIONS
# ===================================================================

def generate_mask_if_missing():
    """
    Build and write the unified watershed mask if it does not already exist.

    The mask is the intersection of active cells across all three datasets:
      - GCM model : cells where value != 0.0  (models use 0 for inactive)
      - MODIS ET  : cells where value != NODATA (-9999)
      - MODIS LAI : cells where value != NODATA (-9999)

    Uses one representative file from each dataset.
    Result written as ASC grid: 1 = active, 0 = inactive.
    """
    if os.path.exists(MASK_PATH):
        _, existing = read_asc(MASK_PATH)
        if np.sum(existing == 1) > 0:
            return  # valid mask exists
        print("Watershed mask exists but has 0 active cells — regenerating...")
        os.remove(MASK_PATH)
    else:
        print("Watershed mask not found — generating...")

    # Pick a representative model ET file
    model_file = None
    for model_name in sorted(os.listdir(GCM_DIR)):
        model_dir = os.path.join(GCM_DIR, model_name)
        if not os.path.isdir(model_dir):
            continue
        for yr in (2015, 2010, 2000, 2005, 1995):
            for m in [6, 7, 8, 5, 9, 4, 10, 3, 11, 2, 12, 1]:  # summer months first — avoids all-zero ET files
                candidate = os.path.join(model_dir, f"et____1_{m}_{yr}_avg_cells.asc")
                if os.path.exists(candidate):
                    model_file = candidate
                    break
            if model_file:
                break
        if model_file:
            break
    if model_file is None:
        raise FileNotFoundError(f"No model ET files found in {GCM_DIR} to build mask.")

    # Pick a representative observed ET file
    obs_et_file = None
    et_dir = os.path.join(OBS_DIR, "ET")
    for yr in range(2015, 2005, -1):
        for m in range(1, 13):
            candidate = os.path.join(et_dir, f"et___{yr}_{m:02d}.asc")
            if os.path.exists(candidate):
                obs_et_file = candidate
                break
        if obs_et_file:
            break
    if obs_et_file is None:
        raise FileNotFoundError(f"No observed ET files found in {et_dir} to build mask.")

    # Pick a representative observed LAI file
    obs_lai_file = None
    lai_dir = os.path.join(OBS_DIR, "LAI")
    for yr in range(2015, 2005, -1):
        for m in range(1, 13):
            candidate = os.path.join(lai_dir, f"lai__{yr}_{m:02d}.asc")
            if os.path.exists(candidate):
                obs_lai_file = candidate
                break
        if obs_lai_file:
            break
    if obs_lai_file is None:
        raise FileNotFoundError(f"No observed LAI files found in {lai_dir} to build mask.")

    print(f"  Model ref  : {os.path.relpath(model_file, DATA_DIR)}")
    print(f"  Obs ET ref : {os.path.relpath(obs_et_file, DATA_DIR)}")
    print(f"  Obs LAI ref: {os.path.relpath(obs_lai_file, DATA_DIR)}")

    header, model_data = read_asc(model_file)
    _, obs_et_data     = read_asc(obs_et_file)
    _, obs_lai_data    = read_asc(obs_lai_file)

    active = (
        (model_data  != 0.0)    &
        (obs_et_data != NODATA) &
        (obs_lai_data != NODATA)
    )

    mask_data = active.astype(np.float64)
    mask_header = dict(header)
    mask_header["nodata_value"] = 0.0

    os.makedirs(os.path.dirname(MASK_PATH), exist_ok=True)
    write_asc(MASK_PATH, mask_header, mask_data)
    print(f"  Mask written: {np.sum(active):,} active cells → {os.path.relpath(MASK_PATH, DATA_DIR)}\n")


def get_reference_header(model_dir):
    """Return the ASC header from a representative ET file in model_dir."""
    for yr in (2015, 2010, 2000, 2020, 1995):
        for m in range(1, 13):
            candidate = os.path.join(model_dir, f"et____1_{m}_{yr}_avg_cells.asc")
            if os.path.exists(candidate):
                return read_asc_header(candidate)
    raise FileNotFoundError(f"No ET files found in {model_dir} to read reference header.")


def build_obs_et_bad_pixel_mask(mask):
    """
    Identify bad pixels in MODIS observed ET (water bodies / sensor artifacts).

    The MODIS ET grids are a monthly climatology (12 unique grids repeated
    across years).  Approximately 135–434 cells contain anomalous values
    (negative ET, extreme highs) corresponding to water features and sensor
    artifacts.

    Detection: for each of the 12 calendar months, flag cells whose value
    falls outside 3× the IQR of that month's valid distribution.  A cell
    is flagged bad if it is an outlier in *any* month.

    Returns
    -------
    bad : np.ndarray[bool]  True for bad pixels (same shape as mask)
    """
    # Use one representative year since files are a monthly climatology
    ref_year = 2015
    bad_indices = np.zeros(np.sum(mask), dtype=bool)

    for month in range(1, 13):
        try:
            g = load_obs_et(OBS_DIR, ref_year, month)
        except FileNotFoundError:
            continue
        vals = g[mask]
        valid = vals[vals != NODATA]
        if len(valid) == 0:
            continue
        q1, q3 = np.percentile(valid, [25, 75])
        iqr = q3 - q1
        lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
        outlier = (vals != NODATA) & ((vals < lo) | (vals > hi))
        bad_indices |= outlier

    # Map back to full-grid boolean mask
    bad = np.zeros_like(mask)
    mask_positions = np.where(mask)[0]
    bad[mask_positions[bad_indices]] = True

    return bad


def compute_seasonal_mean_model(variable, season_name, years, mask, model_dir):
    """
    Compute the multi-year seasonal mean for a model variable.

    Parameters
    ----------
    variable : str   "et" or "lai"
    season_name : str   e.g. "DJF"
    years : range   year range for the period
    mask : np.ndarray[bool]   watershed mask
    model_dir : str   path to the model output directory

    Returns
    -------
    mean_grid : np.ndarray (1-D, full grid size, NODATA outside mask)
    count : int   number of monthly grids averaged
    """
    month_specs = SEASONS[season_name]
    grids = []

    for y in years:
        for month, y_offset in month_specs:
            file_year = y + y_offset
            # Check file_year is within the model data range (1990-2065)
            if file_year < 1990 or file_year > 2065:
                continue
            try:
                if variable == "et":
                    g = load_model_et(model_dir, month, file_year)
                else:  # lai
                    g = load_model_lai_total(model_dir, month, file_year)
                grids.append(g)
            except FileNotFoundError:
                print(f"  WARNING: missing model {variable} file month={month} year={file_year}")

    if not grids:
        raise RuntimeError(
            f"No grids found for model {variable} {season_name} years={years[0]}-{years[-1]}"
        )

    stacked = np.stack(grids, axis=0)
    mean_grid = np.mean(stacked, axis=0)

    # Apply mask — set inactive cells to NODATA
    result = np.full_like(mean_grid, NODATA)
    result[mask] = mean_grid[mask]

    return result, len(grids)


def compute_seasonal_mean_obs(variable, season_name, years, mask, bad_pixel_mask=None):
    """
    Compute the multi-year seasonal mean for MODIS observed data.

    Parameters
    ----------
    variable : str   "et" or "lai"
    season_name : str   e.g. "DJF"
    years : range   year range for baseline
    mask : np.ndarray[bool]   watershed mask
    bad_pixel_mask : np.ndarray[bool] or None
        True for known bad pixels to exclude (e.g. MODIS ET artifacts).

    Returns
    -------
    mean_grid : np.ndarray (1-D, full grid size, NODATA outside mask)
    count : int   number of monthly grids averaged
    """
    month_specs = SEASONS[season_name]
    grids = []

    for y in years:
        for month, y_offset in month_specs:
            file_year = y + y_offset
            # Check file_year is within obs range (2006-2020)
            if file_year < 2006 or file_year > 2020:
                continue
            try:
                if variable == "et":
                    g = load_obs_et(OBS_DIR, file_year, month)
                else:  # lai
                    g = load_obs_lai(OBS_DIR, file_year, month)

                # Replace NODATA with NaN for averaging
                g[g == NODATA] = np.nan
                # Mask known bad pixels
                if bad_pixel_mask is not None:
                    g[bad_pixel_mask] = np.nan
                grids.append(g)
            except FileNotFoundError:
                print(f"  WARNING: missing obs {variable} file month={month} year={file_year}")

    if not grids:
        raise RuntimeError(
            f"No grids found for obs {variable} {season_name} years={years[0]}-{years[-1]}"
        )

    stacked = np.stack(grids, axis=0)
    # nanmean ignores NaN (cells that were NODATA in some months).
    # Suppress RuntimeWarning for cells where ALL months are NaN — handled below.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_grid = np.nanmean(stacked, axis=0)

    # Apply mask; replace any remaining NaN with NODATA
    result = np.full_like(mean_grid, NODATA)
    result[mask] = mean_grid[mask]
    result[np.isnan(result)] = NODATA

    return result, len(grids)


def compute_change_factor(hist_grid, future_grid, mask):
    """
    Compute the multiplicative change factor: CF = future / historical.

    Within masked cells:
      - If both hist and future are ≈0: CF = 1.0 (no change)
      - Otherwise: CF = future / hist

    Outside mask: CF = NODATA

    Returns
    -------
    cf_grid : np.ndarray (1-D)
    """
    cf = np.full_like(hist_grid, NODATA)

    h = hist_grid[mask]
    f = future_grid[mask]

    # Default: ratio
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(np.abs(h) > ZERO_THRESHOLD, f / h, 1.0)

    cf[mask] = ratio
    return cf


def apply_change_factor(obs_baseline, cf_grid, mask):
    """
    Apply multiplicative change factor to the observed baseline.

    adjusted = obs_baseline × CF

    Returns
    -------
    adjusted : np.ndarray (1-D, NODATA outside mask)
    """
    adjusted = np.full_like(obs_baseline, NODATA)
    obs_vals = obs_baseline[mask]
    cf_vals = cf_grid[mask]

    # Only apply CF where observed baseline is valid (not NODATA)
    valid = obs_vals != NODATA
    result = np.full_like(obs_vals, NODATA)
    result[valid] = obs_vals[valid] * cf_vals[valid]
    adjusted[mask] = result
    return adjusted


def grid_stats(grid, mask):
    """Return (min, max, mean, median) for valid (non-NODATA) masked cells."""
    vals = grid[mask]
    valid = vals[vals != NODATA]
    if len(valid) == 0:
        return None, None, None, None
    return float(np.min(valid)), float(np.max(valid)), float(np.mean(valid)), float(np.median(valid))


def write_results_analysis(all_model_stats, variable, output_dir):
    """
    Write RESULTS_ANALYSIS.md for a single variable into its output directory.
    The file is (re)written on every run.
    """
    out_path = os.path.join(output_dir, "RESULTS_ANALYSIS.md")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    model_names = sorted(all_model_stats.keys())
    var_upper = variable.upper()

    lines = []
    lines.append(f"# Delta Change Downscaling \u2014 {var_upper} Results Analysis\n\n")
    lines.append(f"*Generated: {now}*\n\n")
    lines.append("---\n\n")
    lines.append("## Run Summary\n\n")
    lines.append("| Parameter | Value |\n|-----------|-------|\n")
    lines.append(f"| Models processed | {len(model_names)} |\n")
    lines.append(f"| Variable | {var_upper} |\n")
    lines.append(f"| Historical period | {HIST_YEARS[0]}\u2013{HIST_YEARS[-1]} |\n")
    lines.append(f"| Future period | {FUTURE_YEARS[0]}\u2013{FUTURE_YEARS[-1]} |\n")
    lines.append(f"| Observational baseline | {OBS_YEARS[0]}\u2013{OBS_YEARS[-1]} |\n\n")
    lines.append("---\n\n")

    LAYER_KEYS = [
        ("hist",   "GCM Historical Seasonal Mean"),
        ("future", "GCM Future Seasonal Mean"),
        ("obs",    "Observational Baseline (MODIS)"),
        ("cf",     "Change Factor (Future / Historical)"),
        ("adj",    "Downscaled Future"),
    ]

    for layer_key, layer_label in LAYER_KEYS:
        lines.append(f"## {var_upper} \u2014 {layer_label}\n\n")
        lines.append("| Model | Season | Min | Max | Mean | Median |\n")
        lines.append("|-------|--------|-----|-----|------|--------|\n")
        for mn in model_names:
            for season in SEASONS:
                s = all_model_stats[mn].get((variable, season), {})
                vals = [s.get(f"{layer_key}_{k}") for k in ("min", "max", "mean", "median")]
                if any(v is None for v in vals):
                    continue
                lines.append(
                    f"| {mn} | {season} | {vals[0]:.4f} | {vals[1]:.4f}"
                    f" | {vals[2]:.4f} | {vals[3]:.4f} |\n"
                )
        lines.append("\n")

    lines.append("*End of results analysis.*\n")

    os.makedirs(output_dir, exist_ok=True)
    with open(out_path, "w") as f:
        f.writelines(lines)
    print(f"  Results analysis written to: {os.path.relpath(out_path, REPO_ROOT)}")


# ===================================================================
# MAIN PIPELINE
# ===================================================================

def main():
    args = parse_args()
    variables = get_variables(args.variable)

    print("=" * 60)
    print("L-Range Delta Change Downscaling")
    print(f"Variable(s): {', '.join(v.upper() for v in variables)}")
    print("=" * 60)

    # --- Verify base paths ---
    for label, path in [("GCM dir", GCM_DIR), ("Obs dir", OBS_DIR)]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    # --- Generate watershed mask if missing ---
    try:
        generate_mask_if_missing()
    except FileNotFoundError as e:
        print(f"ERROR generating mask: {e}")
        sys.exit(1)

    # --- Discover model directories ---
    model_names = sorted([
        d for d in os.listdir(GCM_DIR)
        if os.path.isdir(os.path.join(GCM_DIR, d))
        and any(f.startswith("et____") for f in os.listdir(os.path.join(GCM_DIR, d)))
    ])
    if not model_names:
        print(f"ERROR: No model directories found in {GCM_DIR}")
        sys.exit(1)
    print(f"\nFound {len(model_names)} model(s): {', '.join(model_names)}")

    # --- Load mask and shared reference header ---
    mask = read_mask(MASK_PATH)
    print(f"Watershed mask: {np.sum(mask):,} active cells")
    first_model_dir = os.path.join(GCM_DIR, model_names[0])
    ref_header = get_reference_header(first_model_dir)
    ref_header["nodata_value"] = NODATA
    print(f"Grid: {ref_header['ncols']}×{ref_header['nrows']}, cellsize={ref_header['cellsize']}m")

    # --- Build MODIS ET bad-pixel mask (shared across all models) ---
    et_bad = build_obs_et_bad_pixel_mask(mask)
    print(f"MODIS ET bad pixels: {np.sum(et_bad)} cells excluded\n")

    # --- Compute and write observed baselines once (shared across all models) ---
    print(f"{'─' * 50}")
    print("Computing observational baselines (shared across models)...")
    obs_baselines = {}        # (var, season) -> 1-D grid
    obs_baseline_stats = {}   # (var, season) -> stats dict
    for var in variables:
        seas_root = os.path.join(OUTPUT_DIRS[var], "01_seasonal_means")
        var_upper = var.upper()
        for season in SEASONS:
            bpm = et_bad if var == "et" else None
            obs_mean, n_obs = compute_seasonal_mean_obs(
                var, season, OBS_YEARS, mask, bad_pixel_mask=bpm
            )
            obs_baselines[(var, season)] = obs_mean
            o_min, o_max, o_mean, o_med = grid_stats(obs_mean, mask)
            obs_baseline_stats[(var, season)] = {
                "min": o_min, "max": o_max, "mean": o_mean, "median": o_med
            }
            obs_path = os.path.join(
                seas_root, "obs_baseline", f"{var_upper}_{season}_obs_baseline_MODIS.asc"
            )
            write_asc(obs_path, ref_header, obs_mean)
            print(f"  {var_upper} {season}: mean={o_mean:.4f}, min={o_min:.4f}, max={o_max:.4f} ({n_obs} grids)")

    # --- Per-model stats accumulator ---
    all_model_stats = {}

    # --- Process each model ---
    for model_name in model_names:
        model_dir = os.path.join(GCM_DIR, model_name)
        print(f"\n{'=' * 60}")
        print(f"Model: {model_name}")
        print(f"{'=' * 60}")

        if not any(f.startswith("et____") for f in os.listdir(model_dir)):
            print(f"  WARNING: No ET files found in {model_dir}, skipping.")
            continue

        model_header = get_reference_header(model_dir)
        model_header["nodata_value"] = NODATA
        model_stats = {}

        for var in variables:
            var_upper = var.upper()
            seas_root = os.path.join(OUTPUT_DIRS[var], "01_seasonal_means")
            cf_root   = os.path.join(OUTPUT_DIRS[var], "02_change_factors")
            adj_root  = os.path.join(OUTPUT_DIRS[var], "03_downscaled_future")
            print(f"\n{'─' * 50}")
            print(f"  Variable: {var_upper}")

            for season in SEASONS:
                print(f"\n    Season: {season}")
                stats = {}

                # Copy obs baseline stats (shared, written once above)
                obs_s = obs_baseline_stats[(var, season)]
                stats.update({
                    "obs_min":    obs_s["min"],
                    "obs_max":    obs_s["max"],
                    "obs_mean":   obs_s["mean"],
                    "obs_median": obs_s["median"],
                })

                # 1. Model historical seasonal mean
                print(f"      Computing historical mean ({HIST_YEARS[0]}–{HIST_YEARS[-1]})...")
                hist_mean, n_hist = compute_seasonal_mean_model(
                    var, season, HIST_YEARS, mask, model_dir
                )
                h_min, h_max, h_mean, h_med = grid_stats(hist_mean, mask)
                stats.update({
                    "hist_min": h_min, "hist_max": h_max,
                    "hist_mean": h_mean, "hist_median": h_med,
                })
                print(f"        {n_hist} grids → mean={h_mean:.4f}, min={h_min:.4f}, max={h_max:.4f}")
                write_asc(
                    os.path.join(seas_root, model_name, f"{var_upper}_{season}_model_hist_{model_name}.asc"),
                    model_header, hist_mean,
                )

                # 2. Model future seasonal mean
                print(f"      Computing future mean ({FUTURE_YEARS[0]}–{FUTURE_YEARS[-1]})...")
                future_mean, n_fut = compute_seasonal_mean_model(
                    var, season, FUTURE_YEARS, mask, model_dir
                )
                f_min, f_max, f_mean, f_med = grid_stats(future_mean, mask)
                stats.update({
                    "future_min": f_min, "future_max": f_max,
                    "future_mean": f_mean, "future_median": f_med,
                })
                print(f"        {n_fut} grids → mean={f_mean:.4f}, min={f_min:.4f}, max={f_max:.4f}")
                write_asc(
                    os.path.join(seas_root, model_name, f"{var_upper}_{season}_model_future_{model_name}.asc"),
                    model_header, future_mean,
                )

                # 3. Change factor
                print("      Computing change factor (CF = future / historical)...")
                cf = compute_change_factor(hist_mean, future_mean, mask)
                cf_vals  = cf[mask]
                cf_valid = cf_vals[cf_vals != NODATA]
                cf_min_v  = float(np.min(cf_valid))
                cf_max_v  = float(np.max(cf_valid))
                cf_mean_v = float(np.mean(cf_valid))
                cf_med_v  = float(np.median(cf_valid))
                n_neg_cf  = int(np.sum(cf_valid < 0))
                stats.update({
                    "cf_min": cf_min_v, "cf_max": cf_max_v,
                    "cf_mean": cf_mean_v, "cf_median": cf_med_v,
                    "cf_anomaly_count": n_neg_cf,
                })
                print(f"        CF: mean={cf_mean_v:.4f}, min={cf_min_v:.4f}, max={cf_max_v:.4f}")
                write_asc(
                    os.path.join(cf_root, model_name, f"{var_upper}_{season}_change_factor_{model_name}.asc"),
                    model_header, cf,
                )

                # 4. Apply change factor to observational baseline
                print("      Applying CF to baseline...")
                adjusted = apply_change_factor(obs_baselines[(var, season)], cf, mask)
                a_min, a_max, a_mean, a_med = grid_stats(adjusted, mask)
                stats.update({
                    "adj_min": a_min, "adj_max": a_max,
                    "adj_mean": a_mean, "adj_median": a_med,
                })
                print(f"        Adjusted: mean={a_mean:.4f}, min={a_min:.4f}, max={a_max:.4f}")
                write_asc(
                    os.path.join(adj_root, model_name, f"{var_upper}_{season}_downscaled_future_{model_name}.asc"),
                    model_header, adjusted,
                )

                # Sanity-check notes
                notes = []
                if n_neg_cf > 0:
                    notes.append(f"{n_neg_cf} negative CFs")
                if a_min is not None and a_min < 0:
                    notes.append("negative adj values")
                stats["notes"] = "; ".join(notes) if notes else "—"

                model_stats[(var, season)] = stats

        all_model_stats[model_name] = model_stats

    # --- Write results analysis ---
    for var in variables:
        write_results_analysis(all_model_stats, var, OUTPUT_DIRS[var])

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print("COMPLETE")
    print(f"{'=' * 60}")
    for var in variables:
        print(f"  Output ({var.upper()}): {os.path.relpath(OUTPUT_DIRS[var], REPO_ROOT)}/")


if __name__ == "__main__":
    main()
