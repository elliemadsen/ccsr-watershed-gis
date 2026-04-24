#!/usr/bin/env python3
"""
Step 1: Compute seasonal means for historical and future periods (both from GCM data)

This script computes seasonal temperature means at the 6 GCM grid points covering
the watershed for two time periods from each GCM model:

- Historical (1990-2019): GCM modeled historical data
- Future (2035-2064): GCM projection data

These means are used in Step 2 to compute change factors (GCM_future / GCM_historical).
This approach keeps GCM biases consistent by comparing within the same model.

Seasons:
- DJF: December, January, February (Winter)
- MAM: March, April, May (Spring)
- JJA: June, July, August (Summer)
- SON: September, October, November (Fall)

Usage:
    python 1_compute_seasonal_means.py

Output:
    - seasonal_means_historical_{model}_tasmin_ssp370.csv: GCM historical min temp means
    - seasonal_means_future_{model}_tasmin_ssp370.csv: GCM future min temp means
    - seasonal_means_historical_{model}_tasmax_ssp370.csv: GCM historical max temp means
    - seasonal_means_future_{model}_tasmax_ssp370.csv: GCM future max temp means
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Configuration
# Data is in ccsr-watershed-gis/data/climate_models/
# Scripts are in ccsr-watershed-gis/data_processing/climate_models/
GCM_HISTORICAL_DIR = Path(__file__).parent.parent.parent / 'data' / 'GCM' / 'raw' / 'daily_1990_2015'
GCM_FUTURE_DIR = Path(__file__).parent.parent.parent / 'data' / 'GCM' / 'raw' / 'daily_2015_2065'
HIST_OUTPUT_DIR   = Path(__file__).parent.parent.parent / 'data' / 'temperature' / 'hist_GCM' / 'csv'
FUTURE_OUTPUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'temperature' / 'future_GCM' / 'csv'
HISTORICAL_PERIOD = (1990, 2019)
FUTURE_PERIOD = (2035, 2064)

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0']

# Temperature variables to process
VARIABLES = ['tasmin', 'tasmax']

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


def load_temperature_data(model_name, variable, period):
    """
    Load daily temperature data for a given GCM model, variable, and period.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        period: 'historical' (1990-2015) or 'future' (2015-2065)
        
    Returns:
        DataFrame with datetime index and grid cell columns (units: K)
    """
    # Select the appropriate directory and filename based on period
    if period == 'historical':
        data_dir = GCM_HISTORICAL_DIR
        file_path = data_dir / f'Catskills_{model_name}_{variable}_historical_daily_avg.csv'
    else:
        data_dir = GCM_FUTURE_DIR
        file_path = data_dir / f'Catskills_{model_name}_{variable}_ssp370_daily_avg.csv'

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
    
    # GCM temperature data is already in Kelvin (K), no conversion needed
    
    print(f"  Loaded {len(df)} days from {df.index.min()} to {df.index.max()}")
    print(f"  Number of grid cells: {len(df.columns)}")
    print(f"  Temperature units: K")
    
    return df


def compute_seasonal_averages(df, year_start, year_end):
    """
    Compute seasonal averages for each year in the given period.
    
    Args:
        df: DataFrame with daily temperature data
        year_start: Start year of the period
        year_end: End year of the period (inclusive)
        
    Returns:
        DataFrame with seasonal averages, indexed by (year, season)
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
    
    # Group by year and season, compute mean temperature
    grid_cell_cols = [col for col in df_period.columns 
                     if col not in ['year', 'month', 'season']]
    
    seasonal_averages = df_period.groupby(['year', 'season'])[grid_cell_cols].mean()
    
    return seasonal_averages


def compute_seasonal_means(seasonal_averages):
    """
    Compute multi-year mean of seasonal averages.
    
    Args:
        seasonal_averages: DataFrame with seasonal averages indexed by (year, season)
        
    Returns:
        Series with seasonal means indexed by season
    """
    # Group by season and compute mean across years
    seasonal_means = seasonal_averages.groupby('season').mean()
    
    return seasonal_means


def process_gcm(model_name, variable):
    """
    Process GCM model and variable: compute seasonal means for both historical and future periods.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        
    Returns:
        Tuple of (historical seasonal means, future seasonal means)
    """
    print(f"\nProcessing GCM model: {model_name} - Variable: {variable}")
    print("=" * 60)
    
    # Load GCM historical data (1990-2014 from historical folder)
    print("\nLoading historical period data (1990-2014)...")
    df_hist_file = load_temperature_data(model_name, variable, 'historical')
    hist_data_end = df_hist_file.index.max().year
    print(f"Historical file data available from {df_hist_file.index.min().year} to {hist_data_end}")
    
    # Check if we need additional years from the future file to complete historical period (1990-2019)
    hist_start, hist_end = HISTORICAL_PERIOD
    if hist_data_end < hist_end:
        # Load future data file to get years 2015-2019
        print(f"\nLoading additional years ({hist_data_end + 1}-{hist_end}) from future data file...")
        df_future_file = load_temperature_data(model_name, variable, 'future')
        
        # Extract only the years we need for historical period
        mask = (df_future_file.index.year >= hist_data_end + 1) & (df_future_file.index.year <= hist_end)
        df_additional = df_future_file[mask]
        print(f"Extracted {df_additional.index.min().year} to {df_additional.index.max().year} from future file")
        
        # Combine historical file data with additional years from future file
        df_historical = pd.concat([df_hist_file, df_additional])
        print(f"Combined historical period now covers {df_historical.index.min().year} to {df_historical.index.max().year}")
    else:
        df_historical = df_hist_file
    
    # Process historical period (1990-2019)
    print(f"\nComputing seasonal averages for historical period ({hist_start}-{hist_end})...")
    hist_seasonal_averages = compute_seasonal_averages(df_historical, hist_start, hist_end)
    print(f"  Computed {len(hist_seasonal_averages)} year-season combinations")
    
    print(f"Computing seasonal means for historical period...")
    hist_seasonal_means = compute_seasonal_means(hist_seasonal_averages)
    print(f"  Computed means for {len(hist_seasonal_means)} seasons")
    
    # Load GCM future data (2015-2065) if not already loaded
    if hist_data_end < hist_end:
        # We already loaded df_future_file above, so just use it
        print("\nUsing previously loaded future data file for future period...")
    else:
        # Need to load the future file
        print("\nLoading future period data (2015-2065)...")
        df_future_file = load_temperature_data(model_name, variable, 'future')
    
    # Check available data range for future
    fut_data_start = df_future_file.index.min().year
    fut_data_end = df_future_file.index.max().year
    print(f"Future data available from {fut_data_start} to {fut_data_end}")
    
    # Process future period
    fut_start, fut_end = FUTURE_PERIOD
    if fut_data_start > fut_start or fut_data_end < fut_end:
        print(f"WARNING: Future period ({fut_start}-{fut_end}) not fully covered by data")
        fut_start = max(fut_start, fut_data_start)
        fut_end = min(fut_end, fut_data_end)
        print(f"  Using adjusted period: {fut_start}-{fut_end}")
    
    print(f"\nComputing seasonal averages for future period ({fut_start}-{fut_end})...")
    fut_seasonal_averages = compute_seasonal_averages(df_future_file, fut_start, fut_end)
    print(f"  Computed {len(fut_seasonal_averages)} year-season combinations")
    
    print(f"Computing seasonal means for future period...")
    fut_seasonal_means = compute_seasonal_means(fut_seasonal_averages)
    print(f"  Computed means for {len(fut_seasonal_means)} seasons")
    
    return hist_seasonal_means, fut_seasonal_means


def save_gcm_seasonal_means(hist_means, fut_means, model_name, variable):
    """
    Save GCM historical and future seasonal means to CSV files.
    
    Args:
        hist_means: Historical seasonal means DataFrame
        fut_means: Future seasonal means DataFrame
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
    """
    # Create output directories if they don't exist
    HIST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FUTURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save historical means
    hist_file = HIST_OUTPUT_DIR / f'seasonal_means_historical_{model_name}_{variable}_ssp370.csv'
    hist_means.to_csv(hist_file)
    print(f"\nSaved GCM historical seasonal means to: {hist_file}")
    
    # Save future means
    fut_file = FUTURE_OUTPUT_DIR / f'seasonal_means_future_{model_name}_{variable}_ssp370.csv'
    fut_means.to_csv(fut_file)
    print(f"Saved GCM future seasonal means to: {fut_file}")
    
    # Print summary statistics and comparison
    print(f"\n{model_name} Historical vs Future:")
    print("-" * 60)
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        if season in hist_means.index and season in fut_means.index:
            hist_mean = hist_means.loc[season].mean()
            fut_mean = fut_means.loc[season].mean()
            change_pct = ((fut_mean - hist_mean) / hist_mean) * 100
            # Convert K to Celsius for display
            hist_c = hist_mean - 273.15
            fut_c = fut_mean - 273.15
            print(f"{season}: Historical={hist_c:.2f}°C, "
                  f"Future={fut_c:.2f}°C, "
                  f"Change={change_pct:+.2f}%")


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 1: Compute Seasonal Means (GCM Historical and Future)")
    print("=" * 60)
    print(f"\nHistorical period (GCM): {HISTORICAL_PERIOD[0]}-{HISTORICAL_PERIOD[1]}")
    print(f"Future period (GCM): {FUTURE_PERIOD[0]}-{FUTURE_PERIOD[1]}")
    print(f"\nGCM models to process: {', '.join(MODELS)}")
    print(f"Temperature variables: {', '.join(VARIABLES)}")
    
    # Process each variable and model combination
    for variable in VARIABLES:
        print(f"\n" + "#" * 60)
        print(f"# Processing variable: {variable.upper()}")
        print("#" * 60)
        
        for model_name in MODELS:
            try:
                print(f"\n" + "=" * 60)
                print(f"Processing: {model_name} - {variable}")
                print("=" * 60)
                
                hist_means, fut_means = process_gcm(model_name, variable)
                save_gcm_seasonal_means(hist_means, fut_means, model_name, variable)
            except Exception as e:
                print(f"\nERROR processing {model_name} {variable}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print("\n" + "=" * 60)
    print("Step 1 completed!")
    print("=" * 60)
    print("\nOutput files:")
    for variable in VARIABLES:
        for model in MODELS:
            print(f"  - seasonal_means_historical_{model}_{variable}_ssp370.csv")
            print(f"  - seasonal_means_future_{model}_{variable}_ssp370.csv")


if __name__ == '__main__':
    main()
