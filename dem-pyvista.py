"""
DEM + Raster Draping Visualization with PyVista
Requirements:
- Python 3.11
- pyvista, rioxarray, xarray, rasterio, numpy, matplotlib

To Run:
(geo) emadsen@Ellies-MacBook-Air ccsr-watershed-gis % python dem-pyvista.py

"""

import rioxarray as rxr
import pyvista as pv
import numpy as np
from matplotlib import pyplot as plt

# -----------------------------
# CONFIG: Paths to DEM and rasters
# -----------------------------
dem_path = "DEM/tif/DEM_UTM.tif"
raster_paths = [
    # "ndvi.tif",
    # "landcover.tif"
]  # Add as many raster layers as you like
raster_cmaps = [
    "viridis",   # NDVI
    "tab20"      # Landcover
]
raster_opacities = [
    1.0,
    0.6
]

# -----------------------------
# Load DEM
# -----------------------------
dem = rxr.open_rasterio(dem_path, masked=True).squeeze()

# -----------------------------
# Create structured grid for PyVista
# -----------------------------
# Create coordinate grids - PyVista expects shape (ny, nx)
xx, yy = np.meshgrid(dem.x.values, dem.y.values)
zz = dem.values

# Create grid with elevation at each point
grid = pv.StructuredGrid(xx, yy, zz)
# Store elevation as scalar data (use original z values, not geometry)
grid["Elevation"] = zz.ravel(order='F')  # Fortran order matches StructuredGrid

# -----------------------------
# Setup PyVista plotter
# -----------------------------
plotter = pv.Plotter()
plotter.add_mesh(
    grid, 
    scalars="Elevation",
    cmap="gist_earth",
    show_edges=False, 
    opacity=1.0,
    scalar_bar_args={'title': 'Elevation (m)'}
)

# -----------------------------
# Add raster layers as scalar fields
# -----------------------------
for path, cmap, opacity in zip(raster_paths, raster_cmaps, raster_opacities):
    raster = rxr.open_rasterio(path, masked=True).squeeze()

    # Resample raster if dimensions differ
    if raster.shape != dem.shape:
        raster = raster.interp_like(dem, method="nearest")

    # Flatten to 1D and attach as new mesh
    grid_layer = pv.StructuredGrid(xx, yy, zz + 0.01)  # tiny offset to avoid z-fighting
    grid_layer["values"] = raster.values.ravel(order='F')

    plotter.add_mesh(
        grid_layer,
        scalars="values",
        cmap=cmap,
        opacity=opacity,
        show_edges=False
    )

# -----------------------------
# Camera, lighting, and interaction
# -----------------------------
plotter.view_isometric()
plotter.add_light(pv.Light(position=(100, 100, 100)))
plotter.show()

# -----------------------------
# Optional exports
# -----------------------------
# plotter.screenshot("dem_raster.png")
# plotter.export_html("dem_raster.html")
