"""
DEM + Raster Draping Visualization with PyVista
Requirements:
- Python 3.11
- pyvista, rioxarray, xarray, rasterio, numpy, matplotlib

To Run:
(geo) emadsen@Ellies-MacBook-Air ccsr-watershed-gis % python watershed3d.py --color elevation
(geo) emadsen@Ellies-MacBook-Air ccsr-watershed-gis % python watershed3d.py --color nlcd

"""

import argparse
import rioxarray as rxr
import pyvista as pv
import numpy as np
from matplotlib import pyplot as plt

# CONFIG: Paths to DEM and rasters
dem_path = "DEM/tif/DEM_UTM.tif"
nlcd_path = "NLCD/nlcd2016_ny.tif"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Visualize DEM with optional raster overlay")
parser.add_argument(
    "--color",
    choices=["elevation", "nlcd"],
    default="elevation",
    help="Coloring method: 'elevation' (gradient by height) or 'nlcd' (landcover classification)"
)
parser.add_argument(
    "--export",
    action="store_true",
    default=False,
    help="Enable export of HTML and PNG outputs"
)

parser.add_argument(
    "--scale_z",
    type=float,
    default=1.0,
    help="Vertical exaggeration factor for terrain (default 1.0)"
)

args = parser.parse_args()

# Load DEM
dem = rxr.open_rasterio(dem_path, masked=True).squeeze()

# Create coordinate grids - PyVista expects shape (ny, nx)
xx, yy = np.meshgrid(dem.x.values, dem.y.values)
zz = dem.values

# Apply vertical exaggeration to geometry
zz_geom = zz * args.scale_z

# Create grid with elevation at each point (geometry uses scaled z)
grid = pv.StructuredGrid(xx, yy, zz_geom)
# Store elevation as scalar data (use original z values for color)
grid["Elevation"] = zz.ravel(order='F')  # Fortran order matches StructuredGrid

# Setup PyVista plotters
# Main plotter (shows window)
plotter = pv.Plotter(off_screen=False)
# Export plotter (off-screen for HTML/PNG)
export_plotter = pv.Plotter(off_screen=True)

if args.color == "elevation":
    # Color by elevation
    plotter.add_mesh(
        grid, 
        scalars="Elevation",
        cmap="gist_earth",
        show_edges=False, 
        opacity=1.0,
        scalar_bar_args={'title': 'Elevation (m)'}
    )
    export_plotter.add_mesh(
        grid, 
        scalars="Elevation",
        cmap="gist_earth",
        show_edges=False, 
        opacity=1.0,
        scalar_bar_args={'title': 'Elevation (m)'}
    )
elif args.color == "nlcd":
    # Load NLCD raster
    nlcd_data = rxr.open_rasterio(nlcd_path, masked=True).squeeze()
    
    print(f"NLCD CRS: {nlcd_data.rio.crs}")
    print(f"DEM CRS: {dem.rio.crs}")
    
    # Reproject NLCD to match DEM CRS if needed
    if nlcd_data.rio.crs != dem.rio.crs:
        print(f"Reprojecting NLCD from {nlcd_data.rio.crs} to {dem.rio.crs}")
        nlcd_data = nlcd_data.rio.reproject(dem.rio.crs)
    
    # Resample NLCD to DEM's exact grid (same resolution and alignment)
    print(f"Resampling NLCD to DEM grid...")
    nlcd_resampled = nlcd_data.rio.reproject_match(dem)
    print(f"Resampled NLCD shape: {nlcd_resampled.shape}, DEM shape: {dem.shape}")
    
    # Add NLCD as scalar field
    grid["NLCD"] = nlcd_resampled.values.ravel(order='F')
    
    plotter.add_mesh(
        grid,
        scalars="NLCD",
        cmap="tab20",
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'NLCD Landcover'}
    )
    export_plotter.add_mesh(
        grid,
        scalars="NLCD",
        cmap="tab20",
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'NLCD Landcover'}
    )

# Camera, lighting, and interaction
plotter.view_isometric()
plotter.add_light(pv.Light(position=(100, 100, 100)))
export_plotter.view_isometric()
export_plotter.add_light(pv.Light(position=(100, 100, 100)))

# Show interactive window first
plotter.show()

# Then export using off-screen plotter (if enabled)
if args.export:
    filename = f"outputs/watershed_dem_{args.color}"
    export_plotter.export_html(filename + ".html")
    export_plotter.screenshot(filename + ".png")