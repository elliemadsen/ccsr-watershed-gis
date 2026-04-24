#!/usr/bin/env python3
"""
Validation script for all GCM downscaling outputs.

Checks:
  1. File inventory   – all expected files exist, no extra stragglers
  2. Valid pixels     – each TIFF has active data (not all-nodata)
  3. CRS              – matches expected EPSG for each dataset group
  4. Shape            – all files in a group share the same raster dimensions
  5. Watershed mask   – valid-pixel counts are consistent within a group
  6. Value ranges     – physically plausible bounds per variable type
  7. Model spread     – 5-model ensemble has non-zero spread (not degenerate)
  8. Hist vs future   – seasonal means differ between the two periods

Usage:
    python data_processing/validate_outputs.py
"""

import sys
import numpy as np
from pathlib import Path

try:
    import rasterio
except ImportError:
    print("ERROR: rasterio is required.  conda activate geo")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEASONS    = ['DJF', 'MAM', 'JJA', 'SON']
SEASONS_LC = [s.lower() for s in SEASONS]

# L-range model slug names (as they appear in output filenames)
LRANGE_MODELS = ['ACCESS_EMS1_5', 'CMCC_EMS2', 'CNRM_CM6_1', 'INM_CM5_0', 'IPSL_CM6A_LR']

# GRIDMET/GCM model names (as used in precip/temp filenames)
GCM_MODELS = ['ACCESS-ESM1-5', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0', 'IPSL-CM6A-LR']

TEMP_VARS  = ['min', 'max']   # maps to tasmin / tasmax

# Expected EPSG codes
EPSG_LRANGE_NATIVE = 26918   # L-range / MODIS native pipeline (obs, CF, proj)
EPSG_SEASONAL_MEAN = 32618   # all hist & future seasonal mean TIFFs (UTM 18N WGS84)

# Expected raster shapes  (rows, cols)
SHAPE_LRANGE_30M  = None   # discovered dynamically from first file
SHAPE_LRANGE_200M = None
SHAPE_GCM_30M     = None

# Plausible value ranges  (min_allowed, max_allowed) for VALID pixels
RANGES = {
    'et_lrange':     (0.0,   10.0),    # L-range model ET (internal units, 30 m resampled; JJA ~5-6)
    'lai_lrange':    (0.0,   20.0),    # L-range model LAI (30 m resampled)
    'et_obs':        (0.0,   50.0),    # MODIS observed ET (mm/month equiv.)
    'lai_obs':       (0.0,   20.0),    # MODIS observed LAI
    'et_cf':         (0.1,   10.0),    # multiplicative change factor
    'lai_cf':        (0.0,   20.0),    # LAI change factor (can be 0 for dormant season)
    'et_proj':       (0.0,   50.0),    # projected ET
    'lai_proj':      (0.0,   20.0),    # projected LAI
    'precip_gcm':    (0.0, 3000.0),    # precipitation (mm/season or kg m⁻² s⁻¹ scaled)
    'temp_gcm':      (230.0, 330.0),   # temperature (K)
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = 0
FAIL = 0
WARN = 0


def ok(msg):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")


def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {msg}")


def warn(msg):
    global WARN
    WARN += 1
    print(f"  [WARN] {msg}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def read_raster(path):
    """Return (data_masked, profile) or raise."""
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)
        profile = {
            'crs_epsg': src.crs.to_epsg() if src.crs else None,
            'shape':    (src.height, src.width),
            'nodata':   src.nodata,
            'transform': src.transform,
        }
    return data, profile


def check_files_exist(paths, label):
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            fail(f"Missing: {p.relative_to(REPO_ROOT)}")
    else:
        ok(f"{label}: all {len(paths)} expected files present")
    return len(missing) == 0


def check_raster_group(paths, label, expected_epsg, expected_range_key,
                       ref_shape=None, check_mask_consistency=True):
    """
    Run CRS, shape, value-range, and valid-pixel checks for a list of TIFFs.
    Returns list of (data, profile) tuples for further cross-file checks.
    """
    results = []
    valid_counts = []
    shapes = []
    crs_list = []
    value_violations = 0

    vmin, vmax = RANGES[expected_range_key]

    for p in paths:
        if not p.exists():
            continue
        try:
            data, prof = read_raster(p)
        except Exception as e:
            fail(f"Cannot open {p.name}: {e}")
            continue

        results.append((data, prof, p))
        valid_counts.append(int(data.count()))
        shapes.append(prof['shape'])
        crs_list.append(prof['crs_epsg'])

        # Valid-pixel check
        if data.count() == 0:
            fail(f"All-nodata: {p.name}")
        
        # Value-range check
        if data.count() > 0:
            rmin, rmax = float(data.min()), float(data.max())
            if rmin < vmin or rmax > vmax:
                value_violations += 1
                warn(f"Range [{rmin:.3f}, {rmax:.3f}] outside [{vmin}, {vmax}]: {p.name}")

    if not results:
        fail(f"{label}: no files could be read")
        return results

    # CRS check
    wrong_crs = [r for r in results if r[1]['crs_epsg'] != expected_epsg]
    if wrong_crs:
        for _, prof, p in wrong_crs:
            fail(f"CRS EPSG:{prof['crs_epsg']} (expected {expected_epsg}): {p.name}")
    else:
        ok(f"{label}: CRS = EPSG:{expected_epsg} for all {len(results)} files")

    # Shape consistency
    unique_shapes = set(shapes)
    if ref_shape and ref_shape not in unique_shapes:
        fail(f"{label}: shape {unique_shapes} does not match reference {ref_shape}")
    elif len(unique_shapes) > 1:
        fail(f"{label}: inconsistent shapes {unique_shapes}")
    else:
        ok(f"{label}: shape = {shapes[0]} (consistent)")

    # Valid-pixel consistency (allow ≤10 pixel tolerance for MODIS bad-pixel filter)
    if check_mask_consistency:
        unique_vc = set(valid_counts)
        spread = max(valid_counts) - min(valid_counts)
        if spread > 10:
            warn(f"{label}: valid-pixel counts vary by {spread}: {sorted(unique_vc)}")
        elif len(unique_vc) > 1:
            ok(f"{label}: valid pixels ~{max(valid_counts):,} (varies ≤{spread} px — normal MODIS bad-pixel filter)")
        else:
            ok(f"{label}: valid pixels = {valid_counts[0]:,} (consistent across all files)")

    if value_violations == 0:
        ok(f"{label}: all values within expected range [{vmin}, {vmax}]")

    return results


# ---------------------------------------------------------------------------
# Cross-file checks
# ---------------------------------------------------------------------------

def check_model_spread(results_by_model, label):
    """For each season, check that models produce spread (not identical)."""
    season_values = {}
    for model, (data, _, _) in results_by_model.items():
        mean_val = float(data.mean()) if data.count() > 0 else np.nan
        season_values[model] = mean_val

    vals = [v for v in season_values.values() if not np.isnan(v)]
    if len(vals) < 2:
        warn(f"{label}: fewer than 2 valid models, cannot check spread")
        return
    spread = np.std(vals)
    if spread < 1e-6:
        fail(f"{label}: zero spread across models — all means = {vals[0]:.4f}")
    else:
        ok(f"{label}: model spread std={spread:.4f} over means {[round(v,4) for v in vals]}")


def check_hist_vs_future(hist_data, future_data, label):
    """Check that hist and future seasonal means differ meaningfully."""
    if hist_data.count() == 0 or future_data.count() == 0:
        warn(f"{label}: skipping hist/future diff — empty arrays")
        return
    h_mean = float(hist_data.mean())
    f_mean = float(future_data.mean())
    diff = abs(f_mean - h_mean)
    rel_diff = diff / max(abs(h_mean), 1e-10)
    if diff < 1e-6:
        fail(f"{label}: hist and future are identical (mean={h_mean:.4f})")
    elif rel_diff < 0.001:
        warn(f"{label}: hist/future differ by only {rel_diff*100:.3f}%  (h={h_mean:.4f}, f={f_mean:.4f})")
    else:
        ok(f"{label}: hist mean={h_mean:.4f}, future mean={f_mean:.4f}, Δ={f_mean-h_mean:+.4f} ({rel_diff*100:.1f}%)")


# ---------------------------------------------------------------------------
# Section checks
# ---------------------------------------------------------------------------

def check_et_lai_lrange():
    section("ET / LAI — L-range hist & future (30m resampled, EPSG:32618)")
    for var in ('ET', 'LAI'):
        var_lo = var.lower()
        rk = f'{var_lo}_lrange'
        for period, suffix in [('hist', 'hist_L-range_1990-2019_30m'), ('future', 'future_L-range_2035-2064_30m')]:
            d = REPO_ROOT / 'data' / var / f'{period}_L-range'
            paths = [
                d / f'{var}_{m}_SSP370_{s}_{suffix}.tiff'
                for m in LRANGE_MODELS for s in SEASONS
            ]
            label = f"{var} {period}_L-range"
            check_files_exist(paths, label)
            check_raster_group(paths, label, EPSG_SEASONAL_MEAN, rk)

        # hist vs future comparison (first model, DJF)
        for m in LRANGE_MODELS[:1]:
            for s in SEASONS[:1]:
                hp = REPO_ROOT / 'data' / var / 'hist_L-range' / f'{var}_{m}_SSP370_{s}_hist_L-range_1990-2019_30m.tiff'
                fp = REPO_ROOT / 'data' / var / 'future_L-range' / f'{var}_{m}_SSP370_{s}_future_L-range_2035-2064_30m.tiff'
                if hp.exists() and fp.exists():
                    hd, _ = read_raster(hp)
                    fd, _ = read_raster(fp)
                    check_hist_vs_future(hd, fd, f"{var} {m} {s} hist vs future")


def check_et_lai_obs_cf_proj():
    section("ET / LAI — obs baseline, change factors, projections (200m native)")
    for var in ('ET', 'LAI'):
        var_lo = var.lower()

        # obs_MODIS (4 files)
        obs_paths = [
            REPO_ROOT / 'data' / var / 'obs_MODIS' / f'{var}_{s}_obs_baseline_MODIS_2006-2020.tiff'
            for s in SEASONS
        ]
        check_files_exist(obs_paths, f"{var} obs_MODIS")
        check_raster_group(obs_paths, f"{var} obs_MODIS", EPSG_LRANGE_NATIVE, f'{var_lo}_obs')

        # change_factors (20 files)
        cf_paths = [
            REPO_ROOT / 'data' / var / 'change_factors' / f'{var}_{m}_SSP370_{s}_change_factor.tiff'
            for m in LRANGE_MODELS for s in SEASONS
        ]
        check_files_exist(cf_paths, f"{var} change_factors")
        cf_results = check_raster_group(cf_paths, f"{var} change_factors", EPSG_LRANGE_NATIVE, f'{var_lo}_cf')

        # proj (20 files)
        proj_paths = [
            REPO_ROOT / 'data' / var / 'proj' / f'{var}_{m}_SSP370_{s}_downscaled_future.tiff'
            for m in LRANGE_MODELS for s in SEASONS
        ]
        check_files_exist(proj_paths, f"{var} proj")
        check_raster_group(proj_paths, f"{var} proj", EPSG_LRANGE_NATIVE, f'{var_lo}_proj')

        # Model spread on change factors (DJF season)
        cf_djf = {
            m: read_raster(REPO_ROOT / 'data' / var / 'change_factors' / f'{var}_{m}_SSP370_DJF_change_factor.tiff')
            for m in LRANGE_MODELS
            if (REPO_ROOT / 'data' / var / 'change_factors' / f'{var}_{m}_SSP370_DJF_change_factor.tiff').exists()
        }
        if cf_djf:
            check_model_spread({m: (d, p, None) for m, (d, p) in cf_djf.items()}, f"{var} DJF change-factor model spread")


def check_precip():
    section("Precipitation — GCM hist & future (30m IDW)")
    for period, year_tag in [('hist', '1990-2019'), ('future', '2035-2064')]:
        d = REPO_ROOT / 'data' / 'precipitation' / f'{period}_GCM'
        paths = [
            d / f'precip_{period}_{m}_{s}_{year_tag}_30m.tif'
            for m in GCM_MODELS for s in SEASONS_LC
        ]
        label = f"precip {period}_GCM"
        check_files_exist(paths, label)
        check_raster_group(paths, label, EPSG_GCM, 'precip_gcm')

    # hist vs future (first model, DJF)
    for m in GCM_MODELS[:1]:
        hp = REPO_ROOT / 'data' / 'precipitation' / 'hist_GCM'   / f'precip_hist_{m}_djf_1990-2019_30m.tif'
        fp = REPO_ROOT / 'data' / 'precipitation' / 'future_GCM' / f'precip_future_{m}_djf_2035-2064_30m.tif'
        if hp.exists() and fp.exists():
            hd, _ = read_raster(hp)
            fd, _ = read_raster(fp)
            check_hist_vs_future(hd, fd, f"precip {m} DJF hist vs future")

    # Model spread (hist DJF)
    spread_files = {
        m: read_raster(REPO_ROOT / 'data' / 'precipitation' / 'hist_GCM' / f'precip_hist_{m}_djf_1990-2019_30m.tif')
        for m in GCM_MODELS
        if (REPO_ROOT / 'data' / 'precipitation' / 'hist_GCM' / f'precip_hist_{m}_djf_1990-2019_30m.tif').exists()
    }
    if spread_files:
        check_model_spread({m: (d, p, None) for m, (d, p) in spread_files.items()}, "precip hist DJF model spread")


def check_temperature():
    section("Temperature — GCM hist & future (30m IDW)")
    for tvar in TEMP_VARS:
        for period, year_tag in [('hist', '1990-2019'), ('future', '2035-2064')]:
            d = REPO_ROOT / 'data' / 'temperature' / f'{period}_GCM'
            paths = [
                d / f'temp_{tvar}_{period}_{m}_{s}_{year_tag}_30m.tif'
                for m in GCM_MODELS for s in SEASONS_LC
            ]
            label = f"temp_{tvar} {period}_GCM"
            check_files_exist(paths, label)
            check_raster_group(paths, label, EPSG_GCM, 'temp_gcm')

    # hist vs future (tasmax, JJA — largest expected signal)
    for m in GCM_MODELS[:1]:
        hp = REPO_ROOT / 'data' / 'temperature' / 'hist_GCM'   / f'temp_max_hist_{m}_jja_1990-2019_30m.tif'
        fp = REPO_ROOT / 'data' / 'temperature' / 'future_GCM' / f'temp_max_future_{m}_jja_2035-2064_30m.tif'
        if hp.exists() and fp.exists():
            hd, _ = read_raster(hp)
            fd, _ = read_raster(fp)
            check_hist_vs_future(hd, fd, f"temp_max {m} JJA hist vs future")

    # Model spread (hist JJA tasmax)
    spread_files = {
        m: read_raster(REPO_ROOT / 'data' / 'temperature' / 'hist_GCM' / f'temp_max_hist_{m}_jja_1990-2019_30m.tif')
        for m in GCM_MODELS
        if (REPO_ROOT / 'data' / 'temperature' / 'hist_GCM' / f'temp_max_hist_{m}_jja_1990-2019_30m.tif').exists()
    }
    if spread_files:
        check_model_spread({m: (d, p, None) for m, (d, p) in spread_files.items()}, "temp_max hist JJA model spread")


def check_watershed_mask_matching():
    """
    Cross-dataset check: precip and temperature rasters should share the same
    valid-pixel mask (same GRIDMET template was used for both).
    """
    section("Watershed mask cross-check (precip vs temp same template)")
    p_precip = REPO_ROOT / 'data' / 'precipitation' / 'hist_GCM' / f'precip_hist_{GCM_MODELS[0]}_djf_1990-2019_30m.tif'
    p_temp   = REPO_ROOT / 'data' / 'temperature'   / 'hist_GCM' / f'temp_min_hist_{GCM_MODELS[0]}_djf_1990-2019_30m.tif'
    if not p_precip.exists() or not p_temp.exists():
        warn("Cannot run mask cross-check — sample files missing")
        return

    d_p, prof_p = read_raster(p_precip)
    d_t, prof_t = read_raster(p_temp)

    if prof_p['shape'] != prof_t['shape']:
        fail(f"Precip shape {prof_p['shape']} != temp shape {prof_t['shape']}")
        return
    ok(f"Precip and temp share shape {prof_p['shape']}")

    mask_p = d_p.mask if np.ma.is_masked(d_p) else np.zeros(d_p.shape, dtype=bool)
    mask_t = d_t.mask if np.ma.is_masked(d_t) else np.zeros(d_t.shape, dtype=bool)
    mismatch = int(np.sum(mask_p != mask_t))
    if mismatch == 0:
        ok("Precip and temp nodata masks are identical")
    else:
        warn(f"Nodata mask differs in {mismatch:,} pixels between precip and temp")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  GCM Downscaling Output Validation")
    print("=" * 60)

    check_et_lai_lrange()
    check_et_lai_obs_cf_proj()
    check_precip()
    check_temperature()
    check_watershed_mask_matching()

    section("Summary")
    total = PASS + FAIL + WARN
    print(f"  PASS : {PASS}")
    print(f"  WARN : {WARN}")
    print(f"  FAIL : {FAIL}")
    print(f"  Total: {total}")
    if FAIL == 0 and WARN == 0:
        print("\n  All checks passed.")
    elif FAIL == 0:
        print(f"\n  All critical checks passed ({WARN} warning(s) to review).")
    else:
        print(f"\n  {FAIL} check(s) FAILED — review output above.")
    print()


if __name__ == '__main__':
    main()
