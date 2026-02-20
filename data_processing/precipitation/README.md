# GRIDMET Precipitation Processing

This script processes GRIDMET daily precipitation data according to the requirements:

Source: GRIDMET daily precipitation at ~4 km resolution. Download daily grids and aggregate to seasonal totals (DJF, MAM, JJA, SON). Compute multi-year seasonal averages over the same period as SMAP data. (2015 - present)

Processing steps:
(1) Download GRIDMET data (automatically renamed to `precip_raw_4000m_YYYY.nc`)
(2) Aggregate to seasonal totals.
(3) Compute multi-year seasonal means.
(4) Reproject to UTM Zone 18N and resample to 30 m using bilinear interpolation.

Quality check: Verify orographic gradient — higher elevations in the northwest of the watershed should show higher precipitation.

## File Naming Convention

**Raw data:** `data/precipitation/raw/precip_raw_4000m_YYYY.nc`

- Format: `precip_raw_4000m_{year}.nc`
- Resolution: ~4000m (4km)
- Source: GRIDMET daily precipitation (downloaded as `pr_YYYY.nc`, renamed on save)

**Processed data:** `data/precipitation/processed/precip_final_30m_{year_range}_{season}.tif`

- Format: `precip_final_30m_{year_range}_{season}.tif`
- Example: `precip_final_30m_2015-2025_djf.tif`
- Seasons: djf, mam, jja, son
- Resolution: 30m
- CRS: EPSG:26918 (UTM Zone 18N)

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

- `precip_final_30m_{year_range}_djf.tif` (Winter: December-January-February)
- `precip_final_30m_{year_range}_mam.tif` (Spring: March-April-May)
- `precip_final_30m_{year_range}_jja.tif` (Summer: June-July-August)
- `precip_final_30m_{year_range}_son.tif` (Fall: September-October-November)

where `{year_range}` is automatically determined from available data (e.g., `2015-2025`)

Each file contains the multi-year seasonal average precipitation in mm, reprojected to UTM Zone 18N at 30m resolution.
