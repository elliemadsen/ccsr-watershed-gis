#!/usr/bin/env python3
"""
GRIDMET Min/Max Temperature Processing Script

This script processes GRIDMET daily minimum and maximum temperature data separately:
1. Downloads GRIDMET minimum (tmmn) and maximum (tmmx) temperature data from 2006 to 2020
2. Processes each variable separately (no averaging)
3. Clips to DEM boundary
4. Aggregates to seasonal averages (DJF, MAM, JJA, SON) and individual monthly averages
5. Computes multi-year seasonal averages (seasonal only, not monthly)
6. Reprojects to UTM Zone 18N and resamples to 30m resolution
7. Performs quality check with basic statistics

Output: Separate files for tmmn and tmmx at each processing stage

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


def download_gridmet_data(year, variable, output_dir='../../data/temp/raw', watershed_path='../../data/sub-basins/Subbasins.shp'):
    """
    Download GRIDMET temperature data for a specific year and variable.
    Uses OpenDAP to spatially subset data before downloading (much faster).
    
    Args:
        year (int): Year to download
        variable (str): Either 'tmmn' (min temp) or 'tmmx' (max temp)
        output_dir (str): Directory to save downloaded files
        watershed_path (str): Path to watershed shapefile for spatial subsetting
    
    Returns:
        str: Path to downloaded file
    """
    import xarray as xr
    import geopandas as gpd
    from pyproj import Transformer
    
    output_dir = Path(output_dir)
    # Create separate folders for min and max
    var_dir = output_dir / ('min' if variable == 'tmmn' else 'max')
    var_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file
    filename = f"{variable}_raw_4000m_{year}.nc"
    filepath = var_dir / filename
    
    if filepath.exists():
        print(f"File already exists: {filepath}")
        return str(filepath)
    
    print(f"Downloading {variable} data for {year}...")
    
    try:
        # Get watershed bounds for spatial subsetting
        watershed = gpd.read_file(watershed_path)
        bounds = watershed.total_bounds  # minx, miny, maxx, maxy
        
        # Add buffer (5km)
        buffer_m = 5000
        minx_utm, miny_utm, maxx_utm, maxy_utm = bounds
        minx_utm -= buffer_m
        miny_utm -= buffer_m
        maxx_utm += buffer_m
        maxy_utm += buffer_m
        
        # Transform to lat/lon for GRIDMET
        transformer = Transformer.from_crs(watershed.crs, "EPSG:4326", always_xy=True)
        minlon, minlat = transformer.transform(minx_utm, miny_utm)
        maxlon, maxlat = transformer.transform(maxx_utm, maxy_utm)
        
        print(f"  Spatial subset: lon=[{minlon:.4f}, {maxlon:.4f}], lat=[{minlat:.4f}, {maxlat:.4f}]")
        
        # Use OpenDAP to access data with spatial subsetting
        opendap_base = "http://thredds.northwestknowledge.net:8080/thredds/dodsC/MET"
        
        # Download temperature data via OpenDAP
        print(f"  Loading {variable} via OpenDAP...")
        url = f"{opendap_base}/{variable}/{variable}_{year}.nc"
        ds = xr.open_dataset(url)
        ds = ds.sel(lon=slice(minlon, maxlon), lat=slice(maxlat, minlat))
        
        # Load data into memory and save (this is where actual download happens)
        print(f"  Downloading spatial subset...")
        ds = ds.load()
        ds.to_netcdf(filepath)
        
        ds.close()
        
        print(f"  Successfully created {filename}")
        return str(filepath)
        
    except Exception as e:
        print(f"  Error downloading/processing temperature data: {e}")
        import traceback
        traceback.print_exc()
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
    Aggregate daily temperature to seasonal averages.
    
    Seasons:
        DJF: December-January-February (Winter)
        MAM: March-April-May (Spring)
        JJA: June-July-August (Summer)
        SON: September-October-November (Fall)
    
    Args:
        ds (xarray.Dataset): Daily temperature dataset
    
    Returns:
        xarray.Dataset: Seasonal averages
    """
    # Add season coordinate
    ds = ds.assign_coords(season=ds['day'].dt.season)
    
    # Group by season and compute mean (not sum for temperature)
    seasonal = ds.groupby('season').mean(dim='day')
    
    # Check which seasons are present
    available_seasons = seasonal.season.values
    print(f"  Available seasons: {', '.join(available_seasons)}")
    
    return seasonal


def aggregate_to_months(ds, year):
    """
    Aggregate daily temperature to monthly averages for a specific year.
    
    Args:
        ds (xarray.Dataset): Daily temperature dataset
        year (int): Year being processed
    
    Returns:
        dict: Dictionary mapping (year, month) to monthly datasets
    """
    # Create month number coordinate
    ds = ds.assign_coords(month=ds['day'].dt.month)
    ds = ds.assign_coords(year=ds['day'].dt.year)
    
    # Group by month and compute mean (not sum for temperature)
    monthly = ds.groupby('month').mean(dim='day')
    
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
    
    # Get temperature variable name
    var_name = 'air_temperature' if 'air_temperature' in ds else 'tmmean'
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
            shapes,
            out_shape=(height, width),
            transform=dst_transform,
            fill=0,
            dtype='uint8'
        )
    
    # Perform reprojection
    reproject(
        source=data,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
        src_nodata=None,
        dst_nodata=nodata_value
    )
    
    # Apply watershed mask if available
    if watershed_mask is not None:
        dst_data[watershed_mask == 0] = nodata_value
    
    # Write output
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=dst_data.dtype,
        crs=dst_crs,
        transform=dst_transform,
        nodata=nodata_value,
        compress='lzw'
    ) as dst:
        dst.write(dst_data, 1)
    
    print(f"  Saved: {output_path}")


def quality_check_statistics(raster_path):
    """
    Perform basic quality check on output raster.
    
    Args:
        raster_path (str): Path to raster file
    """
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        nodata = src.nodata
        
        # Mask NoData values
        valid_data = data[data != nodata]
        
        if len(valid_data) == 0:
            print("Warning: No valid data in raster!")
            return
        
        print("\nQuality Check:")
        print(f"  Valid pixels: {len(valid_data):,}")
        print(f"  Mean: {valid_data.mean():.2f} K")
        print(f"  Std: {valid_data.std():.2f} K")
        print(f"  Min: {valid_data.min():.2f} K")
        print(f"  Max: {valid_data.max():.2f} K")
        print(f"  Median: {np.median(valid_data):.2f} K")


def main():
    """
    Main processing pipeline for GRIDMET temperature data.
    """
    print("="*60)
    print("GRIDMET Mean Temperature Processing Pipeline")
    print("="*60)
    
    # Configuration
    start_year = 2006
    end_year = 2020
    skip_download = False  # Set to True to skip downloading and only process existing files
    
    # Paths (relative to script location in data_processing/temp/)
    raw_data_dir = Path('../../data/temp/raw')
    seasonal_dir = Path('../../data/temp/processed/seasonal')
    monthly_dir = Path('../../data/temp/processed/monthly')
    watershed_path = '../../data/sub-basins/Subbasins.shp'
    
    # Create directories
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    seasonal_dir.mkdir(parents=True, exist_ok=True)
    monthly_dir.mkdir(parents=True, exist_ok=True)
    
    # Process both tmmn (min) and tmmx (max) separately
    for variable in ['tmmn', 'tmmx']:
        var_name = 'min' if variable == 'tmmn' else 'max'
        print(f"\n{'='*60}")
        print(f"Processing {var_name.upper()} temperature ({variable})")
        print(f"{'='*60}")
        
        # Step 1: Download data
        if not skip_download:
            print(f"\n--- Step 1: Downloading GRIDMET {variable} data ---")
            for year in range(start_year, end_year + 1):
                download_gridmet_data(year, variable, str(raw_data_dir), watershed_path)
        
        # Step 2-3: Process each year
        print(f"\n--- Step 2-3: Processing yearly {variable} data ---")
        seasonal_datasets = []
        monthly_datasets = {}  # Dict with (year, month) keys
        
        var_dir = raw_data_dir / ('min' if variable == 'tmmn' else 'max')
        
        for year in range(start_year, end_year + 1):
            nc_file = var_dir / f"{variable}_raw_4000m_{year}.nc"
            
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
            
            # Aggregate to seasons (mean, not sum)
            seasonal = aggregate_to_seasons(ds_clipped)
            seasonal_datasets.append(seasonal)
            
            # Aggregate to months (mean, not sum)
            monthly = aggregate_to_months(ds_clipped, year)
            monthly_datasets.update(monthly)
            
            ds.close()
        
        if not seasonal_datasets:
            print(f"Error: No {variable} data to process!")
            continue
        
        # Step 4: Compute multi-year means
        print(f"\n--- Step 4: Computing multi-year seasonal means for {variable} ---")
        multiyear_means = compute_multiyear_means(seasonal_datasets)
        
        # Determine actual year range processed (min and max from successfully loaded files)
        years_processed = []
        for year in range(start_year, end_year + 1):
            nc_file = var_dir / f"{variable}_raw_4000m_{year}.nc"
            if nc_file.exists():
                years_processed.append(year)
        
        year_range = f"{min(years_processed)}-{max(years_processed)}"
        print(f"Year range: {year_range}")
        
        # Step 5a: Reproject and save seasonal data
        print(f"\n--- Step 5a: Reprojecting seasonal {variable} data to UTM Zone 18N ---")
        
        seasons = {'DJF': 'Winter', 'MAM': 'Spring', 'JJA': 'Summer', 'SON': 'Fall'}
        
        for season_code, season_name in seasons.items():
            if season_code in multiyear_means.season.values:
                output_file = seasonal_dir / f"temp_{var_name}_final_30m_{year_range}_{season_code.lower()}.tif"
                season_data = multiyear_means.sel(season=season_code)
                print(f"Saving {season_name} ({season_code})...")
                reproject_to_utm(season_data, output_file, target_resolution=30, watershed_path=watershed_path)
        
        # Step 5b: Save individual monthly files
        print(f"\n--- Step 5b: Saving individual monthly {variable} files ---")
        
        # Sort by year and month for organized output
        sorted_keys = sorted(monthly_datasets.keys())
        
        for (year, month_num) in sorted_keys:
            month_data = monthly_datasets[(year, month_num)]
            output_file = monthly_dir / f"temp_{var_name}_{year}_{month_num:02d}_30m.tif"
            print(f"Saving {year}-{month_num:02d}...")
            reproject_to_utm(month_data, output_file, target_resolution=30, watershed_path=watershed_path)
        
        # Step 6: Quality check
        print(f"\n--- Step 6: Quality Check for {variable} ---")
        # Check one season as example
        example_file = seasonal_dir / f"temp_{var_name}_final_30m_{year_range}_jja.tif"
        if example_file.exists():
            quality_check_statistics(example_file)
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Seasonal files saved to: {seasonal_dir}")
    print(f"Monthly files saved to: {monthly_dir}")
    print("="*60)


if __name__ == '__main__':
    main()
