# ccsr-watershed-gis

Simple PyVista-based viewer to drape DEM elevation or NLCD landcover over terrain.

## Usage

From the repository root:

```bash
python watershed3d.py [--color elevation|nlcd] [--scale_z FACTOR] [--export]
```

### Arguments

- `--color` (default: `elevation`)
  - `elevation`: colors by DEM elevation.
  - `nlcd`: colors by NLCD landcover (auto reprojects/resamples to DEM grid).
- `--scale_z FACTOR` (default: `1.0`)
  - Vertical exaggeration applied to terrain geometry (colors still use original elevations).
- `--export`
  - When set, saves `outputs/watershed_dem_<color>.html` (interactive) and `.png`.

### Data

- DEM path: `DEM/tif/DEM_UTM.tif`
- NLCD path: `NLCD/nlcd2016_ny.tif`

### Examples

```bash
# Elevation, no exaggeration, no export
python watershed3d.py

# Elevation with 3x vertical exaggeration
python watershed3d.py --scale_z 3

# NLCD coloring with export
python watershed3d.py --color nlcd --export
```
