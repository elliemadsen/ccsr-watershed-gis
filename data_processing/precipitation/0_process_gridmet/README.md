# GRIDMET Precipitation Processing

This script processes GRIDMET daily precipitation data by aggregating to seasonal and monthly totals, computing multi-year seasonal means, reprojecting to UTM Zone 18N and resampling to 30 m using bilinear interpolation.

## Data Source

https://www.climatologylab.org/gridmet.html

gridMET is a dataset of daily high-spatial resolution (~4-km) surface meteorological data covering the contiguous US from 1979-yesterday.

## Usage

```bash
conda install numpy xarray rasterio scipy netCDF4
```

```bash
python process_gridmet.py
```

## What the script does

1. **Downloads GRIDMET data** - Fetches daily precipitation NetCDF files from 2006 to 2020
2. **Clips to watershed boundary** - Extracts data using the Subbasins shapefile with a 5km buffer
3. **Aggregates to seasons and months** - Computes both:
   - **Seasonal totals:**
     - DJF (Winter): December-January-February
     - MAM (Spring): March-April-May
     - JJA (Summer): June-July-August
     - SON (Fall): September-October-November
   - **Monthly totals:** Individual months for each year
4. **Multi-year averages** - Computes mean seasonal precipitation across all years (seasonal only)
5. **Reprojects to UTM** - Converts from WGS84 to UTM Zone 18N at 30m resolution using bilinear interpolation
6. **Quality check** - Validates output with basic statistics (min, max, mean, valid pixel count)

## Output files

**Raw data:** (`data/precipitation/raw/`)

- `precip_raw_4000m_{year}.nc`
  for years 1990-2026

**Seasonal averages** (`data/precipitation/processed/seasonal/`):

- `precip_final_30m_{year_range}_djf.tif` (Winter: December-January-February)
- `precip_final_30m_{year_range}_mam.tif` (Spring: March-April-May)
- `precip_final_30m_{year_range}_jja.tif` (Summer: June-July-August)
- `precip_final_30m_{year_range}_son.tif` (Fall: September-October-November)

where `{year_range}` is `2006-2020`

Each seasonal file contains the multi-year average precipitation in mm, reprojected to UTM Zone 18N at 30m resolution.

**Individual monthly totals** (`data/precipitation/processed/monthly/`):

- `precip_30m_2006_01.tif`, `precip_30m_2006_02.tif`, ... `precip_30m_2006_12.tif`
- `precip_30m_2007_01.tif`, `precip_30m_2007_02.tif`, ... `precip_30m_2007_12.tif`
- ... and so on through 2020

Each monthly file contains the total precipitation for that specific month in mm, reprojected to UTM Zone 18N at 30m resolution.

```

```
