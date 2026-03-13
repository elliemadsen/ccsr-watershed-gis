import xarray as xr
import numpy as np
import gridded_data as GD
import geopandas as gpd
import rioxarray
import os
import datasets
import matplotlib.pyplot as plt
from rasterio.enums import Resampling
import gc

start_month = np.datetime64("2015-04")
half_month = np.datetime64("2020-01")
end_month = np.datetime64("2026-01")
months = np.arange(start_month, end_month) # SMAP Months

def process():
    modis = rioxarray.open_rasterio('MYD21A2.061_1km_aid0001.nc')
    modis_times = modis["time"].to_numpy()
    modis_x = modis["x"]
    modis_y = modis["y"]
    times = []
    for time in modis_times:
        iso = time.isoformat()
        times.append(np.datetime64(iso))
    times = np.array(times)

    times_months = times.astype("datetime64[M]")

    target_resolution = 30

    # Calculate dimensions based on target resolution

    intermediate = modis.rio.reproject("EPSG:26918")
    int_res = intermediate.rio.resolution()
    print(int_res)
    upscale = int_res[0] / target_resolution
    print(upscale)

    lst_day = intermediate["LST_Day_1KM"]
    lst_night = intermediate["LST_Night_1KM"]

    new_height, new_width = (int(lst_day.rio.height * upscale), int(lst_day.rio.width * upscale))

    def process_months(months_proc, monthly_name):
        cache = 'lst_cache.npz'
        if os.path.exists(cache):
            cached = np.load(cache)
            lst_monthly = cached['lst']
            new_x = cached['x']
            new_y = cached['y']
        else:
            i = 0
            new_x = None
            new_y = None
            lst_monthly = []
            for month in months_proc:
                print(f'Processing {month}')
                indices = np.where(times_months == month)
                days = lst_day.isel(time=indices[0])
                days_proj = days.rio.reproject(days.rio.crs, shape=(int(days.rio.height * upscale), int(days.rio.width * upscale)), resampling=Resampling.bilinear)
                nights = lst_night.isel(time=indices[0])
                nights_proj = nights.rio.reproject(nights.rio.crs, shape=(int(nights.rio.height * upscale), int(nights.rio.width * upscale)), resampling=Resampling.bilinear)
                days_and_nights = np.append(days_proj, nights_proj, axis=0)

                new_x = days_proj.x.to_numpy()
                new_y = days_proj.y.to_numpy()
        
                # There is a massive excess in the width direction, so let's clip it down to make it workable
                clip_x = np.where((new_x >= 468000) & (new_x <= 537000))
                new_x = new_x[clip_x]
                monthly_avg = np.nanmean(np.squeeze(days_and_nights[:,:,clip_x]), axis=0)
                lst_monthly.append(monthly_avg)

                del days, days_proj, nights, nights_proj, days_and_nights
                gc.collect()

                i += 1
            lst_monthly = np.array(lst_monthly)
            np.savez(cache, x=new_x, y=new_y, lst=lst_monthly)

        new_modis = xr.DataArray(
            data=lst_monthly,
            dims=["time","y","x"],
            coords=dict(
                x=new_x,
                y=new_y,
                time=months_proc
            )
        )
        new_modis.rio.to_raster(monthly_name)
        

    months_half = np.arange(start_month, half_month)
    process_months(months_half, 'lst_reproject_30m_monthly_1.tif')
    months_half = np.arange(half_month, end_month)
    process_months(months_half, 'lst_reproject_30m_monthly_2.tif')

def mask():
    lst_monthly = rioxarray.open_rasterio('lst_reproject_30m_monthly_1.tif')


def seasonals():
    lst_monthly = rioxarray.open_rasterio('lst_reproject_30m_monthly_1.tif')
    lst_monthly2 = rioxarray.open_rasterio('lst_reproject_30m_monthly_2.tif')
    monthly_data = lst_monthly.to_numpy()
    monthly_data2 = lst_monthly2.to_numpy()
    
    monthly_data = np.append(monthly_data, monthly_data2, axis=0)

    del lst_monthly2, monthly_data2
    gc.collect()

    # Seasonal
    _, lst_winter = GD.get_winter(months, monthly_data)
    winter = np.mean(lst_winter, axis=0)
    winter_modis = xr.DataArray(
        data=winter,
        dims=["y","x"],
        coords=dict(
            x=lst_monthly.x,
            y=lst_monthly.y
        )
    )
    winter_modis.rio.to_raster("lst_reproject_30m_djf.tif")

    _, lst_spring = GD.get_spring(months, monthly_data)
    spring = np.mean(lst_spring, axis=0)
    spring_modis = xr.DataArray(
        data=spring,
        dims=["y","x"],
        coords=dict(
            x=lst_monthly.x,
            y=lst_monthly.y
        )
    )
    spring_modis.rio.to_raster("lst_reproject_30m_mam.tif")

    _, lst_summer = GD.get_summer(months, monthly_data)
    summer = np.mean(lst_summer, axis=0)
    summer_modis = xr.DataArray(
        data=summer,
        dims=["y","x"],
        coords=dict(
            x=lst_monthly.x,
            y=lst_monthly.y
        )
    )
    summer_modis.rio.to_raster("lst_reproject_30m_jja.tif")

    _, lst_autumn = GD.get_autumn(months, monthly_data)
    autumn = np.mean(lst_autumn, axis=0)
    autumn_modis = xr.DataArray(
        data=autumn,
        dims=["y","x"],
        coords=dict(
            x=lst_monthly.x,
            y=lst_monthly.y
        )
    )
    autumn_modis.rio.to_raster("lst_reproject_30m_son.tif")

mask()