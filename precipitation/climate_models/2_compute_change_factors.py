#!/usr/bin/env python3
"""
Step 2: Compute precipitation change factors

This script computes change factors (CF) for each GCM and season by dividing
future seasonal means by historical seasonal means. The change factors represent
the multiplicative change in precipitation between periods.

Formula: CF_precip = mean_future_season / mean_historical_season

- If historical mean < 0.1 mm (converted from kg/m²/s), set CF = 1.0

Usage:
    python step2_compute_change_factors.py

Output:
    - change_factors_{model}_pr_ssp370.csv: Change factors for each grid cell and season
    - change_factors_summary.csv: Summary statistics across models and seasons
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Configuration
# Data is in ccsr-watershed-gis/climate_models/data/
# Scripts are in ccsr-watershed-gis/precipitation/climate_models/
DATA_DIR = Path(__file__).parent.parent.parent / 'climate_models' / 'data' / 'seasonal_means'
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'climate_models' / 'data' / 'change_factors'

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR']

# Threshold for near-zero precipitation (in kg/m²/s)
# 0.1 mm/day ≈ 1.16e-6 kg/m²/s (0.1 mm/day * 1 kg/m²/mm * 1 day/86400 s)
# However, we're dealing with seasonal totals, so let's use a more appropriate threshold
# For seasonal means of daily rates: 0.1 mm/season is very small
NEAR_ZERO_THRESHOLD = 1e-6  # kg/m²/s


def load_seasonal_means(model_name, period):
    """
    Load seasonal means for a given model and period.
    
    Args:
        model_name: Name of the GCM model (or 'gridmet' for historical)
        period: 'historical' or 'future'
        
    Returns:
        DataFrame with seasonal means indexed by season
    """
    if period == 'historical':
        # Historical baseline comes from GRIDMET
        file_path = DATA_DIR / 'seasonal_means_historical_gridmet_pr.csv'
    else:
        # Future comes from GCM
        file_path = DATA_DIR / f'seasonal_means_{period}_{model_name}_pr_ssp370.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path, index_col=0)
    
    # Clean column names
    df.columns = [col.strip().strip('"') for col in df.columns]
    
    return df


def compute_change_factors(hist_means, fut_means, model_name):
    """
    Compute change factors for all grid cells and seasons.
    
    Args:
        hist_means: Historical seasonal means DataFrame
        fut_means: Future seasonal means DataFrame
        model_name: Name of the GCM model
        
    Returns:
        DataFrame with change factors indexed by season
    """
    print(f"\nComputing change factors for {model_name}...")
    
    # Ensure both DataFrames have the same structure
    assert list(hist_means.columns) == list(fut_means.columns), \
        "Historical and future data have different grid cells"
    assert list(hist_means.index) == list(fut_means.index), \
        "Historical and future data have different seasons"
    
    # Initialize change factors DataFrame
    change_factors = pd.DataFrame(
        index=hist_means.index,
        columns=hist_means.columns,
        dtype=float
    )
    
    # Compute change factors for each cell and season
    for season in hist_means.index:
        for grid_cell in hist_means.columns:
            hist_value = hist_means.loc[season, grid_cell]
            fut_value = fut_means.loc[season, grid_cell]
            
            # Check for near-zero historical values
            if hist_value < NEAR_ZERO_THRESHOLD:
                cf = 1.0
                print(f"  WARNING: Near-zero historical value for {season}, {grid_cell}: "
                      f"{hist_value:.2e} kg/m²/s. Setting CF = 1.0")
            else:
                cf = fut_value / hist_value
            
            change_factors.loc[season, grid_cell] = cf
    
    return change_factors


def print_change_factor_summary(change_factors, model_name):
    """
    Print summary statistics for change factors.
    
    Args:
        change_factors: DataFrame with change factors
        model_name: Name of the GCM model
    """
    print(f"\nChange Factor Summary for {model_name}:")
    print("-" * 70)
    
    summary_data = []
    
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        if season in change_factors.index:
            season_cfs = change_factors.loc[season].values.astype(float)
            
            mean_cf = season_cfs.mean()
            min_cf = season_cfs.min()
            max_cf = season_cfs.max()
            std_cf = season_cfs.std()
            
            # Convert to percentage change
            mean_pct = (mean_cf - 1.0) * 100
            min_pct = (min_cf - 1.0) * 100
            max_pct = (max_cf - 1.0) * 100
            
            print(f"{season}: CF range = [{min_cf:.4f}, {max_cf:.4f}], "
                  f"mean = {mean_cf:.4f} ({mean_pct:+.2f}%), std = {std_cf:.4f}")
            
            summary_data.append({
                'model': model_name,
                'season': season,
                'mean_cf': mean_cf,
                'min_cf': min_cf,
                'max_cf': max_cf,
                'std_cf': std_cf,
                'mean_pct_change': mean_pct,
                'min_pct_change': min_pct,
                'max_pct_change': max_pct
            })
    
    return summary_data


def save_change_factors(change_factors, model_name):
    """
    Save change factors to CSV file.
    
    Args:
        change_factors: DataFrame with change factors
        model_name: Name of the GCM model
        
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save change factors
    output_file = OUTPUT_DIR / f'change_factors_{model_name}_pr_ssp370.csv'
    change_factors.to_csv(output_file)
    print(f"\nSaved change factors to: {output_file}")
    
    return output_file


def extract_grid_coordinates(change_factors):
    """
    Extract lat/lon coordinates from grid cell column names.
    
    Args:
        change_factors: DataFrame with grid cell columns like "(42.125, -75.125)"
        
    Returns:
        List of (lat, lon) tuples
    """
    coords = []
    for col in change_factors.columns:
        # Parse "(lat, lon)" format
        coord_str = col.strip('()').split(',')
        lat = float(coord_str[0].strip())
        lon = float(coord_str[1].strip())
        coords.append((lat, lon))
    
    return coords


def save_change_factors_geojson(change_factors, model_name):
    """
    Save change factors as GeoJSON for easier visualization and interpolation.
    
    Args:
        change_factors: DataFrame with change factors
        model_name: Name of the GCM model
        
    Returns:
        Path to the saved GeoJSON file
    """
    # Extract coordinates
    coords = extract_grid_coordinates(change_factors)
    
    # Create GeoJSON structure
    features = []
    
    for idx, (lat, lon) in enumerate(coords):
        grid_cell = change_factors.columns[idx]
        
        properties = {
            'grid_cell': grid_cell,
            'lat': lat,
            'lon': lon
        }
        
        # Add change factors for each season
        for season in change_factors.index:
            cf = float(change_factors.loc[season, grid_cell])
            properties[f'cf_{season}'] = cf
            properties[f'pct_change_{season}'] = (cf - 1.0) * 100
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]  # GeoJSON uses [lon, lat]
            },
            'properties': properties
        }
        
        features.append(feature)
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'model': model_name,
            'variable': 'precipitation',
            'scenario': 'ssp370',
            'historical_period': '2015-2019',
            'future_period': '2035-2064',
            'description': 'Precipitation change factors (future/historical) by season'
        }
    }
    
    # Save GeoJSON
    output_file = OUTPUT_DIR / f'change_factors_{model_name}_pr_ssp370.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"Saved change factors GeoJSON to: {output_file}")
    
    return output_file


def process_model(model_name):
    """
    Process a single GCM model: load means and compute change factors.
    
    Args:
        model_name: Name of the GCM model
        
    Returns:
        Tuple of (change_factors DataFrame, summary data list)
    """
    print(f"\nProcessing model: {model_name}")
    print("=" * 70)
    
    # Load seasonal means
    # Historical baseline comes from GRIDMET (shared across all models)
    print(f"Loading GRIDMET historical seasonal means...")
    hist_means = load_seasonal_means('gridmet', 'historical')
    print(f"  Loaded {len(hist_means)} seasons, {len(hist_means.columns)} grid cells")
    
    print(f"Loading {model_name} future seasonal means...")
    fut_means = load_seasonal_means(model_name, 'future')
    print(f"  Loaded {len(fut_means)} seasons, {len(fut_means.columns)} grid cells")
    
    # Compute change factors
    change_factors = compute_change_factors(hist_means, fut_means, model_name)
    
    # Print summary
    summary_data = print_change_factor_summary(change_factors, model_name)
    
    # Save outputs
    save_change_factors(change_factors, model_name)
    save_change_factors_geojson(change_factors, model_name)
    
    return change_factors, summary_data


def save_summary(all_summary_data):
    """
    Save summary statistics for all models.
    
    Args:
        all_summary_data: List of summary dictionaries
    """
    summary_df = pd.DataFrame(all_summary_data)
    
    output_file = OUTPUT_DIR / 'change_factors_summary.csv'
    summary_df.to_csv(output_file, index=False)
    print(f"\nSaved summary statistics to: {output_file}")
    
    # Print overall comparison
    print("\n" + "=" * 70)
    print("Overall Comparison:")
    print("=" * 70)
    
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        season_data = summary_df[summary_df['season'] == season]
        if len(season_data) > 0:
            print(f"\n{season}:")
            for _, row in season_data.iterrows():
                print(f"  {row['model']:20s}: {row['mean_pct_change']:+6.2f}% "
                      f"(range: {row['min_pct_change']:+6.2f}% to {row['max_pct_change']:+6.2f}%)")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Step 2: Compute Precipitation Change Factors")
    print("=" * 70)
    print(f"\nModels to process: {', '.join(MODELS)}")
    print(f"Near-zero threshold: {NEAR_ZERO_THRESHOLD} kg/m²/s")
    
    all_summary_data = []
    
    # Process each model
    for model_name in MODELS:
        try:
            change_factors, summary_data = process_model(model_name)
            all_summary_data.extend(summary_data)
        except Exception as e:
            print(f"\nERROR processing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save overall summary
    if all_summary_data:
        save_summary(all_summary_data)
    
    print("\n" + "=" * 70)
    print("Step 2 completed!")
    print("=" * 70)
    print("\nNext step: Apply change factors to observed GRIDMET baseline (Step 3)")


if __name__ == '__main__':
    main()
