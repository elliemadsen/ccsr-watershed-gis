#!/usr/bin/env python3
"""
GRIDMET Precipitation Processing Script

This script processes GRIDMET daily precipitation data:
1. Downloads GRIDMET precipitation data from 2015 to present
2. Clips to DEM boundary
3. Aggregates to seasonal totals (DJF, MAM, JJA, SON)
4. Computes multi-year seasonal averages
5. Reprojects to UTM Zone 18N and resamples to 30m resolution
6. Performs quality check for orographic gradient

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


def download_gridmet_data(year, output_dir='raw'):
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
    return seasonal


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
    # Target CRS (UTM Zone 18N)
    dst_crs = 'EPSG:26918'
    
    # Get coordinates
    lons = ds.lon.values
    lats = ds.lat.values
    
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
    
    # Handle both 2D and 3D arrays
    if data.ndim == 2:
        data = data[np.newaxis, :, :]
    
    # Set NoData value
    nodata_value = -9999.0
    
    # Initialize with NoData instead of zeros
    dst_data = np.full((data.shape[0], height, width), nodata_value, dtype=data.dtype)
    
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
    
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=height,
        width=width,
        count=data.shape[0],
        dtype=data.dtype,
        crs=dst_crs,
        transform=dst_transform,
        nodata=nodata_value,
        compress='lzw'
    ) as dst:
        for i in range(data.shape[0]):
            reproject(
                source=data[i],
                destination=dst_data[i],
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
            
            # Apply watershed mask if available
            if watershed_mask is not None:
                dst_data[i][~watershed_mask] = nodata_value
            
            dst.write(dst_data[i], i + 1)
    
    print(f"Reprojected to UTM Zone 18N at {target_resolution}m resolution: {output_path}")


def quality_check_orographic_gradient(raster_path, watershed_path=None):
    """
    Quality check: Verify orographic gradient.
    Higher elevations should show higher precipitation.
    
    Args:
        raster_path (str): Path to precipitation raster
        watershed_path (str): Path to watershed shapefile (not used for QC)
    """
    print("\n=== Quality Check: Orographic Gradient ===")
    
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
        
        # Check gradient (northwest should be higher)
        # Divide into quadrants
        h, w = precip.shape
        nw_quadrant = precip[:h//2, :w//2].mean()
        se_quadrant = precip[h//2:, w//2:].mean()
        
        print(f"\nQuadrant analysis:")
        print(f"  Northwest mean: {nw_quadrant:.2f} mm")
        print(f"  Southeast mean: {se_quadrant:.2f} mm")
        print(f"  NW/SE ratio: {nw_quadrant/se_quadrant:.3f}")
        
        if nw_quadrant > se_quadrant:
            print("  ✓ Orographic gradient verified: NW > SE")
        else:
            print("  ⚠ Warning: Expected higher precipitation in NW")


def main():
    # Hard-coded configuration
    start_year = 2015
    end_year = datetime.now().year
    watershed_path = '../../data/sub-basins/Subbasins.shp'
    output_dir = Path('processed')
    skip_download = False
    
    print("="*60)
    print("GRIDMET Precipitation Processing")
    print("="*60)
    print(f"Period: {start_year} - {end_year}")
    print(f"Watershed boundary: {watershed_path}")
    print(f"Output directory: {output_dir}")
    print("="*60 + "\n")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download data
    if not skip_download:
        print("\n--- Step 1: Downloading GRIDMET data ---")
        for year in range(start_year, end_year + 1):
            download_gridmet_data(year)
    
    # Step 2-3: Process each year
    print("\n--- Step 2-3: Processing yearly data ---")
    seasonal_datasets = []
    
    for year in range(start_year, end_year + 1):
        nc_file = f"raw/precip_raw_4000m_{year}.nc"
        
        if not os.path.exists(nc_file):
            print(f"Warning: {nc_file} not found, skipping...")
            continue
        
        print(f"\nProcessing {year}...")
        
        # Load dataset
        ds = xr.open_dataset(nc_file)
        
        # Clip to watershed boundary
        ds_clipped = clip_to_watershed(ds, watershed_path)
        
        # Aggregate to seasons
        seasonal = aggregate_to_seasons(ds_clipped)
        seasonal_datasets.append(seasonal)
        
        ds.close()
    
    if not seasonal_datasets:
        print("Error: No data to process!")
        return
    
    # Step 4: Compute multi-year means
    print("\n--- Step 4: Computing multi-year seasonal means ---")
    multiyear_means = compute_multiyear_means(seasonal_datasets)
    
    # Step 5: Reproject and save each season
    print("\n--- Step 5: Reprojecting to UTM Zone 18N ---")
    
    seasons = {'DJF': 'Winter', 'MAM': 'Spring', 'JJA': 'Summer', 'SON': 'Fall'}
    
    for season_code, season_name in seasons.items():
        if season_code in multiyear_means.season.values:
            output_file = output_dir / f"precip_final_30m_{season_code.lower()}.tif"
            season_data = multiyear_means.sel(season=season_code)
            print(f"Saving {season_name} ({season_code})...")
            reproject_to_utm(season_data, output_file, target_resolution=30, watershed_path=watershed_path)
    
    # Step 6: Quality check
    print("\n--- Step 6: Quality Check ---")
    # Check one season as example
    example_file = output_dir / "precip_final_30m_jja.tif"
    if example_file.exists():
        quality_check_orographic_gradient(example_file, watershed_path)
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Output files saved to: {output_dir}")
    print("="*60)


if __name__ == '__main__':
    main()
