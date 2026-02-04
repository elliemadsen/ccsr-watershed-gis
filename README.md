# ccsr-watershed-gis

3D terrain visualization of Catskills watershed with multiple data layers.

## Browser Visualization (Three.js)

Interactive 3D terrain viewer that runs entirely in the browser with real-time controls for data layers, vertical exaggeration, and resolution sampling.

### Setup

1. Generate data files from the `precipitation-viz` directory:

```bash
cd precipitation-viz
conda run -n geo python prepare_dem.py
conda run -n geo python prepare_cdl.py
conda run -n geo python prepare_nlcd.py
conda run -n geo python prepare_runoff.py
```

2. Open `precipitation-viz/index.html` in a web browser

### Features

- **Data Layers**: Switch between Elevation, Cropland Data Layer (CDL), Land Cover (NLCD), Runoff Coefficient, or None
- **Vertical Exaggeration**: 1x to 5x real-time adjustment
- **Resolution Sampling**: 1x (full 2556×1688) to 8x downsampling for performance
- **Wireframe Mode**: Toggle mesh display
- **Interactive Legends**:
  - Gradient legends for elevation and runoff coefficient with min/max values
  - Categorical legends for NLCD and CDL showing colored squares with class names
  - Only displays classes actually present in the data
- **Camera Controls**:
  - Orbit and zoom enabled by default
  - Optional panning to "fly to" specific terrain locations

### Data Files

Generated JSON files (loaded by browser):

- `dem_data.json` (27 MB) - Elevation data
- `cdl_data.json` (21 MB) - Cropland classification with colormap
- `nlcd_data.json` (17 MB) - Land cover with colormap
- `runoff_data.json` (46 MB) - Runoff coefficients

All data automatically reprojected to match DEM coordinate system (EPSG:26918).

### Data Sources

- **DEM**: `DEM/tif/DEM_UTM.tif` (EPSG:26918, 2556×1688 pixels)
- **NLCD**: `NLCD/nlcd2016_ny.tif` (2016 land cover, 15 classes)
- **CDL**: `CDL/CDL_2020_36.tif` (2020 cropland data, 41 classes)
- **Runoff**: `runoff_coefficient/runoff_coefficient.tif` (0.000-0.601 range)

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
