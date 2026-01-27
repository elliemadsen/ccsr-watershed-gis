"""
DEM + Raster Draping Visualization with PyVista
Requirements:
- Python 3.11
- pyvista, rioxarray, xarray, rasterio, numpy, matplotlib

To Run:
(geo) emadsen@Ellies-MacBook-Air ccsr-watershed-gis % python watershed3d.py

Example to 
(geo) emadsen@Ellies-MacBook-Air ccsr-watershed-gis % python watershed3d.py --color nlcd --export

"""

import argparse
import rioxarray as rxr
import rasterio
from rasterio.enums import Resampling
import pyvista as pv
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap


def create_categorical_lut(tif_path, num_values=256):
    """
    Extract colormap from GeoTIFF and create a PyVista-compatible lookup table.
    Returns a matplotlib ListedColormap that maps raster values to RGBA colors.
    """
    with rasterio.open(tif_path) as src:
        colormap = src.colormap(1)
        if not colormap:
            return None
        
        # Create a lookup table (256 x 4 array for RGBA, normalized to 0-1)
        lut = np.zeros((num_values, 4), dtype=np.float32)
        
        # Fill in colors from the colormap (convert 0-255 to 0-1 range)
        for value, (r, g, b, a) in colormap.items():
            if value < num_values:
                lut[value] = [r/255.0, g/255.0, b/255.0, a/255.0]
        
        # Create a matplotlib colormap
        return ListedColormap(lut, N=num_values)


# CONFIG: Paths to DEM and rasters
dem_path = "DEM/tif/DEM_UTM.tif"
nlcd_path = "NLCD/nlcd2016_ny.tif"
runoff_path = "runoff_coefficient/runoff_coefficient.tif"
cdl_path = "CDL/CDL_2020_36.tif"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Visualize DEM with optional raster overlay")
parser.add_argument(
    "--color",
    choices=["elevation", "nlcd", "runoff", "cdl", "interactive"],
    default="interactive",
    help="Coloring method: 'elevation' (gradient by height), 'nlcd' (landcover classification), 'cdl' (cropland data layer), 'runoff', or 'interactive' (toggle between layers)"
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
    
    # Reproject NLCD to match DEM CRS if needed (use nearest neighbor for categorical data)
    if nlcd_data.rio.crs != dem.rio.crs:
        print(f"Reprojecting NLCD from {nlcd_data.rio.crs} to {dem.rio.crs}")
        nlcd_data = nlcd_data.rio.reproject(dem.rio.crs, resampling=Resampling.nearest)
    
    # Resample NLCD to DEM's exact grid (same resolution and alignment)
    print(f"Resampling NLCD to DEM grid...")
    nlcd_resampled = nlcd_data.rio.reproject_match(dem, resampling=Resampling.nearest)
    print(f"Resampled NLCD shape: {nlcd_resampled.shape}, DEM shape: {dem.shape}")
    
    # Add NLCD as scalar field
    grid["NLCD"] = nlcd_resampled.values.ravel(order='F')

    # Create custom colormap from TIF
    nlcd_lut = create_categorical_lut(nlcd_path)
    
    plotter.add_mesh(
        grid,
        scalars="NLCD",
        cmap=nlcd_lut,
        clim=[0, 255],
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'NLCD Landcover'}
    )
    export_plotter.add_mesh(
        grid,
        scalars="NLCD",
        cmap=nlcd_lut,
        clim=[0, 255],
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'NLCD Landcover'}
    )

elif args.color == "cdl":
    # Load Cropland Data Layer raster
    cdl_data = rxr.open_rasterio(cdl_path, masked=True).squeeze()
    
    print(f"CDL CRS: {cdl_data.rio.crs}")
    print(f"DEM CRS: {dem.rio.crs}")
    
    # Reproject CDL to match DEM CRS if needed (use nearest neighbor for categorical data)
    if cdl_data.rio.crs != dem.rio.crs:
        print(f"Reprojecting CDL from {cdl_data.rio.crs} to {dem.rio.crs}")
        cdl_data = cdl_data.rio.reproject(dem.rio.crs, resampling=Resampling.nearest)
    
    # Resample CDL to DEM's exact grid (same resolution and alignment)
    print(f"Resampling CDL to DEM grid...")
    cdl_resampled = cdl_data.rio.reproject_match(dem, resampling=Resampling.nearest)
    print(f"Resampled CDL shape: {cdl_resampled.shape}, DEM shape: {dem.shape}")
    
    # Add CDL as scalar field
    grid["CDL"] = cdl_resampled.values.ravel(order='F')
    
    # Create custom colormap from TIF
    cdl_lut = create_categorical_lut(cdl_path)
    
    plotter.add_mesh(
        grid,
        scalars="CDL",
        cmap=cdl_lut,
        clim=[0, 255],
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'CDL Landcover'}
    )
    export_plotter.add_mesh(
        grid,
        scalars="CDL",
        cmap=cdl_lut,
        clim=[0, 255],
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'CDL Landcover'}
    )

elif args.color == "runoff":
    # Load runoff coefficient raster
    runoff_data = rxr.open_rasterio(runoff_path, masked=True).squeeze()
    
    print(f"Runoff CRS: {runoff_data.rio.crs}")
    print(f"DEM CRS: {dem.rio.crs}")
    
    # Reproject runoff to match DEM CRS if needed
    if runoff_data.rio.crs != dem.rio.crs:
        print(f"Reprojecting runoff from {runoff_data.rio.crs} to {dem.rio.crs}")
        runoff_data = runoff_data.rio.reproject(dem.rio.crs)
    
    # Resample runoff to DEM's exact grid (same resolution and alignment)
    print(f"Resampling runoff to DEM grid...")
    runoff_resampled = runoff_data.rio.reproject_match(dem)
    print(f"Resampled runoff shape: {runoff_resampled.shape}, DEM shape: {dem.shape}")
    
    # Add runoff as scalar field
    grid["Runoff"] = runoff_resampled.values.ravel(order='F')
    
    plotter.add_mesh(
        grid,
        scalars="Runoff",
        cmap="viridis_r",
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'Runoff Coefficient'}
    )
    export_plotter.add_mesh(
        grid,
        scalars="Runoff",
        cmap="viridis_r",
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'Runoff Coefficient'}
    )

elif args.color == "interactive":
    # Load NLCD, CDL, and runoff for interactive toggling
    nlcd_data = rxr.open_rasterio(nlcd_path, masked=True).squeeze()
    cdl_data = rxr.open_rasterio(cdl_path, masked=True).squeeze()
    runoff_data = rxr.open_rasterio(runoff_path, masked=True).squeeze()
    
    # Reproject if needed (use nearest neighbor for categorical data)
    if nlcd_data.rio.crs != dem.rio.crs:
        nlcd_data = nlcd_data.rio.reproject(dem.rio.crs, resampling=Resampling.nearest)
    if cdl_data.rio.crs != dem.rio.crs:
        cdl_data = cdl_data.rio.reproject(dem.rio.crs, resampling=Resampling.nearest)
    if runoff_data.rio.crs != dem.rio.crs:
        runoff_data = runoff_data.rio.reproject(dem.rio.crs)
    
    # Resample to DEM grid (use nearest neighbor for categorical, default for continuous)
    nlcd_resampled = nlcd_data.rio.reproject_match(dem, resampling=Resampling.nearest)
    cdl_resampled = cdl_data.rio.reproject_match(dem, resampling=Resampling.nearest)
    runoff_resampled = runoff_data.rio.reproject_match(dem)
    
    # Add both as scalar fields
    grid["NLCD"] = nlcd_resampled.values.ravel(order='F')
    grid["CDL"] = cdl_resampled.values.ravel(order='F')
    grid["Runoff"] = runoff_resampled.values.ravel(order='F')
    
    # Create custom colormaps from TIFs
    nlcd_lut = create_categorical_lut(nlcd_path)
    cdl_lut = create_categorical_lut(cdl_path)
    
    # Add mesh with initial scalar
    mesh_actor = plotter.add_mesh(
        grid,
        scalars="NLCD",
        cmap=nlcd_lut,
        clim=[0, 255],
        show_edges=False,
        opacity=1.0,
        scalar_bar_args={'title': 'NLCD Landcover', 'vertical': True, 'position_x': 0.02, 'position_y': 0.35, 'width': 0.06, 'height': 0.4},
        name='terrain'
    )
    
    # Callback for NLCD button
    def show_nlcd(value):
        plotter.remove_actor('terrain')
        plotter.remove_scalar_bar()
        mesh_actor = plotter.add_mesh(
            grid,
            scalars="NLCD",
            cmap=nlcd_lut,
            clim=[0, 255],
            show_edges=False,
            opacity=1.0,
            scalar_bar_args={'title': 'NLCD Landcover', 'vertical': True, 'position_x': 0.02, 'position_y': 0.35, 'width': 0.06, 'height': 0.3},
            name='terrain'
        )
        # Uncheck other buttons
        if hasattr(plotter, '_cdl_widget'):
            plotter._cdl_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_runoff_widget'):
            plotter._runoff_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_elevation_widget'):
            plotter._elevation_widget.GetRepresentation().SetState(0)
    
    # Callback for Runoff button
    def show_runoff(value):
        plotter.remove_actor('terrain')
        plotter.remove_scalar_bar()
        mesh_actor = plotter.add_mesh(
            grid,
            scalars="Runoff",
            cmap="viridis_r",
            show_edges=False,
            opacity=1.0,
            scalar_bar_args={'title': 'Runoff Coefficient', 'vertical': True, 'position_x': 0.02, 'position_y': 0.35, 'width': 0.06, 'height': 0.3},
            name='terrain'
        )
        # Uncheck other buttons
        if hasattr(plotter, '_nlcd_widget'):
            plotter._nlcd_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_cdl_widget'):
            plotter._cdl_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_elevation_widget'):
            plotter._elevation_widget.GetRepresentation().SetState(0)

    # Callback for CDL button
    def show_cdl(value):
        plotter.remove_actor('terrain')
        plotter.remove_scalar_bar()
        mesh_actor = plotter.add_mesh(
            grid,
            scalars="CDL",
            cmap=cdl_lut,
            clim=[0, 255],
            show_edges=False,
            opacity=1.0,
            scalar_bar_args={'title': 'CDL Landcover', 'vertical': True, 'position_x': 0.02, 'position_y': 0.35, 'width': 0.06, 'height': 0.3},
            name='terrain'
        )
        # Uncheck other buttons
        if hasattr(plotter, '_nlcd_widget'):
            plotter._nlcd_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_runoff_widget'):
            plotter._runoff_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_elevation_widget'):
            plotter._elevation_widget.GetRepresentation().SetState(0)
    
    # Callback for Elevation button
    def show_elevation(value):
        plotter.remove_actor('terrain')
        plotter.remove_scalar_bar()
        mesh_actor = plotter.add_mesh(
            grid,
            scalars="Elevation",
            cmap="gist_earth",
            show_edges=False,
            opacity=1.0,
            scalar_bar_args={'title': 'Elevation (m)', 'vertical': True, 'position_x': 0.02, 'position_y': 0.35, 'width': 0.06, 'height': 0.3},
            name='terrain'
        )
        # Uncheck other buttons
        if hasattr(plotter, '_nlcd_widget'):
            plotter._nlcd_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_cdl_widget'):
            plotter._cdl_widget.GetRepresentation().SetState(0)
        if hasattr(plotter, '_runoff_widget'):
            plotter._runoff_widget.GetRepresentation().SetState(0)
    
    # Add clickable buttons (vertical on left) - ordered as NLCD, CDL, Runoff, Elevation
    plotter._nlcd_widget = plotter.add_checkbox_button_widget(show_nlcd, value=True, position=(10, 230), size=30, border_size=3, color_on='black', color_off='grey')
    plotter.add_text("NLCD", position=(60, 230), font_size=12)
    plotter._cdl_widget = plotter.add_checkbox_button_widget(show_cdl, value=False, position=(10, 190), size=30, border_size=3, color_on='black', color_off='grey')
    plotter.add_text("CDL", position=(60, 190), font_size=12)
    plotter._runoff_widget = plotter.add_checkbox_button_widget(show_runoff, value=False, position=(10, 150), size=30, border_size=3, color_on='black', color_off='grey')
    plotter.add_text("Runoff", position=(60, 150), font_size=12)
    plotter._elevation_widget = plotter.add_checkbox_button_widget(show_elevation, value=False, position=(10, 110), size=30, border_size=3, color_on='black', color_off='grey')
    plotter.add_text("Elevation", position=(60, 110), font_size=12)
    
    # Add slider for elevation exaggeration (vertical on left)
    def update_elevation(value):
        # Get current points and update z-coordinates
        points = grid.points.copy()
        points[:, 2] = zz.ravel(order='F') * value  # Update z with new scale
        grid.points = points
        plotter.render()
    
    plotter.add_slider_widget(
        update_elevation,
        [0.1, 5.0],
        value=args.scale_z,
        title="Z Scale",
        title_height=0.015,
        title_opacity=0.8,
        fmt="%.1f",
        pointa=(0.0, 0.95),
        pointb=(0.1, 0.95),
        style='modern',
        color='black',
        tube_width=0.002,
        slider_width=0.015
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