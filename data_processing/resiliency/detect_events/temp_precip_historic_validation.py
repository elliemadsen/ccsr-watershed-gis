#!/usr/bin/env python3
"""
temp_precip_historic_validation.py

Historic validation of GRIDMET seasonal precipitation and maximum temperature
over the watershed, using the full available daily record:

    data/precipitation/obs_GRIDMET/raw/precip_raw_4000m_{year}.nc   (1990-present)
    data/temperature/obs_GRIDMET/raw/max/tmmx_raw_4000m_{year}.nc   (2006-present)

For each variable, daily values are averaged spatially over the watershed
(bounding box + 5km buffer, matching the convention used in
data_processing/{precipitation,temperature}/0_process_gridmet/process_gridmet.py),
then aggregated to seasonal (DJF/MAM/JJA/SON) values per year:
    - precipitation: seasonal total (mm)
    - max temperature: seasonal mean (deg C)

Two figures are produced per variable:
    1. Raw seasonal time series, one panel per season, with the long-term
       seasonal mean and +/-1 / +/-2 standard deviation bands so anomalous
       years are easy to spot.
    2. A rolling (10-year window) standard deviation of the seasonal values,
       one panel per season, to show whether variability/anomaly magnitude
       is changing over time.

Usage:
    python temp_precip_historic_validation.py
    python temp_precip_historic_validation.py --rolling-window 8
"""

import argparse
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Transformer

warnings.filterwarnings('ignore')

REPO_ROOT = Path(__file__).parent.parent.parent.parent
OUT_DIR = Path(__file__).parent / "historic_validation"

PRECIP_DIR = REPO_ROOT / 'data' / 'precipitation' / 'obs_GRIDMET' / 'raw'
TMAX_DIR = REPO_ROOT / 'data' / 'temperature' / 'obs_GRIDMET' / 'raw' / 'max'
WATERSHED_PATH = REPO_ROOT / 'data' / 'sub-basins' / 'Subbasins.shp'

SEASONS = ['DJF', 'MAM', 'JJA', 'SON']
SEASON_NAMES = {'DJF': 'Winter (DJF)', 'MAM': 'Spring (MAM)',
                'JJA': 'Summer (JJA)', 'SON': 'Fall (SON)'}
BUFFER_M = 5000


def get_watershed_bounds_lonlat(watershed_path=WATERSHED_PATH, buffer_m=BUFFER_M):
    """Watershed bounding box (with buffer) in lon/lat, matching process_gridmet.py."""
    watershed = gpd.read_file(watershed_path)
    minx, miny, maxx, maxy = watershed.total_bounds
    minx -= buffer_m
    miny -= buffer_m
    maxx += buffer_m
    maxy += buffer_m

    transformer = Transformer.from_crs(watershed.crs, "EPSG:4326", always_xy=True)
    minlon, minlat = transformer.transform(minx, miny)
    maxlon, maxlat = transformer.transform(maxx, maxy)
    return minlon, minlat, maxlon, maxlat


def clip_lonlat(ds, bounds):
    minlon, minlat, maxlon, maxlat = bounds
    lat_ascending = bool(ds.lat[0] < ds.lat[-1])
    if lat_ascending:
        return ds.sel(lon=slice(minlon, maxlon), lat=slice(minlat, maxlat))
    return ds.sel(lon=slice(minlon, maxlon), lat=slice(maxlat, minlat))


def load_daily_series(raw_dir, filename_template, var_name, bounds=None, year_range=None):
    """
    Build a daily watershed-mean series from yearly GRIDMET netCDFs.

    Args:
        raw_dir (Path): directory containing the yearly .nc files
        filename_template (str): e.g. "precip_raw_4000m_{year}.nc"
        var_name (str): data variable name within each file
        bounds (tuple or None): lon/lat bounds to clip to; if None, the file
            is assumed to already be clipped (as GRIDMET temperature raw is)
        year_range (tuple): (start_year, end_year) inclusive to scan for

    Returns:
        pd.Series indexed by date
    """
    pieces = []
    found_years = []
    for year in range(year_range[0], year_range[1] + 1):
        f = raw_dir / filename_template.format(year=year)
        if not f.exists():
            continue
        ds = xr.open_dataset(f)
        if bounds is not None:
            ds = clip_lonlat(ds, bounds)
        daily_mean = ds[var_name].mean(dim=['lat', 'lon'])
        s = daily_mean.to_series()
        s.index = pd.to_datetime(ds['day'].values)
        pieces.append(s)
        found_years.append(year)
        ds.close()

    if not pieces:
        raise FileNotFoundError(f"No files found in {raw_dir} matching {filename_template} "
                                 f"for years {year_range[0]}-{year_range[1]}")

    series = pd.concat(pieces).sort_index()
    print(f"  Loaded {raw_dir.name}: years {min(found_years)}-{max(found_years)} "
          f"({len(found_years)} files, {len(series)} daily values)")
    return series


def to_seasonal(series, how='mean'):
    """
    Aggregate a daily series to one value per (season, season-year).

    Winter (DJF) is assigned to the year of January/February, matching
    standard meteorological-season convention (Dec belongs to the
    following year's winter).

    Returns:
        pd.DataFrame with columns ['season', 'season_year', 'value']
    """
    df = series.to_frame('value')
    df['season'] = df.index.month % 12 // 3 + 1  # 1=DJF,2=MAM,3=JJA,4=SON (Dec->DJF of next)
    season_map = {1: 'DJF', 2: 'MAM', 3: 'JJA', 4: 'SON'}
    df['season'] = df['season'].map(season_map)
    df['season_year'] = df.index.year
    df.loc[df.index.month == 12, 'season_year'] += 1

    agg = df.groupby(['season', 'season_year'])['value']
    seasonal = agg.sum() if how == 'sum' else agg.mean()
    seasonal = seasonal.reset_index().rename(columns={'value': how})
    return seasonal


def plot_raw_with_bands(seasonal_df, value_col, var_label, units, out_path):
    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    for ax, season in zip(axes, SEASONS):
        sub = seasonal_df[seasonal_df['season'] == season].sort_values('season_year')
        years = sub['season_year'].values
        values = sub[value_col].values

        mean = values.mean()
        std = values.std()

        ax.fill_between(years, mean - 2 * std, mean + 2 * std, color='gray', alpha=0.15,
                         label='+/-2 std' if season == SEASONS[0] else None)
        ax.fill_between(years, mean - std, mean + std, color='gray', alpha=0.3,
                         label='+/-1 std' if season == SEASONS[0] else None)
        ax.axhline(mean, color='black', linewidth=1, linestyle='--',
                    label='mean' if season == SEASONS[0] else None)

        anomalous = np.abs(values - mean) > 2 * std
        ax.plot(years, values, color='tab:blue', marker='o', markersize=4, linewidth=1.2,
                label=var_label if season == SEASONS[0] else None)
        ax.scatter(years[anomalous], values[anomalous], color='tab:red', zorder=5, s=45,
                    label='|anomaly| > 2 std' if season == SEASONS[0] else None)

        ax.set_title(SEASON_NAMES[season])
        ax.set_ylabel(units)
        ax.grid(alpha=0.3)

    axes[0].legend(loc='upper left', fontsize=8, ncol=2)
    axes[-1].set_xlabel('Year')
    fig.suptitle(f'{var_label}: seasonal raw values (1990-present record)', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def plot_rolling_std(seasonal_df, value_col, var_label, units, out_path, window):
    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    for ax, season in zip(axes, SEASONS):
        sub = seasonal_df[seasonal_df['season'] == season].sort_values('season_year')
        years = sub['season_year'].values
        values = pd.Series(sub[value_col].values, index=years)

        rolling_std = values.rolling(window=window, min_periods=max(3, window // 2)).std()
        overall_std = values.std()

        ax.plot(years, rolling_std.values, color='tab:orange', marker='o', markersize=4,
                linewidth=1.5, label=f'{window}-yr rolling std' if season == SEASONS[0] else None)
        ax.axhline(overall_std, color='black', linewidth=1, linestyle='--',
                    label='full-record std' if season == SEASONS[0] else None)

        ax.set_title(SEASON_NAMES[season])
        ax.set_ylabel(units)
        ax.grid(alpha=0.3)

    axes[0].legend(loc='upper left', fontsize=8)
    axes[-1].set_xlabel('Year')
    fig.suptitle(f'{var_label}: {window}-year rolling standard deviation by season', fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rolling-window', type=int, default=10,
                         help='Window (years) for rolling standard deviation plots (default: 10)')
    parser.add_argument('--precip-start-year', type=int, default=1990)
    parser.add_argument('--precip-end-year', type=int, default=2025)
    parser.add_argument('--tmax-start-year', type=int, default=2006)
    parser.add_argument('--tmax-end-year', type=int, default=2025)
    args = parser.parse_args()

    print("=" * 60)
    print("Historic GRIDMET precipitation & max temperature validation")
    print("=" * 60)

    bounds = get_watershed_bounds_lonlat()
    print(f"Watershed bounds (lon/lat, +{BUFFER_M}m buffer): {bounds}")

    # --- Precipitation (full CONUS extent raw files -> must clip) ---
    print("\nLoading precipitation...")
    precip_daily = load_daily_series(
        PRECIP_DIR, "precip_raw_4000m_{year}.nc", "precipitation_amount",
        bounds=bounds, year_range=(args.precip_start_year, args.precip_end_year))
    precip_seasonal = to_seasonal(precip_daily, how='sum')

    # --- Max temperature (raw files already clipped to watershed) ---
    print("\nLoading max temperature...")
    tmax_daily_k = load_daily_series(
        TMAX_DIR, "tmmx_raw_4000m_{year}.nc", "air_temperature",
        bounds=None, year_range=(args.tmax_start_year, args.tmax_end_year))
    tmax_daily_c = tmax_daily_k - 273.15
    tmax_seasonal = to_seasonal(tmax_daily_c, how='mean')

    # --- Plots ---
    print("\nGenerating plots...")
    plot_raw_with_bands(precip_seasonal, 'sum', 'Seasonal total precipitation', 'mm',
                         OUT_DIR / 'precip_seasonal_raw_anomalies.png')
    plot_rolling_std(precip_seasonal, 'sum', 'Seasonal total precipitation', 'mm',
                      OUT_DIR / 'precip_seasonal_rolling_std.png', args.rolling_window)

    plot_raw_with_bands(tmax_seasonal, 'mean', 'Seasonal mean max temperature', 'deg C',
                         OUT_DIR / 'tmax_seasonal_raw_anomalies.png')
    plot_rolling_std(tmax_seasonal, 'mean', 'Seasonal mean max temperature', 'deg C',
                      OUT_DIR / 'tmax_seasonal_rolling_std.png', args.rolling_window)

    # Save underlying seasonal tables for reference
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    precip_seasonal.to_csv(OUT_DIR / 'precip_seasonal_totals.csv', index=False)
    tmax_seasonal.to_csv(OUT_DIR / 'tmax_seasonal_means.csv', index=False)

    print("\n" + "=" * 60)
    print(f"Done. Outputs in: {OUT_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
