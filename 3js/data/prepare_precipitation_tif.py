"""
Prepare precipitation data from multi-band tif for Three.js visualization.
For now, extracts ONE time step to test the approach.
"""
import sys
sys.path.insert(0, '..')

import rasterio
import numpy as np
import json
from scipy.spatial import Voronoi

# Load DEM for target dimensions
print("Loading DEM...")
dem_path = '../DEM/tif/DEM_UTM.tif'
with rasterio.open(dem_path) as dem:
    dem_width = dem.width
    dem_height = dem.height
    dem_bounds = {
        'minX': float(dem.bounds.left),
        'maxX': float(dem.bounds.right),
        'minY': float(dem.bounds.bottom),
        'maxY': float(dem.bounds.top)
    }

print(f'DEM dimensions: {dem_width}x{dem_height}')

# Load precipitation tif
precip_tif = '../climate_models/tifs/ACCESS-ESM1-5_pr_ssp370_TEST.tif'
print(f'\nLoading {precip_tif}...')

with rasterio.open(precip_tif) as src:
    print(f'Bands: {src.count}')
    print(f'Dimensions: {src.width}x{src.height}')
    
    # Get band descriptions (dates)
    band_dates = []
    for i in range(1, min(src.count + 1, 10)):  # Show first few
        desc = src.descriptions[i-1] if src.descriptions else f'Band {i}'
        band_dates.append(desc)
    print(f'First bands: {band_dates}')
    
    # Read band 7 (July 2015 - should have more precipitation)
    band_idx = 7
    band_desc = src.descriptions[band_idx-1] if src.descriptions else f'Band {band_idx}'
    print(f'\nExtracting band {band_idx}: {band_desc}')
    
    data = src.read(band_idx)
    
    # Get stats
    valid_mask = ~np.isnan(data)
    if valid_mask.any():
        min_val = float(np.nanmin(data))
        max_val = float(np.nanmax(data))
        mean_val = float(np.nanmean(data))
        print(f'Value range: {min_val:.6e} - {max_val:.6e}')
        print(f'Mean: {mean_val:.6e}')
        
        # Calculate percentiles for better visualization
        valid_data = data[valid_mask]
        p2 = np.percentile(valid_data, 2)
        p98 = np.percentile(valid_data, 98)
        print(f'2nd-98th percentile: {p2:.6e} - {p98:.6e}')
        
        # Count zeros
        zero_count = np.sum(data == 0)
        print(f'Zero values: {zero_count} ({100*zero_count/data.size:.2f}%)')
        
        # Use percentile-based range for better contrast
        stretch_min = float(p2)
        stretch_max = float(p98)
        print(f'Using percentile stretch: {stretch_min:.6e} - {stretch_max:.6e}')
    else:
        print('No valid data!')
        sys.exit(1)

# Resample to match DEM if needed
if data.shape != (dem_height, dem_width):
    print(f'Resampling from {data.shape} to {(dem_height, dem_width)}...')
    from scipy.ndimage import zoom
    zoom_factors = (dem_height / data.shape[0], dem_width / data.shape[1])
    data = zoom(data, zoom_factors, order=1)

# Convert to list format for JSON
print('Converting to JSON format...')
data_list = []
for row in data:
    data_list.append([None if np.isnan(val) else float(val) for val in row])

# Calculate Voronoi cell boundaries in UTM coordinates
print('Calculating Voronoi cell boundaries...')

def latlon_to_utm(lat, lon):
    """Convert lat/lon to approximate UTM coordinates."""
    x = (lon + 75) * 85000 + 500000
    y = (lat - 42) * 111000 + 4650000
    return x, y

# Get centroids from the tif (read from CSV header)
import pandas as pd
import re

def parse_grid_coords(column_name):
    match = re.search(r'\(([-\d.]+),\s*([-\d.]+)\)', column_name)
    if match:
        return [float(match.group(1)), float(match.group(2))]
    return None

csv_file = '../climate_models/Catskills_ACCESS-ESM1-5_pr_ssp370_monthly_avg.csv'
df = pd.read_csv(csv_file, index_col=0, nrows=1)
centroids_latlon = [parse_grid_coords(col) for col in df.columns if parse_grid_coords(col)]

# Convert to UTM
centroids_utm = np.array([latlon_to_utm(lat, lon) for lat, lon in centroids_latlon])
print(f'Grid centroids: {len(centroids_utm)}')

# Create Voronoi diagram
vor = Voronoi(centroids_utm)

# Extract ridge segments (cell boundaries)
# For a simple grid of 6 points (2x3), we'll draw lines between centroids
cell_boundaries = []

# Since we have a 2x3 grid, draw horizontal and vertical lines between them
# Grid layout: 
# [3] [4] [5]
# [0] [1] [2]

# Horizontal lines
for i in range(2):  # 2 rows
    for j in range(2):  # 2 internal vertical boundaries per row
        idx1 = i * 3 + j
        idx2 = i * 3 + j + 1
        cell_boundaries.append({
            'start': [float(centroids_utm[idx1][0]), float(centroids_utm[idx1][1])],
            'end': [float(centroids_utm[idx2][0]), float(centroids_utm[idx2][1])]
        })

# Vertical lines  
for j in range(3):  # 3 columns
    idx1 = j
    idx2 = j + 3
    cell_boundaries.append({
        'start': [float(centroids_utm[idx1][0]), float(centroids_utm[idx1][1])],
        'end': [float(centroids_utm[idx2][0]), float(centroids_utm[idx2][1])]
    })

print(f'Cell boundary segments: {len(cell_boundaries)}')

# Prepare output
output = {
    'width': int(dem_width),
    'height': int(dem_height),
    'bounds': dem_bounds,
    'range': {
        'min': min_val,
        'max': max_val,
        'stretch_min': stretch_min,
        'stretch_max': stretch_max
    },
    'timeStep': band_desc,
    'data': data_list,
    'cellBoundaries': cell_boundaries
}

# Save
output_path = 'precipitation_test_data.json'
print(f'\nSaving to {output_path}...')
with open(output_path, 'w') as f:
    json.dump(output, f)

file_size = len(json.dumps(output)) / (1024 * 1024)
print(f'File size: {file_size:.1f} MB')
print('Done!')
