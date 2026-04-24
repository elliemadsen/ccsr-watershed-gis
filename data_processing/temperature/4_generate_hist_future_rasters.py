#!/usr/bin/env python3
"""
Step 4: Generate historical and future GCM temperature rasters at 30m

Reads the 6-point seasonal-mean CSVs produced by Step 1 for both
the historical (1990-2019) and future (2035-2064) periods and
IDW-interpolates them to 30m watershed rasters.

Interpolation method: Inverse Distance Weighting (IDW, power=2)
  - Identical approach used in Step 3 for change-factor downscaling
  - 6 GCM grid points in WGS-84 reproduced to the GRIDMET 30m UTM grid

Two variables are processed separately: tasmin (minimum) and tasmax (maximum).

Output locations:
  data/temperature/hist_GCM/   – one TIFF per model × variable × season (1990-2019)
  data/temperature/future_GCM/ – one TIFF per model × variable × season (2035-2064)

Filename convention:
  temp_min_hist_{MODEL}_{SEASON}_1990-2019_30m.tif
  temp_max_hist_{MODEL}_{SEASON}_1990-2019_30m.tif
  temp_min_future_{MODEL}_{SEASON}_2035-2064_30m.tif
  temp_max_future_{MODEL}_{SEASON}_2035-2064_30m.tif

Units: Kelvin (K) — unchanged from GCM source data.

Usage:
    python 4_generate_hist_future_rasters.py
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path

try:
    import rasterio
except ImportError:
    print("ERROR: rasterio is required. Install with: pip install rasterio")
    sys.exit(1)

try:
    from pyproj import Transformer
except ImportError:
    print("ERROR: pyproj is required. Install with: pip install pyproj")
    sys.exit(1)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent

HIST_CSV_DIR   = REPO_ROOT / 'data' / 'temperature' / 'hist_GCM' / 'csv'
FUTURE_CSV_DIR = REPO_ROOT / 'data' / 'temperature' / 'future_GCM' / 'csv'
HIST_OUT_DIR   = REPO_ROOT / 'data' / 'temperature' / 'hist_GCM'
FUTURE_OUT_DIR = REPO_ROOT / 'data' / 'temperature' / 'future_GCM'

# Spatial template: any GRIDMET 30m seasonal raster gives us the target grid
TEMPLATE_RASTER = (REPO_ROOT / 'data' / 'temperature' / 'obs_GRIDMET' /
                   'processed' / 'seasonal' / 'temp_min_final_30m_2006-2020_djf.tif')

MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0']
VARIABLES = ['tasmin', 'tasmax']   # maps to 'min' / 'max' in output filenames
SEASONS = ['DJF', 'MAM', 'JJA', 'SON']

HIST_PERIOD   = '1990-2019'
FUTURE_PERIOD = '2035-2064'


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def load_seasonal_means_csv(csv_path):
    """
    Load a seasonal-means CSV.

    Returns a dict mapping season (upper-case) to a numpy array of
    6 grid-cell values in column order (units: K).
    """
    df = pd.read_csv(csv_path, index_col=0)
    df.columns = [c.strip().strip('"') for c in df.columns]
    return {season: df.loc[season].values.astype(float) for season in df.index}


def parse_coords(csv_path):
    """
    Extract (lon, lat) coordinate tuples from the column headers of a seasonal CSV.
    Column format: "(lat, lon)" — note lat first, lon second.
    Returns an array of shape (n_points, 2) with columns [lon, lat].
    """
    df = pd.read_csv(csv_path, index_col=0, nrows=0)
    coords = []
    for col in df.columns:
        col = col.strip().strip('"')
        lat_s, lon_s = col.strip('()').split(',')
        coords.append((float(lon_s), float(lat_s)))
    return np.array(coords)   # shape (n_points, 2), columns: [lon, lat]


def load_template(template_path):
    """Load spatial metadata and valid-pixel mask from the template raster."""
    with rasterio.open(template_path) as src:
        profile = src.profile.copy()
        transform = src.transform
        shape = (src.height, src.width)
        crs = src.crs
        nodata = src.nodata if src.nodata is not None else -9999.0
        data = src.read(1)
        valid_mask = (data != nodata) & np.isfinite(data)
    return profile, transform, shape, crs, nodata, valid_mask


def idw_interpolate(cf_coords_lonlat, cf_values, target_shape, target_transform,
                    target_crs, source_crs='EPSG:4326', power=2):
    """
    IDW interpolation from n point values (lon/lat) to a 30m raster grid.

    Parameters
    ----------
    cf_coords_lonlat : ndarray (n, 2)  columns [lon, lat] in source_crs
    cf_values        : ndarray (n,)
    target_shape     : (height, width)
    target_transform : affine.Affine
    target_crs       : rasterio CRS of the output raster
    source_crs       : CRS string of the input coordinates
    power            : IDW power (default 2)

    Returns
    -------
    2D ndarray, shape == target_shape
    """
    transformer = Transformer.from_crs(source_crs, str(target_crs), always_xy=True)
    cf_x, cf_y = transformer.transform(cf_coords_lonlat[:, 0], cf_coords_lonlat[:, 1])
    cf_pts = np.column_stack([cf_x, cf_y])

    height, width = target_shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(target_transform, rows, cols)
    target_pts = np.column_stack([np.array(xs).ravel(), np.array(ys).ravel()])

    # Pairwise distances  (n_target × n_source)
    dists = np.sqrt(((target_pts[:, np.newaxis, :] - cf_pts[np.newaxis, :, :]) ** 2).sum(axis=2))
    dists = np.maximum(dists, 1e-10)

    weights = 1.0 / (dists ** power)
    weights /= weights.sum(axis=1, keepdims=True)

    interpolated = (weights * cf_values[np.newaxis, :]).sum(axis=1)
    return interpolated.reshape(height, width)


def save_raster(data, profile, out_path, nodata):
    """Write a float32 raster to disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    p = profile.copy()
    p.update(dtype='float32', count=1, nodata=nodata, compress='lzw')
    with rasterio.open(out_path, 'w', **p) as dst:
        dst.write(data.astype('float32'), 1)
    print(f"  Saved: {out_path.relative_to(REPO_ROOT)}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    if not TEMPLATE_RASTER.exists():
        print(f"ERROR: template raster not found: {TEMPLATE_RASTER}")
        sys.exit(1)

    profile, transform, shape, crs, nodata, valid_mask = load_template(TEMPLATE_RASTER)
    print(f"Template raster: {TEMPLATE_RASTER.name}")
    print(f"  Shape: {shape}, CRS: {crs}\n")

    # Extract GCM grid coordinates from first available CSV (same for all models)
    first_csv = HIST_CSV_DIR / f'seasonal_means_historical_{MODELS[0]}_tasmin_ssp370.csv'
    coords_lonlat = parse_coords(first_csv)
    print(f"GCM grid points: {len(coords_lonlat)}\n")

    for model in MODELS:
        print(f"Processing: {model}")

        for variable in VARIABLES:
            var_label = 'min' if variable == 'tasmin' else 'max'

            hist_csv   = HIST_CSV_DIR   / f'seasonal_means_historical_{model}_{variable}_ssp370.csv'
            future_csv = FUTURE_CSV_DIR / f'seasonal_means_future_{model}_{variable}_ssp370.csv'

            hist_means   = load_seasonal_means_csv(hist_csv)
            future_means = load_seasonal_means_csv(future_csv)

            for season in SEASONS:
                season_lc = season.lower()

                # Historical
                hist_grid = idw_interpolate(coords_lonlat, hist_means[season],
                                            shape, transform, crs)
                hist_grid[~valid_mask] = nodata
                save_raster(hist_grid, profile,
                            HIST_OUT_DIR / f'temp_{var_label}_hist_{model}_{season_lc}_{HIST_PERIOD}_30m.tif',
                            nodata)

                # Future
                future_grid = idw_interpolate(coords_lonlat, future_means[season],
                                              shape, transform, crs)
                future_grid[~valid_mask] = nodata
                save_raster(future_grid, profile,
                            FUTURE_OUT_DIR / f'temp_{var_label}_future_{model}_{season_lc}_{FUTURE_PERIOD}_30m.tif',
                            nodata)

        print()

    print("Done.")


if __name__ == '__main__':
    main()
