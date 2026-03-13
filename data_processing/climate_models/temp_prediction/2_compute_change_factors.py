#!/usr/bin/env python3
"""
Step 2: Compute temperature change factors

This script computes change factors (CF) for each GCM and season by dividing
GCM future seasonal means by GCM historical seasonal means. The change factors
represent the multiplicative change in temperature between periods within the
same model, keeping GCM biases consistent.

Formula: ΔT = mean_future_season (GCM) - mean_historical_season (GCM)

Key characteristics:
- Historical baseline: GCM modeled historical data (1990-2019) at 6 grid points
- Future projections: GCM future data (2035-2064) at the same grid points from the same model
- Each model uses its own historical baseline (not a shared observed baseline)
- This preserves model-specific biases and captures only the projected change
- Temperature uses ADDITIVE change factors (ΔT in Kelvin) unlike precipitation (multiplicative)

Usage:
    python 2_compute_change_factors.py

Output:
    - change_factors_{model}_tas_ssp370.csv: Change factors (tabular format)
    - change_factors_{model}_tas_ssp370.geojson: Change factors (spatial format)
    - change_factors_summary.csv: Summary statistics across models and seasons
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Configuration
# Data is in ccsr-watershed-gis/data/climate_models/
# Scripts are in ccsr-watershed-gis/data_processing/climate_models/
DATA_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'temp_prediction' / '1_seasonal_means'
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'temp_prediction' / '2_change_factors'

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0']

# Temperature variables to process
VARIABLES = ['tasmin', 'tasmax']


def load_seasonal_means(model_name, variable, period):
    """
    Load seasonal means for a given model, variable, and period.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        period: 'historical' or 'future'
        
    Returns:
        DataFrame with seasonal means indexed by season
    """
    # Both historical and future come from the same GCM model
    file_path = DATA_DIR / f'seasonal_means_{period}_{model_name}_{variable}_ssp370.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path, index_col=0)
    
    # Clean column names
    df.columns = [col.strip().strip('"') for col in df.columns]
    
    return df


def compute_change_factors(hist_means, fut_means, model_name):
    """
    Compute additive temperature change factors for all grid cells and seasons.
    
    For temperature, we use ADDITIVE change factors (ΔT = future - historical)
    rather than multiplicative ratios, because temperature change is additive
    and reporting in Kelvin/Celsius is more meaningful than percentages.
    
    Args:
        hist_means: Historical seasonal means DataFrame (K)
        fut_means: Future seasonal means DataFrame (K)
        model_name: Name of the GCM model
        
    Returns:
        DataFrame with additive change factors (ΔT in K) indexed by season
    """
    print(f"\nComputing additive temperature change factors for {model_name}...")
    
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
    
    # Compute additive change factors (ΔT) for each cell and season
    for season in hist_means.index:
        for grid_cell in hist_means.columns:
            hist_value = hist_means.loc[season, grid_cell]
            fut_value = fut_means.loc[season, grid_cell]
            
            # Additive change: ΔT = future - historical
            delta_t = fut_value - hist_value
            
            change_factors.loc[season, grid_cell] = delta_t
    
    return change_factors


def print_change_factor_summary(change_factors, model_name):
    """
    Print summary statistics for additive temperature change factors.
    
    Args:
        change_factors: DataFrame with additive change factors (ΔT in K)
        model_name: Name of the GCM model
    """
    print(f"\nTemperature Change Summary for {model_name}:")
    print("-" * 70)
    
    summary_data = []
    
    for season in ['DJF', 'MAM', 'JJA', 'SON']:
        if season in change_factors.index:
            season_deltas = change_factors.loc[season].values.astype(float)
            
            mean_delta = season_deltas.mean()
            min_delta = season_deltas.min()
            max_delta = season_deltas.max()
            std_delta = season_deltas.std()
            
            print(f"{season}: ΔT range = [{min_delta:+.2f}, {max_delta:+.2f}] K, "
                  f"mean = {mean_delta:+.2f} K, std = {std_delta:.2f} K")
            
            summary_data.append({
                'model': model_name,
                'season': season,
                'mean_delta_K': mean_delta,
                'min_delta_K': min_delta,
                'max_delta_K': max_delta,
                'std_delta_K': std_delta
            })
    
    return summary_data


def save_change_factors(change_factors, model_name, variable):
    """
    Save change factors to CSV file.
    
    Args:
        change_factors: DataFrame with change factors
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save change factors
    output_file = OUTPUT_DIR / f'change_factors_{model_name}_{variable}_ssp370.csv'
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


def save_change_factors_geojson(change_factors, model_name, variable):
    """
    Save change factors as GeoJSON for easier visualization and interpolation.
    
    Args:
        change_factors: DataFrame with change factors
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        
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
        
        # Add change factors for each season (ΔT in K)
        for season in change_factors.index:
            delta_t = float(change_factors.loc[season, grid_cell])
            properties[f'delta_T_{season}_K'] = delta_t
        
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
            'variable': variable,
            'scenario': 'ssp370',
            'historical_period': '1990-2019',
            'future_period': '2035-2064',
            'baseline_source': model_name,
            'description': f'Additive temperature change factors (ΔT = {model_name} future - {model_name} historical) by season for {variable} in Kelvin'
        }
    }
    
    # Save GeoJSON
    output_file = OUTPUT_DIR / f'change_factors_{model_name}_{variable}_ssp370.geojson'
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"Saved change factors GeoJSON to: {output_file}")
    
    return output_file


def process_model(model_name, variable):
    """
    Process a single GCM model and variable: load means and compute change factors.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        
    Returns:
        Tuple of (change_factors DataFrame, summary data list)
    """
    print(f"\nProcessing model: {model_name} - Variable: {variable}")
    print("=" * 70)
    
    # Load seasonal means
    # Both historical and future come from the same GCM model
    print(f"Loading {model_name} {variable} historical seasonal means...")
    hist_means = load_seasonal_means(model_name, variable, 'historical')
    print(f"  Loaded {len(hist_means)} seasons, {len(hist_means.columns)} grid cells")
    
    print(f"Loading {model_name} {variable} future seasonal means...")
    fut_means = load_seasonal_means(model_name, variable, 'future')
    print(f"  Loaded {len(fut_means)} seasons, {len(fut_means.columns)} grid cells")
    
    # Compute change factors
    change_factors = compute_change_factors(hist_means, fut_means, model_name)
    
    # Print summary
    summary_data = print_change_factor_summary(change_factors, model_name)
    
    # Save outputs
    save_change_factors(change_factors, model_name, variable)
    save_change_factors_geojson(change_factors, model_name, variable)
    
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
                print(f"  {row['model']:20s}: {row['mean_delta_K']:+5.2f} K "
                      f"(range: {row['min_delta_K']:+5.2f} to {row['max_delta_K']:+5.2f} K)")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Step 2: Compute Temperature Change Factors")
    print("=" * 70)
    print(f"\nModels to process: {', '.join(MODELS)}")
    print(f"Variables to process: {', '.join(VARIABLES)}")
    print(f"\nUsing ADDITIVE change factors: ΔT = future - historical (in Kelvin)")
    
    all_summary_data = []
    
    # Process each variable and model combination
    for variable in VARIABLES:
        print(f"\n" + "#" * 70)
        print(f"# Processing variable: {variable.upper()}")
        print("#" * 70)
        
        for model_name in MODELS:
            try:
                change_factors, summary_data = process_model(model_name, variable)
                # Add variable to summary data
                for item in summary_data:
                    item['variable'] = variable
                all_summary_data.extend(summary_data)
            except Exception as e:
                print(f"\nERROR processing {model_name} {variable}: {e}")
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
    print("\nNote: Change factors are ADDITIVE (ΔT in K) representing absolute temperature")
    print("      change projected by each GCM (future - historical). They will be added")
    print("      to high-resolution GRIDMET baseline data.")


if __name__ == '__main__':
    main()
