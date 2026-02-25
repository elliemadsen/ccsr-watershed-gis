#!/usr/bin/env python3
"""
TWI-based Stream Proximity Processing Script

This script derives stream networks from Topographic Wetness Index (TWI) 
and calculates distance to nearest stream for the watershed.

Processing steps:
1. Load TWI raster
2. Generate binary stream networks at multiple TWI thresholds
3. Calculate Euclidean distance to nearest stream for each threshold
4. Crop outputs to watershed boundary

Usage:
    python process_twi_stream_proximity.py
"""

import numpy as np
import rasterio
from rasterio.mask import mask
from pathlib import Path
from scipy.ndimage import distance_transform_edt
import geopandas as gpd
import warnings

warnings.filterwarnings('ignore')


def crop_to_watershed(input_raster, watershed_boundary, output_path):
    """
    Crop a raster to the watershed boundary.
    
    Args:
        input_raster: Path to input raster file
        watershed_boundary: Path to watershed boundary shapefile
        output_path: Path to save cropped raster
    
    Returns:
        Path to cropped raster
    """
    # Load watershed boundary
    boundary = gpd.read_file(watershed_boundary)
    
    # Reproject to match raster CRS if needed
    with rasterio.open(input_raster) as src:
        raster_crs = src.crs
        if boundary.crs != raster_crs:
            boundary = boundary.to_crs(raster_crs)
        
        # Dissolve all features into a single polygon (watershed outline)
        boundary_dissolved = boundary.dissolve()
        
        # Crop raster to boundary
        out_image, out_transform = mask(src, boundary_dissolved.geometry, crop=True)
        out_meta = src.meta.copy()
    
    # Update metadata
    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })
    
    # Write cropped raster
    with rasterio.open(output_path, 'w', **out_meta) as dst:
        dst.write(out_image)
    
    return output_path


def generate_twi_stream_network(twi_path, threshold, output_dir):
    """
    Generate binary stream network from TWI using a threshold.
    Higher TWI values indicate wetter areas (potential streams).
    
    Args:
        twi_path: Path to TWI raster
        threshold: TWI threshold for stream definition (e.g., 12, 14, 16, 18)
        output_dir: Directory to save stream network
    
    Returns:
        Path to stream network raster
    """
    print(f"\n--- Generating Stream Network (TWI Threshold: {threshold}) ---")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load TWI
    with rasterio.open(twi_path) as src:
        twi = src.read(1, masked=True)
        meta = src.meta.copy()
        cell_size = src.res[0]
    
    print(f"TWI loaded: {twi.shape}")
    print(f"TWI range: {np.min(twi):.2f} to {np.max(twi):.2f}")
    print(f"TWI threshold: {threshold}")
    
    # Create binary stream raster (1 = stream where TWI >= threshold, 0 = non-stream)
    stream_binary = np.where(twi >= threshold, 1, 0)
    
    # Count stream cells
    stream_cells = np.sum(stream_binary == 1)
    stream_area_m2 = stream_cells * (cell_size * cell_size)
    stream_km2 = stream_area_m2 / 1000000
    
    print(f"Stream cells: {stream_cells:,}")
    print(f"Stream area: {stream_km2:.2f} km²")
    print(f"Stream percentage: {(stream_cells / stream_binary.size) * 100:.2f}%")
    
    # Save stream network
    stream_path = output_dir / f'stream_network_twi{threshold}.tif'
    
    meta.update({
        'dtype': 'uint8',
        'nodata': 255
    })
    
    with rasterio.open(stream_path, 'w', **meta) as dst:
        dst.write(stream_binary.astype('uint8'), 1)
    
    print(f"Stream network saved to: {stream_path}")
    
    return stream_path


def calculate_stream_distance(stream_path, output_dir, cell_size=30):
    """
    Calculate Euclidean distance to nearest stream.
    
    Args:
        stream_path: Path to binary stream network raster
        output_dir: Directory to save distance raster
        cell_size: Cell size in meters (default 30m for TWI)
    
    Returns:
        Path to distance raster
    """
    threshold_name = stream_path.stem.replace('stream_network_', '')
    print(f"\n--- Calculating Distance to Stream ({threshold_name}) ---")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load stream network
    with rasterio.open(stream_path) as src:
        stream = src.read(1, masked=True)
        meta = src.meta.copy()
    
    # Invert stream raster (streams = 0, non-streams = 1) for distance transform
    # Also handle masked values
    inverted = np.ones_like(stream.filled(1), dtype=np.uint8)
    inverted[stream == 1] = 0
    
    # Calculate Euclidean distance transform
    print("Computing Euclidean distance transform...")
    distance = distance_transform_edt(inverted)
    
    # Convert from cells to meters
    distance_m = distance * cell_size
    
    print(f"Distance statistics:")
    print(f"  Min: {np.min(distance_m):.1f} m")
    print(f"  Max: {np.max(distance_m):.1f} m")
    print(f"  Mean: {np.mean(distance_m):.1f} m")
    print(f"  Median: {np.median(distance_m):.1f} m")
    
    # Save distance raster
    distance_path = output_dir / f'stream_distance_{threshold_name}.tif'
    
    meta.update({
        'dtype': 'float32',
        'nodata': -9999
    })
    
    with rasterio.open(distance_path, 'w', **meta) as dst:
        dst.write(distance_m.astype('float32'), 1)
    
    print(f"Distance raster saved to: {distance_path}")
    
    return distance_path


def main():
    """Main processing workflow."""
    
    # Configuration
    twi_path = '../../data/topographic_wetness_index/TWI_30m.tif'
    watershed_boundary = '../../data/sub-basins/Subbasins.shp'
    output_dir = Path('../../data/stream_proximity/twi')
    
    # Create output subdirectories
    stream_dir = output_dir / 'stream_networks'
    distance_dir = output_dir / 'stream_distance'
    
    # TWI thresholds (higher TWI = wetter areas = potential streams)
    # Typical values: 12-18, adjust based on your watershed characteristics
    twi_thresholds = [12, 14, 16, 18]
    
    print("="*60)
    print("TWI-based Stream Proximity Processing")
    print("="*60)
    print(f"TWI: {twi_path}")
    print(f"Watershed boundary: {watershed_boundary}")
    print(f"Output directory: {output_dir}")
    print(f"TWI Thresholds: {twi_thresholds}")
    print("="*60)
    
    # Check if TWI exists
    if not Path(twi_path).exists():
        print(f"\n❌ Error: TWI not found at {twi_path}")
        return
    
    # Check if watershed boundary exists
    if not Path(watershed_boundary).exists():
        print(f"\n❌ Error: Watershed boundary not found at {watershed_boundary}")
        return
    
    # Get cell size from TWI
    with rasterio.open(twi_path) as src:
        cell_size = src.res[0]
    
    # Process each TWI threshold
    for threshold in twi_thresholds:
        stream_output_path = stream_dir / f'stream_network_twi{threshold}.tif'
        distance_output_path = distance_dir / f'stream_distance_twi{threshold}.tif'
        
        # Generate and crop stream network
        if not stream_output_path.exists():
            # Generate uncropped stream network
            stream_uncropped = generate_twi_stream_network(
                twi_path, 
                threshold, 
                stream_dir
            )
            
            # Crop to watershed boundary (overwrites the uncropped version)
            print(f"Cropping stream network to watershed boundary...")
            crop_to_watershed(stream_uncropped, watershed_boundary, stream_output_path)
            print(f"Stream network saved to: {stream_output_path}")
            
            # Remove uncropped version if different from output
            if stream_uncropped != stream_output_path:
                stream_uncropped.unlink()
        else:
            print(f"\n✓ Stream network already exists: {stream_output_path}")
        
        # Calculate and crop distance from stream network
        if not distance_output_path.exists():
            # Calculate distance from cropped stream network
            distance_uncropped = calculate_stream_distance(
                stream_output_path,
                distance_dir,
                cell_size
            )
            
            # Crop to watershed boundary (overwrites the uncropped version)
            print(f"Cropping distance raster to watershed boundary...")
            crop_to_watershed(distance_uncropped, watershed_boundary, distance_output_path)
            print(f"Distance raster saved to: {distance_output_path}")
            
            # Remove uncropped version if different from output
            if distance_uncropped != distance_output_path:
                distance_uncropped.unlink()
        else:
            print(f"✓ Distance raster already exists: {distance_output_path}")
    
    print("\n" + "="*60)
    print("Processing complete!")
    print("="*60)
    print("\nOutput files:")
    print(f"  Stream networks: {stream_dir}/")
    print(f"  Distance rasters: {distance_dir}/")
    print("\nNote: Load stream networks in QGIS to compare with NHD flowlines")
    print("and select the optimal TWI threshold based on visual agreement.")
    print("="*60)


if __name__ == '__main__':
    main()
