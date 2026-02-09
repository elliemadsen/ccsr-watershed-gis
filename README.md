# ccsr-watershed-gis

3D terrain visualization of Catskills watershed with multiple data layers including climate model projections.

## Browser Visualization (Three.js)

Interactive 3D terrain viewer that runs entirely in the browser with real-time controls for data layers, vertical exaggeration, resolution sampling, and climate data visualization.

### Setup

1. Generate data files from the `web_data/` directory:

```bash
conda run -n geo python prepare_dem.py
conda run -n geo python prepare_cdl.py
conda run -n geo python prepare_nlcd.py
conda run -n geo python prepare_runoff.py
conda run -n geo python prepare_climate_models.py
```

2. Start a local web server from the root directory:

```bash
python3 -m http.server 8080
# Open http://localhost:8080 in web browser
```

### Features

- **Data Layers**: Switch between Elevation, Cropland Data Layer (CDL), Land Cover (NLCD), Runoff Coefficient, or Climate Data (Precipitation, Temperature, Humidity)
- **Category Filtering**: Toggle individual land cover and cropland categories on/off with interactive legends
  - Select All / Deselect All buttons for quick selection
  - Click individual categories to show/hide specific land uses
  - Visual feedback with grayed-out unselected categories
- **Climate Model Visualization**:
  - ACCESS-ESM1-5 and IPSL-CM6A-LR models with SSP3-7.0 scenario
  - Seasonal time series data (612 timesteps from 2024-2176)
  - Real-time interpolation or grid cell visualization modes
  - Global or per-timestamp color normalization
  - Interactive timeline slider
  - Grid boundary overlays showing 2×3 climate data cells
- **Vertical Exaggeration**: 1x to 5x real-time adjustment
- **Resolution Sampling**: 1x (full 2556×1688) to 8x downsampling for performance
- **Wireframe Mode**: Toggle mesh display
- **Interactive Legends**:
  - Gradient legends for elevation, runoff coefficient, and climate data with min/max values and units
  - Categorical legends for NLCD and CDL with individual category toggles
  - Dynamic updates based on selected data layer and climate model
  - Only displays classes actually present in the data
- **Camera Controls**:
  - Orbit, zoom, and pan enabled by default

### Data Files

Generated JSON files:

- `web_data/dem_data.json` (27 MB) - Elevation data
- `web_data/cdl_data.json` (21 MB) - Cropland classification with colormap
- `web_data/nlcd_data.json` (17 MB) - Land cover with colormap
- `web_data/runoff_data.json` (46 MB) - Runoff coefficients
- `web_data/ACCESS-ESM1-5_pr_ssp370.json` - Precipitation projections (ACCESS model)
- `web_data/ACCESS-ESM1-5_tasmax_ssp370.json` - Maximum temperature projections
- `web_data/ACCESS-ESM1-5_tasmin_ssp370.json` - Minimum temperature projections
- `web_data/ACCESS-ESM1-5_hurs_ssp370.json` - Relative humidity projections
- `web_data/IPSL-CM6A-LR_*_ssp370.json` - Corresponding IPSL model files

Climate data contains 612 seasonal timesteps (2024-2176) with 6 spatial centroids in a 2×3 grid covering the watershed.

All data automatically reprojected to match DEM coordinate system (EPSG:26918).

### Data Sources

- **DEM**: `DEM/tif/DEM_UTM.tif` (EPSG:26918, 2556×1688 pixels)
- **NLCD**: `NLCD/nlcd2016_ny.tif` (2016 land cover, 15 classes)
- **CDL**: `CDL/CDL_2020_36.tif` (2020 cropland data, 41 classes)
- **Runoff**: `runoff_coefficient/runoff_coefficient.tif` (0.000-0.601 range)
- **Climate Models**: `climate_models/` directory containing downscaled ACCESS-ESM1-5 and IPSL-CM6A-LR projections
  - Variables: precipitation (pr), max/min temperature (tasmax/tasmin), humidity (hurs), solar radiation (rlds/rsds), wind (sfcWind)
  - Scenario: SSP3-7.0 (high emissions pathway)
  - Temporal: Daily data aggregated to seasonal (Mar/Jun/Sep/Dec)
  - Spatial: 6-point 2×3 grid covering Catskills watershed

### Known Bugs

- **Grid Boundaries**: Climate data grid boundaries may not align perfectly with actual climate model centroids due to coordinate transformation approximations
- **Performance**: Large climate datasets (612 timesteps) may cause brief delays when switching between models
- **Legend Units**: Some climate variables display raw model units (e.g., Kelvin for temperature) rather than user-friendly units
- **Wireframe Rendering**: Wireframe mode may render slowly on high-resolution terrain data
- **Mobile Compatibility**: Touch controls for 3D navigation may be limited on mobile devices

---

## PyVista Visualization

Desktop 3D terrain visualization with PyVista, draping DEM elevation and multiple raster overlays (NLCD landcover, CDL cropland, runoff coefficients).

### Usage

From the repository root:

```bash
python watershed3d.py
```

### Arguments

- `--color` (default: `interactive`)
  - `elevation`: colors by DEM elevation using gist_earth colormap.
  - `nlcd`: colors by NLCD 2016 landcover (uses embedded TIF colormap).
  - `cdl`: colors by Cropland Data Layer 2020 (uses embedded TIF colormap).
  - `runoff`: colors by runoff coefficient (continuous scale).
  - `interactive`: launches with toggle buttons to switch between all layers + Z scale slider.
- `--scale_z FACTOR` (default: `1.0`)
  - Vertical exaggeration applied to terrain geometry (colors still use original elevations).
- `--export`
  - When set, saves `outputs/watershed_dem_<color>.html` (interactive) and `.png`.

### Interactive Mode

The default interactive mode provides:

- **Toggle buttons** (left side): Switch between NLCD, CDL, Runoff, and Elevation layers
- **Z Scale slider** (top): Adjust vertical exaggeration in real-time (0.1x to 5.0x)
- **Color legend**: Shows classification colors for categorical data (NLCD/CDL) or continuous scale (runoff/elevation)

All categorical rasters (NLCD, CDL) use nearest-neighbor resampling to preserve classification values and display embedded colormaps matching QGIS rendering.

### Examples

```bash
# Launch interactive viewer with toggles and slider (default)
python watershed3d.py

# CDL coloring only with 2x vertical exaggeration
python watershed3d.py --color cdl --scale_z 2

# NLCD with export
python watershed3d.py --color nlcd --export
```
