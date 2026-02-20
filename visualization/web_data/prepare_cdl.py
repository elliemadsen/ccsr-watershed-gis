"""
Convert CDL to JSON for Three.js visualization
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

# Load CDL
cdl_path = '../../data/CDL/CDL_2020_36.tif'

with rasterio.open(cdl_path) as src:
    # Get colormap
    colormap = src.colormap(1)
    
    if not colormap:
        print("No colormap found!")
        sys.exit(1)
    
    print(f'Colormap entries: {len(colormap)}')
    
    # Convert colormap to RGB dict (value -> [r, g, b])
    cdl_colors = {}
    for value, (r, g, b, a) in colormap.items():
        if value < 256:  # Only store valid entries
            cdl_colors[str(value)] = [r/255.0, g/255.0, b/255.0]
    
    print(f'Stored {len(cdl_colors)} color mappings')

# Load CDL with rioxarray and reproject to DEM CRS
cdl = rxr.open_rasterio(cdl_path, masked=True).squeeze()

print(f'Original CDL CRS: {cdl.rio.crs}')
print(f'DEM CRS: {dem.rio.crs}')
print(f'Original CDL bounds: minX={cdl.x.values.min():.1f}, maxX={cdl.x.values.max():.1f}, minY={cdl.y.values.min():.1f}, maxY={cdl.y.values.max():.1f}')

# Reproject CDL to match DEM CRS
print('Reprojecting CDL to DEM CRS...')
cdl_reprojected = cdl.rio.reproject(dem.rio.crs, resampling=0)  # resampling=0 for nearest neighbor (categorical data)

print(f'Reprojected CDL bounds: minX={cdl_reprojected.x.values.min():.1f}, maxX={cdl_reprojected.x.values.max():.1f}, minY={cdl_reprojected.y.values.min():.1f}, maxY={cdl_reprojected.y.values.max():.1f}')

# Clip CDL to DEM extent
cdl_clipped = cdl_reprojected.rio.clip_box(
    minx=dem_bounds['minX'],
    maxx=dem_bounds['maxX'],
    miny=dem_bounds['minY'],
    maxy=dem_bounds['maxY']
)

orig_width = len(cdl_clipped.x)
orig_height = len(cdl_clipped.y)
print(f'Clipped CDL size: {orig_width}x{orig_height}')

# Get DEM full resolution dimensions to match exactly
dem_width = len(dem.x)
dem_height = len(dem.y)

print(f'Target DEM dimensions: {dem_width}x{dem_height}')

# Resample CDL to exact DEM resolution using rasterio reproject
from rasterio.enums import Resampling

# Create target shape matching full DEM resolution
cdl_resampled = cdl_clipped.rio.reproject(
    cdl_clipped.rio.crs,
    shape=(dem_height, dem_width),
    resampling=Resampling.nearest  # Use nearest neighbor for categorical data
)

data = cdl_resampled.values
height, width = data.shape
print(f'Resampled CDL to: {width}x{height}')

# Get bounds from resampled CDL
x_coords = cdl_resampled.x.values
y_coords = cdl_resampled.y.values

# Convert to integers and handle NoData
data_int = np.where(np.isnan(data) | (data == 0), -1, data.astype(int))

# Count valid pixels
valid_count = np.sum(data_int >= 0)
print(f'Valid pixels: {valid_count} / {data_int.size} ({100*valid_count/data_int.size:.1f}%)')

# Get unique values
unique_vals = np.unique(data_int[data_int >= 0])
print(f'Unique CDL values: {len(unique_vals)}')
print(f'Sample values: {unique_vals[:10]}')

# Convert to list, replacing invalid with null
cdl_data = []
for row in data_int:
    cdl_data.append([None if val < 0 else int(val) for val in row])

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
    'colormap': cdl_colors,
    'data': cdl_data
}

# Save
output_path = 'cdl_data.json'
with open(output_path, 'w') as f:
    json.dump(output, f)

file_size = len(json.dumps(output)) / 1024
print(f'Saved to {output_path}')
print(f'File size: {file_size:.1f} KB')
