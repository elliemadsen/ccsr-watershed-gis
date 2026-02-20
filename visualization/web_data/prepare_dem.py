"""
Convert DEM to JSON for Three.js visualization
"""
import sys
sys.path.insert(0, '..')

import rioxarray as rxr
import numpy as np
import json

# Load DEM
dem_path = '../../data/DEM/tif/DEM_UTM.tif'
dem = rxr.open_rasterio(dem_path, masked=True).squeeze()

# Use full resolution
data = dem.values

height, width = data.shape
print(f'Full resolution: {width}x{height}')

# Filter NoData - be more strict
valid_mask = (data < 10000) & (data > 0) & (~np.isnan(data)) & (data != 0)
valid_data = data[valid_mask]

if len(valid_data) == 0:
    print("No valid data found!")
    sys.exit(1)

min_elev = float(np.min(valid_data))
max_elev = float(np.max(valid_data))
print(f'Elevation range: {min_elev:.1f}m - {max_elev:.1f}m')
print(f'Valid pixels: {len(valid_data)} / {data.size} ({100*len(valid_data)/data.size:.1f}%)')

# Replace invalid with NaN (we'll handle in JS)
data = np.where(valid_mask, data, np.nan)

# Convert to list, replacing NaN with None for valid JSON
elevation_data = []
for row in data:
    elevation_data.append([None if (val != val or val is None) else float(val) for val in row])

# Get bounds
x_coords = dem.x.values
y_coords = dem.y.values

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
    'elevation': {
        'min': min_elev,
        'max': max_elev
    },
    'data': elevation_data
}

# Save
output_path = 'dem_data.json'
with open(output_path, 'w') as f:
    json.dump(output, f)

file_size = len(json.dumps(output)) / 1024
print(f'Saved to {output_path}')
print(f'File size: {file_size:.1f} KB')
