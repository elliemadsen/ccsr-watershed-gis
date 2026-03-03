#!/usr/bin/env python3
"""
Step 1: Compute seasonal means for historical (GRIDMET) and future (GCM) periods

This script computes seasonal precipitation means at the 6 GCM grid points covering
the watershed for two time periods:

- Historical (1990-2019): GRIDMET observed data, downloaded if needed
- Future (2035-2064): GCM projection data for each model

These means are used in Step 2 to compute change factors. Note that the present
baseline rasters (2015-2025 @ 30m) used in Step 3 are separate files.

Seasons:
- DJF: December, January, February (Winter)
- MAM: March, April, May (Spring)
- JJA: June, July, August (Summer)
- SON: September, October, November (Fall)

Usage:
    python 1_compute_seasonal_means.py

Output:
    - seasonal_means_historical_gridmet_pr.csv: GRIDMET historical means (at GCM grid points)
    - seasonal_means_future_{model}_pr_ssp370.csv: GCM future means
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import subprocess
import xarray as xr
from datetime import datetime

# Configuration
# Data is in ccsr-watershed-gis/data/climate_models/
# Scripts are in ccsr-watershed-gis/data_processing/climate_models/
GCM_DATA_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'daily'
GRIDMET_RAW_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'precipitation' / 'raw'
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'seasonal_means'
HISTORICAL_PERIOD = (1990, 2019)
FUTURE_PERIOD = (2035, 2064)

# GCM grid points covering the watershed (from change_factors GeoJSON)
# These are the centroids where we need to extract GRIDMET data
GCM_GRID_POINTS = [
    (-75.125, 42.125),
    (-74.875, 42.125),
    (-74.625, 42.125),
    (-75.125, 42.375),
    (-74.875, 42.375),
    (-74.625, 42.375)
]

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0']

# Season definitions (month numbers)
SEASONS = {
    'DJF': [12, 1, 2],   # Winter
    'MAM': [3, 4, 5],    # Spring
    'JJA': [6, 7, 8],    # Summer
    'SON': [9, 10, 11]   # Fall
}


def assign_season(month):
    """Assign a season name to a given month."""
    for season_name, months in SEASONS.items():
        if month in months:
            return season_name
    return None


def download_gridmet_data(year):
    """
    Download GRIDMET precipitation data for a specific year.
    
    Args:
        year: Year to download
        
    Returns:
        Path to downloaded file or None if failed
    """
    GRIDMET_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use new naming convention: precip_raw_4000m_YYYY.nc
    filename = f"precip_raw_4000m_{year}.nc"
    filepath = GRIDMET_RAW_DIR / filename

    print(f"filepath: {filepath}")
    
    if filepath.exists():
        print(f"  File already exists: {filename}")
        return filepath
    
    # GRIDMET server uses pr_YYYY.nc naming
    source_filename = f"pr_{year}.nc"
    url = f"http://www.northwestknowledge.net/metdata/data/{source_filename}"
    print(f"  Downloading {source_filename} as {filename}...")
    
    try:
        subprocess.run(['wget', '-nc', '-c', '-O', str(filepath), url], 
                      check=True, capture_output=True, text=True)
        print(f"  Successfully downloaded {filename}")
        return filepath
    except subprocess.CalledProcessError as e:
        print(f"  ERROR downloading {filename}: {e}")
        return None


def extract_gridmet_at_points(year, grid_points):
    """
    Extract GRIDMET precipitation data at specific lat/lon points.
    
    Args:
        year: Year to process
        grid_points: List of (lon, lat) tuples
        
    Returns:
        DataFrame with daily precipitation at each grid point (in kg/m²)
    """
    # Download if needed
    filepath = download_gridmet_data(year)
    if filepath is None:
        return None
    
    # Load GRIDMET data
    ds = xr.open_dataset(filepath)
    
    # Extract data at each grid point
    data = {}
    for lon, lat in grid_points:
        # Find nearest grid cell in GRIDMET data
        point_data = ds['precipitation_amount'].sel(
            lon=lon, lat=lat, method='nearest'
        )
        # GRIDMET units are mm, which equals kg/m² for water
        # (no conversion needed: 1 mm water = 1 kg/m²)
        data[f'({lat}, {lon})'] = point_data.values
    
    # Create DataFrame with dates
    df = pd.DataFrame(data, index=pd.to_datetime(ds['day'].values))
    ds.close()
    
    return df


def load_gridmet_historical():
    """
    Load and process GRIDMET historical data (1990-2019) at GCM grid points.
    
    Returns:
        DataFrame with daily precipitation at GCM grid points
    """
    print("\nLoading GRIDMET historical data (1990-2019)...")
    print("=" * 60)
    
    all_years = []
    hist_start, hist_end = HISTORICAL_PERIOD
    
    for year in range(hist_start, hist_end + 1):
        print(f"Processing {year}...")
        df_year = extract_gridmet_at_points(year, GCM_GRID_POINTS)
        if df_year is not None:
            all_years.append(df_year)
        else:
            print(f"  WARNING: Could not load data for {year}")
    
    if not all_years:
        raise RuntimeError("No GRIDMET data could be loaded!")
    
    # Concatenate all years
    df = pd.concat(all_years)
    print(f"\nLoaded {len(df)} days from {df.index.min()} to {df.index.max()}")
    print(f"Grid points: {len(df.columns)}")
    
    return df


def load_precipitation_data(model_name):
    """
    Load daily precipitation data for a given GCM model.
    
    Args:
        model_name: Name of the GCM model
        
    Returns:
        DataFrame with datetime index and grid cell columns (units: kg/m² per day)
    """
    file_path = GCM_DATA_DIR / f'Catskills_{model_name}_pr_ssp370_daily_avg.csv'

    print(f"file_path: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    print(f"Loading data from {file_path}...")
    
    # Read the CSV file
    df = pd.read_csv(file_path, index_col=0)
    
    # Convert index to datetime
    df.index = pd.to_datetime(df.index)
    
    # Clean column names (remove extra quotes and spaces)
    df.columns = [col.strip().strip('"') for col in df.columns]
    
    # Convert from kg/m²/s to kg/m² (daily total)
    # GCM data is in kg/m²/s (precipitation rate)
    # Multiply by seconds per day (86400) to get daily total
    df = df * 86400
    
    print(f"  Loaded {len(df)} days from {df.index.min()} to {df.index.max()}")
    print(f"  Number of grid cells: {len(df.columns)}")
    print(f"  Converted from kg/m²/s to kg/m² (daily total)")
    
    return df


def compute_seasonal_totals(df, year_start, year_end):
    """
    Compute seasonal totals for each year in the given period.
    
    Args:
        df: DataFrame with daily precipitation data
        year_start: Start year of the period
        year_end: End year of the period (inclusive)
        
    Returns:
        DataFrame with seasonal totals, indexed by (year, season)
    """
    # Filter data to the specified period
    mask = (df.index.year >= year_start) & (df.index.year <= year_end)
    df_period = df[mask].copy()
    
    # Add year, month, and season columns
    df_period['year'] = df_period.index.year
    df_period['month'] = df_period.index.month
    df_period['season'] = df_period['month'].apply(assign_season)
    
    # Adjust year for December (DJF season belongs to the following year)
    # E.g., December 2019 belongs to DJF 2020
    mask_december = df_period['month'] == 12
    df_period.loc[mask_december, 'year'] = df_period.loc[mask_december, 'year'] + 1
    
    # Group by year and season, sum precipitation
    grid_cell_cols = [col for col in df_period.columns 
                     if col not in ['year', 'month', 'season']]
    
    seasonal_totals = df_period.groupby(['year', 'season'])[grid_cell_cols].sum()
    
    return seasonal_totals


def compute_seasonal_means(seasonal_totals):
    """
    Compute multi-year mean of seasonal totals.
    
    Args:
        seasonal_totals: DataFrame with seasonal totals indexed by (year, season)
        
    Returns:
        Series with seasonal means indexed by season
    """
    # Group by season and compute mean across years
    seasonal_means = seasonal_totals.groupby('season').mean()
    
    return seasonal_means


def process_gcm_future(model_name):
    """
    Process GCM model: compute seasonal means for future period only.
    
    Args:
        model_name: Name of the GCM model
        
    Returns:
        DataFrame with future seasonal means
    """
    print(f"\nProcessing GCM model: {model_name}")
    print("=" * 60)
    
    # Load GCM data
    df = load_precipitation_data(model_name)
    
    # Check available data range
    data_start_year = df.index.min().year
    data_end_year = df.index.max().year
    
    print(f"Data available from {data_start_year} to {data_end_year}")
    
    # Process future period
    fut_start, fut_end = FUTURE_PERIOD
    if data_start_year > fut_start or data_end_year < fut_end:
        print(f"WARNING: Future period ({fut_start}-{fut_end}) not fully covered by data")
        fut_start = max(fut_start, data_start_year)
        fut_end = min(fut_end, data_end_year)
        print(f"  Using adjusted period: {fut_start}-{fut_end}")
    
    print(f"\nComputing seasonal totals for future period ({fut_start}-{fut_end})...")
    fut_seasonal_totals = compute_seasonal_totals(df, fut_start, fut_end)
    print(f"  Computed {len(fut_seasonal_totals)} year-season combinations")
    
    print(f"Computing seasonal means for future period...")
    fut_seasonal_means = compute_seasonal_means(fut_seasonal_totals)
    print(f"  Computed means for {len(fut_seasonal_means)} seasons")
    
    return fut_seasonal_means


def process_gridmet_historical():
    """
    Process GRIDMET data: compute seasonal means for historical period.
    
    Returns:
        DataFrame with historical seasonal means
    """
    print("\nProcessing GRIDMET historical data")
    print("=" * 60)
    
    # Load GRIDMET data
    df = load_gridmet_historical()
    
    # Process historical period
    hist_start, hist_end = HISTORICAL_PERIOD
    
    # Check actual data range
    data_start_year = df.index.min().year
    data_end_year = df.index.max().year
    
    if data_start_year > hist_start:
        print(f"\nWARNING: GRIDMET data starts in {data_start_year}, not {hist_start}")
        hist_start = data_start_year
    if data_end_year < hist_end:
        print(f"WARNING: GRIDMET data ends in {data_end_year}, not {hist_end}")
        hist_end = data_end_year
    
    print(f"\nComputing seasonal totals for historical period ({hist_start}-{hist_end})...")
    hist_seasonal_totals = compute_seasonal_totals(df, hist_start, hist_end)
    print(f"  Computed {len(hist_seasonal_totals)} year-season combinations")
    
    print(f"Computing seasonal means for historical period...")
    hist_seasonal_means = compute_seasonal_means(hist_seasonal_totals)
    print(f"  Computed means for {len(hist_seasonal_means)} seasons")
    
    return hist_seasonal_means


def save_gridmet_historical(hist_means):
    """
    Save GRIDMET historical seasonal means to CSV file.
    
    Args:
        hist_means: Historical seasonal means DataFrame
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    
    # Save historical means
    hist_file = OUTPUT_DIR / 'seasonal_means_historical_gridmet_pr.csv'
    hist_means.to_csv(hist_file)
    print(f"\nSaved GRIDMET historical seasonal means to: {hist_file}")
    
    # Print summary statistics
    print("\nGRIDMET Historical Summary:")
    print("-" * 60)
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        if season in hist_means.index:
            hist_mean = hist_means.loc[season].mean()
            print(f"{season}: {hist_mean:.6f} kg/m²/s")


def save_gcm_future(fut_means, model_name, hist_means):
    """
    Save GCM future seasonal means to CSV file.
    
    Args:
        fut_means: Future seasonal means DataFrame
        model_name: Name of the GCM model
        hist_means: Historical (GRIDMET) seasonal means for comparison
    """
    # Save future means
    fut_file = OUTPUT_DIR / f'seasonal_means_future_{model_name}_pr_ssp370.csv'
    fut_means.to_csv(fut_file)
    print(f"\nSaved GCM future seasonal means to: {fut_file}")
    
    # Print summary statistics
    print(f"\n{model_name} Future vs GRIDMET Historical:")
    print("-" * 60)
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        if season in hist_means.index and season in fut_means.index:
            hist_mean = hist_means.loc[season].mean()
            fut_mean = fut_means.loc[season].mean()
            change_pct = ((fut_mean - hist_mean) / hist_mean) * 100
            print(f"{season}: GRIDMET={hist_mean:.6f}, "
                  f"GCM_future={fut_mean:.6f}, "
                  f"Change={change_pct:+.2f}%")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 1: Compute Seasonal Means")
    print("=" * 60)
    print(f"\nHistorical period (GRIDMET): {HISTORICAL_PERIOD[0]}-{HISTORICAL_PERIOD[1]}")
    print(f"Future period (GCM): {FUTURE_PERIOD[0]}-{FUTURE_PERIOD[1]}")
    print(f"\nGCM models to process: {', '.join(MODELS)}")
    print(f"GCM grid points: {len(GCM_GRID_POINTS)}")
    
    # Step 1a: Process GRIDMET historical (shared baseline for all models)
    try:
        print("\n" + "=" * 60)
        print("STEP 1a: Process GRIDMET Historical Baseline")
        print("=" * 60)
        hist_means = process_gridmet_historical()
        save_gridmet_historical(hist_means)
    except Exception as e:
        print(f"\nERROR processing GRIDMET historical: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 1b: Process each GCM model's future projections
    print("\n" + "=" * 60)
    print("STEP 1b: Process GCM Future Projections")
    print("=" * 60)
    
    for model_name in MODELS:
        try:
            fut_means = process_gcm_future(model_name)
            save_gcm_future(fut_means, model_name, hist_means)
        except Exception as e:
            print(f"\nERROR processing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 60)
    print("Step 1 completed!")
    print("=" * 60)
    print("\nOutput files:")
    print("  - seasonal_means_historical_gridmet_pr.csv (shared baseline)")
    for model in MODELS:
        print(f"  - seasonal_means_future_{model}_pr_ssp370.csv")


if __name__ == '__main__':
    main()
