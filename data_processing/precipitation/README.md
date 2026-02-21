# GRIDMET Precipitation Processing

This script processes GRIDMET daily precipitation data according to the requirements:

Source: GRIDMET daily precipitation at ~4 km resolution. Download daily grids and aggregate to seasonal and monthly totals. Compute multi-year averages over the same period as SMAP data. (2015 - present)

Processing steps:
(1) Download GRIDMET data (automatically renamed to `precip_raw_4000m_YYYY.nc`)
(2) Aggregate to seasonal and monthly totals.
(3) Compute multi-year seasonal and monthly means.
(4) Reproject to UTM Zone 18N and resample to 30 m using bilinear interpolation.
(5) Quality check with basic statistics validation.

## File Naming Convention

**Raw data:** `data/precipitation/raw/precip_raw_4000m_YYYY.nc`

- Format: `precip_raw_4000m_{year}.nc`
- Resolution: ~4000m (4km)
- Source: GRIDMET daily precipitation (downloaded as `pr_YYYY.nc`, renamed on save)

**Processed data:** Organized into two subdirectories:

**Seasonal:** `data/precipitation/processed/seasonal/precip_final_30m_{year_range}_{season}.tif`

- Format: `precip_final_30m_{year_range}_{season}.tif`
- Example: `precip_final_30m_2015-2025_djf.tif`
- Seasons: djf, mam, jja, son
- Resolution: 30m
- CRS: EPSG:26918 (UTM Zone 18N)

**Monthly:** `data/precipitation/processed/monthly/precip_final_30m_{year_range}_{month}.tif`

- Format: `precip_final_30m_{year_range}_{month}.tif`
- Example: `precip_final_30m_2015-2025_01.tif`
- Months: 01-12 (January through December)
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

```bash and months** - Computes both:
   - **Seasonal totals:**
     - DJF (Winter): December-January-February
     - MAM (Spring): March-April-May
     - JJA (Summer): June-July-August
     - SON (Fall): September-October-November
   - **Monthly totals:** January (01) through December (12)
4. **Multi-year averages** - Computes mean seasonal and monthly precipitation across all years
5. **Reprojects to UTM** - Converts from WGS84 to UTM Zone 18N at 30m resolution using bilinear interpolation
6. **Quality check** - Validates output with basic statistics (min, max, mean, valid pixel count
3. **Aggregates to seasons** - Computes seasonal totals:
   - DJF (Winter): December-January-February
   - MAM (Spring): March-April-May
   - JJA (Summer): June-July-August
   - SON (Fall): September-October-November
4. **Multi-year averages** - Computes mean seasonal precipitation across all years
5. **Reprojects to UTM** - Converts from WGS84 to UTM Zone 18N at 30m resolution using bilinear interpolation
6. **Quality check** - Verifies orographic gradient (higher precipitation at higher elevations in NW)

## Output fileswo subdirectories:

**Seasonal averages** (`processed/seasonal/`):
- `precip_final_30m_{year_range}_djf.tif` (Winter: December-January-February)
- `precip_final_30m_{year_range}_mam.tif` (Spring: March-April-May)
- `precip_final_30m_{year_range}_jja.tif` (Summer: June-July-August)
- `precip_final_30m_{year_range}_son.tif` (Fall: September-October-November)

**Monthly averages** (`processed/monthly/`):
- `precip_final_30m_{year_range}_01.tif` through `precip_final_30m_{year_range}_12.tif`
- Each file represents the multi-year average for that month (01 = January, 12 = December)

where `{year_range}` is automatically determined from available data (e.g., `2015-2025`)

Each file contains the multi-year average precipitation in mm, reprojected to UTM Zone 18N at 30m resolution.

## Validation

Run `validate_seasonal_monthly.py` to verify that seasonal totals equal the sum of their constituent monthly totals:
- DJF = December + January + February
- MAM = March + April + May
- JJA = June + July + August
- SON = September + October + November

The validation script checks pixel-by-pixel alignment with a 0.1% tolerance threshold

Each file contains the multi-year seasonal average precipitation in mm, reprojected to UTM Zone 18N at 30m resolution.
```
