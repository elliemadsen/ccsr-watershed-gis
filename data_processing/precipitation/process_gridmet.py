#!/usr/bin/env python3
"""
GRIDMET Precipitation Processing Script

This script processes GRIDMET daily precipitation data:
1. Downloads GRIDMET precipitation data from 2006 to 2020
2. Clips to DEM boundary
3. Aggregates to seasonal totals (DJF, MAM, JJA, SON) and individual monthly totals
4. Computes multi-year seasonal averages (seasonal only, not monthly)
5. Reprojects to UTM Zone 18N and resamples to 30m resolution
6. Performs quality check with basic statistics

Usage:
    python process_gridmet.py
"""

import os
import subprocess
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
from scipy import stats

warnings.filterwarnings('ignore')


def download_gridmet_data(year, output_dir='../../data/precipitation/raw'):
    """
    Download GRIDMET precipitation data for a specific year.
    
    Args:
        year (int): Year to download
        output_dir (str): Directory to save downloaded files
    
    Returns:
        str: Path to downloaded file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"precip_raw_4000m_{year}.nc"
    filepath = output_dir / filename
    
    if filepath.exists():
        print(f"File already exists: {filepath}")
        return str(filepath)
    
    # GRIDMET uses pr_YYYY.nc naming on server
    source_filename = f"pr_{year}.nc"
    url = f"http://www.northwestknowledge.net/metdata/data/{source_filename}"
    print(f"Downloading {source_filename} as {filename}...")
    
    try:
        # Download with original name then rename
        subprocess.run(['wget', '-nc', '-c', '-O', str(filepath), url], 
                      check=True, capture_output=True)
        print(f"Successfully downloaded {filename}")
        return str(filepath)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading {filename}: {e}")
        return None


def clip_to_watershed(ds, watershed_path):
    """
    Clip dataset to watershed boundary with buffer.
    
    Args:
        ds (xarray.Dataset): Input dataset
        watershed_path (str): Path to watershed shapefile
    
    Returns:
        xarray.Dataset: Clipped dataset
    """
    import geopandas as gpd
    from pyproj import Transformer
    
    # Read watershed shapefile
    watershed = gpd.read_file(watershed_path)
    
    # Get bounding box in shapefile's CRS (likely UTM)
    bounds = watershed.total_bounds  # minx, miny, maxx, maxy
    minx_utm, miny_utm, maxx_utm, maxy_utm = bounds
    
    # Add buffer in UTM coordinates (5000m = 5km buffer)
    buffer_m = 5000
    minx_utm -= buffer_m
    miny_utm -= buffer_m
    maxx_utm += buffer_m
    maxy_utm += buffer_m
    
    # Get the CRS from the shapefile
    src_crs = watershed.crs
    
    # Convert buffered bounds to lat/lon for clipping GRIDMET data
    transformer = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
    
    # Transform corners (with buffer)
    minlon, minlat = transformer.transform(minx_utm, miny_utm)
    maxlon, maxlat = transformer.transform(maxx_utm, maxy_utm)
    
    # Check if lat coordinate is ascending or descending
    # Many climate datasets store lat in descending order (north to south)
    lat_ascending = ds.lat[0] < ds.lat[-1]
    
    # Clip dataset - handle descending lat coordinates
    if lat_ascending:
        ds_clipped = ds.sel(
            lon=slice(minlon, maxlon),
            lat=slice(minlat, maxlat)
        )
    else:
        # For descending lat, reverse the slice order
        ds_clipped = ds.sel(
            lon=slice(minlon, maxlon),
            lat=slice(maxlat, minlat)
        )
    
    print(f"Clipped to watershed bounds (with 5km buffer): lon=[{minlon:.4f}, {maxlon:.4f}], lat=[{minlat:.4f}, {maxlat:.4f}]")
    return ds_clipped


def aggregate_to_seasons(ds):
    """
    Aggregate daily precipitation to seasonal totals.
    
    Seasons:
        DJF: December-January-February (Winter)
        MAM: March-April-May (Spring)
        JJA: June-July-August (Summer)
        SON: September-October-November (Fall)
    
    Args:
        ds (xarray.Dataset): Daily precipitation dataset
    
    Returns:
        xarray.Dataset: Seasonal totals
    """
    # Add season coordinate
    ds = ds.assign_coords(season=ds['day'].dt.season)
    
    # Group by season and sum
    seasonal = ds.groupby('season').sum(dim='day')
    
    # Check which seasons are present
    available_seasons = seasonal.season.values
    print(f"  Available seasons: {', '.join(available_seasons)}")
    
    return seasonal


def aggregate_to_months(ds, year):
    """
    Aggregate daily precipitation to monthly totals for a specific year.
    
    Args:
        ds (xarray.Dataset): Daily precipitation dataset
        year (int): Year being processed
    
    Returns:
        dict: Dictionary mapping (year, month) to monthly datasets
    """
    # Create month number coordinate
    ds = ds.assign_coords(month=ds['day'].dt.month)
    ds = ds.assign_coords(year=ds['day'].dt.year)
    
    # Group by month and sum
    monthly = ds.groupby('month').sum(dim='day')
    
    # Check which months are present
    available_months = monthly.month.values
    print(f"  Available months: {available_months[0]} to {available_months[-1]} ({len(available_months)} months)")
    
    # Return as dict with (year, month) keys
    monthly_dict = {}
    for month_num in available_months:
        monthly_dict[(year, int(month_num))] = monthly.sel(month=month_num)
    
    return monthly_dict


def compute_multiyear_means(seasonal_datasets):
    """
    Compute multi-year seasonal averages.
    
    Args:
        seasonal_datasets (list): List of seasonal datasets from different years
    
    Returns:
        xarray.Dataset: Multi-year seasonal means
    """
    # Concatenate all years
    combined = xr.concat(seasonal_datasets, dim='year')
    
    # Compute mean across years
    multiyear_mean = combined.mean(dim='year')
    
    print(f"Computed multi-year means across {len(seasonal_datasets)} years")
    return multiyear_mean


def reproject_to_utm(ds, output_path, target_resolution=30, watershed_path=None):
    """
    Reproject from WGS84 to UTM Zone 18N and resample to target resolution.
    
    Args:
        ds (xarray.Dataset): Input dataset in WGS84
        output_path (str): Output GeoTIFF path
        target_resolution (int): Target resolution in meters
        watershed_path (str): Path to watershed shapefile for masking (optional)
    """
    import geopandas as gpd
    from rasterio import features
    
    # Get precipitation variable name
    var_name = 'precipitation_amount' if 'precipitation_amount' in ds else 'pr'
    data = ds[var_name].values
    
    # Source CRS (WGS84)
    src_crs = 'EPSG:4326'
    # Target CRS (UTM Zone 18N - WGS84)
    dst_crs = 'EPSG:32618'
    
    # Get coordinates
    lons = ds.lon.values
    lats = ds.lat.values
    
    # Ensure data is 2D - squeeze all singleton dimensions and validate
    data = np.squeeze(data)
    
    # If still not 2D, we need to handle it differently
    if data.ndim > 2:
        # Take the first slice if there are extra dimensions
        # This shouldn't happen if data is properly aggregated, but handle it
        print(f"Warning: Data has unexpected shape {data.shape}, taking first 2D slice")
        while data.ndim > 2:
            data = data[0]
    
    if data.ndim != 2:
        raise ValueError(f"Cannot reduce data to 2D, final shape: {data.shape}")
    
    # Calculate source transform
    src_transform = rasterio.transform.from_bounds(
        lons.min(), lats.min(), lons.max(), lats.max(),
        data.shape[-1], data.shape[-2]
    )
    
    # If watershed provided, use its bounds to define output grid
    if watershed_path and os.path.exists(watershed_path):
        watershed = gpd.read_file(watershed_path)
        
        # Ensure watershed is in destination CRS
        if watershed.crs != dst_crs:
            watershed = watershed.to_crs(dst_crs)
        
        # Get watershed bounds
        minx, miny, maxx, maxy = watershed.total_bounds
        
        # Calculate dimensions based on target resolution
        width = int((maxx - minx) / target_resolution)
        height = int((maxy - miny) / target_resolution)
        
        # Create transform from watershed bounds
        dst_transform = rasterio.transform.from_bounds(
            minx, miny, maxx, maxy,
            width, height
        )
    else:
        # Fallback: calculate from GRIDMET data bounds
        dst_transform, width, height = calculate_default_transform(
            src_crs, dst_crs,
            data.shape[-1], data.shape[-2],
            left=lons.min(), bottom=lats.min(),
            right=lons.max(), top=lats.max(),
            resolution=target_resolution
        )
    
    # Prepare output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set NoData value
    nodata_value = -9999.0
    
    # Initialize output with NoData
    dst_data = np.full((height, width), nodata_value, dtype=data.dtype)
    
    # Create watershed mask if provided
    watershed_mask = None
    if watershed_path and os.path.exists(watershed_path):
        # Watershed already loaded and reprojected above
        # Create a raster mask from the watershed polygons
        shapes = [(geom, 1) for geom in watershed.geometry]
        watershed_mask = features.rasterize(
            shapes=shapes,
            out_shape=(height, width),
            transform=dst_transform,
            fill=0,
            dtype=np.uint8
        ).astype(bool)
    
    # Reproject the data
    reproject(
        source=data,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )
    
    # Apply watershed mask if available
    if watershed_mask is not None:
        dst_data[~watershed_mask] = nodata_value
    
    # Write single-band output
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs=dst_crs,
        transform=dst_transform,
        nodata=nodata_value,
        compress='lzw'
    ) as dst:
        dst.write(dst_data, 1)
    
    print(f"Reprojected to UTM Zone 18N at {target_resolution}m resolution: {output_path}")


def quality_check_statistics(raster_path):
    """
    Quality check: Basic precipitation statistics.
    
    Args:
        raster_path (str): Path to precipitation raster
    """
    print("\n=== Quality Check: Precipitation Statistics ===")
    
    with rasterio.open(raster_path) as src:
        precip = src.read(1, masked=True)
        
        # Get valid (non-masked) data only
        valid_data = precip.compressed()  # Gets unmasked values
        
        # Basic statistics
        print(f"Precipitation statistics (valid data only):")
        print(f"  Min: {valid_data.min():.2f} mm")
        print(f"  Max: {valid_data.max():.2f} mm")
        print(f"  Mean: {valid_data.mean():.2f} mm")
        print(f"  Std: {valid_data.std():.2f} mm")
        print(f"  Valid pixels: {len(valid_data)}")
        print(f"  Masked pixels: {precip.mask.sum() if hasattr(precip.mask, 'sum') else 0}")


def main():
    # Hard-coded configuration
    start_year = 2006
    end_year = 2020
    
    watershed_path = '../../data/sub-basins/Subbasins.shp'
    raw_data_dir = Path('../../data/precipitation/raw')
    output_dir = Path('../../data/precipitation/processed')
    seasonal_dir = output_dir / 'seasonal'
    monthly_dir = output_dir / 'monthly'
    skip_download = False
    
    print("="*60)
    print("GRIDMET Precipitation Processing")
    print("="*60)
    print(f"Period: {start_year} - {end_year}")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Watershed boundary: {watershed_path}")
    print(f"Output directory: {output_dir}")
    print("  Seasonal: {}".format(seasonal_dir))
    print("  Monthly: {}".format(monthly_dir))
    print("="*60 + "\n")
    
    # Create output directories
    seasonal_dir.mkdir(parents=True, exist_ok=True)
    monthly_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download data
    if not skip_download:
        print("\n--- Step 1: Downloading GRIDMET data ---")
        for year in range(start_year, end_year + 1):
            download_gridmet_data(year, str(raw_data_dir))
    
    # Step 2-3: Process each year
    print("\n--- Step 2-3: Processing yearly data ---")
    seasonal_datasets = []
    monthly_datasets = {}  # Dict with (year, month) keys
    
    for year in range(start_year, end_year + 1):
        nc_file = raw_data_dir / f"precip_raw_4000m_{year}.nc"
        
        if not nc_file.exists():
            print(f"Warning: {nc_file} not found, skipping...")
            continue
        
        print(f"\nProcessing {year}...")
        
        # Load dataset
        ds = xr.open_dataset(nc_file)
        
        # Check temporal coverage
        time_start = ds['day'].values[0]
        time_end = ds['day'].values[-1]
        print(f"  Data coverage: {time_start} to {time_end}")
        
        # Clip to watershed boundary
        ds_clipped = clip_to_watershed(ds, watershed_path)
        
        # Aggregate to seasons
        seasonal = aggregate_to_seasons(ds_clipped)
        seasonal_datasets.append(seasonal)
        
        # Aggregate to months
        monthly = aggregate_to_months(ds_clipped, year)
        monthly_datasets.update(monthly)
        
        ds.close()
    
    if not seasonal_datasets:
        print("Error: No data to process!")
        return
    
    # Step 4: Compute multi-year means
    print("\n--- Step 4: Computing multi-year seasonal means ---")
    multiyear_means = compute_multiyear_means(seasonal_datasets)
    
    # Determine actual year range processed (min and max from successfully loaded files)
    years_processed = []
    for year in range(start_year, end_year + 1):
        nc_file = raw_data_dir / f"precip_raw_4000m_{year}.nc"
        if nc_file.exists():
            years_processed.append(year)
    
    year_range = f"{min(years_processed)}-{max(years_processed)}"
    print(f"Year range: {year_range}")
    
    # Step 5a: Reproject and save seasonal data
    print("\n--- Step 5a: Reprojecting seasonal data to UTM Zone 18N ---")
    
    seasons = {'DJF': 'Winter', 'MAM': 'Spring', 'JJA': 'Summer', 'SON': 'Fall'}
    
    for season_code, season_name in seasons.items():
        if season_code in multiyear_means.season.values:
            output_file = seasonal_dir / f"precip_final_30m_{year_range}_{season_code.lower()}.tif"
            season_data = multiyear_means.sel(season=season_code)
            print(f"Saving {season_name} ({season_code})...")
            reproject_to_utm(season_data, output_file, target_resolution=30, watershed_path=watershed_path)
    
    # Step 5b: Save individual monthly files
    print("\n--- Step 5b: Saving individual monthly files ---")
    
    # Sort by year and month for organized output
    sorted_keys = sorted(monthly_datasets.keys())
    
    for (year, month_num) in sorted_keys:
        month_data = monthly_datasets[(year, month_num)]
        output_file = monthly_dir / f"precip_30m_{year}_{month_num:02d}.tif"
        print(f"Saving {year}-{month_num:02d}...")
        reproject_to_utm(month_data, output_file, target_resolution=30, watershed_path=watershed_path)
    
    # Step 6: Quality check
    print("\n--- Step 6: Quality Check ---")
    # Check one season as example
    example_file = seasonal_dir / f"precip_final_30m_{year_range}_jja.tif"
    if example_file.exists():
        quality_check_statistics(example_file)
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Seasonal files saved to: {seasonal_dir}")
    print(f"Monthly files saved to: {monthly_dir}")
    print("="*60)


if __name__ == '__main__':
    main()
