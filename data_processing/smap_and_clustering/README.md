# SMAP Downsampling and Clustering
All the necessary dependencies are included in the [environment.yml](environment.yml) file for a conda setup.

## SMAP Downsampling
The main entrypoint here is [downsample_smap.py](downsample_smap.py). It is expecting the data inputs to be in this directory, or, if included as part of this git repo, then in its corresponding directory.

## Clustering
The main entrypoint here is [clustering.py](clustering.py). It is also expecting the data inputs to be in this directory, or, if included as part of the git repo, then in its corresponding directory.

## Datasets
All tifs that are not part of this repo are expected to be downloaded and in this directory, detailed below. In addition, it expects the Subbasins.shp shapefile in a directory called data/  

Downsampling:  
1. natag_mask.tif
1. smap_sm_reproject_9000m_monthly.tif
1. DEM_10m_gapfilled.tif
1. sand_r_reproject_30m.tif
1. TWI_30m.tif
1. lst_reproject_30m_monthly_1.tif and lst_reproject_30m_monthly_2.tif
1. lst_reproject_30m_djf.tif, lst_reproject_30m_mam, lst_reproject_30m_jja, lst_reproject_30m_son
1. NDVI_monthly_2015_2025-0000000000-0000000000.tif, NDVI_monthly_2015_2025-0000000000-0000002048.tif
1. ndvi_reproject_30m_djf.tif, ndvi_reproject_30m_mam, ndvi_reproject_30m_jja, ndvi_reproject_30m_son
1. smap_sm_reproject_9000m_djf.tif, smap_sm_reproject_9000m_mam.tif, smap_sm_reproject_9000m_jja.tif, smap_sm_reproject_9000m_son.tif

Clustering:  
1. natag_mask.tif
1. runoff_curve_number.tif
1. depth_restrictive_30m.tif
1. TWI_30m.tif
1. Outputs from downsampling