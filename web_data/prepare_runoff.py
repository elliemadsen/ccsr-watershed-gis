"""
Convert Runoff Coefficient to JSON for Three.js visualization
"""
import sys
sys.path.insert(0, '..')

import rioxarray as rxr
import numpy as np
import json

# First load DEM to get target bounds
print("Loading DEM bounds...")
dem_path = '../DEM/tif/DEM_UTM.tif'
dem = rxr.open_rasterio(dem_path, masked=True).squeeze()
dem_bounds = {
    'minX': float(dem.x.values.min()),
    'maxX': float(dem.x.values.max()),
    'minY': float(dem.y.values.min()),
    'maxY': float(dem.y.values.max())
}
print(f'DEM bounds: {dem_bounds}')

# Load Runoff Coefficient
runoff_path = '../runoff_coefficient/runoff_coefficient.tif'
runoff = rxr.open_rasterio(runoff_path, masked=True).squeeze()

print(f'Original Runoff CRS: {runoff.rio.crs}')
print(f'DEM CRS: {dem.rio.crs}')
print(f'Original Runoff bounds: minX={runoff.x.values.min():.1f}, maxX={runoff.x.values.max():.1f}, minY={runoff.y.values.min():.1f}, maxY={runoff.y.values.max():.1f}')

# Reproject to match DEM CRS if needed
if runoff.rio.crs != dem.rio.crs:
    print('Reprojecting Runoff to DEM CRS...')
    runoff_reprojected = runoff.rio.reproject(dem.rio.crs, resampling=1)  # bilinear for continuous data
else:
    runoff_reprojected = runoff
    print('Runoff already in DEM CRS')

print(f'Reprojected Runoff bounds: minX={runoff_reprojected.x.values.min():.1f}, maxX={runoff_reprojected.x.values.max():.1f}, minY={runoff_reprojected.y.values.min():.1f}, maxY={runoff_reprojected.y.values.max():.1f}')

# Clip to DEM extent
runoff_clipped = runoff_reprojected.rio.clip_box(
    minx=dem_bounds['minX'],
    maxx=dem_bounds['maxX'],
    miny=dem_bounds['minY'],
    maxy=dem_bounds['maxY']
)

orig_width = len(runoff_clipped.x)
orig_height = len(runoff_clipped.y)
print(f'Clipped Runoff size: {orig_width}x{orig_height}')

# Get DEM full resolution dimensions to match exactly
dem_width = len(dem.x)
dem_height = len(dem.y)

print(f'Target DEM dimensions: {dem_width}x{dem_height}')

# Resample to exact DEM resolution
from rasterio.enums import Resampling

runoff_resampled = runoff_clipped.rio.reproject(
    runoff_clipped.rio.crs,
    shape=(dem_height, dem_width),
    resampling=Resampling.bilinear  # Use bilinear for continuous data
)

data = runoff_resampled.values
height, width = data.shape
print(f'Resampled Runoff to: {width}x{height}')

# Get bounds from resampled data
x_coords = runoff_resampled.x.values
y_coords = runoff_resampled.y.values

# Handle NoData and get value range
valid_mask = ~np.isnan(data)
valid_data = data[valid_mask]

if len(valid_data) == 0:
    print("No valid data found!")
    sys.exit(1)

min_val = float(np.min(valid_data))
max_val = float(np.max(valid_data))
print(f'Runoff coefficient range: {min_val:.3f} - {max_val:.3f}')

# Count valid pixels
valid_count = np.sum(valid_mask)
print(f'Valid pixels: {valid_count} / {data.size} ({100*valid_count/data.size:.1f}%)')

# Convert to list, replacing invalid with null
runoff_data = []
for row in data:
    runoff_data.append([None if (val != val or np.isnan(val)) else float(val) for val in row])

# Prepare output
output = {
    'width': int(width),
    'height': int(height),
    'bounds': {
        'minX': float(x_coords[0]),
        'maxX': float(x_coords[-1]),
        'minY': float(y_coords[-1]),
        'maxY': float(y_coords[0])
    },
    'range': {
        'min': min_val,
        'max': max_val
    },
    'data': runoff_data
}

# Save
output_path = 'runoff_data.json'
with open(output_path, 'w') as f:
    json.dump(output, f)

file_size = len(json.dumps(output)) / 1024
print(f'Saved to {output_path}')
print(f'File size: {file_size:.1f} KB')
