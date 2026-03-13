#!/usr/bin/env python3
"""
Step 3: Apply change factors to observed GRIDMET baseline

This script applies the computed change factors to the baseline GRIDMET
temperature rasters (2015-2025 @ 30m) to create future climate projections
(2035-2064 @ 30m).

The process:
1. Load change factors for each model and season (point data at 6 GCM grid points)
2. Interpolate change factors to 30m resolution using Inverse Distance Weighting (IDW)
3. Add the interpolated change factors to the present GRIDMET baseline rasters (2015-2025)

Interpolation method: IDW with power=2 (inverse square distance)
- Creates smooth gradients between GCM grid points
- More physically realistic than nearest neighbor (Voronoi)
- Each pixel weighted by all GCM points based on distance

Formula: temp_future_30m (2035-2064) = temp_baseline_30m (2015-2025) + ΔT

Note: Temperature uses ADDITIVE change factors (ΔT in Kelvin), unlike precipitation
      which uses multiplicative change factors (ratios).

Usage:
    python 3_apply_change_factors.py

Requirements:
    - rasterio (available in conda geo environment)
    - scipy (for IDW interpolation)
    - numpy
    - pandas

Output:
    - temp_future_{model}_2035-2064_{season}_30m.tif: Future temperature rasters
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.interpolate import griddata
import json
import sys

try:
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling
except ImportError:
    print("ERROR: rasterio library is required. Install with: pip install rasterio")
    sys.exit(1)

# Configuration
CHANGE_FACTORS_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'temp_prediction' / '2_change_factors'
GRIDMET_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'temp' / 'processed' / 'seasonal'
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / 'data' / 'climate_models' / 'temp_prediction' / '3_future_projections'

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CMCC-ESM2', 'CNRM-CM6-1', 'INM-CM5-0']

# Temperature variables
VARIABLES = ['tasmin', 'tasmax']

# Seasons (must match GRIDMET file names)
SEASONS = ['djf', 'mam', 'jja', 'son']

# Period labels
HISTORICAL_PERIOD = '1990-2019'
FUTURE_PERIOD = '2035-2064'


def load_change_factors_geojson(model_name, variable):
    """
    Load change factors from GeoJSON file.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        
    Returns:
        Dictionary with season keys and (coords, values) tuples
    """
    file_path = CHANGE_FACTORS_DIR / f'change_factors_{model_name}_{variable}_ssp370.geojson'
    
    if not file_path.exists():
        raise FileNotFoundError(f"Change factors file not found: {file_path}")
    
    print(f"Loading change factors from {file_path}...")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract change factors by season
    change_factors = {}
    
    for season in SEASONS:
        season_upper = season.upper()
        coords = []
        values = []
        
        for feature in data['features']:
            lon, lat = feature['geometry']['coordinates']
            # Updated to use delta_T instead of cf
            delta_t = feature['properties'][f'delta_T_{season_upper}_K']
            
            coords.append((lon, lat))
            values.append(delta_t)
        
        coords = np.array(coords)
        values = np.array(values)
        
        change_factors[season] = {
            'coords': coords,
            'values': values,
            'count': len(coords)
        }
        
        print(f"  {season_upper}: {len(coords)} grid points, "
              f"ΔT range [{values.min():+.2f}, {values.max():+.2f}] K")
    
    return change_factors


def load_gridmet_baseline(season, variable):
    """
    Load GRIDMET baseline temperature raster for a given season and variable.
    Searches for files with year range pattern: temp_{min|max}_final_30m_YYYY-YYYY_{season}.tif
    
    Args:
        season: Season code (djf, mam, jja, son)
        variable: 'tasmin' or 'tasmax'
        
    Returns:
        tuple: (data array, raster profile)
    """
    # Look for files matching the pattern with year range
    import glob
    var_name = 'min' if variable == 'tasmin' else 'max'
    pattern = str(GRIDMET_DIR / f'temp_{var_name}_final_30m_*_{season}.tif')
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        # Fallback to old naming without year range
        file_path = GRIDMET_DIR / f'temp_{var_name}_final_30m_{season}.tif'
    else:
        # Use the most recent file (sorted alphabetically, which works for year ranges)
        file_path = Path(sorted(matching_files)[-1])
    
    if not file_path.exists():
        raise FileNotFoundError(f"GRIDMET baseline raster not found: {file_path}")
    
    print(f"Loading GRIDMET baseline raster: {file_path}...")
    
    with rasterio.open(file_path) as src:
        data = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        bounds = src.bounds
        crs = src.crs
        
        print(f"  Shape: {data.shape}")
        print(f"  CRS: {crs}")
        print(f"  Bounds: {bounds}")
        
        # Get valid (non-nodata) statistics
        nodata = src.nodata
        valid_mask = data != nodata
        if valid_mask.any():
            valid_data = data[valid_mask]
            print(f"  Temperature range: {valid_data.min():.2f} to {valid_data.max():.2f} K")
            print(f"  Mean temperature: {valid_data.mean():.2f} K ({valid_data.mean()-273.15:.2f}°C)")
    
    return data, profile, transform, bounds, crs, nodata


def interpolate_change_factors_idw(cf_coords, cf_values, target_shape, target_transform, target_crs, source_crs='EPSG:4326', power=2):
    """
    Interpolate change factors using Inverse Distance Weighting (IDW).
    
    Args:
        cf_coords: Array of (lon, lat) coordinates for change factor points
        cf_values: Array of change factor values
        target_shape: (height, width) of target raster
        target_transform: Affine transform of target raster
        target_crs: CRS of target raster
        source_crs: CRS of change factor coordinates (default: WGS84)
        power: IDW power parameter (default: 2 for inverse square distance)
        
    Returns:
        2D array of interpolated change factors
    """
    from pyproj import Transformer
    
    # Create transformer from source CRS to target CRS
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    
    # Transform change factor coordinates to target CRS
    cf_x, cf_y = transformer.transform(cf_coords[:, 0], cf_coords[:, 1])
    cf_points = np.column_stack([cf_x, cf_y])
    
    print(f"  Transforming CF points from {source_crs} to {target_crs}")
    print(f"  CF point range: X=[{cf_x.min():.2f}, {cf_x.max():.2f}], Y=[{cf_y.min():.2f}, {cf_y.max():.2f}]")
    
    # Create grid of target raster coordinates
    height, width = target_shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    
    # Convert pixel coordinates to spatial coordinates
    xs, ys = rasterio.transform.xy(target_transform, rows, cols)
    xs = np.array(xs)
    ys = np.array(ys)
    target_points = np.column_stack([xs.ravel(), ys.ravel()])
    
    # Compute IDW interpolation
    print(f"  Computing IDW interpolation (power={power})...")
    
    # Calculate distances from each target point to all CF points
    distances = np.sqrt(((target_points[:, np.newaxis, :] - cf_points[np.newaxis, :, :]) ** 2).sum(axis=2))
    
    # Handle points that coincide with CF points (distance = 0)
    # Set minimum distance to avoid division by zero
    distances = np.maximum(distances, 1e-10)
    
    # Compute weights (inverse distance to the power)
    weights = 1.0 / (distances ** power)
    
    # Normalize weights
    weights = weights / weights.sum(axis=1, keepdims=True)
    
    # Compute weighted average
    interpolated = (weights * cf_values[np.newaxis, :]).sum(axis=1)
    
    # Reshape to grid
    interpolated_grid = interpolated.reshape(height, width)
    
    print(f"  Interpolated CF range: [{interpolated_grid.min():.4f}, {interpolated_grid.max():.4f}]")
    
    return interpolated_grid


def apply_change_factors(baseline_data, change_factors, nodata_value):
    """
    Apply additive temperature change factors to baseline data.
    
    For temperature, change factors are ADDITIVE (ΔT in Kelvin),
    so we ADD them to the baseline rather than multiplying.
    
    Args:
        baseline_data: Baseline raster data (K)
        change_factors: Interpolated additive change factors (ΔT in K)
        nodata_value: NoData value to preserve
        
    Returns:
        Future projection data (K)
    """
    # Create output array
    future_data = baseline_data.copy()
    
    # Apply additive change factors only to valid data
    valid_mask = baseline_data != nodata_value
    future_data[valid_mask] = baseline_data[valid_mask] + change_factors[valid_mask]
    
    return future_data


def save_future_projection(data, profile, output_path):
    """
    Save future projection raster to file.
    
    Args:
        data: Future projection data
        profile: Rasterio profile
        output_path: Output file path
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data, 1)
    
    print(f"  Saved: {output_path}")
    
    # Print statistics
    nodata = profile.get('nodata')
    valid_mask = data != nodata
    if valid_mask.any():
        valid_data = data[valid_mask]
        print(f"  Future temperature range: {valid_data.min():.2f} to {valid_data.max():.2f} K")
        print(f"  Future mean temperature: {valid_data.mean():.2f} K ({valid_data.mean()-273.15:.2f}°C)")


def process_model_season(model_name, variable, season, change_factors_dict):
    """
    Process a single model, variable, and season.
    
    Args:
        model_name: Name of the GCM model
        variable: 'tasmin' or 'tasmax'
        season: Season code (djf, mam, jja, son)
        change_factors_dict: Dictionary of change factors by season
    """
    print(f"\nProcessing {model_name} - {variable} - {season.upper()}...")
    print("-" * 60)
    
    # Load GRIDMET baseline
    baseline_data, profile, transform, bounds, crs, nodata = load_gridmet_baseline(season, variable)
    
    # Get change factors for this season
    cf_data = change_factors_dict[season]
    cf_coords = cf_data['coords']
    cf_values = cf_data['values']
    
    # Interpolate change factors to baseline grid
    print("Interpolating change factors...")
    interpolated_cf = interpolate_change_factors_idw(
        cf_coords, cf_values,
        baseline_data.shape, transform, crs,
        power=2
    )
    
    # Apply change factors
    print("Applying additive change factors to baseline...")
    future_data = apply_change_factors(baseline_data, interpolated_cf, nodata)
    
    # Save future projection
    var_name = 'min' if variable == 'tasmin' else 'max'
    output_file = OUTPUT_DIR / f'temp_{var_name}_future_{model_name}_{FUTURE_PERIOD}_{season}_30m.tif'
    save_future_projection(future_data, profile, output_file)


def main():
    """Main execution function."""
    print("=" * 70)
    print("Step 3: Apply Temperature Change Factors to GRIDMET Baseline")
    print("=" * 70)
    print(f"\nModels to process: {', '.join(MODELS)}")
    print(f"Variables to process: {', '.join(VARIABLES)}")
    print(f"Seasons: {', '.join([s.upper() for s in SEASONS])}")
    print(f"Future period: {FUTURE_PERIOD}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process each variable
    for variable in VARIABLES:
        print(f"\n" + "#" * 70)
        print(f"# Processing variable: {variable.upper()}")
        print("#" * 70)
        
        # Process each model
        for model_name in MODELS:
            try:
                print(f"\n" + "=" * 70)
                print(f"Model: {model_name} - Variable: {variable}")
                print("=" * 70)
                
                # Load change factors for this model and variable
                change_factors_dict = load_change_factors_geojson(model_name, variable)
                
                # Process each season
                for season in SEASONS:
                    process_model_season(model_name, variable, season, change_factors_dict)
                    
            except Exception as e:
                print(f"\nERROR processing {model_name} {variable}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    print("\n" + "=" * 70)
    print("Step 3 completed!")
    print("=" * 70)
    print(f"\nFuture temperature projections saved to: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
