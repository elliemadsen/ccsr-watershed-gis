"""
Convert NLCD to JSON for Three.js visualization
"""
import sys
sys.path.insert(0, '..')

import rioxarray as rxr
import rasterio
import numpy as np
import json

# First load DEM to get target bounds
print("Loading DEM bounds...")
dem_path = '../../data/DEM/tif/DEM_UTM.tif'
dem = rxr.open_rasterio(dem_path, masked=True).squeeze()
dem_bounds = {
    'minX': float(dem.x.values.min()),
    'maxX': float(dem.x.values.max()),
    'minY': float(dem.y.values.min()),
    'maxY': float(dem.y.values.max())
}
print(f'DEM bounds: {dem_bounds}')

# Load NLCD
nlcd_path = '../../data/NLCD/nlcd2016_ny.tif'

with rasterio.open(nlcd_path) as src:
    # Get colormap
    colormap = src.colormap(1)
    
    if not colormap:
        print("No colormap found!")
        sys.exit(1)
    
    print(f'Colormap entries: {len(colormap)}')
    
    # Convert colormap to RGB dict (value -> [r, g, b])
    nlcd_colors = {}
    for value, (r, g, b, a) in colormap.items():
        if value < 256:  # Only store valid entries
            nlcd_colors[str(value)] = [r/255.0, g/255.0, b/255.0]
    
    print(f'Stored {len(nlcd_colors)} color mappings')

# Load NLCD with rioxarray and reproject to DEM CRS
nlcd = rxr.open_rasterio(nlcd_path, masked=True).squeeze()

print(f'Original NLCD CRS: {nlcd.rio.crs}')
print(f'DEM CRS: {dem.rio.crs}')
print(f'Original NLCD bounds: minX={nlcd.x.values.min():.1f}, maxX={nlcd.x.values.max():.1f}, minY={nlcd.y.values.min():.1f}, maxY={nlcd.y.values.max():.1f}')

# Reproject NLCD to match DEM CRS if needed
if nlcd.rio.crs != dem.rio.crs:
    print('Reprojecting NLCD to DEM CRS...')
    nlcd_reprojected = nlcd.rio.reproject(dem.rio.crs, resampling=0)  # resampling=0 for nearest neighbor (categorical data)
else:
    nlcd_reprojected = nlcd
    print('NLCD already in DEM CRS')

print(f'Reprojected NLCD bounds: minX={nlcd_reprojected.x.values.min():.1f}, maxX={nlcd_reprojected.x.values.max():.1f}, minY={nlcd_reprojected.y.values.min():.1f}, maxY={nlcd_reprojected.y.values.max():.1f}')

# Clip NLCD to DEM extent
nlcd_clipped = nlcd_reprojected.rio.clip_box(
    minx=dem_bounds['minX'],
    maxx=dem_bounds['maxX'],
    miny=dem_bounds['minY'],
    maxy=dem_bounds['maxY']
)

orig_width = len(nlcd_clipped.x)
orig_height = len(nlcd_clipped.y)
print(f'Clipped NLCD size: {orig_width}x{orig_height}')

# Get DEM full resolution dimensions to match exactly
dem_width = len(dem.x)
dem_height = len(dem.y)

print(f'Target DEM dimensions: {dem_width}x{dem_height}')

# Resample NLCD to exact DEM resolution using rasterio reproject
from rasterio.enums import Resampling

# Create target shape matching full DEM resolution
nlcd_resampled = nlcd_clipped.rio.reproject(
    nlcd_clipped.rio.crs,
    shape=(dem_height, dem_width),
    resampling=Resampling.nearest  # Use nearest neighbor for categorical data
)

data = nlcd_resampled.values
height, width = data.shape
print(f'Resampled NLCD to: {width}x{height}')

# Get bounds from resampled NLCD
x_coords = nlcd_resampled.x.values
y_coords = nlcd_resampled.y.values

# Convert to integers and handle NoData
data_int = np.where(np.isnan(data) | (data == 0), -1, data.astype(int))

# Count valid pixels
valid_count = np.sum(data_int >= 0)
print(f'Valid pixels: {valid_count} / {data_int.size} ({100*valid_count/data_int.size:.1f}%)')

# Get unique values
unique_vals = np.unique(data_int[data_int >= 0])
print(f'Unique NLCD values: {len(unique_vals)}')
print(f'Sample values: {unique_vals[:10]}')

# Convert to list, replacing invalid with null
nlcd_data = []
for row in data_int:
    nlcd_data.append([None if val < 0 else int(val) for val in row])

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
    'colormap': nlcd_colors,
    'data': nlcd_data
}

# Save
output_path = 'nlcd_data.json'
with open(output_path, 'w') as f:
    json.dump(output, f)

file_size = len(json.dumps(output)) / 1024
print(f'Saved to {output_path}')
print(f'File size: {file_size:.1f} KB')
