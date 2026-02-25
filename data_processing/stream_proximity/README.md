## Instructions

Source: Derived from the DEM (flow accumulation in 3.2).

Processing steps: To make a stream network, set a threshold: any cell with flow accumulation above that threshold is classified as "stream," everything else is "not stream." The result is a binary raster — 1 for stream, 0 for everything else.

1. Convert flow accumulation to total contributing area (A, m²):
   - A = flow_accum × cell_area
   - For a 10 m DEM: cell_area = 100 m²

2. Define binary raster: stream = 1 if (A > threshold), 0 otherwise.

3. Compute stream networks at thresholds of 25, 50, 75, 100 ha (thresholds must be converted to m² before comparison)

4. Overlay derived stream network on NHD (download NHD from nhd.usgs.gov) flowlines and verify reasonable agreement. Check that near-stream agricultural areas show low distance values. Minor mismatches in headwater extent are fine.

5. Calculate Euclidean distance in ArcGIS or in Python (scipy.ndimage.distance_transform_edt) applied to an inverted stream raster (streams must be 0, non-streams must be 1).
   - The output is a raster where each cell's value is its distance in meters to the nearest stream.
   - Cells right next to a stream get values close to 0, cells on distant ridgetops get values of several kilometers.

## Installation

**Dependencies:**

- `whitebox` - D-infinity flow accumulation
- `scipy` - Euclidean distance transform
- `rasterio` - Raster I/O
- `geopandas` - Vector data handling

```bash
# Install via pip
pip install whitebox scipy rasterio geopandas
```

## Usage

```bash
# D-infinity flow accumulation (recommended)
python process_stream_proximity.py
```

## What the script does

1. **Calculates flow accumulation** - Uses WhiteboxTools D-infinity algorithm (Tarboton 1997) for more accurate flow routing
2. **Converts to contributing area** - Multiplies flow accumulation by cell area (100 m² for 10m DEM)
3. **Generates stream networks** - Creates binary rasters at 25, 50, 75, 100 ha thresholds
4. **Calculates distances** - Computes Euclidean distance to nearest stream for each threshold
5. **Crops to watershed** - All outputs are clipped to the sub-basins boundary

## Input Data

- DEM: `data/DEM/processed/DEM_10m_gapfilled.tif`
- Watershed boundary: `data/sub-basins/Subbasins.shp`
- NHD data (optional, for validation): `data/hydrography/` (HUC4 region 0204)

## Output files

All outputs are cropped to the watershed boundary and saved in `data/stream_proximity/`:

**Flow accumulation** (`flow_accumulation/`):

- `flow_accumulation.tif` - D-infinity flow accumulation (cells)

**Stream networks** (`stream_networks/`):

- `stream_network_25ha.tif` - Binary stream network (25 ha threshold)
- `stream_network_50ha.tif` - Binary stream network (50 ha threshold)
- `stream_network_75ha.tif` - Binary stream network (75 ha threshold)
- `stream_network_100ha.tif` - Binary stream network (100 ha threshold)

**Distance rasters** (`stream_distance/`):

- `stream_distance_25ha.tif` - Distance to nearest stream in meters (25 ha)
- `stream_distance_50ha.tif` - Distance to nearest stream in meters (50 ha)
- `stream_distance_75ha.tif` - Distance to nearest stream in meters (75 ha)
- `stream_distance_100ha.tif` - Distance to nearest stream in meters (100 ha)

**TWI-based alternative** (`twi/`):

- `process_twi_stream_proximity.py` uses Topographic Wetness Index raster as input instead of running D-infinity flow accumulation algorithm
- outputs to `twi/stream_networks/` and `twi/stream_distance/` with filenames like `stream_network_twi12.tif`
