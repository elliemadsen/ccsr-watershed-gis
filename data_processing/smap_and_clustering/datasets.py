import gridded_data as GD
import os
import numpy as np
import xarray as xr
import rioxarray
import glob

def read_gridmet(start_month, end_month, path='../../data/precipitation/processed/monthly'):
    tiffs = glob.glob(os.path.join(path, "*"))
    times = []
    datalist = []
    for tiff in tiffs:
        date = f'20{tiff[-9:-4]}'
        time = np.datetime64(date.replace("_", '-'))
        if time < start_month or time >= end_month:
            continue
        times.append(time)

        dataset = xr.open_dataset(tiff)
        transform = dataset.rio.transform()
        lats = dataset["y"].to_numpy()
        lons = dataset["x"].to_numpy()
        data = dataset["band_data"].to_numpy()
        data = np.where(data == -9999, np.nan, data) # Replace the fill value with nans
        datalist.append(np.squeeze(data))
    times = np.array(times)
    precip = np.array(datalist)
    x, y = np.meshgrid(lons, lats)
    return GD.TimeGriddedData(times, y, x, precip, transform)

def read_tif(path, fill_val=None, times=None):
    raster = rioxarray.open_rasterio(path)
    transform = raster.rio.transform()
    raster_lat = raster.y.to_numpy()
    raster_lon = raster.x.to_numpy()
    raster_x, raster_y = np.meshgrid(raster_lon, raster_lat)
    raster = raster.to_numpy()
    if fill_val is not None:
        raster = np.where(raster == fill_val, np.nan, raster) # Replace the fill value with nans

    if times is not None:
        return GD.TimeGriddedData(times, raster_y, raster_x, raster, transform)
    else:
        raster = np.squeeze(raster)
        return GD.GriddedData(raster_y, raster_x, raster, transform)

def read_ndvi(ndvi1_path='NDVI_monthly_2015_2025-0000000000-0000000000.tif', ndvi2_path='NDVI_monthly_2015_2025-0000000000-0000002048.tif'):
    ndvi1 = xr.open_dataset(ndvi1_path)
    ndvi2 = xr.open_dataset(ndvi2_path)
    transform = ndvi1.rio.transform()
    x1 = ndvi1.x.to_numpy()
    x2 = ndvi2.x.to_numpy()
    xvals = np.append(x1,x2)
    yvals = ndvi1.y.to_numpy() # Y's are the same

    data1 = ndvi1.band_data.isel(band=np.arange(3,132)).to_numpy()
    data2 = ndvi2.band_data.isel(band=np.arange(3,132)).to_numpy()
    new_data = np.append(data1, data2, axis=2)

    start_month = np.datetime64("2015-04")
    end_month = np.datetime64("2026-01") # Exclusive
    times = np.arange(start_month, end_month)
    raster_x, raster_y = np.meshgrid(xvals, yvals)
    return GD.TimeGriddedData(times, raster_y, raster_x, new_data, transform)

def read_ndvi_indices(indices = np.arange(3,132), ndvi1_path='NDVI_monthly_2015_2025-0000000000-0000000000.tif', ndvi2_path='NDVI_monthly_2015_2025-0000000000-0000002048.tif'):
    ndvi1 = xr.open_dataset(ndvi1_path)
    ndvi2 = xr.open_dataset(ndvi2_path)
    transform = ndvi1.rio.transform()
    x1 = ndvi1.x.to_numpy()
    x2 = ndvi2.x.to_numpy()
    xvals = np.append(x1,x2)
    yvals = ndvi1.y.to_numpy() # Y's are the same

    data1 = ndvi1.band_data.isel(band=indices).to_numpy()
    data2 = ndvi2.band_data.isel(band=indices).to_numpy()
    new_data = np.append(data1, data2, axis=2)

    start_month = np.datetime64("2015-01")
    end_month = np.datetime64("2026-01") # Exclusive
    times = np.arange(start_month, end_month)
    times = times[indices]
    raster_x, raster_y = np.meshgrid(xvals, yvals)
    return GD.TimeGriddedData(times, raster_y, raster_x, new_data, transform)

def read_lst(lst1_path='lst_reproject_30m_monthly_1.tif', lst2_path='lst_reproject_30m_monthly_2.tif'):
    lst_monthly = rioxarray.open_rasterio(lst1_path)
    lst_monthly2 = rioxarray.open_rasterio(lst2_path)
    transform = lst_monthly.rio.transform()
    monthly_data = lst_monthly.to_numpy()
    monthly_data2 = lst_monthly2.to_numpy()
    x = lst_monthly.x.to_numpy()
    y = lst_monthly.y.to_numpy()
    
    monthly_data = np.append(monthly_data, monthly_data2, axis=0)
    start_month = np.datetime64("2015-04")
    end_month = np.datetime64("2026-01") # Exclusive
    times = np.arange(start_month, end_month)
    raster_x, raster_y = np.meshgrid(x, y)
    return GD.TimeGriddedData(times, raster_y, raster_x, monthly_data, transform)
