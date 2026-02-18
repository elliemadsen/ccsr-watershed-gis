#!/usr/bin/env python3
"""
Step 3: Apply change factors to observed GRIDMET baseline

This script applies the computed change factors to the GRIDMET baseline 
precipitation rasters to create future climate projections at 30m resolution.

The process:
1. Load change factors for each model and season (point data at GCM grid scale)
2. Interpolate change factors to 30m resolution using Inverse Distance Weighting (IDW)
3. Multiply the interpolated change factors by the GRIDMET baseline rasters

Interpolation method: IDW with power=2 (inverse square distance)
- Creates smooth gradients between GCM grid points
- More physically realistic than nearest neighbor (Voronoi)
- Each pixel weighted by all GCM points based on distance

Formula: precip_future_30m = precip_baseline_30m × CF_precip

Usage:
    python 3_apply_change_factors.py

Requirements:
    - rasterio (available in conda geo environment)
    - scipy (for IDW interpolation)
    - numpy
    - pandas

Output:
    - precip_future_{model}_2035-2064_{season}_30m.tif: Future precipitation rasters
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
CHANGE_FACTORS_DIR = Path(__file__).parent.parent.parent / 'climate_models' / 'data' / 'change_factors'
GRIDMET_DIR = Path(__file__).parent.parent / 'gridmet' / 'processed'
OUTPUT_DIR = Path(__file__).parent / 'future_projections'

# Models to process
MODELS = ['ACCESS-ESM1-5', 'IPSL-CM6A-LR']

# Seasons (must match GRIDMET file names)
SEASONS = ['djf', 'mam', 'jja', 'son']

# Period labels
HISTORICAL_PERIOD = '1990-2019'
FUTURE_PERIOD = '2035-2064'


def load_change_factors_geojson(model_name):
    """
    Load change factors from GeoJSON file.
    
    Args:
        model_name: Name of the GCM model
        
    Returns:
        Dictionary with season keys and (coords, values) tuples
    """
    file_path = CHANGE_FACTORS_DIR / f'change_factors_{model_name}_pr_ssp370.geojson'
    
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
            cf = feature['properties'][f'cf_{season_upper}']
            
            coords.append((lon, lat))
            values.append(cf)
        
        coords = np.array(coords)
        values = np.array(values)
        
        change_factors[season] = {
            'coords': coords,
            'values': values,
            'count': len(coords)
        }
        
        print(f"  {season_upper}: {len(coords)} grid points, "
              f"CF range [{values.min():.4f}, {values.max():.4f}]")
    
    return change_factors


def load_gridmet_baseline(season):
    """
    Load GRIDMET baseline precipitation raster for a given season.
    
    Args:
        season: Season name (djf, mam, jja, son)
        
    Returns:
        Tuple of (data array, profile dict, transform)
    """
    file_path = GRIDMET_DIR / f'precip_final_30m_{season}.tif'
    
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
        print(f"  Resolution: {transform.a:.2f}m x {-transform.e:.2f}m")
        print(f"  Data range: [{np.nanmin(data):.4f}, {np.nanmax(data):.4f}]")
        print(f"  NoData value: {profile.get('nodata', 'None')}")
    
    return data, profile, transform, bounds, crs


def interpolate_change_factors(cf_data, raster_shape, transform, bounds, crs):
    """
    Interpolate change factors from GCM grid points to 30m raster grid.
    
    Args:
        cf_data: Dictionary with 'coords' and 'values' arrays
        raster_shape: Shape of target raster (height, width)
        transform: Affine transform of target raster
        bounds: Bounds of target raster
        crs: CRS of target raster
        
    Returns:
        Interpolated change factor array matching raster_shape
    """
    from rasterio.warp import transform as transform_coords
    
    print("  Interpolating change factors to 30m grid...")
    
    # Create meshgrid for target raster
    height, width = raster_shape
    
    # Generate pixel coordinates
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    
    # Convert pixel coordinates to projected coordinates
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    xs = np.array(xs)
    ys = np.array(ys)
    
    # Convert projected coordinates to geographic (lat/lon) for matching with GCM data
    xs_geo, ys_geo = transform_coords(crs, 'EPSG:4326', xs.flatten(), ys.flatten())
    
    # Flatten for interpolation (lon, lat format to match source)
    target_points = np.column_stack([xs_geo, ys_geo])
    
    # Source points (GCM grid) - already in (lon, lat) format
    source_points = cf_data['coords']
    source_values = cf_data['values']
    
    print(f"    Source points: {len(source_points)}")
    print(f"    Target points: {len(target_points)}")
    
    # Use Inverse Distance Weighting (IDW) interpolation
    # Each pixel gets weighted average of all GCM points based on distance
    # This creates smooth gradients instead of sharp Voronoi boundaries
    # More realistic for continuous atmospheric variables
    
    # Calculate distances from each target point to all source points
    from scipy.spatial.distance import cdist
    
    # Reshape target points for distance calculation
    distances = cdist(target_points, source_points, metric='euclidean')
    
    # IDW parameters
    power = 2  # Standard IDW uses power=2 (inverse square distance)
    min_distance = 1e-10  # Avoid division by zero
    
    # Calculate weights (inverse distance to power p)
    # Add small epsilon to avoid division by zero for points exactly on GCM grid
    weights = 1.0 / np.maximum(distances**power, min_distance)
    
    # Normalize weights to sum to 1 for each target point
    weights_normalized = weights / weights.sum(axis=1, keepdims=True)
    
    # Apply weights to get interpolated values
    interpolated = (weights_normalized * source_values).sum(axis=1)
    
    # Reshape to raster shape
    cf_raster = interpolated.reshape(raster_shape)
    
    print(f"    Interpolated CF range: [{np.nanmin(cf_raster):.4f}, {np.nanmax(cf_raster):.4f}]")
    
    return cf_raster


def apply_change_factors(baseline_data, cf_raster, nodata_value=None):
    """
    Apply change factors to baseline precipitation data.
    
    Args:
        baseline_data: GRIDMET baseline precipitation array
        cf_raster: Change factor array (same shape)
        nodata_value: NoData value to preserve
        
    Returns:
        Future precipitation array
    """
    print("  Applying change factors to baseline...")
    
    # Create mask for valid data
    if nodata_value is not None:
        valid_mask = baseline_data != nodata_value
    else:
        valid_mask = ~np.isnan(baseline_data)
    
    # Apply change factors
    future_data = baseline_data.copy()
    future_data[valid_mask] = baseline_data[valid_mask] * cf_raster[valid_mask]
    
    print(f"    Baseline range: [{np.nanmin(baseline_data[valid_mask]):.4f}, "
          f"{np.nanmax(baseline_data[valid_mask]):.4f}]")
    print(f"    Future range: [{np.nanmin(future_data[valid_mask]):.4f}, "
          f"{np.nanmax(future_data[valid_mask]):.4f}]")
    
    return future_data


def save_future_raster(data, profile, model_name, season, output_dir):
    """
    Save future precipitation raster to file.
    
    Args:
        data: Future precipitation array
        profile: Raster profile (metadata)
        model_name: Name of the GCM model
        season: Season name
        output_dir: Output directory path
        
    Returns:
        Path to saved file
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f'precip_future_{model_name}_{FUTURE_PERIOD}_{season}_30m.tif'
    output_path = output_dir / filename
    
    # Update profile
    profile.update(
        dtype=rasterio.float32,
        compress='lzw',
        tiled=True,
        blockxsize=256,
        blockysize=256
    )
    
    # Write raster
    print(f"  Saving to: {output_path}")
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data.astype(rasterio.float32), 1)
        
        # Add metadata
        dst.update_tags(
            model=model_name,
            scenario='ssp370',
            variable='precipitation',
            season=season.upper(),
            period=FUTURE_PERIOD,
            baseline_period=HISTORICAL_PERIOD,
            method='delta_change',
            description=f'Future precipitation projection for {model_name} under SSP3-7.0'
        )
    
    return output_path


def process_model_season(model_name, season, change_factors):
    """
    Process a single model-season combination.
    
    Args:
        model_name: Name of the GCM model
        season: Season name (djf, mam, jja, son)
        change_factors: Dictionary of change factors for all seasons
        
    Returns:
        Path to output file
    """
    print(f"\nProcessing {model_name} - {season.upper()}")
    print("-" * 70)
    
    # Load GRIDMET baseline
    baseline_data, profile, transform, bounds, crs = load_gridmet_baseline(season)
    
    # Get change factors for this season
    cf_data = change_factors[season]
    
    # Interpolate change factors to 30m grid
    cf_raster = interpolate_change_factors(
        cf_data,
        baseline_data.shape,
        transform,
        bounds,
        crs
    )
    
    # Apply change factors
    future_data = apply_change_factors(
        baseline_data,
        cf_raster,
        nodata_value=profile.get('nodata')
    )
    
    # Save result
    output_path = save_future_raster(
        future_data,
        profile,
        model_name,
        season,
        OUTPUT_DIR
    )
    
    print(f"  ✓ Successfully created future projection")
    
    return output_path


def process_model(model_name):
    """
    Process all seasons for a single GCM model.
    
    Args:
        model_name: Name of the GCM model
        
    Returns:
        List of output file paths
    """
    print(f"\n{'='*70}")
    print(f"Processing model: {model_name}")
    print(f"{'='*70}")
    
    # Load change factors for all seasons
    change_factors = load_change_factors_geojson(model_name)
    
    output_files = []
    
    # Process each season
    for season in SEASONS:
        try:
            output_path = process_model_season(model_name, season, change_factors)
            output_files.append(output_path)
        except Exception as e:
            print(f"\nERROR processing {model_name} - {season}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return output_files


def print_summary(all_output_files):
    """
    Print summary of generated files.
    
    Args:
        all_output_files: List of all output file paths
    """
    print("\n" + "="*70)
    print("Summary of Generated Files")
    print("="*70)
    
    for file_path in sorted(all_output_files):
        file_size = file_path.stat().st_size / 1024  # KB
        print(f"  {file_path.name:60s} ({file_size:>8.1f} KB)")
    
    print(f"\nTotal files created: {len(all_output_files)}")
    print(f"Output directory: {OUTPUT_DIR}")


def main():
    """Main execution function."""
    print("="*70)
    print("Step 3: Apply Change Factors to GRIDMET Baseline")
    print("="*70)
    print(f"\nModels to process: {', '.join(MODELS)}")
    print(f"Seasons: {', '.join([s.upper() for s in SEASONS])}")
    print(f"Baseline period: {HISTORICAL_PERIOD}")
    print(f"Future period: {FUTURE_PERIOD}")
    
    # Check that required files exist
    print(f"\nChecking required files...")
    print(f"  Change factors directory: {CHANGE_FACTORS_DIR}")
    print(f"  GRIDMET baseline directory: {GRIDMET_DIR}")
    
    all_output_files = []
    
    # Process each model
    for model_name in MODELS:
        try:
            output_files = process_model(model_name)
            all_output_files.extend(output_files)
        except Exception as e:
            print(f"\nERROR processing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    if all_output_files:
        print_summary(all_output_files)
    
    print("\n" + "="*70)
    print("Step 3 completed!")
    print("="*70)


if __name__ == '__main__':
    main()
