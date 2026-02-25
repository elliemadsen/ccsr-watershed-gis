#!/usr/bin/env python3
"""
Stream Proximity Processing Script

This script derives stream networks from DEM flow accumulation and calculates
distance to nearest stream for the watershed.

Processing steps:
1. Load DEM and calculate flow accumulation using D-infinity algorithm (Tarboton 1997)
2. Convert flow accumulation to contributing area (m²)
3. Generate binary stream networks at multiple thresholds (25, 50, 75, 100 ha)
4. Calculate Euclidean distance to nearest stream for each threshold

Usage:
    python process_stream_proximity.py
"""

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio import features
from rasterio.mask import mask
from pathlib import Path
from scipy.ndimage import distance_transform_edt
import geopandas as gpd
import whitebox
import warnings

warnings.filterwarnings('ignore')


def calculate_flow_accumulation(dem_path, output_dir):
    """
    Calculate flow accumulation from DEM using D-infinity algorithm (Tarboton 1997).
    
    Args:
        dem_path: Path to DEM file
        output_dir: Directory to save flow accumulation raster
    
    Returns:
        Path to flow accumulation raster
    """
    print("\n--- Step 1: Calculating Flow Accumulation (D-infinity) ---")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize WhiteboxTools
    wbt = whitebox.WhiteboxTools()
    wbt.set_verbose_mode(True)  # Enable to see what's happening
    wbt.set_compress_rasters(False)  # Avoid compression issues
    
    # Convert to absolute paths
    dem_path = Path(dem_path).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get DEM info
    with rasterio.open(dem_path) as src:
        dem_shape = (src.height, src.width)
        cell_size = src.res
    
    print(f"DEM loaded: {dem_shape}")
    print(f"DEM resolution: {cell_size}")
    
    # Condition DEM (fill depressions, breach, etc.)
    print("Conditioning DEM (filling depressions and breaching)...")
    conditioned_path = output_dir / 'dem_conditioned.tif'
    wbt.breach_depressions(
        str(dem_path),
        str(conditioned_path)
    )
    
    # Check if conditioned DEM was created
    if not conditioned_path.exists():
        raise RuntimeError(f"Failed to create conditioned DEM at {conditioned_path}")
    
    # Calculate D-infinity flow accumulation
    print("Calculating D-infinity flow accumulation...")
    flow_acc_path = output_dir / 'flow_accumulation.tif'
    
    wbt.d_inf_flow_accumulation(
        str(conditioned_path),
        str(flow_acc_path),
        out_type="cells"
    )
    
    # Check if flow accumulation was created
    if not flow_acc_path.exists():
        raise RuntimeError(f"Failed to create flow accumulation at {flow_acc_path}")
    
    # Read and report statistics
    with rasterio.open(flow_acc_path) as src:
        acc = src.read(1, masked=True)
    
    print(f"Flow accumulation saved to: {flow_acc_path}")
    print(f"  Min: {np.min(acc):.0f}, Max: {np.max(acc):.0f}, Mean: {np.mean(acc):.0f}")
    
    # Clean up conditioned DEM
    conditioned_path.unlink()
    
    return flow_acc_path


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


def generate_stream_network(flow_acc_path, threshold_ha, output_dir, cell_size=10):
    """
    Generate binary stream network from flow accumulation.
    
    Args:
        flow_acc_path: Path to flow accumulation raster
        threshold_ha: Threshold in hectares for stream definition
        output_dir: Directory to save stream network
        cell_size: Cell size in meters (default 10m)
    
    Returns:
        Path to stream network raster
    """
    print(f"\n--- Generating Stream Network (Threshold: {threshold_ha} ha) ---")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load flow accumulation
    with rasterio.open(flow_acc_path) as src:
        flow_acc = src.read(1, masked=True)
        meta = src.meta.copy()
    
    # Convert flow accumulation to contributing area (m²)
    cell_area = cell_size * cell_size  # m²
    contributing_area_m2 = flow_acc * cell_area
    
    # Convert threshold from hectares to m²
    threshold_m2 = threshold_ha * 10000  # 1 ha = 10,000 m²
    
    print(f"Cell area: {cell_area} m²")
    print(f"Threshold: {threshold_ha} ha = {threshold_m2} m²")
    
    # Create binary stream raster (1 = stream, 0 = non-stream)
    stream_binary = np.where(contributing_area_m2 > threshold_m2, 1, 0)
    
    # Count stream cells
    stream_cells = np.sum(stream_binary == 1)
    stream_km = (stream_cells * cell_area) / 1000000  # Convert to km²
    
    print(f"Stream cells: {stream_cells:,}")
    print(f"Stream area: {stream_km:.2f} km²")
    
    # Save stream network
    stream_path = output_dir / f'stream_network_{threshold_ha}ha.tif'
    
    meta.update({
        'dtype': 'uint8',
        'nodata': 255
    })
    
    with rasterio.open(stream_path, 'w', **meta) as dst:
        dst.write(stream_binary.astype('uint8'), 1)
    
    print(f"Stream network saved to: {stream_path}")
    
    return stream_path


def calculate_stream_distance(stream_path, output_dir, cell_size=10):
    """
    Calculate Euclidean distance to nearest stream.
    
    Args:
        stream_path: Path to binary stream network raster
        output_dir: Directory to save distance raster
        cell_size: Cell size in meters (default 10m)
    
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
    dem_path = '../../data/DEM/processed/DEM_10m_gapfilled.tif'
    watershed_boundary = '../../data/sub-basins/Subbasins.shp'
    output_dir = Path('../../data/stream_proximity')
    
    # Create output subdirectories
    flow_dir = output_dir / 'flow_accumulation'
    stream_dir = output_dir / 'stream_networks'
    distance_dir = output_dir / 'stream_distance'
    
    # Thresholds in hectares
    thresholds_ha = [25, 50, 75, 100]
    
    print("="*60)
    print("Stream Proximity Processing")
    print("="*60)
    print(f"DEM: {dem_path}")
    print(f"Watershed boundary: {watershed_boundary}")
    print(f"Output directory: {output_dir}")
    print(f"Thresholds: {thresholds_ha} ha")
    print("="*60)
    
    # Check if DEM exists
    if not Path(dem_path).exists():
        print(f"\n❌ Error: DEM not found at {dem_path}")
        return
    
    # Check if watershed boundary exists
    if not Path(watershed_boundary).exists():
        print(f"\n❌ Error: Watershed boundary not found at {watershed_boundary}")
        return
    
    # Step 1: Calculate flow accumulation (only once)
    flow_acc_path = flow_dir / 'flow_accumulation.tif'
    
    if flow_acc_path.exists():
        print(f"\n✓ Flow accumulation already exists: {flow_acc_path}")
        print("  (Delete file to recalculate)")
    else:
        flow_acc_uncropped = calculate_flow_accumulation(dem_path, flow_dir / 'temp')
        
        # Crop flow accumulation to watershed boundary
        print("\nCropping flow accumulation to watershed boundary...")
        crop_to_watershed(flow_acc_uncropped, watershed_boundary, flow_acc_path)
        print(f"Flow accumulation saved to: {flow_acc_path}")
        
        # Clean up uncropped version
        flow_acc_uncropped.unlink()
        (flow_dir / 'temp').rmdir()
    
    # Steps 2-4: Generate stream networks and calculate distances for each threshold
    for threshold_ha in thresholds_ha:
        stream_output_path = stream_dir / f'stream_network_{threshold_ha}ha.tif'
        distance_output_path = distance_dir / f'stream_distance_{threshold_ha}ha.tif'
        
        # Generate and crop stream network from full flow accumulation
        if not stream_output_path.exists():
            # Generate uncropped stream network
            stream_uncropped = generate_stream_network(
                flow_acc_path, 
                threshold_ha, 
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
                distance_dir
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
    print(f"  Flow accumulation: {flow_dir}/")
    print(f"  Stream networks: {stream_dir}/")
    print(f"  Distance rasters: {distance_dir}/")
    print("="*60)


if __name__ == '__main__':
    main()
