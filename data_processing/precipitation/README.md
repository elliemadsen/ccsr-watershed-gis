# GRIDMET Precipitation Processing

This script processes GRIDMET daily precipitation data according to the requirements:

Source: GRIDMET daily precipitation at ~400 m resolution. Download daily grids and aggregate to seasonal totals (DJF, MAM, JJA, SON). Compute multi-year seasonal averages over the same period as SMAP data. (2015 - present)

Processing steps:
(1) Find and upload GRIDMET data
(2) Aggregate to seasonal totals.
(3) Compute multi-year seasonal means.
(4) Reproject to UTM Zone 18N and resample to 30 m using bilinear interpolation.

Quality check: Verify orographic gradient — higher elevations in the northwest of the watershed should show higher precipitation.

## Data Source

https://www.climatologylab.org/gridmet.html

gridMET is a dataset of daily high-spatial resolution (~4-km, 1/24th degree) surface meteorological data covering the contiguous US from 1979-yesterday. These data are updated daily.

## Installation

```bash
conda install numpy xarray rasterio scipy netCDF4
```

## Usage

```bash
python process_gridmet.py
```

## What the script does

1. **Downloads GRIDMET data** - Fetches daily precipitation NetCDF files from 2015 to present
2. **Clips to watershed boundary** - Extracts data using the Subbasins shapefile with a 5km buffer
3. **Aggregates to seasons** - Computes seasonal totals:
   - DJF (Winter): December-January-February
   - MAM (Spring): March-April-May
   - JJA (Summer): June-July-August
   - SON (Fall): September-October-November
4. **Multi-year averages** - Computes mean seasonal precipitation across all years
5. **Reprojects to UTM** - Converts from WGS84 to UTM Zone 18N at 30m resolution using bilinear interpolation
6. **Quality check** - Verifies orographic gradient (higher precipitation at higher elevations in NW)

## Output files

The script creates GeoTIFF files in the `processed/` directory:

- `precip_final_30m_djf.tif`
- `precip_final_30m_jja.tif`
- `precip_final_30m_mam.tif`
- `precip_final_30m_son.tif`

Each file contains the multi-year seasonal average precipitation in mm, reprojected to UTM Zone 18N at 30m resolution.
