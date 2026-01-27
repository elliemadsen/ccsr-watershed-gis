# ccsr-watershed-gis

3D terrain visualization with PyVista, draping DEM elevation and multiple raster overlays (NLCD landcover, CDL cropland, runoff coefficients).

## Usage

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

### Data Sources

- **DEM**: `DEM/tif/DEM_UTM.tif` (EPSG:26918)
- **NLCD**: `NLCD/nlcd2016_ny.tif` (2016 landcover)
- **CDL**: `CDL/CDL_2020_36.tif` (2020 cropland data)
- **Runoff**: `runoff_coefficient/runoff_coefficient.tif`

### Examples

```bash
# Launch interactive viewer with toggles and slider (default)
python watershed3d.py

# CDL coloring only with 2x vertical exaggeration
python watershed3d.py --color cdl --scale_z 2

# NLCD with export
python watershed3d.py --color nlcd --export
```
